"""
Construction des dimensions et de la table de faits.
"""

import logging
import random
from datetime import date, timedelta

import pandas as pd

logger = logging.getLogger("mexora_etl")


# ============================================================
# DIM TEMPS
# ============================================================
def build_dim_temps(date_debut: str = "2020-01-01", date_fin: str = "2025-12-31") -> pd.DataFrame:
    """
    Genere la dimension temporelle complete entre deux dates.
    Inclut les jours feries marocains et les periodes Ramadan.
    """
    dates = pd.date_range(start=date_debut, end=date_fin, freq="D")

    feries_maroc = [
        "2020-01-01", "2020-01-11", "2020-05-01", "2020-07-30", "2020-08-14",
        "2020-11-06", "2020-11-18",
        "2021-01-01", "2021-01-11", "2021-05-01", "2021-07-30", "2021-08-14",
        "2021-11-06", "2021-11-18",
        "2022-01-01", "2022-01-11", "2022-05-01", "2022-07-30", "2022-08-14",
        "2022-11-06", "2022-11-18",
        "2023-01-01", "2023-01-11", "2023-05-01", "2023-07-30", "2023-08-14",
        "2023-11-06", "2023-11-18",
        "2024-01-01", "2024-01-11", "2024-05-01", "2024-07-30", "2024-08-14",
        "2024-11-06", "2024-11-18",
        "2025-01-01", "2025-01-11", "2025-05-01", "2025-07-30", "2025-08-14",
        "2025-11-06", "2025-11-18",
    ]

    ramadan_periodes = [
        ("2020-04-24", "2020-05-23"),
        ("2021-04-13", "2021-05-12"),
        ("2022-04-02", "2022-05-01"),
        ("2023-03-22", "2023-04-20"),
        ("2024-03-10", "2024-04-09"),
        ("2025-03-01", "2025-03-30"),
    ]

    df = pd.DataFrame({
        "id_date": dates.strftime("%Y%m%d").astype(int),
        "date_complete": dates,
        "jour": dates.day,
        "mois": dates.month,
        "trimestre": dates.quarter,
        "annee": dates.year,
        "semaine": dates.isocalendar().week.astype(int),
        "libelle_jour": dates.strftime("%A"),
        "libelle_mois": dates.strftime("%B"),
        "est_weekend": dates.dayofweek >= 5,
        "est_ferie_maroc": dates.strftime("%Y-%m-%d").isin(feries_maroc),
    })

    df["periode_ramadan"] = False
    for debut, fin in ramadan_periodes:
        masque = (df["date_complete"] >= debut) & (df["date_complete"] <= fin)
        df.loc[masque, "periode_ramadan"] = True

    logger.info(f"[TRANSFORM] Dim temps : {len(df)} jours generees ({date_debut} -> {date_fin})")
    return df[[
        "id_date", "date_complete", "jour", "mois", "trimestre", "annee",
        "semaine", "libelle_jour", "libelle_mois", "est_weekend",
        "est_ferie_maroc", "periode_ramadan",
    ]]


# ============================================================
# DIM REGION
# ============================================================
def build_dim_region(df_regions: pd.DataFrame) -> pd.DataFrame:
    """Construit la dimension region depuis le referentiel propre."""
    df = df_regions.rename(columns={"nom_ville_standard": "ville"}).copy()
    df["pays"] = "Maroc"
    df = df[["ville", "province", "region_admin", "zone_geo", "pays"]]
    df = df.reset_index(drop=True)
    df.insert(0, "id_region", range(1, len(df) + 1))
    logger.info(f"[TRANSFORM] Dim region : {len(df)} regions creees")
    return df


# ============================================================
# DIM PRODUIT (SCD Type 2)
# ============================================================
def build_dim_produit(df_produits: pd.DataFrame) -> pd.DataFrame:
    """
    Construit la dimension produit avec SCD Type 2.
    Chaque produit a un surrogate key unique ; changement = nouvelle version.
    """
    df = df_produits.copy()
    df["date_debut"] = pd.to_datetime(df.get("date_debut", "2020-01-01"))
    df["date_fin"] = pd.Timestamp("9999-12-31")
    df["est_actif"] = True

    df = df.reset_index(drop=True)
    df.insert(0, "id_produit_sk", range(1, len(df) + 1))
    df["id_produit_nk"] = df["id_produit"]

    # Rename nom -> nom_produit
    if "nom_produit" not in df.columns and "nom" in df.columns:
        df = df.rename(columns={"nom": "nom_produit"})

    expected = [
        "id_produit_sk", "id_produit_nk", "nom_produit", "categorie", "sous_categorie",
        "marque", "fournisseur", "prix_catalogue", "origine_pays",
        "date_debut", "date_fin", "est_actif",
    ]

    logger.info(f"[TRANSFORM] Dim produit : {len(df)} versions (SCD Type 2)")
    return df[[c for c in expected if c in df.columns]]


