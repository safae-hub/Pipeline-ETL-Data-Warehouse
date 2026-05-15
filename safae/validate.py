import sys
sys.path.insert(0, 'mexora_etl')

from extract.extractor import extract_commandes, extract_produits, extract_clients, extract_regions
from transform.clean_commandes import transform_commandes
from transform.clean_clients import transform_clients
from transform.clean_produits import transform_produits
from config.settings import FILES

df_cmd_raw = extract_commandes(str(FILES['commandes']))
df_cli_raw = extract_clients(str(FILES['clients']))
df_prod_raw = extract_produits(str(FILES['produits']))
df_reg = extract_regions(str(FILES['regions']))

df_cmd = transform_commandes(df_cmd_raw, str(FILES['regions']))
df_cli = transform_clients(df_cli_raw)
df_prod = transform_produits(df_prod_raw)

print('========== DATA QUALITY REPORT ==========')
print(f'Commandes brutes: {len(df_cmd_raw)}')
print(f'Commandes nettoyees: {len(df_cmd)}')
print(f'  -> Doublons supprimes: ~{len(df_cmd_raw) - len(df_cmd)}')
print(f'  -> Statuts uniques: {list(df_cmd["statut"].unique())}')
print(f'  -> Villes non reconnues: {(df_cmd["ville_livraison"] == "Non renseignee").sum()}')
print(f'  -> Livreurs INCONNU: {(df_cmd["id_livreur"] == "INCONNU").sum()}')
print()
print(f'Clients bruts: {len(df_cli_raw)}')
print(f'Clients nettoyes: {len(df_cli)}')
print('  -> Sexe repartition:')
print(df_cli['sexe'].value_counts().to_string())
print('  -> Tranches age:')
print(df_cli['tranche_age'].value_counts().to_string())
print()
print(f'Produits: {len(df_prod)}')
print(f'  -> Categories: {list(df_prod["categorie"].unique())}')
print(f'  -> Prix NULL restants: {df_prod["prix_catalogue"].isna().sum()}')
print()
print(f'Regions referentiel: {len(df_reg)} villes')
print('=========================================')
