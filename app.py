import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from dealradar.engine import enrich_listing, validate_listing, DEFAULT_SETTINGS
from dealradar.storage import init_db, save_listings, load_listings, save_settings, load_settings

st.set_page_config(page_title="DealRadar — chasse aux bonnes affaires", page_icon="📡", layout="wide")
st.markdown("""
<style>
.dr-sidebrand { background:linear-gradient(120deg,#071b49,#1457e8,#0bb9e8); color:white; padding:1rem; border-radius:16px; margin:.2rem 0 1rem; }
.dr-sidebrand b { font-size:1.35rem; letter-spacing:-.5px; }
.dr-sidebrand b span { color:#35d5ff; }
.dr-sidebrand small { display:block; font-size:.62rem; letter-spacing:1px; margin-top:.3rem; opacity:.9; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { background:rgba(255,255,255,.78); border:1px solid #dce8ff; padding:.55rem .65rem; border-radius:12px; margin:.25rem 0; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) { background:#e0ebff; border-color:#7da7ff; color:#104bd0; font-weight:800; }
.stApp { background: linear-gradient(180deg,#f1f6ff 0%,#ffffff 48%,#f7faff 100%); }
.block-container { padding-top:1.3rem; padding-bottom:3rem; max-width:1240px; }
.dr-hero { background:linear-gradient(120deg,#071b49 0%,#104bd0 68%,#0bb9e8 100%); color:white; padding:1.55rem 1.6rem; border-radius:24px; margin-bottom:1.15rem; box-shadow:0 12px 32px rgba(20,87,232,.18); }
.dr-brand { font-size:clamp(2rem,5vw,3.1rem); font-weight:850; letter-spacing:-1.5px; line-height:1.1; }
.dr-brand span { color:#35d5ff; }
.dr-tagline { font-size:1rem; opacity:.94; margin-top:.45rem; }
.dr-pill { display:inline-block; background:#ffca3a; color:#17264b; padding:.32rem .75rem; border-radius:999px; font-weight:800; font-size:.78rem; margin-top:.85rem; }
div[data-testid="stMetric"] { background:white; border:1px solid #e0eaff; border-radius:18px; padding:1rem 1.1rem; box-shadow:0 5px 18px rgba(18,54,120,.06); }
div[data-testid="stMetricLabel"] { color:#52658a; font-weight:650; }
div[data-testid="stMetricValue"] { color:#104bd0; font-weight:850; }
.stButton > button, .stDownloadButton > button { border-radius:13px; border:0; background:linear-gradient(110deg,#1457e8,#08aeea); color:white; font-weight:750; min-height:2.7rem; box-shadow:0 5px 13px rgba(20,87,232,.15); }
.stButton > button:hover { border:0; color:white; filter:brightness(1.06); transform:translateY(-1px); }
div[data-testid="stFileUploader"] section { border:2px dashed #b8cdfc; border-radius:16px; background:#f8fbff; }
div[data-testid="stDataFrame"] { border:1px solid #e0eaff; border-radius:14px; overflow:hidden; }
div[data-testid="stExpander"] { border:1px solid #e0eaff; border-radius:14px; background:white; }
h2,h3 { color:#102b62; letter-spacing:-.3px; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#eef5ff,#ffffff); }
@media(max-width:700px) { .block-container{padding-left:.8rem;padding-right:.8rem;} .dr-hero{padding:1.2rem;border-radius:18px;} }
</style>
<div class="dr-hero">
  <div class="dr-brand">📡 Deal<span>Radar</span> 🎁</div>
  <div class="dr-tagline">On traque les bonnes affaires. Tu gardes les meilleurs deals !</div>
  <div class="dr-pill">⚡ CHASSE AUX OPPORTUNITÉS</div>
</div>
""", unsafe_allow_html=True)
init_db()

st.caption("Ton tableau de chasse aux bonnes affaires : estime la marge, filtre les opportunités et garde le cap sur ton budget.")

