import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.environ['VAERS_DATABASE_URL'])

def get_top_symptoms(year, limit=20):
    vintage = f"symptoms_{str(year)}"
    query = f"""
        SELECT symptom, COUNT(*) AS reports
        FROM (
            SELECT "SYMPTOM1" AS symptom FROM {vintage}
            UNION ALL
            SELECT "SYMPTOM2" FROM {vintage}
            UNION ALL
            SELECT "SYMPTOM3" FROM {vintage}
            UNION ALL
            SELECT "SYMPTOM4" FROM {vintage}
            UNION ALL
            SELECT "SYMPTOM5" FROM {vintage}
        ) AS all_symptoms
        WHERE symptom IS NOT NULL
        AND symptom NOT LIKE '%No adverse event%'
        GROUP BY symptom
        ORDER BY reports DESC
        LIMIT %(limit)s;
    """
    return pd.read_sql(query, engine, params={"limit": limit})

