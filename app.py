import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from dealradar.engine import enrich_listing, validate_listing, DEFAULT_SETTINGS
from dealradar.storage import init_db, save_listings, load_listings, save_settings, load_settings

st.set_page_config(page_title="DealRadar Électronique", page_icon="📡", layout="wide")
init_db()

st.title("📡 DealRadar Électronique")
st.caption("MVP — moteur de rentabilité et tableau de bord. Les données de démonstration sont explicitement signalées.")

settings = load_settings()
with st.sidebar:
    st.header("Paramètres")
    capital = st.number_input("Capital disponible (€)", min_value=0.0, value=float(settings.get("capital", 1000)), step=100.0)
    max_buy = st.number_input("Achat maximal par article (€)", min_value=1.0, value=float(settings.get("max_buy", 500)), step=25.0)
    min_roi = st.number_input("ROI net minimal (%)", min_value=0.0, value=float(settings.get("min_roi", 40)), step=5.0)
    max_age = st.number_input("Âge maximal du modèle (années)", min_value=1, max_value=20, value=int(settings.get("max_age", 4)), step=1)
    saved = st.button("Enregistrer les paramètres", use_container_width=True)
    if saved:
        save_settings({"capital": capital, "max_buy": max_buy, "min_roi": min_roi, "max_age": max_age})
        st.success("Paramètres enregistrés.")
    st.divider()
    st.info("Les connecteurs de plateformes ne sont pas encore activés. Aucune annonce réelle n'est récupérée automatiquement par cette version.")

st.subheader("1. Ajouter des annonces")
col_demo, col_upload = st.columns([1, 1])
with col_demo:
    st.markdown("**Données de démonstration**")
    st.write("Charge cinq exemples fictifs pour tester les filtres et les calculs.")
    if st.button("Charger les exemples fictifs", use_container_width=True):
        demo = pd.DataFrame([
            {"listing_id":"DEMO-001","product_name":"Appareil photo hybride récent","category":"Photo et vidéo","platform":"DEMO — Leboncoin","condition":"Occasion","model_age_years":2,"buy_price":300,"buy_fees":8,"repair_cost":0,"resale_price":520,"sell_fees":52,"outbound_shipping":12,"data_origin":"DEMO","listing_url":"","notes":"Exemple fictif — prix non vérifiés"},
            {"listing_id":"DEMO-002","product_name":"Ordinateur portable premium","category":"Informatique","platform":"DEMO — eBay","condition":"Occasion","model_age_years":2,"buy_price":250,"buy_fees":10,"repair_cost":0,"resale_price":430,"sell_fees":43,"outbound_shipping":10,"data_origin":"DEMO","listing_url":"","notes":"Exemple fictif — prix non vérifiés"},
            {"listing_id":"DEMO-003","product_name":"Drone compact récent","category":"Drones et objets connectés","platform":"DEMO — Amazon","condition":"Neuf","model_age_years":3,"buy_price":260,"buy_fees":0,"repair_cost":0,"resale_price":370,"sell_fees":37,"outbound_shipping":10,"data_origin":"DEMO","listing_url":"","notes":"Exemple fictif — prix non vérifiés"},
            {"listing_id":"DEMO-004","product_name":"Console de jeu récente","category":"Gaming","platform":"DEMO — Cdiscount","condition":"Neuf","model_age_years":2,"buy_price":320,"buy_fees":0,"repair_cost":0,"resale_price":400,"sell_fees":40,"outbound_shipping":10,"data_origin":"DEMO","listing_url":"","notes":"Exemple fictif — prix non vérifiés"},
            {"listing_id":"DEMO-005","product_name":"Smartphone haut de gamme","category":"Smartphones et tablettes","platform":"DEMO — Back Market","condition":"Occasion","model_age_years":3,"buy_price":280,"buy_fees":8,"repair_cost":0,"resale_price":390,"sell_fees":39,"outbound_shipping":8,"data_origin":"DEMO","listing_url":"","notes":"Exemple fictif — prix non vérifiés"},
        ])
        save_listings(demo)
        st.success("Exemples ajoutés. Ils sont marqués DEMO et ne sont pas des annonces réelles.")