settings = load_settings()
with st.sidebar:
    st.markdown("""
    <div class="dr-sidebrand">📡 <b>Deal<span>Radar</span></b><small>TON COACH DES BONNES AFFAIRES</small></div>
    """, unsafe_allow_html=True)
    st.markdown("### 🧭 Navigation")
    page = st.radio(
        "Menu principal",
        ["🏠  Tableau de bord", "➕  Ajouter des annonces", "🎯  Opportunités", "🔎  Recherche automatique", "⚙️  Paramètres", "💡  Guide & aide"],
        label_visibility="collapsed",
        key="dr_navigation"
    )
    st.markdown("---")
    st.markdown("#### 🎯 Tes critères")
    if page == "⚙️  Paramètres":
        capital = st.number_input("Capital disponible (€)", min_value=0.0, value=float(settings.get("capital", 1000)), step=100.0)
        max_buy = st.number_input("Achat maximal par article (€)", min_value=1.0, value=float(settings.get("max_buy", 500)), step=25.0)
        min_roi = st.number_input("ROI net minimal (%)", min_value=0.0, value=float(settings.get("min_roi", 40)), step=5.0)
        max_age = st.number_input("Âge maximal du modèle (années)", min_value=1, max_value=20, value=int(settings.get("max_age", 4)), step=1)
        if st.button("💾 Enregistrer les paramètres", use_container_width=True):
            save_settings({"capital": capital, "max_buy": max_buy, "min_roi": min_roi, "max_age": max_age})
            st.success("Paramètres enregistrés.")
    else:
        capital = float(settings.get("capital", 1000))
        max_buy = float(settings.get("max_buy", 500))
        min_roi = float(settings.get("min_roi", 40))
        max_age = int(settings.get("max_age", 4))
        st.caption(f"Capital : **{capital:,.0f} €**".replace(",", " "))
        st.caption(f"ROI cible : **{min_roi:.0f} %**")
    st.markdown("---")
    st.caption("🟢 Interface MVP • Sources automatiques en préparation")

