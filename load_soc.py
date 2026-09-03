import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.environ['VAERS_DATABASE_URL'])

# add soc columns to symptoms table
years = [2025]

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
    print(df.iloc[0:20,1])

    return df

#print(list(encode_soc_symptoms(y).head() for y in years))
encode_soc_symptoms(2026)