with col_upload:
    st.markdown("**Importer un fichier CSV**")
    st.write("Importe des annonces collectées légalement ou exportées depuis tes propres sources.")
    uploaded = st.file_uploader("Fichier CSV", type=["csv"], help="Le fichier doit contenir les colonnes décrites dans le guide.")
    if uploaded is not None:
        try:
            incoming = pd.read_csv(uploaded)
            required = ["listing_id","product_name","category","platform","condition","model_age_years","buy_price","buy_fees","repair_cost","resale_price","sell_fees","outbound_shipping"]
            missing = [c for c in required if c not in incoming.columns]
            if missing:
                st.error("Colonnes manquantes : " + ", ".join(missing))
            else:
                if "data_origin" not in incoming.columns:
                    incoming["data_origin"] = "IMPORTED"
                if "listing_url" not in incoming.columns:
                    incoming["listing_url"] = ""
                if "notes" not in incoming.columns:
                    incoming["notes"] = ""
                if st.button("Importer ces lignes", use_container_width=True):
                    save_listings(incoming)
                    st.success(f"{len(incoming)} lignes importées.")
        except Exception as exc:
            st.error(f"Impossible de lire le CSV : {exc}")

st.divider()
st.subheader("2. Opportunités et rentabilité")
raw = load_listings()
if raw.empty:
    st.warning("Aucune annonce pour l'instant. Charge les exemples fictifs ou importe un CSV.")
    st.stop()

enriched = []
for _, row in raw.iterrows():
    item = enrich_listing(row.to_dict())
    item["eligible"] = validate_listing(item, max_buy=max_buy, min_roi=min_roi, max_age=max_age)
    enriched.append(item)
df = pd.DataFrame(enriched)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Annonces enregistrées", len(df))
k2.metric("Opportunités qualifiées", int(df["eligible"].sum()))
k3.metric("Capital disponible", f"{capital:,.0f} €".replace(",", " "))
k4.metric("Sources réelles importées", int((df["data_origin"].fillna("IMPORTED").str.upper() != "DEMO").sum()))

filter1, filter2, filter3 = st.columns([2, 1, 1])
categories = ["Toutes"] + sorted([x for x in df["category"].dropna().unique().tolist()])
selected_cat = filter1.selectbox("Catégorie", categories)
origins = ["Toutes"] + sorted([x for x in df["data_origin"].dropna().unique().tolist()])
selected_origin = filter2.selectbox("Origine", origins)
show_only = filter3.checkbox("ROI conforme uniquement", value=True)

view = df.copy()
if selected_cat != "Toutes":
    view = view[view["category"] == selected_cat]
if selected_origin != "Toutes":
    view = view[view["data_origin"] == selected_origin]
if show_only:
    view = view[view["eligible"]]
if not view.empty:
    view = view.sort_values("roi_net_pct", ascending=False)

display_cols = ["product_name","platform","category","condition","model_age_years","buy_price","total_cost","resale_price","net_profit","roi_net_pct","data_origin","eligible"]
labels = {"product_name":"Produit","platform":"Plateforme/source","category":"Catégorie","condition":"État","model_age_years":"Âge modèle","buy_price":"Achat (€)","total_cost":"Coût total (€)","resale_price":"Revente cible (€)","net_profit":"Gain net estimé (€)","roi_net_pct":"ROI net (%)","data_origin":"Origine","eligible":"Qualifiée"}
if view.empty:
    st.info("Aucune annonce ne correspond aux filtres actuels.")
else:
    shown = view[display_cols].rename(columns=labels).copy()
    for col in ["Achat (€)","Coût total (€)","Revente cible (€)","Gain net estimé (€)","ROI net (%)"]:
        shown[col] = shown[col].round(2)
    st.dataframe(shown, use_container_width=True, hide_index=True)

st.caption("Le ROI est une estimation avant fiscalité/cotisations. Les données DEMO sont fictives. Une annonce n'est pas validée par le seul fait que son ROI calculé dépasse le seuil.")

with st.expander("Détail d'une annonce"):
    ids = df["listing_id"].astype(str).tolist()
    chosen = st.selectbox("Choisir un identifiant", ids)
    detail = df[df["listing_id"].astype(str) == chosen].iloc[0].to_dict()
    st.json({k: (v.item() if hasattr(v, "item") else v) for k, v in detail.items() if k not in ["created_at"]})
    url = str(detail.get("listing_url","") or "")
    if url.startswith("http"):
        st.link_button("Ouvrir l'annonce source", url)

st.subheader("3. Limites de cette version")
st.markdown("""
- Pas encore de connexion directe aux cinq plateformes.
- Pas de collecte horaire active ni d'envoi automatique d'alertes.
- Le prix de revente doit être renseigné/importé ; il n'est pas encore estimé à partir de comparables réels.
- Les annonces et prix fictifs ne doivent jamais servir à prendre une décision d'achat.
""")
