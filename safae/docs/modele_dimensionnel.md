# Mexora Analytics — Modélisation du Data Warehouse (Étape 1)

---

## 1.1 Analyse des besoins décisionnels (Requêtes-types)

```
Requête R1 — CA par région et catégorie :
  Analyser    → le chiffre d'affaires (montant TTC)
  En fonction de → la région administrative, la catégorie de produit, le mois/trimestre
  Pour        → les commandes avec statut "livré" uniquement

Requête R2 — Top produits Tanger par trimestre :
  Analyser    → la quantité vendue et le montant TTC
  En fonction de → le produit, le trimestre, la ville de livraison (Tanger)
  Pour        → les 12 derniers mois

Requête R3 — Panier moyen par segment client :
  Analyser    → le panier moyen (montant TTC moyen par commande)
  En fonction de → le segment client (Gold/Silver/Bronze), le mois
  Pour        → l'année en cours

Requête R4 — Taux de retour par catégorie :
  Analyser    → le taux de retour (% retourné / total)
  En fonction de → la catégorie de produit, le mois
  Pour        → toutes les commandes (livré + retourné)

Requête R5 — Effet Ramadan sur l'alimentation :
  Analyser    → le volume vendu et le CA journalier moyen
  En fonction de → la période (Ramadan vs hors Ramadan), la catégorie (Alimentation)
  Pour        → les années 2022-2025

Requête R6 — Performance livreurs (bonus) :
  Analyser    → le délai moyen de livraison et le taux de retard (>3 jours)
  En fonction de → le livreur, le mois, la zone de couverture
  Pour        → les commandes livrées ou retournées
```

---

## 1.2 Conception du schéma en étoile

### Table de faits : `fait_ventes`

| Clé étrangère | Dimension source | Description |
|---|---|---|
| `id_date` | `dim_temps` | Date de la commande |
| `id_produit` | `dim_produit` | Produit commandé (SK SCD2) |
| `id_client` | `dim_client` | Client (SK SCD1) |
| `id_region` | `dim_region` | Ville de livraison |
| `id_livreur` | `dim_livreur` | Livreur assigné |

### Mesures et additivité

| Mesure | Type | Justification |
|---|---|---|
| `quantite_vendue` | **Additive** | Somme logique sur toutes les dimensions |
| `montant_ht` | **Additive** | Somme logique sur toutes les dimensions |
| `montant_ttc` | **Additive** | Somme logique sur toutes les dimensions |
| `cout_livraison` | **Additive** | Somme logique sur toutes les dimensions |
| `delai_livraison_jours` | **Semi-additive** | Moyenne pertinente par livreur/mois ; somme totale non-sens |
| `remise_pct` | **Non-additive** | Taux moyen biaisé ; doit être recalculé au niveau agrégé |

### Granularité

