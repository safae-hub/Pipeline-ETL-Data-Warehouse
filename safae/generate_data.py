"""
Script de generation des donnees brutes Mexora avec imperfections intentionnelles.
"""

import json
import csv
import random
import os
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================
# 1. REGIONS MAROC (referentiel propre)
# ============================================================
VILLES = [
    ("TNG", "Tanger", "Tanger-Assilah", "Tanger-Tetouan-Al Hoceima", "Nord", 1125000, 90000),
    ("TTA", "Tetouan", "Tetouan", "Tanger-Tetouan-Al Hoceima", "Nord", 380000, 93000),
    ("HOC", "Al Hoceima", "Al Hoceima", "Tanger-Tetouan-Al Hoceima", "Nord", 175000, 32000),
    ("RBT", "Rabat", "Rabat", "Rabat-Sale-Kenitra", "Centre", 572000, 10000),
    ("SLA", "Sale", "Sale", "Rabat-Sale-Kenitra", "Centre", 890000, 11000),
    ("KEN", "Kenitra", "Kenitra", "Rabat-Sale-Kenitra", "Centre", 431000, 14000),
    ("CASA", "Casablanca", "Casablanca", "Casablanca-Settat", "Centre", 3710000, 20000),
    ("SETT", "Settat", "Settat", "Casablanca-Settat", "Centre", 142000, 26000),
    ("BER", "Berrechid", "Berrechid", "Casablanca-Settat", "Centre", 136000, 27100),
    ("MRK", "Marrakech", "Marrakech", "Marrakech-Safi", "Sud", 928000, 40000),
    ("SAFI", "Safi", "Safi", "Marrakech-Safi", "Sud", 308000, 46000),
    ("FES", "Fes", "Fes", "Fes-Meknes", "Nord", 1120000, 30000),
    ("MEK", "Meknes", "Meknes", "Fes-Meknes", "Nord", 632000, 50000),
    ("AGD", "Agadir", "Agadir-Ida Ou Tanane", "Souss-Massa", "Sud", 924000, 80000),
    ("TAR", "Taroudant", "Taroudant", "Souss-Massa", "Sud", 149000, 83000),
    ("OUJ", "Oujda", "Oujda-Angad", "Oriental", "Est", 494000, 60000),
    ("NAD", "Nador", "Nador", "Oriental", "Est", 161000, 62000),
    ("TIZ", "Tiznit", "Tiznit", "Souss-Massa", "Sud", 93000, 85000),
    ("KHE", "Khemisset", "Khemisset", "Rabat-Sale-Kenitra", "Centre", 131000, 15000),
    ("ERR", "Errachidia", "Errachidia", "Draa-Tafilalet", "Sud", 92000, 52000),
]

