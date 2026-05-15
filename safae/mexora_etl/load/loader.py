"""
Module de chargement dans PostgreSQL.
"""

import logging

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from config.settings import DATABASE_URL, SCHEMA_DWH, SCHEMA_REPORTING

logger = logging.getLogger("mexora_etl")


def get_engine():
    """Retourne le moteur SQLAlchemy."""
    return create_engine(DATABASE_URL)


def _ensure_schema(schema_name: str):
    """Cree un schema PostgreSQL s'il n'existe pas encore."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        conn.commit()
        logger.info(f"[INIT] Schema '{schema_name}' verifie/cree")


def charger_dimension(df: pd.DataFrame, table_name: str, if_exists: str = "replace"):
    """
    Charge une table de dimension dans PostgreSQL.
    Strategie : replace (drop-create + reload) pour les dimensions.
    """
    _ensure_schema(SCHEMA_DWH)
    engine = get_engine()

    df.to_sql(
        name=table_name,
        con=engine,
        schema=SCHEMA_DWH,
        if_exists=if_exists,
        index=False,
        method="multi",
        chunksize=1000,
    )
    logger.info(f"[LOAD] {table_name} : {len(df)} lignes chargees")


def charger_faits(df: pd.DataFrame, table_name: str = "fait_ventes"):
    """
    Charge la table de faits avec strategie replace.
    """
    _ensure_schema(SCHEMA_DWH)
    engine = get_engine()

    df.to_sql(
        name=table_name,
        con=engine,
        schema=SCHEMA_DWH,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=5000,
    )
    logger.info(f"[LOAD] {table_name} : {len(df)} lignes chargees")


def create_materialized_views():
    """Cree les vues materialisees reporting si elles n'existent pas."""
    engine = get_engine()
    _ensure_schema(SCHEMA_REPORTING)

    ddl = f"""
    CREATE MATERIALIZED VIEW IF NOT EXISTS {SCHEMA_REPORTING}.mv_ca_mensuel AS
    SELECT t.annee, t.mois, t.libelle_mois, t.periode_ramadan,
           r.region_admin, r.zone_geo, p.categorie,
           SUM(f.montant_ttc) AS ca_ttc,
           SUM(f.montant_ht) AS ca_ht,
           COUNT(DISTINCT f.id_client) AS nb_clients_actifs,
           SUM(f.quantite_vendue) AS volume_vendu,
           ROUND(AVG(f.montant_ttc)::numeric, 2) AS panier_moyen,
           COUNT(DISTINCT f.id_vente) AS nb_commandes
    FROM {SCHEMA_DWH}.fait_ventes f
    JOIN {SCHEMA_DWH}.dim_temps t ON f.id_date = t.id_date
    JOIN {SCHEMA_DWH}.dim_region r ON f.id_region = r.id_region
    JOIN {SCHEMA_DWH}.dim_produit p ON f.id_produit = p.id_produit_sk
    WHERE f.statut_commande = 'livré'
    GROUP BY t.annee, t.mois, t.libelle_mois, t.periode_ramadan,
             r.region_admin, r.zone_geo, p.categorie;

    CREATE MATERIALIZED VIEW IF NOT EXISTS {SCHEMA_REPORTING}.mv_top_produits AS
    SELECT t.annee, t.trimestre, p.nom_produit, p.categorie, p.marque,
           SUM(f.quantite_vendue) AS qte_totale,
           SUM(f.montant_ttc) AS ca_total,
           COUNT(DISTINCT f.id_client) AS nb_clients_distincts,
           RANK() OVER (PARTITION BY t.annee, t.trimestre, p.categorie
                        ORDER BY SUM(f.montant_ttc) DESC) AS rang_dans_categorie
    FROM {SCHEMA_DWH}.fait_ventes f
    JOIN {SCHEMA_DWH}.dim_temps t ON f.id_date = t.id_date
    JOIN {SCHEMA_DWH}.dim_produit p ON f.id_produit = p.id_produit_sk
    WHERE f.statut_commande = 'livré'
    GROUP BY t.annee, t.trimestre, p.nom_produit, p.categorie, p.marque;

    CREATE MATERIALIZED VIEW IF NOT EXISTS {SCHEMA_REPORTING}.mv_performance_livreurs AS
    SELECT l.nom_livreur, l.zone_couverture, t.annee, t.mois,
           COUNT(*) AS nb_livraisons,
           ROUND(AVG(f.delai_livraison_jours)::numeric, 2) AS delai_moyen_jours,
           COUNT(*) FILTER (WHERE f.delai_livraison_jours > 3) AS nb_livraisons_retard,
           ROUND(COUNT(*) FILTER (WHERE f.delai_livraison_jours > 3) * 100.0
                 / NULLIF(COUNT(*), 0), 2) AS taux_retard_pct
    FROM {SCHEMA_DWH}.fait_ventes f
    JOIN {SCHEMA_DWH}.dim_livreur l ON f.id_livreur = l.id_livreur
    JOIN {SCHEMA_DWH}.dim_temps t ON f.id_date = t.id_date
    WHERE f.statut_commande IN ('livré', 'retourné')
      AND f.delai_livraison_jours IS NOT NULL
    GROUP BY l.nom_livreur, l.zone_couverture, t.annee, t.mois;
    """

    with engine.connect() as conn:
        for stmt in ddl.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(text(stmt))
                    conn.commit()
                    logger.info(f"[INIT] Vue materialisee creee/verifiee")
                except Exception as e:
                    logger.warning(f"[INIT] Erreur creation vue : {e}")
                    conn.rollback()


def refresh_materialized_views():
    """Rafraichit les vues materialisees du schema reporting."""
    engine = get_engine()
    create_materialized_views()
    views = ["mv_ca_mensuel", "mv_top_produits", "mv_performance_livreurs"]
    with engine.connect() as conn:
        for v in views:
            try:
                conn.execute(text(f"REFRESH MATERIALIZED VIEW {SCHEMA_REPORTING}.{v}"))
                conn.commit()
                logger.info(f"[LOAD] Vue {v} rafraichie")
            except Exception as e:
                logger.warning(f"[LOAD] Vue {v} non rafraichie : {e}")