if page == "🔎  Recherche automatique":
    from urllib.parse import quote_plus
    import base64
    import json
    import urllib.parse
    import urllib.request
    import urllib.error

    st.markdown("## 🔎 Chasse aux bonnes affaires")
    st.write("Recherche par mot-clé et comparaison multi-plateformes.")
    with st.form("dr_search_form"):
        search_term = st.text_input("Quel produit recherches-tu ?", placeholder="Ex. : Sony A7 III, iPhone 15, PS5")
        search_max_price = st.number_input("Prix d'achat maximal (€)", min_value=1.0, value=float(max_buy), step=25.0)
        search_limit = st.select_slider("Nombre de résultats eBay", options=[5, 10, 20, 50], value=20)
        run_search = st.form_submit_button("🚀 Lancer la recherche", use_container_width=True)

    if run_search and not search_term.strip():
        st.warning("Saisis un nom de produit pour lancer la recherche.")
    if run_search and search_term.strip():
        term = search_term.strip()
        st.markdown("### 🌐 Plateformes à explorer")
        link_cols = st.columns(3)
        external_searches = [
            ("🟠 Leboncoin", "https://www.leboncoin.fr/recherche?text=" + quote_plus(term)),
            ("🟡 Amazon", "https://www.amazon.fr/s?k=" + quote_plus(term)),
            ("🔵 eBay", "https://www.ebay.fr/sch/i.html?_nkw=" + quote_plus(term) + "&_udhi=" + quote_plus(str(int(search_max_price)))),
            ("🟢 Back Market", "https://www.backmarket.fr/fr-fr/search?q=" + quote_plus(term)),
            ("🔴 Cdiscount", "https://www.cdiscount.com/search/10/" + quote_plus(term) + ".html"),
        ]
        for i, (label, url) in enumerate(external_searches):
            with link_cols[i % 3]:
                st.link_button(label, url, use_container_width=True)

        st.markdown("### 🟠 Analyse rapide d’une annonce Leboncoin")
        st.caption("Ouvre une recherche Leboncoin ci-dessus, choisis une annonce réelle, puis renseigne ses chiffres ici. DealRadar ne collecte pas automatiquement les annonces Leboncoin.")
        with st.form("dr_leboncoin_profit_form"):
            lbc_url = st.text_input("Lien de l’annonce (facultatif)", placeholder="https://www.leboncoin.fr/...")
            lbc_buy = st.number_input("Prix demandé (€)", min_value=0.0, value=100.0, step=10.0)
            lbc_buy_fees = st.number_input("Frais à l’achat / livraison (€)", min_value=0.0, value=5.0, step=1.0)
            lbc_repair = st.number_input("Réparation ou remise en état (€)", min_value=0.0, value=0.0, step=5.0)
            lbc_resale = st.number_input("Prix de revente estimé (€)", min_value=0.0, value=150.0, step=10.0)
            lbc_sell_fees = st.number_input("Frais de vente estimés (€)", min_value=0.0, value=15.0, step=1.0)
            lbc_shipping = st.number_input("Autres frais / expédition (€)", min_value=0.0, value=5.0, step=1.0)
            lbc_target_roi = st.number_input("ROI net minimum souhaité (%)", min_value=0.0, value=float(min_roi), step=5.0)
            lbc_calculate = st.form_submit_button("🧮 Calculer la rentabilité", use_container_width=True)
        if lbc_calculate:
            lbc_total_cost = lbc_buy + lbc_buy_fees + lbc_repair + lbc_shipping
            lbc_net_profit = lbc_resale - lbc_total_cost - lbc_sell_fees
            lbc_roi = (lbc_net_profit / lbc_total_cost * 100) if lbc_total_cost > 0 else 0.0
            m1, m2, m3 = st.columns(3)
            m1.metric("Coût total", f"{lbc_total_cost:.2f} €")
            m2.metric("Gain net estimé", f"{lbc_net_profit:.2f} €")
            m3.metric("ROI net estimé", f"{lbc_roi:.1f} %")
            if lbc_net_profit <= 0:
                st.error("Cette opération semble déficitaire avec les hypothèses saisies.")
            elif lbc_roi >= lbc_target_roi:
                st.success("Cette annonce atteint ton objectif de ROI estimé. Vérifie l’état, l’authenticité et le prix de revente avant tout achat.")
            else:
                st.warning("Le gain estimé est positif, mais le ROI reste inférieur à ton objectif.")
            if lbc_url.strip().startswith("https://www.leboncoin.fr/") or lbc_url.strip().startswith("https://leboncoin.fr/"):
                st.link_button("🔗 Revoir l’annonce Leboncoin", lbc_url.strip())
            st.caption("Estimation indicative avant fiscalité, cotisations, retours, litiges et temps passé. Le prix de revente n’est pas vérifié automatiquement.")
        
        st.markdown("### ⚡ Résultats eBay dans DealRadar")
        try:
            ebay_client_id = st.secrets.get("EBAY_CLIENT_ID", "")
            ebay_client_secret = st.secrets.get("EBAY_CLIENT_SECRET", "")
        except Exception:
            ebay_client_id, ebay_client_secret = "", ""

        if not ebay_client_id or not ebay_client_secret:
            st.info("Pour afficher les annonces eBay directement ici, il faut configurer les clés API dans les secrets du déploiement. Les recherches sur les sites restent accessibles via les boutons.")
            st.markdown("[Ouvrir le guide officiel eBay pour les clés API](https://developer.ebay.com/api-docs/static/oauth-credentials.html)")
        else:
            try:
                auth = base64.b64encode(f"{ebay_client_id}:{ebay_client_secret}".encode()).decode()
                token_req = urllib.request.Request(
                    "https://api.ebay.com/identity/v1/oauth2/token",
                    data=urllib.parse.urlencode({"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}).encode(),
                    headers={"Authorization": "Basic " + auth, "Content-Type": "application/x-www-form-urlencoded"},
                    method="POST"
                )
                with urllib.request.urlopen(token_req, timeout=20) as response:
                    token_data = json.loads(response.read().decode())
                query = urllib.parse.urlencode({
                    "q": term,
                    "limit": int(search_limit),
                    "filter": f"price:[0..{search_max_price}],priceCurrency:EUR"
                })
                api_req = urllib.request.Request(
                    "https://api.ebay.com/buy/browse/v1/item_summary/search?" + query,
                    headers={"Authorization": "Bearer " + token_data["access_token"], "X-EBAY-C-MARKETPLACE-ID": "EBAY_FR", "Accept": "application/json"}
                )
                with urllib.request.urlopen(api_req, timeout=25) as response:
                    payload = json.loads(response.read().decode())
                items = payload.get("itemSummaries", [])
                if not items:
                    st.warning("Aucun résultat eBay trouvé avec ces critères.")
                else:
                    st.success(f"{len(items)} annonces eBay récupérées.")
                    for item in items:
                        title = item.get("title", "Annonce eBay")
                        price_info = item.get("price", {})
                        price = price_info.get("value", "—")
                        currency = price_info.get("currency", "EUR")
                        item_url = item.get("itemWebUrl", "https://www.ebay.fr")
                        image_url = item.get("image", {}).get("imageUrl")
                        with st.container(border=True):
                            item_cols = st.columns([1, 3])
                            with item_cols[0]:
                                if image_url:
                                    st.image(image_url, use_container_width=True)
                            with item_cols[1]:
                                st.markdown("**" + title + "**")
                                st.markdown(f"### {price} {currency}")
                                st.link_button("Voir l'annonce ↗", item_url)
                                st.caption("Frais de livraison éventuels à vérifier sur l'annonce.")
            except urllib.error.HTTPError as exc:
                st.error(f"eBay a refusé la requête (HTTP {exc.code}). Vérifie l'accès Browse API et les clés Production.")
            except Exception as exc:
                st.error("La recherche eBay n'a pas abouti. Vérifie les clés et l'accès API dans les paramètres de déploiement.")
                st.caption(f"Détail technique : {type(exc).__name__}")

    st.markdown("---")
    st.caption("Leboncoin, Amazon, Back Market et Cdiscount sont pour l'instant ouverts via leurs pages de recherche. Leur collecte intégrée nécessite des API autorisées ou des connecteurs tiers compatibles. Aucun résultat fictif n'est affiché.")
    st.stop()

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
