"""
Module d'extraction des sources de donnees brutes.
"""

import json
import logging

import pandas as pd

from config.settings import FILES

logger = logging.getLogger("mexora_etl")


def extract_commandes(filepath: str | None = None) -> pd.DataFrame:
    """Extrait les commandes depuis le CSV source."""
    path = filepath or str(FILES["commandes"])
    df = pd.read_csv(path, encoding="utf-8", dtype=str)
    logger.info(f"[EXTRACT] Commandes : {len(df)} lignes extraites depuis {path}")
    return df


def extract_produits(filepath: str | None = None) -> pd.DataFrame:
    """Extrait les produits depuis le fichier JSON."""
    path = filepath or str(FILES["produits"])
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data["produits"])
    logger.info(f"[EXTRACT] Produits : {len(df)} lignes extraites depuis {path}")
    return df


def extract_clients(filepath: str | None = None) -> pd.DataFrame:
    """Extrait les clients depuis le CSV source."""
    path = filepath or str(FILES["clients"])
    df = pd.read_csv(path, encoding="utf-8", dtype=str)
    logger.info(f"[EXTRACT] Clients : {len(df)} lignes extraites depuis {path}")
    return df


def extract_regions(filepath: str | None = None) -> pd.DataFrame:
    """Extrait le referentiel geographique depuis le CSV source."""
    path = filepath or str(FILES["regions"])
    df = pd.read_csv(path, encoding="utf-8")
    logger.info(f"[EXTRACT] Regions : {len(df)} lignes extraites depuis {path}")
    return df