# ============================================================
# DIM LIVREUR
# ============================================================
def build_dim_livreur(df_commandes: pd.DataFrame) -> pd.DataFrame:
    """Construit la dimension livreur depuis les IDs presents dans les commandes."""
    livreurs = df_commandes["id_livreur"].dropna().unique()
    livreurs = [l for l in livreurs if l != "INCONNU"]

    noms_livreurs = [
        "Karim Bennani", "Youssef El Amrani", "Ahmed Moussaoui", "Omar Tazi",
        "Hamza Fassi", "Mehdi Idrissi", "Adil Chakir", "Nabil Zizi",
        "Reda Lahbabi", "Said Benali", "Ali Sbai", "Driss Jabiri",
        "Mustapha Kadiri", "Brahim Lahlou", "Hassan Naciri", "Rachid Rami",
    ]
    transports = ["Moto", "Camionnette", "Velo electrique", "Voiture"]

    data = []
    for i, lid in enumerate(livreurs, 1):
        data.append({
            "id_livreur": i,
            "id_livreur_nk": lid,
            "nom_livreur": random.choice(noms_livreurs) if i <= len(noms_livreurs) else f"Livreur_{i}",
            "type_transport": random.choice(transports),
            "zone_couverture": random.choice(["Nord", "Centre", "Sud", "Est", "National"]),
        })

    # Add INCONNU livreur
    data.append({
        "id_livreur": len(data) + 1,
        "id_livreur_nk": "INCONNU",
        "nom_livreur": "Livreur Inconnu",
        "type_transport": "Inconnu",
        "zone_couverture": "Inconnu",
    })

    df = pd.DataFrame(data)
    logger.info(f"[TRANSFORM] Dim livreur : {len(df)} livreurs creees")
    return df