print("[GEN] Generating regions_maroc.csv...")
with open(OUTPUT_DIR / "regions_maroc.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["code_ville", "nom_ville_standard", "province", "region_admin", "zone_geo", "population", "code_postal"])
    for row in VILLES:
        writer.writerow(row)
print("[GEN] regions_maroc.csv done.")

# ============================================================
# 2. PRODUITS (JSON avec imperfections)
# ============================================================
CATEGORIE_BASES = {
    "Electronique": [
        ("Smartphones", ["Apple", "Samsung", "Xiaomi", "Oppo", "Huawei"]),
        ("Ordinateurs", ["Apple", "HP", "Dell", "Lenovo", "Asus"]),
        ("Accessoires", ["Apple", "Samsung", "Logitech", "JBL", "Anker"]),
    ],
    "Mode": [
        ("Vetements Homme", ["Zara", "H&M", "LC Waikiki", "Defacto", "Marwa"]),
        ("Vetements Femme", ["Zara", "H&M", "Mango", "Stradivarius", "Bershka"]),
        ("Chaussures", ["Nike", "Adidas", "Puma", "Converse", "New Balance"]),
    ],
    "Alimentation": [
        ("Epicerie", ["Lesieur", "Olis", "Nutella", "Kiri", "Paturages"]),
        ("Boissons", ["Coca-Cola", "Pepsi", "Sidi Ali", "Oulmes", "Lben"]),
        ("Dates & Confiseries", ["Boudjebbar", "Castilla", "Best", "El Khawas", "Soummam"]),
    ],
}

PRODUCT_NAMES = {
    "Smartphones": ["iPhone 16 Pro 256Go", "iPhone 15 128Go", "Samsung Galaxy S24 Ultra", "Xiaomi Redmi Note 13", "Oppo Reno 11", "Huawei P60 Pro", "iPhone 14 Pro Max", "Samsung A54 5G", "Xiaomi 14 Ultra", "Oppo Find X7"],
    "Ordinateurs": ["MacBook Pro 14 M3", "HP Pavilion 15", "Dell Inspiron 16", "Lenovo ThinkPad E14", "Asus VivoBook 15", "MacBook Air M2", "HP Envy x360", "Dell XPS 13", "Lenovo IdeaPad 3", "Asus ZenBook 14"],
    "Accessoires": ["AirPods Pro 2", "Casque Sony WH-1000XM5", "Chargeur Anker 65W", "Cable Lightning 2m", "Souris Logitech MX", "Ecouteurs JBL Tune", "Support Laptop Aluminium", "Power Bank 20000mAh", "Clavier mecanique RGB", "Webcam Logitech C920"],
    "Vetements Homme": ["T-shirt basique blanc", "Jean slim noir", "Chemise oxford bleue", "Blouson bomber kaki", "Sweat capuche gris", "Polo Lacoste rouge", "Pantalon chino beige", "Veste denim bleue", "Maillot de bain noir", "Costume 2 pieces marine"],
    "Vetements Femme": ["Robe d'ete fleurie", "Jean mom fit bleu", "Blouse en soie blanche", "Jupe midi noire", "Pull oversize rose", "Top basique noir", "Veste tailleur camel", "Pantalon large blanc", "Kimono brode", "Combishort en lin"],
    "Chaussures": ["Baskets Nike Air Force", "Adidas Ultraboost", "Puma RS-X", "Converse Chuck Taylor", "New Balance 530", "Sandales en cuir", "Bottines chelsea", "Mocassins classiques", "Tongs Havaianas", "Chaussures de running"],
    "Epicerie": ["Huile d'olive 5L Lesieur", "Confitures assorties x3", "Cafe moulu 500g", "Riz basmati 1kg", "Lait en poudre 800g", "Sardines en boite x6", "Pates Barilla x5", "Ketchup Heinz 1kg", "Miel d'oranger 500g", "Fruits secs assortis 1kg"],
    "Boissons": ["Coca-Cola pack 24x33cl", "Eau Sidi Ali pack 6x1.5L", "Jus d'orange presse 1L", "Red Bull pack 4x25cl", "Lben biologique 1L", "Jus de grenade 100% naturel", "The vert a la menthe", "Cafe noir long x20", "Smoothie multifruits", "Infusion camomille"],
    "Dates & Confiseries": ["Dates Medjool 1kg", "Chocolat Lindt 70%", "Baklawa assortie 500g", "Pate de dattes 400g", "Corbeille Ramadan deluxe", "Ghriba amande 300g", "Sablés maison 250g", "Loukoum rose 500g", "Amandes grillees 1kg", "Dattes Deglet Nour 2kg"],
}

print("[GEN] Generating produits_mexora.json...")
produits = []
id_counter = 1
for cat_base, sous_cats in CATEGORIE_BASES.items():
    for sous_cat, marques in sous_cats:
        for _ in range(random.randint(4, 7)):
            name = random.choice(PRODUCT_NAMES[sous_cat])
            marque = random.choice(marques)
            prix = round(random.uniform(50, 15000), 2)
            # Imperfections : mixed case categories on ~20% of products
            if random.random() < 0.2:
                cat_display = random.choice([cat_base.lower(), cat_base.upper(), cat_base])
            else:
                cat_display = cat_base
            actif = True
            if random.random() < 0.05:
                actif = False  # Some inactive products still have orders
            prix_cat = prix if random.random() > 0.03 else None
            produits.append({
                "id_produit": f"P{id_counter:03d}",
                "nom": name,
                "categorie": cat_display,
                "sous_categorie": sous_cat,
                "marque": marque,
                "fournisseur": f"{marque} Distribution MENA" if random.random() > 0.3 else f"Import Direct {marque}",
                "prix_catalogue": prix_cat,
                "origine_pays": random.choice(["USA", "Chine", "France", "Maroc", "Turquie", "UAE", "Italie", "Espagne"]),
                "date_creation": (datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1600))).strftime("%Y-%m-%d"),
                "actif": actif
            })
            id_counter += 1

with open(OUTPUT_DIR / "produits_mexora.json", "w", encoding="utf-8") as f:
    json.dump({"produits": produits}, f, ensure_ascii=False, indent=2)
print(f"[GEN] produits_mexora.json done ({len(produits)} produits).")

