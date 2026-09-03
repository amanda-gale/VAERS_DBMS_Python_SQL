from dotenv import load_dotenv
import os
import pandas as pd
from sqlalchemy import create_engine

print("Enter the year of new data to upload.")
year= str(input())

try:
    matches = [f for f in os.listdir("./data") if year in f]
    if len(matches) == 3:
        print(f"Found all files for this year's data.")
        for f in matches:
            print(f"  {f}")
    elif len(matches) == 0:
        print("No files found for this year.")
    else:
        print(f"Improper number of files found for this year's data.")
except FileNotFoundError:
    print("Directory not found.")

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))   # fetch environment variable
engine = create_engine(os.getenv("VAERS_DATABASE_URL"))    # create engine from env

df_data = pd.read_csv(f'data/{year}VAERSDATA.csv', encoding='windows-1252')
df_symptoms = pd.read_csv(f'data/{year}VAERSSYMPTOMS.csv', encoding='windows-1252')
df_vax = pd.read_csv(f'data/{year}VAERSVAX.csv', encoding='windows-1252')

df_data.to_sql(f'data_{year}', engine, if_exists='replace', index=False)
df_symptoms.to_sql(f'symptoms_{year}', engine, if_exists='replace', index=False)
df_vax.to_sql(f'vax_{year}', engine, if_exists='replace', index=False)

print(f"Database populated with VAERs vaccine side effects report data from year {year}.")