# ============================================================
# SEGMENTATION CLIENT
# ============================================================
def calculer_segments_clients(df_commandes: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule le segment client (Gold/Silver/Bronze) base sur le CA cumule
    des 12 derniers mois pour chaque client.
    """
    date_limite = pd.Timestamp(date.today() - timedelta(days=365))

    df_recents = df_commandes[
        (df_commandes["date_commande"] >= date_limite) &
        (df_commandes["statut"] == "livré")
    ].copy()

    ca_par_client = df_recents.groupby("id_client")["montant_ttc"].sum().reset_index()
    ca_par_client.columns = ["id_client", "ca_12m"]

    def segmenter(ca):
        if ca >= 15000:
            return "Gold"
        elif ca >= 5000:
            return "Silver"
        else:
            return "Bronze"

    ca_par_client["segment_client"] = ca_par_client["ca_12m"].apply(segmenter)
    logger.info(f"[TRANSFORM] Segments : {len(ca_par_client)} clients segmentes")
    return ca_par_client[["id_client", "segment_client", "ca_12m"]]


# ============================================================
# DIM CLIENT (SCD Type 1 par defaut, avec date_debut/fin pour compatibilite)
# ============================================================
def build_dim_client(df_clients: pd.DataFrame, df_commandes: pd.DataFrame, df_regions: pd.DataFrame) -> pd.DataFrame:
    """
    Construit la dimension client avec segmentation calculee.
    SCD Type 1 : dernier etat connu (pas d'historisation des changements).
    """
    df = df_clients.copy()
    segments = calculer_segments_clients(df_commandes)
    df = df.merge(segments, on="id_client", how="left")
    df["segment_client"] = df["segment_client"].fillna("Bronze")
    df["ca_12m"] = df["ca_12m"].fillna(0)

    # Mapping ville -> region_admin via referentiel
    ville_to_region = dict(zip(
        df_regions["nom_ville_standard"].str.lower(),
        df_regions["region_admin"]
    ))
    df["ville_norm"] = df["ville"].str.strip().str.lower().str.title()
    df["region_admin"] = df["ville_norm"].str.lower().map(ville_to_region).fillna("Inconnue")

    # SCD Type 1 : pas d'historisation, mais on garde les colonnes pour compatibilite
    df["date_debut"] = pd.Timestamp("2020-01-01")
    df["date_fin"] = pd.Timestamp("9999-12-31")
    df["est_actif"] = True

    df = df.reset_index(drop=True)
    df.insert(0, "id_client_sk", range(1, len(df) + 1))
    df["id_client_nk"] = df["id_client"]

    logger.info(f"[TRANSFORM] Dim client : {len(df)} clients (SCD Type 1)")
    return df[[
        "id_client_sk", "id_client_nk", "nom_complet", "tranche_age", "sexe",
        "ville", "region_admin", "segment_client", "canal_acquisition",
        "date_debut", "date_fin", "est_actif",
    ]]


# ============================================================
# FAIT VENTES
# ============================================================
def build_fait_ventes(
    df_commandes: pd.DataFrame,
    dim_temps: pd.DataFrame,
    dim_client: pd.DataFrame,
    dim_produit: pd.DataFrame,
    dim_region: pd.DataFrame,
    dim_livreur: pd.DataFrame,
) -> pd.DataFrame:
    """
    Construit la table de faits en liant les commandes nettoyees aux dimensions.
    Granularite : une ligne = une ligne de commande (id_commande + id_produit).
    """
    df = df_commandes.copy()

    # id_date
    df["id_date"] = df["date_commande"].dt.strftime("%Y%m%d").astype(int)

    # id_client_sk
    df = df.merge(
        dim_client[["id_client_nk", "id_client_sk"]].rename(columns={"id_client_nk": "id_client"}),
        on="id_client", how="left"
    )

    # id_produit_sk (SCD Type 2 : on prend la version active)
    produits_actifs = dim_produit[dim_produit["est_actif"] == True][["id_produit_nk", "id_produit_sk"]]
    df = df.merge(
        produits_actifs.rename(columns={"id_produit_nk": "id_produit"}),
        on="id_produit", how="left"
    )

    # id_region
    df["ville_livraison_lower"] = df["ville_livraison"].str.lower()
    ville_to_id = dict(zip(
        dim_region["ville"].str.lower(),
        dim_region["id_region"]
    ))
    df["id_region"] = df["ville_livraison_lower"].map(ville_to_id)
    # Fallback : chercher via region_admin si ville non trouvee
    missing = df["id_region"].isna()
    if missing.sum() > 0:
        region_to_id = dict(zip(
            dim_region["region_admin"].str.lower(),
            dim_region["id_region"]
        ))
        df.loc[missing, "id_region"] = df.loc[missing, "ville_livraison_lower"].map(region_to_id)
    df["id_region"] = df["id_region"].fillna(1).astype(int)  # fallback ID 1

    # id_livreur
    df = df.merge(
        dim_livreur[["id_livreur_nk", "id_livreur"]].rename(columns={"id_livreur_nk": "id_livreur_src"}),
        left_on="id_livreur", right_on="id_livreur_src", how="left"
    )
    # INCONNU already mapped by the merge
    df["id_livreur_y"] = df["id_livreur_y"].fillna(
        dim_livreur[dim_livreur["id_livreur_nk"] == "INCONNU"]["id_livreur"].iloc[0]
        if len(dim_livreur[dim_livreur["id_livreur_nk"] == "INCONNU"]) > 0 else -1
    ).astype(int)

    # Cout livraison fictif
    df["cout_livraison"] = df["montant_ht"].apply(lambda x: round(min(max(x * 0.03, 15), 80), 2))

    # Remise % fictive
    df["remise_pct"] = df.apply(lambda r: round(random.uniform(0, 15), 2) if r["montant_ht"] > 1000 else 0, axis=1)

    # id_vente
    df = df.reset_index(drop=True)
    df.insert(0, "id_vente", range(1, len(df) + 1))

    result = df[[
        "id_vente", "id_date", "id_produit_sk", "id_client_sk", "id_region",
        "id_livreur_y", "quantite", "montant_ht", "montant_ttc",
        "cout_livraison", "delai_livraison_jours", "remise_pct", "statut",
    ]].rename(columns={
        "id_livreur_y": "id_livreur",
        "quantite": "quantite_vendue",
        "statut": "statut_commande",
        "id_produit_sk": "id_produit",
        "id_client_sk": "id_client",
    })

    result["date_chargement"] = pd.Timestamp.now()

    logger.info(f"[TRANSFORM] Fait ventes : {len(result)} lignes construites")
    return result
