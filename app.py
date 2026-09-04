"""This script runs all queries of the VAERS data and uses it to launch the Streamlit app."""

import streamlit as st

st.title("VAERS DBMS Python App")

import streamlit as st
from query_data import get_top_symptoms

### set years that dashboard will encompass
year = st.selectbox("Select year", [2025, 2026])
#year=2025

### page title
st.title(f"VAERS {year} Vaccine Adverse Event Explorer")

### run queries from the query_data.py file to produce analyses

# top reported symptoms
st.header("Top Reported Symptoms")
df = get_top_symptoms(year=year, limit=20)
st.bar_chart(df.set_index("symptom"))

