# DealRadar Électronique — MVP

Ce projet fournit un premier tableau de bord local pour tester le moteur de rentabilité d'un outil de veille achat-revente.

## Ce que cette version fait
- Tableau de bord Streamlit.
- Paramètres modifiables : capital, achat maximal, ROI minimal et âge maximal.
- Chargement de données de démonstration, clairement marquées `DEMO`.
- Import CSV d'annonces.
- Calcul du coût total, du gain net estimé, du ROI et du prix d'achat maximal permettant un ROI de 40 %.
- Filtrage par catégorie, origine et seuil de rentabilité.
- Stockage local dans SQLite.

## Ce que cette version ne fait pas encore
- Aucun connecteur direct vers Leboncoin, eBay, Back Market, Amazon ou Cdiscount.
- Aucune collecte horaire automatisée.
- Aucune notification automatique.
- Aucune estimation automatique du prix de revente depuis des ventes conclues.
- Les résultats `DEMO` sont fictifs et sont volontairement exclus des opportunités qualifiées.

## Installation sous Windows
1. Installe Python 3.11 ou 3.12 depuis https://www.python.org/downloads/ et coche l'option `Add Python to PATH`.
2. Décompresse le ZIP dans un dossier, par exemple `C:\\DealRadar`.
3. Ouvre le dossier, clique dans la barre d'adresse de l'Explorateur, tape `cmd`, puis Entrée.
4. Exécute :
   ```bat
   py -m venv .venv
   .venv\\Scripts\\activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   streamlit run app.py
   ```
5. Le navigateur devrait ouvrir l'application. Si ce n'est pas le cas, ouvre l'adresse locale affichée dans le terminal, généralement `http://localhost:8501`.

## Installation sous macOS
1. Installe Python 3.11 ou 3.12 depuis https://www.python.org/downloads/.
2. Décompresse le ZIP, puis ouvre Terminal dans le dossier `dealradar_mvp`.
3. Exécute :
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   streamlit run app.py
   ```
4. Ouvre `http://localhost:8501` si le navigateur ne se lance pas automatiquement.

## Format CSV
Les colonnes requises sont :
- `listing_id`
- `product_name`
- `category`
- `platform`
- `condition` (`Neuf` ou `Occasion`)
- `model_age_years`
- `buy_price`
- `buy_fees`
- `repair_cost`
- `resale_price`
- `sell_fees`
- `outbound_shipping`

Colonnes facultatives : `data_origin`, `listing_url`, `notes`.

Pour une donnée réellement collectée, utiliser `data_origin=REAL` uniquement si elle vient effectivement d'une source réelle vérifiée. Sinon utiliser `IMPORTED` ou `DEMO` selon le cas. Le MVP ne qualifie jamais les lignes `DEMO` comme opportunités.

## Formules
- Coût total = prix d'achat + frais d'achat + remise en état.
- Gain net estimé = prix de revente - frais de vente - expédition - coût total.
- ROI net estimé = gain net estimé / coût total × 100.
- Prix d'achat maximal pour un ROI de 40 % = (revente - frais de vente - expédition) / 1,40 - frais d'achat - remise en état.

Les taxes et cotisations ne sont pas incluses automatiquement. Les estimations ne sont pas des garanties de revente ou de profit.

## Données et confidentialité
La base SQLite `dealradar.sqlite3` est créée localement au premier lancement. Ne partage pas de clés API ou de mots de passe dans un fichier CSV ou dans une conversation. Les connecteurs devront être configurés séparément avec des secrets protégés.
