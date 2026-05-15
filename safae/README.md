# Mexora Analytics — Pipeline ETL & Data Warehouse

> Mini-projet 1 — Construire l'entrepot de donnees from scratch pour Mexora, marketplace e-commerce basee a Tanger.

---

## Architecture du projet

```
mexora-etl/
├── data/                          # Donnees brutes generees
│   ├── commandes_mexora.csv       # 50 000+ lignes (avec imperfections)
│   ├── produits_mexora.json       # ~48 produits (avec imperfections)
│   ├── clients_mexora.csv         # ~2 240 clients (avec imperfections)
│   └── regions_maroc.csv          # Referentiel geographique propre
├── mexora_etl/                    # Pipeline ETL Python
│   ├── config/settings.py
│   ├── extract/extractor.py
│   ├── transform/
│   │   ├── clean_commandes.py
│   │   ├── clean_clients.py
│   │   ├── clean_produits.py
│   │   └── build_dimensions.py
│   ├── load/loader.py
│   ├── utils/logger.py
│   ├── main.py
│   └── requirements.txt
├── sql/
│   ├── create_dwh.sql             # Creation schemas + tables + vues
│   ├── check_integrity.sql        # Verification integrite referentielle
│   └── refresh_views.sql          # Rafraichissement vues materialisees
├── dashboard/
│   └── app.py                     # Dashboard Streamlit interactif
├── generate_data.py              # Generation des donnees brutes
├── logs/                          # Logs ETL (auto-cree)
├── docs/                          # Documentation & captures
├── rapport_transformations.md     # Regles de transformation documentees
└── README.md                      # Ce fichier
```

---

## Pre-requis

- Python 3.10+
- PostgreSQL 14+
- pip

---

## Installation rapide

### 1. Cloner / extraire le projet

```bash
cd mexora-etl
```

### 2. Creer un environnement virtuel (recommande)

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # Linux/Mac
```

### 3. Installer les dependances

```bash
cd mexora_etl
pip install -r requirements.txt
```

### 4. Configurer PostgreSQL

Creer la base de donnees `mexora_dwh` et executer le script SQL :

```bash
psql -U postgres -d postgres -c "CREATE DATABASE mexora_dwh;"
psql -U postgres -d mexora_dwh -f sql/create_dwh.sql
```

> Credentials par defaut : `postgres` / `postgres` / `localhost:5432`
> Modifier `mexora_etl/config/settings.py` ou creer un fichier `.env` si besoin.

### 5. Generer les donnees brutes (si ce n'est pas deja fait)

```bash
cd ..
python generate_data.py
```

### 6. Lancer le pipeline ETL

```bash
cd mexora_etl
python main.py
```

Le pipeline logge toutes les etapes dans `logs/etl_YYYYMMDD_HHMMSS.log`.

### 7. Lancer le dashboard Streamlit

```bash
cd ..
streamlit run dashboard/app.py
```

Ouvrir le navigateur sur `http://localhost:8501`.

---

## Schema en etoile

### Table de faits : `fait_ventes`

| Mesure | Type d'additivite | Description |
|---|---|---|
| `quantite_vendue` | Additive | S'additionne sur toutes les dimensions |
| `montant_ht` | Additive | Chiffre d'affaires HT |
| `montant_ttc` | Additive | Chiffre d'affaires TTC (20% TVA) |
| `cout_livraison` | Additive | Cout de livraison calcule |
| `delai_livraison_jours` | Semi-additive | Moyenne pertinente, somme non-sens |
| `remise_pct` | Non-additive | Taux : a recalculer au niveau agrege |

**Granularite** : une ligne = une ligne de commande (1 produit par commande client).

### Dimensions

| Dimension | Type SCD | Justification |
|---|---|---|
| `dim_produit` | Type 2 | Historisation des changements de categorie / prix |
| `dim_client` | Type 1 | Dernier etat connu (ville, segment) |
| `dim_temps` | Type 0 | Statique, ne change jamais |
| `dim_region` | Type 0 | Referentiel geographique officiel |
| `dim_livreur` | Type 1 | Dernier etat connu |

---

## Dashboard — 5 questions metier

| # | Question | Visualisation |
|---|---|---|
| 1 | CA par region + evolution 12 mois | KPI + line chart + bar chart |
| 2 | Top 10 produits a Tanger par trimestre | Filtre interactif + barres horizontales |
| 3 | Segments clients (Gold/Silver/Bronze) | Donut + tableau panier moyen |
| 4 | Taux de retour par categorie | Barres + seuils d'alerte colorés |
| 5 | Effet Ramadan sur alimentation | Line chart + indice de performance |

---

## Commandes utiles

**Verifier l'integrite du DWH :**
```bash
psql -U postgres -d mexora_dwh -f sql/check_integrity.sql
```

**Rafraichir les vues materialisees :**
```bash
psql -U postgres -d mexora_dwh -f sql/refresh_views.sql
```

---

## Auteur

Projet académique — Mexora Analytics (2025/2026)
