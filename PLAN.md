# Projektplan – Utrikeshandel → arbetsmarknad (Del 2)

Detaljerad dataplan: [docs/data_plan.md](docs/data_plan.md). Tabeller, koder och
kolumnschema: [data/README.md](data/README.md). Detta är arbetschecklistan.

## Mål
Ett komplett flöde: **SCB API → SQLite → lag-features → regression (scikit-learn) → Streamlit**.
Bonus: publicera på Streamlit Community Cloud.

## Arkitektur

```
 SCB PxWebApi v2        SQLite (database/app.db)                 Modell                 Streamlit
 TAB1644 varor    -->   handel_varor       --+                                          app/streamlit_app.py
 TAB5147 tjänster -->   handel_tjanster      +--> merged_monthly --> model_features --> models/model.pkl
 TAB6387 AKU      -->   arbetsmarknad      --+                                          metrics.json
 (scripts/load_data.py)             (scripts/build_features.py)   (scripts/train_model.py)   predictions_test
```

## Struktur att bygga

```
config.py               Alla inställningar på ett ställe: sökvägar, SCB-tabeller/koder (se data/README.md),
                        tabellnamn, målvariabel, lag-perioder, split-datum
requirements.txt        pandas, numpy, scikit-learn, requests, joblib, streamlit, matplotlib/plotly
.gitignore              .venv/, __pycache__/  (commita database/app.db + models/ – behövs på Streamlit Cloud)
data/                   Råa API-svar (finns) – rörs aldrig
database/app.db         SQLite, skapas av load_data
models/                 model.pkl + metrics.json, skapas av train_model
src/scb_api.py          API-klient: GET med paus (rate limit), metadata, FROM()-urval för Tid,
                        json-stat2 -> DataFrame, städning till DB-schemat
src/db.py               Allt som rör SQLite: anslutning, skriv/läs tabell, finns tabell, spara prediktion
src/preprocess.py       Sammanslagning (merged_monthly) + lag-features (model_features) + sklearn-preprocessor
src/train.py            Kronologisk split, modeller, baseline, MAE/RMSE/R², spara modell + metrics
src/predict.py          Ladda modell + prediktera (används av appen)
scripts/load_data.py    Steg 1: API -> data/*.json -> DB   (gärna --offline som läser sparade json)
scripts/build_features.py  Steg 3–4
scripts/train_model.py  Steg 5–6
app/streamlit_app.py    Sidor: Data / Historik / Modell / Vad-om / Om projektet
notebooks/01_eda.py     EDA mot databasen
```

Principer:
- Allt efter steg 1 läser från **databasen**, aldrig från API:t eller json-filerna.
- Appen läser bara DB + sparad modell – ingen träning, inga API-anrop.
- Spara hela sklearn-`Pipeline`n (preprocessor + modell) med joblib, tillsammans med
  featurelistan, så att appen kan mata in råa värden i rätt kolumnordning.
- Håll kolumnnamn identiska mellan DB, träning och appens formulär – definiera dem i `config.py`.

## Arbetsordning

### 1. Datainsamling (backend)
- [ ] `python -m venv .venv`, `requirements.txt`, `pip install -r requirements.txt`, `.gitignore`
- [ ] `config.py` med tabell-ID:n och koder från data/README.md
- [ ] Öppna `https://api.scb.se/OV0104/v2beta/api/v2/tables/TAB6387/metadata?lang=sv` i webbläsaren
      och hitta koderna själv under `dimension -> <variabel> -> category -> index/label`
- [ ] `scb_api.py` nerifrån: periodnormalisering (`2010M03` → `2010-03`, `2010K1` → `2010-Q1`)
      → json-stat2-parser (testa mot `data/*.json`: `value` är en platt lista där sista dimensionen
      i `id` varierar snabbast; `itertools.product` över koderna ger samma ordning)
      → pivotera till en rad per (period, grupp) med måtten som kolumner
      → HTTP-anrop live (metadata, data) med paus mellan anrop
- [ ] `db.py` (sqlite3 + pandas `to_sql`/`read_sql`, index på `period`)
- [ ] `scripts/load_data.py` → `database/app.db` med tre tabeller. Kontroll: 0 saknade värden,
      rader = perioder × grupper (× typ_data för AKU)
- [ ] Commit

### 2. EDA
- [ ] Tidsserier: export/import och arbetslöshet 2005–. Syns 2008/2009 och 2020? Säsong?
- [ ] Korrelation mellan arbetslöshet och export förskjuten k = 0, 1, 3, 6, 12 månader –
      vid vilken fördröjning är sambandet starkast? (motiverar valet av lags)

### 3. Sammanslagning och features
- [ ] `merged_monthly`: totalraden ur varje tabell; AKU delas i O_DATA/SR_DATA-kolumner;
      tjänster (kvartal) kopplas till varje månad som **senast avslutade kvartal**
      (`pd.Period(m, "M").asfreq("Q") - 1`) – annars look-ahead
- [ ] `model_features`: lag t-1/t-3/t-6 (ev. 12-mån förändring) för export/import,
      arbetslöshet t-1 (autoregressiv), månad som kategori, target = arbetslöshet vid t, `dropna()`
- [ ] Kontroll: `arbetsloshet_t1` på rad i == target på rad i-1
- [ ] Kronologisk split (träning t.o.m. 2022-12, test därefter) – inte `train_test_split`

### 4. Modellering
- [ ] Naiv baseline: "samma som förra månaden" – modellen måste slå den
- [ ] `Pipeline([ColumnTransformer(StandardScaler + OneHotEncoder), LinearRegression])`
- [ ] Ridge/Lasso (korrelerade handelsvariabler), RandomForest (icke-linjärt, feature importance)
- [ ] MAE/RMSE/R² på test + R² på träning (överanpassning?); spara metrics.json och
      test-prediktionerna till DB (för appen)
- [ ] Prova målvariabel `arbetsloshet_sa` / `sysselsattning`, fler lags (t-12), horisont t+3
- [ ] Hyperparametrar med `TimeSeriesSplit`

### 5. Frontend
- [ ] Data (tabeller från DB), Modell (metrics + pred vs faktiskt)
- [ ] Historik (grafer, nedbrytning per varugrupp), Vad-om (formulär → prediktion → spara i DB), Om projektet
- [ ] `@st.cache_data` för DB-läsning, `@st.cache_resource` för modellen

### 6. Avslut
- [ ] Deploy: share.streamlit.io (DB + modell commitade)
- [ ] Teknisk rapport (~3 sidor) + README med resultattabell
- [ ] Stäm av med Antonio: docs/data_plan.md avsnitt 5

## Teknikval
| Del | Val | Varför |
|---|---|---|
| Datakälla | SCB PxWebApi v2, json-stat2 | Öppen, CC0, officiell statistik; v1 stängs 2026/2027 |
| Databas | SQLite via `sqlite3` + pandas | Ingen server, en fil, fungerar på Streamlit Cloud |
| ML | scikit-learn Pipeline + joblib | Preprocess + modell sparas som en enhet |
| Frontend | Streamlit (+ plotly) | Kravet i uppgiften |

## Vanliga fallgropar
- PxWebApi v2: `ContentsCode` måste alltid anges. Alla tidskoder i URL:en ger 404 – använd `FROM(2005M01)`.
- Rate limit 30 anrop/10 s – lägg en paus mellan anrop, hantera 429.
- Kvartalsdata får inte läcka framåt: en månad får bara se avslutade kvartal.
- Kronologisk split, inte slumpmässig – annars ser modellen framtiden.
- Python 3.14 är väldigt nytt – vägrar ett paket installera, skapa venv med Python 3.12.
