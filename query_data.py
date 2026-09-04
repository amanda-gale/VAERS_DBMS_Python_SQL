"""This script contains the queries used to build the streamlit dashboard interactive website."""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.environ['VAERS_DATABASE_URL'])


def get_top_symptoms(year, limit=20):

    symptom_table = f"symptoms_{year}"
    query = text(f"""
        SELECT symptom, COUNT(*) AS reports
        FROM (
            SELECT "SYMPTOM1" AS symptom FROM {symptom_table}
            UNION ALL
            SELECT "SYMPTOM2" FROM {symptom_table}
            UNION ALL
            SELECT "SYMPTOM3" FROM {symptom_table}
            UNION ALL
            SELECT "SYMPTOM4" FROM {symptom_table}
            UNION ALL
            SELECT "SYMPTOM5" FROM {symptom_table}
        ) AS all_symptoms
        WHERE symptom IS NOT NULL
        AND symptom NOT LIKE '%No adverse event%'
        GROUP BY symptom
        ORDER BY reports DESC
        LIMIT {int(limit)};
    """)
    return pd.read_sql(query, engine)


def get_top_categories(year, limit=20):
    soc_table = f"soc_symptoms_{int(year)}"
    query = text(f"""
        SELECT soc_category, COUNT(*) as reports
        FROM (
            SELECT soc_symptom1 as soc_category FROM {soc_table}
            UNION ALL
            SELECT soc_symptom2 FROM {soc_table}
            UNION ALL
            SELECT soc_symptom3 FROM {soc_table}
            UNION ALL
            SELECT soc_symptom4 FROM {soc_table}
            UNION ALL
            SELECT soc_symptom5 FROM {soc_table}
        ) AS all_categories
        WHERE soc_category IS NOT NULL
        GROUP BY soc_category
        ORDER BY reports DESC
        LIMIT {int(limit)};
    """)
    return pd.read_sql(query, engine)