# ============================================================
# 3. CLIENTS (CSV avec imperfections)
# ============================================================
PRENOMS_M = ["Ahmed", "Youssef", "Mehdi", "Omar", "Karim", "Hamza", "Amine", "Adil", "Rachid", "Mustapha", "Hassan", "Mohamed", "Ali", "Abdel", "Said", "Brahim", "Driss", "Nabil", "Reda", "Samir"]
PRENOMS_F = ["Fatima", "Sanaa", "Laila", "Nadia", "Imane", "Salma", "Amina", "Khadija", "Houda", "Yasmin", "Zineb", "Rania", "Soukaina", "Ines", "Meriem", "Asmaa", "Ghita", "Oumaima", "Chaimae", "Meryem"]
NOMS = ["Benali", "El Amrani", "Bennani", "Chakir", "Fassi", "Idrissi", "Lahbabi", "Moussaoui", "Ouazzani", "Sbai", "Tazi", "Zizi", "Akharraz", "Dahbi", "Hassani", "Jabiri", "Kadiri", "Lahlou", "Naciri", "Rami"]
DOMAINS = ["gmail.com", "outlook.com", "yahoo.fr", "hotmail.com", "live.ma", "protonmail.com", "inemail.ma"]
VILLES_BRUITEES = {
    "Tanger": ["tanger", "TNG", "TANGER", "Tnja", "Tanger Ville", "tanger ", "  Tanger  ", "tng"],
    "Casablanca": ["casa", "CASA", "Casablanca", "casablanca", "Dar el Beida", "Casa ", "casa blanca"],
    "Rabat": ["rabat", "Rabat", "RBT", "rabat ", "Rabat Ville"],
    "Marrakech": ["marrakech", "Marrakech", "MRK", "Marrakesh", "marrakech ", "Marrakech Medina"],
    "Fes": ["fes", "Fes", "Fez", "fes ", "Fes Ville"],
    "Agadir": ["agadir", "Agadir", "AGD", "agadir ", "Agadir Ville"],
    "Tetouan": ["tetouan", "Tetouan", "TTA", "tetouan ", "Tetouan Ville"],
    "Oujda": ["oujda", "Oujda", "OUJ", "oujda ", "Oujda Ville"],
    "Kenitra": ["kenitra", "Kenitra", "KEN", "kenitra ", "Kenitra Ville"],
    "Sale": ["sale", "Sale", "SLA", "sale ", "Sale Ville"],
    "Settat": ["settat", "Settat", "SETT", "settat ", "Settat Ville"],
    "Al Hoceima": ["al hoceima", "Al Hoceima", "HOC", "al hoceima ", "Hoceima"],
    "Nador": ["nador", "Nador", "NAD", "nador ", "Nador Ville"],
    "Tiznit": ["tiznit", "Tiznit", "TIZ", "tiznit ", "Tiznit Ville"],
    "Safi": ["safi", "Safi", "SAFI", "safi ", "Safi Ville"],
}
CANAUX = ["SEO", "Facebook Ads", "Instagram", "TikTok", "Google Ads", "Referral", "Email", "Influencer"]
SEXE_VAR = ["m", "f", "M", "F", "1", "0", "Homme", "Femme", "male", "female", "h", "HOMME", "FEMME"]

print("[GEN] Generating clients_mexora.csv...")
clients = []
nb_clients = 2200
for i in range(1, nb_clients + 1):
    sexe_raw = random.choice(SEXE_VAR)
    is_m = sexe_raw.lower() in ["m", "1", "homme", "male", "h"]
    prenom = random.choice(PRENOMS_M if is_m else PRENOMS_F)
    nom = random.choice(NOMS)
    ville_std = random.choice(list(VILLES_BRUITEES.keys()))
    ville_brut = random.choice(VILLES_BRUITEES[ville_std])
    email = f"{prenom.lower()}.{nom.lower()}{random.randint(1, 999)}@{random.choice(DOMAINS)}"
    # ~5% bad emails
    if random.random() < 0.05:
        email = email.replace("@", "_") if random.random() < 0.5 else f"{prenom.lower()}@{random.choice(DOMAINS).replace('.', '')}"
    # Birth date : mostly valid, some invalid
    today = datetime(2026, 5, 6)
    age_target = random.randint(18, 70)
    naissance = today - timedelta(days=age_target * 365)
    if random.random() < 0.03:
        # Too old (>120)
        naissance = today - timedelta(days=random.randint(130 * 365, 150 * 365))
    elif random.random() < 0.02:
        # Too young (<16) or future
        naissance = today + timedelta(days=random.randint(1, 365))
    date_insc = datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1900))
    clients.append({
        "id_client": f"C{i:05d}",
        "nom": nom,
        "prenom": prenom,
        "email": email,
        "date_naissance": naissance.strftime("%Y-%m-%d"),
        "sexe": sexe_raw,
        "ville": ville_brut,
        "telephone": f"0{random.choice(['6', '7'])}{random.randint(10000000, 99999999)}",
        "date_inscription": date_insc.strftime("%Y-%m-%d"),
        "canal_acquisition": random.choice(CANAUX)
    })

