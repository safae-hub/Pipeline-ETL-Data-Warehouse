"""
Nettoyage des commandes Mexora.
"""

import logging

import pandas as pd

logger = logging.getLogger("mexora_etl")


def charger_referentiel_villes(filepath: str) -> dict:
    """Charge le mapping ville brute -> ville standardisee depuis regions_maroc.csv."""
    df = pd.read_csv(filepath, encoding="utf-8")
    mapping = {}
    # Alias supplementaires pour les variations generees
    extra_aliases = {
        "tanger": "Tanger",
        "tng": "Tanger",
        "tnja": "Tanger",
        "tanger ville": "Tanger",
        "casablanca": "Casablanca",
        "casa": "Casablanca",
        "casa blanca": "Casablanca",
        "dar el beida": "Casablanca",
        "rabat": "Rabat",
        "rbt": "Rabat",
        "rabat ville": "Rabat",
        "marrakech": "Marrakech",
        "mrk": "Marrakech",
        "marrakesh": "Marrakech",
        "marrakech medina": "Marrakech",
        "fes": "Fes",
        "fez": "Fes",
        "fes ville": "Fes",
        "agadir": "Agadir",
        "agd": "Agadir",
        "agadir ville": "Agadir",
        "tetouan": "Tetouan",
        "tta": "Tetouan",
        "tetouan ville": "Tetouan",
        "oujda": "Oujda",
        "ouj": "Oujda",
        "oujda ville": "Oujda",
        "kenitra": "Kenitra",
        "ken": "Kenitra",
        "kenitra ville": "Kenitra",
        "sale": "Sale",
        "sla": "Sale",
        "sale ville": "Sale",
        "settat": "Settat",
        "sett": "Settat",
        "settat ville": "Settat",
        "al hoceima": "Al Hoceima",
        "hoceima": "Al Hoceima",
        "hoc": "Al Hoceima",
        "nador": "Nador",
        "nad": "Nador",
        "nador ville": "Nador",
        "tiznit": "Tiznit",
        "tiz": "Tiznit",
        "tiznit ville": "Tiznit",
        "safi": "Safi",
        "safi ville": "Safi",
        "berrechid": "Berrechid",
        "errachidia": "Errachidia",
        "khemisset": "Khemisset",
        "taroudant": "Taroudant",
    }
    mapping.update(extra_aliases)
    for _, row in df.iterrows():
        std = row["nom_ville_standard"]
        mapping[std.lower()] = std
        mapping[std.lower().replace(" ", "")] = std
        code = str(row.get("code_ville", "")).lower()
        if code:
            mapping[code] = std
    return mapping


def transform_commandes(df: pd.DataFrame, regions_filepath: str) -> pd.DataFrame:
    """
    Applique l'ensemble des regles de nettoyage sur les commandes Mexora.

    Regles appliquees :
      R1 - Suppression des doublons sur id_commande (conserver la derniere occurrence)
      R2 - Standardisation des dates (format cible : YYYY-MM-DD)
      R3 - Harmonisation des noms de villes via le referentiel regions_maroc
      R4 - Standardisation des statuts de commande
      R5 - Suppression des lignes avec quantite <= 0
      R6 - Suppression des lignes avec prix_unitaire = 0 (commandes test)
      R7 - Remplacement des id_livreur manquants par la valeur 'INCONNU' (livreur inconnu)
    """
    df = df.copy()
    initial = len(df)

    # R1 — Suppression des doublons
    before = len(df)
    df = df.drop_duplicates(subset=["id_commande"], keep="last")
    logger.info(f"[TRANSFORM] R1 doublons : {before - len(df)} lignes supprimees ({before} -> {len(df)})")

    # R2 — Standardisation des dates (mixed formats)
    df["date_commande"] = pd.to_datetime(df["date_commande"], format="mixed", dayfirst=True, errors="coerce")
    dates_invalides = df["date_commande"].isna().sum()
    df = df.dropna(subset=["date_commande"])
    logger.info(f"[TRANSFORM] R2 dates : {dates_invalides} dates invalides supprimees")

    # Parse date_livraison too
    df["date_livraison"] = pd.to_datetime(df["date_livraison"], errors="coerce")

    # R3 — Harmonisation des villes
    mapping_villes = charger_referentiel_villes(regions_filepath)
    df["ville_livraison"] = df["ville_livraison"].str.strip().str.lower()
    df["ville_livraison"] = df["ville_livraison"].map(mapping_villes).fillna("Non renseignee")
    nb_non_renseigne = (df["ville_livraison"] == "Non renseignee").sum()
    if nb_non_renseigne > 0:
        logger.warning(f"[TRANSFORM] R3 villes : {nb_non_renseigne} villes non reconnues → 'Non renseignee'")

    # R4 — Standardisation des statuts
    mapping_statuts = {
        "livré": "livré", "livre": "livré", "LIVRE": "livré", "DONE": "livré",
        "annulé": "annulé", "annule": "annulé", "KO": "annulé",
        "en_cours": "en_cours", "OK": "en_cours",
        "retourné": "retourné", "retourne": "retourné",
    }
    df["statut"] = df["statut"].replace(mapping_statuts)
    invalides = ~df["statut"].isin(["livré", "annulé", "en_cours", "retourné"])
    if invalides.sum() > 0:
        logger.warning(f"[TRANSFORM] R4 statuts : {invalides.sum()} valeurs non reconnues → 'inconnu'")
        df.loc[invalides, "statut"] = "inconnu"

    # R5 — Quantites invalides
    avant = len(df)
    df["quantite"] = pd.to_numeric(df["quantite"], errors="coerce")
    df = df[df["quantite"] > 0]
    logger.info(f"[TRANSFORM] R5 quantites : {avant - len(df)} lignes supprimees (quantite <= 0)")

    # R6 — Prix nuls (commandes test)
    avant = len(df)
    df["prix_unitaire"] = pd.to_numeric(df["prix_unitaire"], errors="coerce")
    df = df[df["prix_unitaire"] > 0]
    logger.info(f"[TRANSFORM] R6 prix : {avant - len(df)} commandes test supprimees (prix = 0)")

    # R7 — Livreurs manquants
    nb_manquants = df["id_livreur"].isna().sum() + (df["id_livreur"] == "").sum()
    df["id_livreur"] = df["id_livreur"].replace("", pd.NA).fillna("INCONNU")
    logger.info(f"[TRANSFORM] R7 livreurs : {nb_manquants} valeurs manquantes remplacees par 'INCONNU'")

    # Calcul montant TTC & HT (suppose 20% TVA)
    df["montant_ht"] = (df["quantite"] * df["prix_unitaire"]).round(2)
    df["montant_ttc"] = (df["montant_ht"] * 1.20).round(2)

    # Delai livraison
    df["delai_livraison_jours"] = (df["date_livraison"] - df["date_commande"]).dt.days
    df.loc[df["delai_livraison_jours"] < 0, "delai_livraison_jours"] = 0

    logger.info(f"[TRANSFORM] Commandes : {initial} -> {len(df)} lignes ({initial - len(df)} supprimees au total)")
    return df
