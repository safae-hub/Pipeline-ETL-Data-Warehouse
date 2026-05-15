"""
Configuration centralisee du pipeline ETL Mexora.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / ".." / "data"
LOGS_DIR = BASE_DIR / ".." / "logs"
LOGS_DIR.mkdir(exist_ok=True)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "mexora_dwh")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "123")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

SCHEMA_STAGING = "staging_mexora"
SCHEMA_DWH = "dwh_mexora"
SCHEMA_REPORTING = "reporting_mexora"

FILES = {
    "commandes": DATA_DIR / "commandes_mexora.csv",
    "produits": DATA_DIR / "produits_mexora.json",
    "clients": DATA_DIR / "clients_mexora.csv",
    "regions": DATA_DIR / "regions_maroc.csv",
}
