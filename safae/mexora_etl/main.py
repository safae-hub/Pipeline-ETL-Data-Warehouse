"""
Point d'entree du pipeline ETL Mexora.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import FILES, SCHEMA_DWH
from utils.logger import setup_logger
from extract.extractor import extract_commandes, extract_produits, extract_clients, extract_regions
from transform.clean_commandes import transform_commandes
from transform.clean_clients import transform_clients
from transform.clean_produits import transform_produits
from transform.build_dimensions import (
    build_dim_temps, build_dim_region, build_dim_produit,
    build_dim_livreur, build_dim_client, build_fait_ventes,
)
from load.loader import charger_dimension, charger_faits, refresh_materialized_views


def run_pipeline():
    logger = setup_logger()
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("DEMARRAGE PIPELINE ETL MEXORA")
    logger.info("=" * 60)

    try:
        # 1. EXTRACT
        logger.info("--- PHASE EXTRACT ---")
        df_commandes_raw = extract_commandes(str(FILES["commandes"]))
        df_produits_raw = extract_produits(str(FILES["produits"]))
        df_clients_raw = extract_clients(str(FILES["clients"]))
        df_regions_raw = extract_regions(str(FILES["regions"]))

        # 2. TRANSFORM
        logger.info("--- PHASE TRANSFORM ---")
        df_commandes = transform_commandes(df_commandes_raw, str(FILES["regions"]))
        df_clients = transform_clients(df_clients_raw)
        df_produits = transform_produits(df_produits_raw)

        dim_temps = build_dim_temps("2020-01-01", "2025-12-31")
        dim_region = build_dim_region(df_regions_raw)
        dim_produit = build_dim_produit(df_produits)
        dim_livreur = build_dim_livreur(df_commandes)
        dim_client = build_dim_client(df_clients, df_commandes, df_regions_raw)
        fait_ventes = build_fait_ventes(
            df_commandes, dim_temps, dim_client, dim_produit, dim_region, dim_livreur
        )

        # 3. LOAD
        logger.info("--- PHASE LOAD ---")
        charger_dimension(dim_temps, "dim_temps")
        charger_dimension(dim_region, "dim_region")
        charger_dimension(dim_produit, "dim_produit")
        charger_dimension(dim_livreur, "dim_livreur")
        charger_dimension(dim_client, "dim_client")
        charger_faits(fait_ventes, "fait_ventes")

        refresh_materialized_views()

        duree = int((datetime.now() - start).total_seconds())
        logger.info("=" * 60)
        logger.info(f"PIPELINE TERMINE EN {duree} secondes")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"ERREUR PIPELINE : {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_pipeline()
