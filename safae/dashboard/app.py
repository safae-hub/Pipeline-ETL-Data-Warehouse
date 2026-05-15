"""
Dashboard decisionnel Mexora Analytics — Streamlit PRO Edition.
Repond aux 5 questions metier obligatoires avec un design premium.
"""

import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from sqlalchemy import create_engine

# ── PAGE CONFIG ────────────────────────────────────────────
st.set_page_config(
    page_title="Mexora Analytics | DWH",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:123@localhost:5432/mexora_dwh",
)

# ── ENGINE ─────────────────────────────────────────────────
@st.cache_resource
def get_engine():
    return create_engine(DB_URL)


@st.cache_data(ttl=300)
def run_query(query: str) -> pd.DataFrame:
    """Execute une requete SQL et retourne un DataFrame."""
    try:
        engine = get_engine()
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Erreur connexion base : {e}")
        return pd.DataFrame()


# ── THEME & CSS ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }

.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

.metric-card {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-radius: 12px;
    padding: 18px 20px;
    color: #f8fafc;
    border-left: 4px solid #38bdf8;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    transition: transform .2s;
}
.metric-card:hover { transform: translateY(-2px); }

.metric-value { font-size: 1.6rem; font-weight: 800; color: #f8fafc; }
.metric-label { font-size: .85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: .05em; }
.metric-delta { font-size: .9rem; font-weight: 600; }

.gold-card   { border-left-color: #fbbf24; }
.silver-card { border-left-color: #94a3b8; }
.bronze-card { border-left-color: #b45309; }
.alert-red   { border-left-color: #ef4444; }
.alert-ora   { border-left-color: #f59e0b; }
.alert-green { border-left-color: #10b981; }

.page-title {
    font-size: 2rem; font-weight: 800; color: #0f172a;
    margin-bottom: .2rem;
}
.page-subtitle {
    font-size: 1rem; color: #64748b; margin-bottom: 1.5rem;
}

.stDataFrame { border-radius: 10px; overflow: hidden; }

hr { border: none; border-top: 1px solid #e2e8f0; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR FILTERS ─────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shopping-cart.png", width=48)
    st.title("Mexora Analytics")
    st.caption("Data Warehouse Decisionnel")
    st.divider()

    menu = st.radio(
        "Navigation",
        [
            "Executive Summary",
            "CA & Regions",
            "Top Produits Tanger",
            "Segments Clients",
            "Taux de Retour",
            "Effet Ramadan",
        ],
        index=0,
    )

    st.divider()
    st.subheader("Filtres globaux")

    years_all = run_query("SELECT DISTINCT annee FROM dwh_mexora.dim_temps WHERE annee BETWEEN 2022 AND 2025 ORDER BY annee DESC;")
    annee_sel = st.selectbox("Annee", years_all["annee"].tolist() if not years_all.empty else [2024, 2025])

    region_all = run_query("SELECT DISTINCT region_admin FROM dwh_mexora.dim_region ORDER BY region_admin;")
    region_sel = st.multiselect(
        "Region",
        region_all["region_admin"].tolist() if not region_all.empty else ["Tanger-Tetouan-Al Hoceima"],
        default=region_all["region_admin"].tolist()[:3] if not region_all.empty else [],
    )

    cat_all = run_query("SELECT DISTINCT categorie FROM dwh_mexora.dim_produit ORDER BY categorie;")
    cat_sel = st.multiselect(
        "Categorie produit",
        cat_all["categorie"].tolist() if not cat_all.empty else ["Electronique", "Mode", "Alimentation"],
        default=cat_all["categorie"].tolist() if not cat_all.empty else [],
    )

    st.divider()
    st.caption(f"v1.0 — {datetime.now().strftime('%d/%m/%Y')}")

# helper pour construire WHERE dynamique
where_parts = ["f.statut_commande = 'livré'"]
if region_sel:
    reg_list = ",".join([f"'{r}'" for r in region_sel])
    where_parts.append(f"r.region_admin IN ({reg_list})")
if cat_sel:
    cat_list = ",".join([f"'{c}'" for c in cat_sel])
    where_parts.append(f"p.categorie IN ({cat_list})")
WHERE_GLOBAL = " AND ".join(where_parts)

# ── EXECUTIVE SUMMARY ───────────────────────────────────────
if menu == "Executive Summary":
    st.markdown("<div class='page-title'>Executive Summary</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Vue d'ensemble des performances Mexora</div>", unsafe_allow_html=True)

    # KPIs
    kpi_q = f"""
    SELECT
        COALESCE(SUM(f.montant_ttc),0) AS ca_total,
        COUNT(DISTINCT f.id_client) AS nb_clients,
        COUNT(*) AS nb_commandes,
        ROUND(AVG(f.montant_ttc)::numeric,0) AS panier_moyen
    FROM dwh_mexora.fait_ventes f
    JOIN dwh_mexora.dim_temps t ON f.id_date = t.id_date
    JOIN dwh_mexora.dim_region r ON f.id_region = r.id_region
    JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
    WHERE {WHERE_GLOBAL}
      AND t.annee = {annee_sel};
    """
    kpi_df = run_query(kpi_q)
    if kpi_df.empty:
        st.error("Connexion base de donnees impossible ou tables vides. Verifiez que PostgreSQL est demarre et que le pipeline ETL a ete execute.")
        st.stop()

    kpi = kpi_df.iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>CA Total {annee_sel}</div>
        <div class='metric-value'>{kpi['ca_total']:,.0f} MAD</div>
    </div>""", unsafe_allow_html=True)
    c2.markdown(f"""
    <div class='metric-card gold-card'>
        <div class='metric-label'>Clients Actifs</div>
        <div class='metric-value'>{int(kpi['nb_clients']):,}</div>
    </div>""", unsafe_allow_html=True)
    c3.markdown(f"""
    <div class='metric-card silver-card'>
        <div class='metric-label'>Commandes</div>
        <div class='metric-value'>{int(kpi['nb_commandes']):,}</div>
    </div>""", unsafe_allow_html=True)
    c4.markdown(f"""
    <div class='metric-card bronze-card'>
        <div class='metric-label'>Panier Moyen</div>
        <div class='metric-value'>{int(kpi['panier_moyen']):,} MAD</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # CA mensuel line + bar combo
    q_ev = f"""
    SELECT t.mois, t.libelle_mois, SUM(f.montant_ttc) AS ca
    FROM dwh_mexora.fait_ventes f
    JOIN dwh_mexora.dim_temps t ON f.id_date = t.id_date
    JOIN dwh_mexora.dim_region r ON f.id_region = r.id_region
    JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
    WHERE {WHERE_GLOBAL}
      AND t.annee = {annee_sel}
    GROUP BY t.mois, t.libelle_mois
    ORDER BY t.mois;
    """
    df_ev = run_query(q_ev)
    if not df_ev.empty:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=df_ev["libelle_mois"], y=df_ev["ca"], name="CA", marker_color="#38bdf8", opacity=.7), secondary_y=False)
        fig.add_trace(go.Scatter(x=df_ev["libelle_mois"], y=df_ev["ca"], name="Tendance", mode="lines+markers", line=dict(color="#0f172a", width=3)), secondary_y=True)
        fig.update_layout(title_text=f"Evolution mensuelle du CA — {annee_sel}", template="plotly_white", height=420)
        fig.update_yaxes(title_text="CA (MAD)", secondary_y=False)
        fig.update_yaxes(title_text="Tendance", secondary_y=True, showgrid=False)
        st.plotly_chart(fig, use_container_width=True)

    # Top 5 regions + Top 5 produits
    col_l, col_r = st.columns(2)

    q_reg = f"""
    SELECT r.region_admin, SUM(f.montant_ttc) AS ca
    FROM dwh_mexora.fait_ventes f
    JOIN dwh_mexora.dim_region r ON f.id_region = r.id_region
    JOIN dwh_mexora.dim_temps t ON f.id_date = t.id_date
    JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
    WHERE {WHERE_GLOBAL}
      AND t.annee = {annee_sel}
    GROUP BY r.region_admin
    ORDER BY ca DESC
    LIMIT 5;
    """
    df_reg = run_query(q_reg)
    if not df_reg.empty:
        fig_reg = px.bar(df_reg, x="ca", y="region_admin", orientation="h", text="ca",
                         title=f"Top 5 Regions — {annee_sel}",
                         color="ca", color_continuous_scale="Blues", template="plotly_white")
        fig_reg.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig_reg.update_layout(height=350, yaxis=dict(categoryorder="total ascending"))
        col_l.plotly_chart(fig_reg, use_container_width=True)

    q_prod = f"""
    SELECT p.nom_produit, SUM(f.montant_ttc) AS ca
    FROM dwh_mexora.fait_ventes f
    JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
    JOIN dwh_mexora.dim_temps t ON f.id_date = t.id_date
    JOIN dwh_mexora.dim_region r ON f.id_region = r.id_region
    WHERE {WHERE_GLOBAL}
      AND t.annee = {annee_sel}
    GROUP BY p.nom_produit
    ORDER BY ca DESC
    LIMIT 5;
    """
    df_prod = run_query(q_prod)
    if not df_prod.empty:
        fig_prod = px.bar(df_prod, x="ca", y="nom_produit", orientation="h", text="ca",
                          title=f"Top 5 Produits — {annee_sel}",
                          color="ca", color_continuous_scale="Teal", template="plotly_white")
        fig_prod.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig_prod.update_layout(height=350, yaxis=dict(categoryorder="total ascending"))
        col_r.plotly_chart(fig_prod, use_container_width=True)

# ── PAGE CA & REGIONS ──────────────────────────────────────
elif menu == "CA & Regions":
    st.markdown("<div class='page-title'>Chiffre d'Affaires & Regions</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Analyse regionale et evolution N/N-1</div>", unsafe_allow_html=True)

    # KPIs
    kpi_q = f"""
    SELECT
        SUM(f.montant_ttc) AS ca_total,
        COUNT(DISTINCT f.id_client) AS nb_clients,
        COUNT(*) AS nb_cmd
    FROM dwh_mexora.fait_ventes f
    JOIN dwh_mexora.dim_temps t ON f.id_date = t.id_date
    JOIN dwh_mexora.dim_region r ON f.id_region = r.id_region
    JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
    WHERE {WHERE_GLOBAL}
      AND t.annee = {annee_sel};
    """
    kpi = run_query(kpi_q).iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 CA Total", f"{kpi['ca_total']:,.0f} MAD")
    c2.metric("👥 Clients Uniques", f"{int(kpi['nb_clients']):,}")
    c3.metric("📦 Commandes", f"{int(kpi['nb_cmd']):,}")

    st.markdown("<hr>", unsafe_allow_html=True)

    q_ca = f"""
    SELECT t.annee, t.mois, t.libelle_mois, r.region_admin, SUM(f.montant_ttc) AS ca_ttc
    FROM dwh_mexora.fait_ventes f
    JOIN dwh_mexora.dim_temps t ON f.id_date = t.id_date
    JOIN dwh_mexora.dim_region r ON f.id_region = r.id_region
    JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
    WHERE {WHERE_GLOBAL}
      AND t.annee IN ({annee_sel}, {annee_sel-1})
    GROUP BY t.annee, t.mois, t.libelle_mois, r.region_admin
    ORDER BY t.annee, t.mois;
    """
    df_ca = run_query(q_ca)

    if not df_ca.empty:
        df_ca["periode"] = df_ca["annee"].astype(str) + "-" + df_ca["mois"].astype(str).str.zfill(2)

        fig_line = px.line(
            df_ca, x="periode", y="ca_ttc", color="region_admin",
            facet_col="annee", facet_col_wrap=2,
            title=f"Evolution mensuelle du CA par region — {annee_sel} vs {annee_sel-1}",
            labels={"ca_ttc": "CA TTC (MAD)", "periode": "Mois"},
            template="plotly_white", height=500,
        )
        fig_line.update_traces(mode="lines+markers", line=dict(width=3))
        st.plotly_chart(fig_line, use_container_width=True)

        # Bar chart region
        df_top = df_ca[df_ca["annee"] == annee_sel].groupby("region_admin")["ca_ttc"].sum().reset_index().sort_values("ca_ttc", ascending=True)
        fig_bar = px.bar(
            df_top, x="ca_ttc", y="region_admin", orientation="h",
            title=f"CA total par region — {annee_sel}",
            color="ca_ttc", color_continuous_scale="Blues", template="plotly_white",
            text="ca_ttc",
        )
        fig_bar.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig_bar.update_layout(height=400, yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("Aucune donnee disponible pour les filtres selectionnes.")

# ── PAGE TOP PRODUITS TANGER ───────────────────────────────
elif menu == "Top Produits Tanger":
    st.markdown("<div class='page-title'>Top Produits — Tanger</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Classement par trimestre et categorie</div>", unsafe_allow_html=True)

    col_a, col_t = st.columns(2)
    trim = col_t.selectbox("Trimestre", [1, 2, 3, 4], index=0)

    q_top = f"""
    SELECT p.nom_produit, p.categorie, p.marque,
           SUM(f.quantite_vendue) AS qte_totale,
           SUM(f.montant_ttc) AS ca_total,
           ROUND(AVG(f.montant_ttc)::numeric,0) AS panier_moyen
    FROM dwh_mexora.fait_ventes f
    JOIN dwh_mexora.dim_temps t ON f.id_date = t.id_date
    JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
    JOIN dwh_mexora.dim_region r ON f.id_region = r.id_region
    WHERE f.statut_commande = 'livré'
      AND r.ville = 'Tanger'
      AND t.annee = {annee_sel}
      AND t.trimestre = {trim}
    GROUP BY p.nom_produit, p.categorie, p.marque
    ORDER BY ca_total DESC
    LIMIT 10;
    """
    df_top = run_query(q_top)

    if not df_top.empty:
        c1, c2, c3 = st.columns(3)
        total_ca = df_top["ca_total"].sum()
        total_qte = df_top["qte_totale"].sum()
        c1.metric("CA Top 10", f"{total_ca:,.0f} MAD")
        c2.metric("Quantite", f"{int(total_qte):,}")
        c3.metric("Top Produit", df_top.iloc[0]["nom_produit"][:25])

        fig = px.bar(
            df_top, x="ca_total", y="nom_produit", orientation="h",
            title=f"Top 10 produits — Tanger Q{trim} {annee_sel}",
            color="categorie", text="qte_totale",
            labels={"ca_total": "CA TTC (MAD)", "nom_produit": "Produit"},
            template="plotly_white", height=500,
            color_discrete_map={"Electronique": "#0ea5e9", "Mode": "#f59e0b", "Alimentation": "#10b981"},
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Detail produits")
        st.dataframe(df_top.style.format({"ca_total": "{:,.0f}", "panier_moyen": "{:,.0f}"}), use_container_width=True)
    else:
        st.info(f"Aucun resultat pour Tanger Q{trim} {annee_sel}.")

# ── PAGE SEGMENTS CLIENTS ──────────────────────────────────
elif menu == "Segments Clients":
    st.markdown("<div class='page-title'>Analyse des Segments Clients</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Gold / Silver / Bronze — Panier moyen & repartition</div>", unsafe_allow_html=True)

    q_seg = f"""
    SELECT
        c.segment_client,
        COUNT(DISTINCT f.id_vente) AS nb_commandes,
        ROUND(SUM(f.montant_ttc)::numeric, 2) AS ca_total,
        ROUND(AVG(f.montant_ttc)::numeric, 2) AS panier_moyen,
        COUNT(DISTINCT f.id_client) AS nb_clients
    FROM dwh_mexora.fait_ventes f
    JOIN dwh_mexora.dim_client c ON f.id_client = c.id_client_sk
    JOIN dwh_mexora.dim_temps t ON f.id_date = t.id_date
    WHERE f.statut_commande = 'livré'
      AND c.est_actif = TRUE
      AND t.annee = {annee_sel}
    GROUP BY c.segment_client
    ORDER BY panier_moyen DESC;
    """
    df_seg = run_query(q_seg)

    if not df_seg.empty:
        cols = st.columns(3)
        colors_seg = {"Gold": "#fbbf24", "Silver": "#94a3b8", "Bronze": "#b45309"}
        for idx, (_, row) in enumerate(df_seg.iterrows()):
            card_class = "gold-card" if row["segment_client"]=="Gold" else "silver-card" if row["segment_client"]=="Silver" else "bronze-card"
            cols[idx].markdown(f"""
            <div class='metric-card {card_class}'>
                <div class='metric-label'>{row['segment_client']} — {int(row['nb_clients'])} clients</div>
                <div class='metric-value'>{row['panier_moyen']:,.0f} MAD</div>
                <div class='metric-delta'>CA: {row['ca_total']:,.0f} MAD | {int(row['nb_commandes'])} cmd</div>
            </div>""", unsafe_allow_html=True)

        col1, col2 = st.columns([2, 3])

        # Donut
        fig_donut = px.pie(
            df_seg, values="ca_total", names="segment_client", hole=0.55,
            title="Repartition du CA par segment",
            color="segment_client",
            color_discrete_map=colors_seg,
            template="plotly_white",
        )
        fig_donut.update_layout(height=400, showlegend=True)
        col1.plotly_chart(fig_donut, use_container_width=True)

        # Panier moyen bar
        fig_bar = px.bar(
            df_seg, x="segment_client", y="panier_moyen", text="panier_moyen",
            title="Panier moyen par segment", color="segment_client",
            color_discrete_map=colors_seg, template="plotly_white",
        )
        fig_bar.update_traces(texttemplate="%{text:,.0f} MAD", textposition="outside")
        fig_bar.update_layout(height=400)
        col2.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("Tableau detaille")
        st.dataframe(
            df_seg.style.format({
                "ca_total": "{:,.0f} MAD",
                "panier_moyen": "{:,.0f} MAD",
                "nb_commandes": "{:,}",
                "nb_clients": "{:,}",
            }),
            use_container_width=True,
        )
    else:
        st.warning("Aucune donnee client disponible.")

# ── PAGE TAUX DE RETOUR ───────────────────────────────────
elif menu == "Taux de Retour":
    st.markdown("<div class='page-title'>Taux de Retour par Categorie</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Seuils d'alerte : >5% critique, 3-5% attention, <3% OK</div>", unsafe_allow_html=True)

    q_retour = f"""
    SELECT
        p.categorie,
        COUNT(*) FILTER (WHERE f.statut_commande = 'retourné') AS nb_retours,
        COUNT(*) AS nb_total,
        ROUND(
            COUNT(*) FILTER (WHERE f.statut_commande = 'retourné') * 100.0
            / NULLIF(COUNT(*), 0), 2
        ) AS taux_retour_pct
    FROM dwh_mexora.fait_ventes f
    JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
    JOIN dwh_mexora.dim_temps t ON f.id_date = t.id_date
    WHERE t.annee = {annee_sel}
    GROUP BY p.categorie
    ORDER BY taux_retour_pct DESC;
    """
    df_ret = run_query(q_retour)

    if not df_ret.empty:
        # KPI alert cards
        cols = st.columns(len(df_ret))
        for idx, (_, row) in enumerate(df_ret.iterrows()):
            val = row["taux_retour_pct"]
            card = "alert-red" if val > 5 else "alert-ora" if val > 3 else "alert-green"
            emoji = "🔴" if val > 5 else "🟠" if val > 3 else "🟢"
            cols[idx].markdown(f"""
            <div class='metric-card {card}'>
                <div class='metric-label'>{row['categorie']}</div>
                <div class='metric-value'>{val}% {emoji}</div>
                <div class='metric-delta'>{int(row['nb_retours'])} / {int(row['nb_total'])} retours</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        colors = ["#ef4444" if v > 5 else "#f59e0b" if v > 3 else "#10b981" for v in df_ret["taux_retour_pct"]]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_ret["categorie"], y=df_ret["taux_retour_pct"],
            marker_color=colors,
            text=df_ret["taux_retour_pct"].apply(lambda x: f"{x}%"),
            textposition="outside",
        ))
        fig.add_hline(y=5, line_dash="dash", line_color="#ef4444", annotation_text="Alerte 5%")
        fig.add_hline(y=3, line_dash="dash", line_color="#f59e0b", annotation_text="Attention 3%")
        fig.update_layout(
            title="Taux de retour par categorie", yaxis_title="Taux (%)",
            template="plotly_white", height=450,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            df_ret.style.format({"taux_retour_pct": "{:.2f}%", "nb_retours": "{:,}", "nb_total": "{:,}"}),
            use_container_width=True,
        )
    else:
        st.warning("Aucune donnee de retour disponible.")

# ── PAGE EFFET RAMADAN ─────────────────────────────────────
elif menu == "Effet Ramadan":
    st.markdown("<div class='page-title'>Effet Ramadan</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Impact sur les ventes d'alimentation</div>", unsafe_allow_html=True)

    q_ramadan = f"""
    SELECT
        t.periode_ramadan,
        t.annee,
        t.mois,
        t.libelle_mois,
        SUM(f.quantite_vendue) AS volume,
        SUM(f.montant_ttc) AS ca_ttc,
        ROUND(AVG(f.montant_ttc)::numeric, 2) AS ca_moyen_jour
    FROM dwh_mexora.fait_ventes f
    JOIN dwh_mexora.dim_temps t ON f.id_date = t.id_date
    JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
    WHERE p.categorie = 'Alimentation'
      AND f.statut_commande = 'livré'
      AND t.annee >= 2022
    GROUP BY t.periode_ramadan, t.annee, t.mois, t.libelle_mois
    ORDER BY t.annee, t.mois;
    """
    df_ram = run_query(q_ramadan)

    if not df_ram.empty:
        comp = df_ram.groupby("periode_ramadan").agg({
            "volume": "sum",
            "ca_ttc": "sum",
            "ca_moyen_jour": "mean",
        }).reset_index()

        col1, col2, col3 = st.columns(3)
        ram_vol = comp.loc[comp["periode_ramadan"] == True, "volume"].sum() if True in comp["periode_ramadan"].values else 0
        non_ram_vol = comp.loc[comp["periode_ramadan"] == False, "volume"].sum() if False in comp["periode_ramadan"].values else 0
        ram_ca = comp.loc[comp["periode_ramadan"] == True, "ca_ttc"].sum() if True in comp["periode_ramadan"].values else 0

        col1.metric("🌙 Volume Ramadan", f"{ram_vol:,.0f}")
        col2.metric("📅 Volume Hors Ramadan", f"{non_ram_vol:,.0f}")
        col3.metric("💰 CA Ramadan", f"{ram_ca:,.0f} MAD")

        if non_ram_vol > 0:
            indice = round((ram_vol / non_ram_vol) * 100, 1)
            delta_color = "inverse" if indice < 100 else "normal"
            st.metric("Indice de performance Ramadan", f"{indice}%", f"{indice-100:+.1f}% vs hors Ramadan", delta_color=delta_color)

        st.markdown("<hr>", unsafe_allow_html=True)

        df_ram["periode_label"] = df_ram["periode_ramadan"].apply(lambda x: "🌙 Ramadan" if x else "📅 Hors Ramadan")
        fig = px.area(
            df_ram, x="libelle_mois", y="volume", color="periode_label",
            facet_col="annee", facet_col_wrap=2,
            title="Volume vendu d'alimentation — Ramadan vs Hors Ramadan",
            labels={"volume": "Quantite vendue", "libelle_mois": "Mois"},
            template="plotly_white", height=500,
            color_discrete_map={"🌙 Ramadan": "#f59e0b", "📅 Hors Ramadan": "#94a3b8"},
        )
        st.plotly_chart(fig, use_container_width=True)

        # Table
        st.subheader("Donnees mensuelles detaillees")
        st.dataframe(
            df_ram[["annee", "libelle_mois", "periode_label", "volume", "ca_ttc", "ca_moyen_jour"]]
            .style.format({"volume": "{:,.0f}", "ca_ttc": "{:,.0f} MAD", "ca_moyen_jour": "{:,.0f} MAD"}),
            use_container_width=True,
        )
    else:
        st.warning("Aucune donnee disponible pour l'analyse Ramadan.")

# ── FOOTER ─────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.caption(f"Mexora Analytics v2.0 PRO — {datetime.now().strftime('%Y-%m-%d')}")