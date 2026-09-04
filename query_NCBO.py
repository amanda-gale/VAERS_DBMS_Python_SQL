"""This script gathers all distinct symptoms from the symptoms tables and retrieves their soc categories using MedDRA
codes, mapping each unique symptom to a category. This data is used to build a lookup table which is saved to Neon."""

import requests
import time
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
engine = create_engine(
    os.getenv("VAERS_DATABASE_URL"),
    pool_pre_ping=True,   # the API loop runs for hours; pooled connections go stale
    pool_recycle=1800,
)

# --- NCBO BioPortal config ---
# Free API key from: https://bioportal.bioontology.org/account
BIOPORTAL_API_KEY = os.getenv("BIOPORTAL_API_KEY")
BASE_URL = "https://data.bioontology.org"
HEADERS = {"Authorization": f"apikey token={BIOPORTAL_API_KEY}"}


def get_unique_symptoms(year: int) -> list[str]:
    """Pull all unique symptom terms from a given year's symptoms table."""
    query = """
    SELECT DISTINCT symptom FROM (
                SELECT "SYMPTOM1" AS symptom FROM symptoms_%(year)s
                UNION ALL
                SELECT "SYMPTOM2" FROM symptoms_%(year)s
                UNION ALL
                SELECT "SYMPTOM3" FROM symptoms_%(year)s
                UNION ALL
                SELECT "SYMPTOM4" FROM symptoms_%(year)s
                UNION ALL
                SELECT "SYMPTOM5" FROM symptoms_%(year)s
            ) AS all_symptoms
    WHERE symptom IS NOT NULL AND symptom != ''"""

    symptoms = pd.read_sql(query, engine, params={"year": year})
    symptoms_list = symptoms["symptom"].tolist()

    return symptoms_list


def lookup_soc(symptom_term: str) -> dict:
    """
    Query the NCBO BioPortal API to find the SOC for a MedDRA PT term.
    Returns a dict with the term, its MedDRA code, and its SOC.
    """
    params = {
        "q": symptom_term,
        "ontologies": "MEDDRA",

        "exact_match": "true",  # PT terms in VAERS are already standardized
        "include": "prefLabel",
    }

    try:
        response = requests.get(
            f"{BASE_URL}/search",
            headers=HEADERS,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("collection", [])
        if not results:
            return {"symptom": symptom_term, "soc": "Unmapped", "meddra_code": None}

        # Take the first (best) match
        match = results[0]
        pref_label = match.get("prefLabel", symptom_term)
        class_id = match.get("@id", "")  # e.g. "http://purl.bioontology.org/ontology/MEDDRA/10016558"
        meddra_code = class_id.split("/")[-1] if class_id else None

        # Now fetch ancestors to find the SOC (highest level = SOC)
        soc = get_soc_from_ancestors(class_id)

        return {
            "symptom": symptom_term,
            "pref_label": pref_label,
            "meddra_code": meddra_code,
            "soc": soc
        }

    except requests.RequestException as e:
        print(f"  API error for '{symptom_term}': {e}")
        return {"symptom": symptom_term, "soc": "API_Error", "meddra_code": None}


def get_soc_from_ancestors(class_id: str) -> str:
    """
    Walk the MedDRA hierarchy upward from a PT to find its SOC.
    MedDRA hierarchy: PT -> HLT -> HLGT -> SOC
    The SOC is the ancestor with no parents (root of its branch).
    """
    if not class_id:
        return "Unknown"

    encoded_id = requests.utils.quote(class_id, safe="")
    url = f"{BASE_URL}/ontologies/MEDDRA/classes/{encoded_id}/ancestors"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        ancestors = response.json()

        # Ancestors are returned from immediate parent up to root.
        # The last ancestor is the SOC (highest level).
        if ancestors:
            soc_entry = ancestors[-1]  # SOC is at the top of the hierarchy
            return soc_entry.get("prefLabel", "Unknown")
        return "Unknown"

    except requests.RequestException as e:
        print(f"  Ancestor lookup error: {e}")
        return "Unknown"


def build_lookup_table(year: int, delay: float = 0.5):
    """
    Main function: fetch all unique symptoms for a year,
    look up each one's SOC, and saves results as a csv.

    delay: seconds to wait between API calls (be a good citizen)
    """

    if os.path.isfile(f"symptom_soc_lookup_{year}.csv"):
        df = pd.read_csv(f"symptom_soc_lookup_{year}.csv")
    else:
        print(f"Fetching unique symptoms for {year}...")
        symptoms = get_unique_symptoms(year)
        #symptoms = symptoms[:10]
        print(f"Found {len(symptoms)} unique symptom terms.")

        results = []
        for i, symptom in enumerate(symptoms):
            print(f"  [{i + 1}/{len(symptoms)}] Looking up: {symptom}")
            result = lookup_soc(symptom)
            results.append(result)
            time.sleep(delay)  # Rate limiting — BioPortal is a shared public resource

        df = pd.DataFrame(results)

        # Checkpoint to disk first — the API loop above is too expensive to redo
        # if the database write fails.
        csv_path = os.path.join(os.path.dirname(__file__), f"symptom_soc_lookup_{year}.csv")
        df.to_csv(csv_path, index=False)
        print(f"Checkpointed {len(df)} rows to {csv_path}")

    # compile all symptom
    print(f"Number of unique symptoms for {year}: {len(df)}")
    compile_tables(df)

    # write table to neon
    upload_csv_to_neon()

    # print(f"\nResults summary:")
    # print(df["soc"].value_counts())

    return df


def compile_tables(df: pd.DataFrame):
    """
    Compiles all symptoms tables.
    """

    file_path = "symptom_soc_lookup.csv"

    if not os.path.exists(file_path):
        # File doesn't exist yet — just write the new data
        df.to_csv(file_path, index=False)
    else:
        # File exists — load it, combine, deduplicate, save
        existing = pd.read_csv(file_path)
        combined = pd.concat([existing, df]).drop_duplicates(subset="symptom")
        combined.to_csv(file_path, index=False)
        print(f"Number of unique symptoms for all years: {len(combined)}")

    print(f"Added data from year {year} to master table.")


def upload_csv_to_neon():
    """
    Uploads the complete soc lookup table to neon.
    """
    data = pd.read_csv("symptom_soc_lookup.csv")
    data.to_sql(f"symptom_soc_lookup", engine, if_exists="replace", index=False)
    print("\nLookup table written to PostgreSQL as 'symptom_soc_lookup'.")


if __name__ == "__main__":

    years = [2025, 2026]

    # build the soc symptom table by year
    for year in years:
        print(f"\nStarting year {year}...")
        build_lookup_table(year)

