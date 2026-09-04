"""This script handles categorizing the raw symptoms data by its soc categories and saving the data to neon."""

import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.environ['VAERS_DATABASE_URL'])


def encode_soc_symptoms(year: int):
    # make new table called soc_symptoms_year
    # left join soc_lookup on symptoms_year
    # include only columns VAERS_ID, symptom 1-5, s0c 1-5
    query = text(f"""
    SELECT
    s."VAERS_ID",
    l1.soc AS soc_symtpom1,
    l2.soc AS soc_symptom2,
    l3.soc AS soc_symptom3,
    l4.soc AS soc_symptom4,
    l5.soc AS soc_symptom5
    FROM symptoms_{year} s
    LEFT JOIN symptom_soc_lookup l1 ON l1.symptom = s."SYMPTOM1"
    LEFT JOIN symptom_soc_lookup l2 ON l2.symptom = s."SYMPTOM2"
    LEFT JOIN symptom_soc_lookup l3 ON l3. symptom = s."SYMPTOM3"
    LEFT JOIN symptom_soc_lookup l4 on l4.symptom = s."SYMPTOM4"
    LEFT JOIN symptom_soc_lookup l5 on l5.symptom = s."SYMPTOM5"
    """)

    df = pd.read_sql(query, engine)
    print(df.head(10))
    print(f"Symptoms encoded from year {year}.")
    store_encoded_table(df, year)
    return df


def store_encoded_table(df, year):

    df.to_sql(f"soc_symptoms_{year}", engine, if_exists="replace", index=False)
    print("Table saved to Neon.")


if __name__ == "__main__":
    years = [2026]
    #print(list(encode_soc_symptoms(y).head() for y in years))
    for year in years:
        encode_soc_symptoms(year)

