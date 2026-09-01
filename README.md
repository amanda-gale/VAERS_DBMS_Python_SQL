# VAERS Adverse Event Explorer

## Author Information
**Name**: Amanda Gale  
**Institution**: Northeastern University  

## Project Report Access URL
https://agale-vaers-explorer.streamlit.app/

## Project Description
An end-to-end data engineering portfolio project analyzing vaccine adverse event reports from the 
CDC/FDA Vaccine Adverse Event Reporting System (VAERS). The project demonstrates a full pipeline from raw 
public data ingestion through to an interactive analytical dashboard.

## Dataset Information
Data was obtained from the [CDC/FDA Vaccine Adverse Event Reporting System (VAERS)](https://vaers.hhs.gov/data/datasets.html).
Data from the source is separated by year and each year contains three table tables containing pertinent information 
regarding patient data, description of symptoms, and vaccine information, respectively. Manipulation of these tables
and creation of new tables is necessary and ongoing for analytical purposes. 

VAERS is a passive surveillance system — reports are submitted voluntarily by patients, healthcare providers, and 
manufacturers. A report of an adverse event following vaccination does not imply that the vaccine caused the event. 
The dataset reflects reported associations only, not established causation. This limitation is a known characteristic 
of passive pharmacovigilance systems and is important context for interpreting any findings from this data.

---

## Project Structure

```
vaers_project/
├── .gitignore            # Excludes .env and other sensitive files from Git
├── load_data.py          # One-time data ingestion script (run manually)
├── query_data.py            # Reusable query functions
├── app.py                # Streamlit dashboard application
├── requirements.txt      # Python library requirements for Streamlit to reference
└── README.md
```

### Architecture Overview

This project separates concerns across three distinct layers:

**1. Ingestion layer — `load_data.py`**
Reads raw VAERS CSV files from local disk and loads them into a hosted PostgreSQL database (Neon). This script is run 
manually by the project author when adding or refreshing data. It is not part of the live application and is not exposed 
to end users. Credentials are sourced from a local `.env` file that is excluded from version control.

**2. Query layer — `query_data.py`**
Contains reusable Python functions that issue SQL queries against the database and return pandas DataFrames. Keeping 
query logic here, separate from the display layer, makes it independently testable and easier to maintain.

**3. Presentation layer — `app.py`**
A Streamlit application that imports from `query_data.py` and renders results as interactive charts and tables. Deployed 
via Streamlit Community Cloud, which injects database credentials securely at runtime through its secrets management 
system — credentials never appear in source code.

---

## Credential & Access Management

This project follows the standard pattern of separating credentials from code:

| Environment | Credential Source |
|---|---|
| Local development | `.env` file (not committed to GitHub) |
| Production (Streamlit Cloud) | Streamlit secrets dashboard |

The database user configured for the Streamlit application is **read-only**. This means the live dashboard can query 
data but cannot modify or delete it, even if the connection string were somehow exposed.

Only the project author, with access to the local `.env` file, can write data to the database via `load_data.py`.

---

## Running Locally

If one desires to run this locally for the sake of running their own queries, they are encourages to create
their own Neon/Streamlit accounts and .env file within the directory and populate their own database. 

**Prerequisites:** Python 3.8+, PostgreSQL client libraries, a Neon (or other hosted PostgreSQL) account.

**1. Clone the repository**
```bash
git clone https://github.com/amanda-gale/vaers-explorer.git
cd vaers-explorer
```

**2. Install dependencies**
```bash
pip install pandas sqlalchemy psycopg2-binary streamlit python-dotenv
```

**3. Configure credentials**

Create a `.env` file in the project root:
```
VAERS_DATABASE_URL=postgresql://user:password@your-neon-host.neon.tech/dbname
```

**4. Download VAERS data**

Download annual CSV files from [vaers.hhs.gov](https://vaers.hhs.gov/data/datasets.html) and place them in a `data/` directory.

**5. Populate the database**
```bash
python load_data.py
```
The ingestion script creates one set of tables per year (e.g. `data_2025`, `data_2026`). To add a new year, 
download the corresponding VAERS CSVs, update the file paths in `load_data.py`, and run it again. 
The Streamlit dashboard includes a year selector for side-by-side comparison of adverse event patterns across years.

**6. Link Streamlit Authentication**
Instructions for this can be found on the [Streamlit Community Cloud Website](https://streamlit.io/cloud).

**7. Customize Queries**
Edit the file query_data.py to include custom queries. Edit the app.py file to include these queries.

**8. Launch the app**
```bash
streamlit run app.py
```

