-- ============================================================
-- Mexora Analytics — Verification de l'integrite referentielle
-- ============================================================

-- 1. Compteurs par table
SELECT 'dim_temps'     AS table_name, COUNT(*) AS nb_lignes FROM dwh_mexora.dim_temps
UNION ALL
SELECT 'dim_produit', COUNT(*) FROM dwh_mexora.dim_produit
UNION ALL
SELECT 'dim_client', COUNT(*) FROM dwh_mexora.dim_client
UNION ALL
SELECT 'dim_region', COUNT(*) FROM dwh_mexora.dim_region
UNION ALL
SELECT 'dim_livreur', COUNT(*) FROM dwh_mexora.dim_livreur
UNION ALL
SELECT 'fait_ventes', COUNT(*) FROM dwh_mexora.fait_ventes;

-- 2. Verifications FK : fait_ventes -> dimensions
SELECT 'FK temps manquantes'    AS check_name, COUNT(*) AS nb_problemes
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_temps t ON f.id_date = t.id_date
WHERE t.id_date IS NULL;

SELECT 'FK produit manquantes'  AS check_name, COUNT(*) AS nb_problemes
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
WHERE p.id_produit_sk IS NULL;

SELECT 'FK client manquantes'   AS check_name, COUNT(*) AS nb_problemes
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_client c ON f.id_client = c.id_client_sk
WHERE c.id_client_sk IS NULL;

SELECT 'FK region manquantes'   AS check_name, COUNT(*) AS nb_problemes
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_region r ON f.id_region = r.id_region
WHERE r.id_region IS NULL;

-- 3. Doublons potentiels sur natural keys
SELECT 'Doublons produit NK'  AS check_name, COUNT(*) - COUNT(DISTINCT id_produit_nk) AS nb_problemes FROM dwh_mexora.dim_produit;
SELECT 'Doublons client NK'   AS check_name, COUNT(*) - COUNT(DISTINCT id_client_nk)  AS nb_problemes FROM dwh_mexora.dim_client;

-- 4. Statuts non standards restants
SELECT statut_commande, COUNT(*) AS nb
FROM dwh_mexora.fait_ventes
WHERE statut_commande NOT IN ('livré', 'annulé', 'en_cours', 'retourné', 'inconnu')
GROUP BY statut_commande;

-- 5. Prix / quantites invalides
SELECT 'Quantites <= 0'   AS check_name, COUNT(*) FROM dwh_mexora.fait_ventes WHERE quantite_vendue <= 0
UNION ALL
SELECT 'Montants <= 0'    AS check_name, COUNT(*) FROM dwh_mexora.fait_ventes WHERE montant_ht <= 0 OR montant_ttc <= 0;