> **Une ligne = une ligne de commande** (un produit dans une commande d'un client à une date dans une ville, livré par un livreur).
>
> Cette granularité transactionnelle permet d'analyser à tout niveau d'agrégation : par produit, par catégorie, par client, par région, par mois, etc. Elle garantit la cohérence des mesures additives (quantité, CA) car elles se somment naturellement.

### Tables de dimensions

#### `dim_temps` (Type 0 — statique)
- `id_date` (PK, format YYYYMMDD)
- `jour`, `mois`, `trimestre`, `annee`, `semaine`
- `libelle_jour`, `libelle_mois`
- `est_weekend`, `est_ferie_maroc`, `periode_ramadan`

#### `dim_produit` (SCD Type 2 — historisé)
- `id_produit_sk` (PK surrogate)
- `id_produit_nk` (natural key)
- `nom_produit`, `categorie`, `sous_categorie`, `marque`, `fournisseur`, `prix_standard`, `origine_pays`
- `date_debut`, `date_fin`, `est_actif` (colonnes SCD2)

#### `dim_client` (SCD Type 1 — écrasement)
- `id_client_sk` (PK surrogate)
- `id_client_nk` (natural key)
- `nom_complet`, `tranche_age`, `sexe`, `ville`, `region_admin`, `segment_client`, `canal_acquisition`
- `date_debut`, `date_fin`, `est_actif`

#### `dim_region` (Type 0)
- `id_region` (PK)
- `ville`, `province`, `region_admin`, `zone_geo`, `pays`

#### `dim_livreur` (SCD Type 1)
- `id_livreur` (PK)
- `id_livreur_nk`, `nom_livreur`, `type_transport`, `zone_couverture`

---

## 1.3 Gestion des SCD (Slowly Changing Dimensions)

### Cas SCD 1 : `dim_produit` — Changement de catégorie

> **Exemple** : Le produit "iPhone 16 Pro" passe de la catégorie historique "Téléphones" à la catégorie moderne "Smartphones" en mars 2024 suite à un reclassement du catalogue.
>
> **Type retenu : SCD Type 2**
>
> **Justification** : Mexora veut que les ventes antérieures à mars 2024 restent classées dans "Téléphones" pour la cohérence historique. Les ventes post-mars 2024 seront associées à "Smartphones". Cela permet de comparer correctement les performances par catégorie dans le temps sans biaiser les historiques.
>
> **Implémentation** : Nouvelle ligne dans `dim_produit` avec `date_debut = '2024-03-01'`, ancienne ligne mise à jour `date_fin = '2024-02-29'`, `est_actif = FALSE`.

### Cas SCD 2 : `dim_client` — Segment client

> **Exemple** : Un client Bronze progresse à Silver après avoir dépassé 5 000 MAD de CA sur 12 mois.
>
> **Type retenu : SCD Type 1 (écrasement)**
>
> **Justification** : Le segment client est une mesure dérivée calculée dynamiquement à chaque exécution du pipeline ETL. Elle reflète l'état **actuel** du client. Si on historisait (Type 2), on compliquerait inutilement la dimension car le segment change fréquemment (chaque mois potentiellement) et l'analyse métier privilégie le segment **actuel** pour la segmentation marketing. Les analyses historiques utilisent plutôt la dimension temps pour reconstituer le CA passé.
>
> **Alternative justifiée** : Si le besoin métier évolue (analyse "combien de clients étaient Gold en Q1 2024 ?"), on pourrait migrer vers un SCD Type 2 sur le segment.

---

## Schéma en étoile (textuel)

```
                    dim_temps (id_date PK)
                         |
                         | 1----N
                         v
                    +-------------+
         dim_region |  fait_ventes | dim_produit (SCD2)
         (id_region)|  (id_vente PK)| (id_produit_sk PK)
              |     +-------------+      |
              |   /    |     |    \      |
              |  /     |     |     \     |
              | /      |     |      \    |
            dim_client |     |    dim_livreur
          (id_client_sk)     (id_livreur)
```

*Le centre est la table de faits `fait_ventes`. Les 5 branches sont les dimensions. Toutes les jointures sont de type 1-N (une dimension → plusieurs faits).*

---

## Justification des choix architecturaux

| Choix | Justification |
|---|---|
| **Schéma en étoile** | Optimisé pour les requêtes analytiques (jointures simples, pas de normalisation excessive). Adapté à PostgreSQL + index bitmap. |
| **Granularité ligne de commande** | Niveau le plus fin disponible dans les données sources. Permet tout agrégat (produit, client, région, temps). |
| `dim_produit` en SCD2 | Historisation nécessaire pour les changements de catégorie/prix qui biaiseraient les analyses temporelles. |
| `dim_client` en SCD1 | Le segment est volatile et dérivé ; l'analyse historique se fait via la dimension temps. |
| `dim_temps` + `dim_region` séparées | Évite la redondance (la ville est dans `dim_region`, pas dans `dim_client` ni `fait_ventes`). |
| `dim_livreur` dédiée | Permet d'analyser la performance des livreurs indépendamment des commandes. |
