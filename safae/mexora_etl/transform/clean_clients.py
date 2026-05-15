"""
Nettoyage des clients Mexora.
"""

import logging
import re
from datetime import date

import pandas as pd

logger = logging.getLogger("mexora_etl")


def transform_clients(df: pd.DataFrame) -> pd.DataFrame:
    """
    Regles :
      R1 - Dedoublonnage sur email normalise (conserver inscription la plus recente)
      R2 - Standardisation du sexe (cible : 'm' / 'f' / 'inconnu')
      R3 - Validation des dates de naissance (age entre 16 et 100 ans)
      R4 - Validation du format email
      R5 - Segmentation client Gold/Silver/Bronze (calculee depuis les commandes)
    """
    initial = len(df)

    # R1 — Dedoublonnage
    df["email_norm"] = df["email"].str.lower().str.strip()
    df["date_inscription"] = pd.to_datetime(df["date_inscription"], errors="coerce")
    df = df.sort_values("date_inscription")
    before = len(df)
    df = df.drop_duplicates(subset=["email_norm"], keep="last")
    logger.info(f"[TRANSFORM] R1 dedoublonnage : {before - len(df)} clients dupliques supprimes ({before} -> {len(df)})")

    # R2 — Standardisation du sexe
    mapping_sexe = {
        "m": "m", "f": "f",
        "1": "m", "0": "f",
        "homme": "m", "femme": "f",
        "male": "m", "female": "f",
        "h": "m",
    }
    df["sexe"] = df["sexe"].str.lower().str.strip().map(mapping_sexe).fillna("inconnu")
    nb_inconnu = (df["sexe"] == "inconnu").sum()
    if nb_inconnu > 0:
        logger.info(f"[TRANSFORM] R2 sexe : {nb_inconnu} valeurs non reconnues → 'inconnu'")

    # R3 — Validation des dates de naissance
    df["date_naissance"] = pd.to_datetime(df["date_naissance"], errors="coerce")
    today = pd.Timestamp(date.today())
    df["age"] = ((today - df["date_naissance"]).dt.days // 365).astype("Int64")
    ages_invalides = ((df["age"] < 16) | (df["age"] > 100)).sum()
    df.loc[(df["age"] < 16) | (df["age"] > 100), "date_naissance"] = pd.NaT
    df.loc[(df["age"] < 16) | (df["age"] > 100), "age"] = pd.NA
    logger.info(f"[TRANSFORM] R3 ages : {ages_invalides} dates de naissance invalides (age hors 16-100)")

    df["tranche_age"] = pd.cut(
        df["age"].fillna(0),
        bins=[0, 18, 25, 35, 45, 55, 65, 200],
        labels=["<18", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
        right=False,
    )
    df["tranche_age"] = df["tranche_age"].astype(str)
    df.loc[df["age"].isna(), "tranche_age"] = "Inconnu"

    # R4 — Validation email
    pattern_email = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    emails_invalides = (~df["email"].str.match(pattern_email, na=False)).sum()
    df.loc[~df["email"].str.match(pattern_email, na=False), "email"] = None
    logger.info(f"[TRANSFORM] R4 emails : {emails_invalides} emails mal formates mis a NULL")

    # Harmonisation ville via mapping simple (on garde ville brute pour build_dim_client)
    df["ville"] = df["ville"].str.strip().str.title()

    # Nom complet
    df["nom_complet"] = (df["prenom"].fillna("") + " " + df["nom"].fillna("")).str.strip()

    logger.info(f"[TRANSFORM] Clients : {initial} -> {len(df)} lignes ({initial - len(df)} supprimees au total)")
    return df
