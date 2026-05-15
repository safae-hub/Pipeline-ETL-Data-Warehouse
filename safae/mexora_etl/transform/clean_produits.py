"""
Nettoyage des produits Mexora avec gestion SCD Type 2.
"""

import logging
from datetime import date

import pandas as pd

logger = logging.getLogger("mexora_etl")


def transform_produits(df: pd.DataFrame) -> pd.DataFrame:
    """
    Regles :
      R1 - Standardisation des categories (casse uniforme : title case)
      R2 - Remplacement des prix catalogue NULL par le prix median de la sous-categorie
      R3 - Initialisation des colonnes SCD Type 2
    """
    initial = len(df)

    # R1 — Standardisation categories
    before = df["categorie"].nunique()
    df["categorie"] = df["categorie"].str.strip().str.title()
    after = df["categorie"].nunique()
    logger.info(f"[TRANSFORM] R1 categories : {before - after} variantes fusionnees ({before} -> {after})")

    # Standardisation sous-categorie
    df["sous_categorie"] = df["sous_categorie"].str.strip().str.title()
    df["marque"] = df["marque"].str.strip()
    df["fournisseur"] = df["fournisseur"].str.strip()

    # R2 — Prix catalogue NULL
    nb_null = df["prix_catalogue"].isna().sum()
    if nb_null > 0:
        df["prix_catalogue"] = pd.to_numeric(df["prix_catalogue"], errors="coerce")
        medianes = df.groupby("sous_categorie")["prix_catalogue"].transform("median")
        df["prix_catalogue"] = df["prix_catalogue"].fillna(medianes)
        # Si toujours null (sous-categorie inconnue), fallback global
        global_median = df["prix_catalogue"].median()
        df["prix_catalogue"] = df["prix_catalogue"].fillna(global_median)
        logger.info(f"[TRANSFORM] R2 prix : {nb_null} prix catalogue NULL remplaces par mediane sous-categorie")

    # R3 — SCD Type 2 : initialisation
    df["date_debut"] = pd.to_datetime(df.get("date_debut", date(2020, 1, 1)))
    df["date_fin"] = pd.Timestamp("9999-12-31")
    df["est_actif"] = True

    logger.info(f"[TRANSFORM] Produits : {initial} lignes, SCD Type 2 active")
    return df