# Create duplicates : ~40 clients with same email, different id
for _ in range(40):
    dup = random.choice(clients).copy()
    dup["id_client"] = f"C{nb_clients + _ + 1:05d}"
    # Slight variation in name or phone
    dup["telephone"] = f"0{random.choice(['6', '7'])}{random.randint(10000000, 99999999)}"
    clients.append(dup)

random.shuffle(clients)
with open(OUTPUT_DIR / "clients_mexora.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["id_client", "nom", "prenom", "email", "date_naissance", "sexe", "ville", "telephone", "date_inscription", "canal_acquisition"])
    writer.writeheader()
    writer.writerows(clients)
print(f"[GEN] clients_mexora.csv done ({len(clients)} clients).")

# ============================================================
# 4. COMMANDES (50 000 lignes avec imperfections)
# ============================================================
print("[GEN] Generating commandes_mexora.csv...")
STATUTS_BRUITE = ["livré", "livré", "livré", "livre", "LIVRE", "DONE", "annulé", "annule", "KO", "en_cours", "en_cours", "OK", "retourné", "retourne"]
MODES_PAIEMENT = ["Carte bancaire", "Paiement a la livraison", "PayPal", "Virement", "Maroc Pay", "CMI"]
LIVREURS = [f"L{i:03d}" for i in range(1, 51)]

commandes = []
ids_commande = set()
nb_commandes = 50000
for i in range(nb_commandes):
    id_cmd = f"CMD{random.randint(100000, 999999)}"
    # ~3% duplicates
    if random.random() < 0.03 and i > 100:
        id_cmd = random.choice(list(ids_commande))
    ids_commande.add(id_cmd)

    id_client = random.choice(clients)["id_client"]
    id_produit = random.choice(produits)["id_produit"]
    date_cmd = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 450))
    # Mixed date formats
    fmt_roll = random.random()
    if fmt_roll < 0.33:
        date_str = date_cmd.strftime("%d/%m/%Y")
    elif fmt_roll < 0.66:
        date_str = date_cmd.strftime("%Y-%m-%d")
    else:
        date_str = date_cmd.strftime("%b %d %Y")

    ville_std = random.choice(list(VILLES_BRUITEES.keys()))
    ville_brut = random.choice(VILLES_BRUITEES[ville_std])

    qte = random.randint(1, 5)
    # ~0.5% negative
    if random.random() < 0.005:
        qte = -random.randint(1, 3)

    prix_unit = round(random.uniform(30, 12000), 2)
    # ~0.3% test orders with prix=0
    if random.random() < 0.003:
        prix_unit = 0.0

    statut = random.choice(STATUTS_BRUITE)
    id_livreur = random.choice(LIVREURS)
    # ~7% missing livreur
    if random.random() < 0.07:
        id_livreur = ""

    date_livr = (date_cmd + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d")

    commandes.append({
        "id_commande": id_cmd,
        "id_client": id_client,
        "id_produit": id_produit,
        "date_commande": date_str,
        "quantite": qte,
        "prix_unitaire": prix_unit,
        "statut": statut,
        "ville_livraison": ville_brut,
        "mode_paiement": random.choice(MODES_PAIEMENT),
        "id_livreur": id_livreur,
        "date_livraison": date_livr,
    })

# Ensure some inactive products still have orders
inactive_prods = [p["id_produit"] for p in produits if not p["actif"]]
for ip in inactive_prods[:10]:
    for _ in range(random.randint(2, 8)):
        cmd = random.choice(commandes).copy()
        cmd["id_produit"] = ip
        cmd["id_commande"] = f"CMD{random.randint(100000, 999999)}"
        commandes.append(cmd)

random.shuffle(commandes)
with open(OUTPUT_DIR / "commandes_mexora.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["id_commande", "id_client", "id_produit", "date_commande", "quantite", "prix_unitaire", "statut", "ville_livraison", "mode_paiement", "id_livreur", "date_livraison"])
    writer.writeheader()
    writer.writerows(commandes)
print(f"[GEN] commandes_mexora.csv done ({len(commandes)} lignes).")

print("\n[GEN] All data files generated successfully in ./data/")
