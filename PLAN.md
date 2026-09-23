
# Projektplan – Utrikeshandel → arbetsmarknad (Del 2)

**Kurs:** AI - teori och tillämpning (MAI24HA/MAI25HA)
**Metod:** Regression (klassisk ML, inga tidsseriemodeller – tidsberoendet hanteras via lag-features)

Tabeller, koder och kolumnschema: [data/README.md](data/README.md).

**Detta är den enda checklistan för hela arbetet.** Koden i `src/`, `scripts/`, `app/` och
`notebooks/` innehåller inga kommentarer eller TODO:s – allt som ska göras står här.

## Syfte och hypotes
Kan förändringar i Sveriges export/import av varor och tjänster förklara/prediktera
arbetsmarknadsutvecklingen (arbetslöshet, sysselsättningsgrad) några månader senare?
Testas som ett rent regressionsproblem: kontinuerligt utfall, med historisk handelsdata
(inklusive fördröjda lag-värden) som förklarande variabler.

## Data
Alla källor hämtas via **SCB:s öppna API, PxWebApi v2** (json-stat2, CC0). v2 är inte
bakåtkompatibelt med v1, som stängs vid årsskiftet 2026/2027 – gamla v1-exempel går inte att återanvända.
- API-rot: `https://api.scb.se/OV0104/v2beta/api/v2/`
- Hitta tabeller och testa frågor: `https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/`
- Endpoints: `tables?query=...` (sök), `tables/{id}/metadata` (variabler/koder), `tables/{id}/data`
  (data via GET med `valueCodes[variabel]=...`)
- Rate limits: max 150 000 celler per uttag, max 30 anrop per 10 s (per IP)

| Datamängd | SCB-tabell | Frekvens | Innehåll |
|---|---|---|---|
| Utrikeshandel med varor | TAB1644 | Månad | Export/import per SITC-varugrupp (mnkr) |
| Utrikeshandel med tjänster | TAB5147 | Kvartal | Export/import per tjänsteslag (mnkr) |
| Arbetsmarknad (AKU) | TAB6387 | Månad | Arbetslöshet %, sysselsättningsgrad %, per kön |

Tidsomfång: fr.o.m. 2005 (`config.START_YEAR`), så att det finns tillräckligt många
observationer kvar efter `dropna()` på lag-featurerna. SCB byter ibland tabell-ID vid
metodändringar (t.ex. AKU:s brott 2021) – verifiera mot metadata om ett anrop slutar fungera.

## Status (2026-09-23)

**Klart:** förberedelserna och steg 1 (datainsamling). `config.py` (tabell-ID:n och koder verifierade mot API:ts metadata
2026-09-18), `requirements.txt`, `.gitignore`, `data/README.md` och de tre
råa API-svaren i `data/` (hämtade manuellt 2026-09-18). Virtuell miljö skapad och paketen
installerade. `src/scb_api.py`, `src/db.py` och `scripts/load_data.py` är klara och testade (offline och
live, 2026-09-23). `database/app.db` innehåller de tre rådatatabellerna. Övriga moduler är
fortfarande **skelett**: bara signaturer, kropparna `raise NotImplementedError`.

**Kvar:** steg 2 och framåt. `models/` är tom, och koden är stagad men inte committad ännu.


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
config.py               (finns) Alla inställningar: sökvägar, SCB-tabeller/koder, tabellnamn,
                        målvariabel, lag-perioder, split-datum – förslagen under "Modellering" får ändras
requirements.txt        (finns)
.gitignore              (finns) database/app.db + models/ commitas medvetet – behövs på Streamlit Cloud
data/                   (finns) Råa API-svar, hämtade 2026-09-18 – rörs aldrig
database/app.db         (finns) SQLite, skapas av load_data
models/                 (tom) model.pkl + metrics.json, skapas av train_model
src/scb_api.py          (klar) API-klient: GET med paus (rate limit), metadata, FROM()-urval för Tid,
                        json-stat2 -> DataFrame, städning till DB-schemat
src/db.py               (klar) Allt som rör SQLite: anslutning, skriv/läs tabell, finns tabell, spara prediktion
src/preprocess.py       (skelett) Sammanslagning (merged_monthly) + lag-features (model_features) + sklearn-preprocessor
src/train.py            (skelett) Kronologisk split, modeller, baseline, MAE/RMSE/R², spara modell + metrics
src/predict.py          (skelett) Ladda modell + prediktera (används av appen)
scripts/load_data.py    (klar) Steg 1: API -> data/*.json -> DB   (gärna --offline som läser sparade json)
scripts/build_features.py  (skelett) Steg 3–4
scripts/train_model.py  (skelett) Steg 5–6
app/streamlit_app.py    (skelett) Sidor: Data / Historik / Modell / Vad-om / Om projektet
notebooks/01_eda.py     (skelett) EDA mot databasen
```

Principer:
- Allt efter steg 1 läser från **databasen**, aldrig från API:t eller json-filerna.
- Appen läser bara DB + sparad modell – ingen träning, inga API-anrop.
- Spara hela sklearn-`Pipeline`n (preprocessor + modell) med joblib, tillsammans med
  featurelistan, så att appen kan mata in råa värden i rätt kolumnordning.
- Håll kolumnnamn identiska mellan DB, träning och appens formulär – definiera dem i `config.py`.

## Arbetsordning

### 1. Datainsamling (backend)
- [x] `python -m venv .venv` + `pip install -r requirements.txt`
- [x] Läs igenom `config.py` – där finns tabell-ID:n, koder och hur du verifierar dem
- [x] Öppna `https://api.scb.se/OV0104/v2beta/api/v2/tables/TAB6387/metadata?lang=sv` i webbläsaren
      och hitta koderna själv under `dimension -> <variabel> -> category -> index/label`
      (klart 2026-09-18: koderna ligger i `config.SCB_DATASETS` och är dokumenterade i `data/README.md`)
- [x] Råsvaren hämtade manuellt till `data/*.json` – bygg och testa parsern mot dem innan live-anrop
- [x] `scb_api.py` – en funktion i taget, nerifrån. De tre första kräver inget nätverk: utveckla och
      testa dem mot de sparade `data/*.json`, och skriv HTTP-anropen först när de fungerar.
  - [x] `normalize_period` – SCB:s tidskod till DB-format: `2010M03` → `2010-03`, `2010K1` → `2010-Q1`
  - [x] `parse_jsonstat2` – platt `value`-lista → lång DataFrame (en kolumn per dimension + `value`).
        Svaret är en tabell utrullad till en lista: `id` ger dimensionsordningen, `size` antalet koder
        per dimension, och **sista dimensionen varierar snabbast**. `itertools.product` över koderna
        i `id`-ordning ger därför exakt samma ordning som `value`.
        Kontroll: `len(value)` == produkten av `size` (t.ex. tjänster: 2 × 13 × 1 × 86 = 2236).
  - [x] `tidy_dataframe` – lång DataFrame → DB-schemat: en rad per (period, grupp) med måtten
        (`measure_dim` via `measure_map`) som kolumner, klartext i `grupp_namn`, värden skalade med `scale`
  - [x] `_get` / `get_metadata` / `get_data` – live mot API:t, med paus mellan anrop (30 anrop/10 s)
        och omförsök vid 429
- [x] `db.py` (sqlite3 + pandas `to_sql`/`read_sql`, index på `period`)
- [x] `scripts/load_data.py` → `database/app.db` med tre tabeller. Kontroll: 0 saknade värden,
      rader = perioder × grupper (× typ_data för AKU)
      (resultat: varor 2838 rader, tjänster 1086, AKU 1560. Tjänsteslag D1 saknar data 2005–2012,
      de 32 raderna tas bort – totalraden D0 är komplett)
- [ ] Commit

### 2. EDA
Allt görs i `notebooks/01_eda.py`. Kör filen med `python notebooks/01_eda.py`, eller cell för
cell (`# %%`) i VS Code. Läs **bara** från databasen med `db.read_table` – inte från json-filerna.

#### 2.1 Förberedelser
- [ ] Lägg till `from src import db` och `import pandas as pd`, `import matplotlib.pyplot as plt`
      under `import config`
- [ ] Skapa en mapp för figurerna (t.ex. `figurer/`) – de behövs till rapporten
- [ ] Kör filen en gång och kontrollera att importerna fungerar innan du går vidare

#### 2.2 Läs data (cellen "Läs data")
- [ ] Läs `handel_varor` med bara totalraden (`grupp='0-9'`)
- [ ] Läs `handel_tjanster` med bara totalraden (`grupp='D0'`)
- [ ] Läs `arbetsmarknad` med totalraden för båda könen (`grupp='1+2'`) – behåll både `O_DATA` och `SR_DATA`
- [ ] Skriv ut `.head()`, `.shape` och första/sista `period` för varje tabell – stämmer det med
      utskriften från `load_data.py`?
- [ ] Kolumnen `period` är text (`"2010-03"`). Gör en ny kolumn med riktiga datum så att
      graferna blir rätt: `pd.to_datetime(...)` fungerar för månader. Kvartal (`"2010-Q1"`)
      kräver `pd.PeriodIndex(..., freq="Q").to_timestamp()`

#### 2.3 Tidsserier (cellen "Tidsserier")
- [ ] Graf 1: export och import av varor över tid (två linjer i samma figur)
- [ ] Graf 2: export och import av tjänster över tid (kvartal)
- [ ] Graf 3: arbetslöshet `O_DATA` och `SR_DATA` i samma figur – vad gör säsongrensningen?
- [ ] Alla grafer: titel, axeltitlar med enhet (mnkr / %), förklaring (`plt.legend()`),
      "Källa: SCB". Spara med `plt.savefig(...)` innan `plt.show()`
- [ ] Svara skriftligt (i PLAN.md eller rapportutkastet):
  - [ ] Syns finanskrisen 2008/2009 och pandemin 2020 i handeln? I arbetslösheten?
  - [ ] Kommer förändringen i arbetslösheten samtidigt som i handeln, eller efteråt?
  - [ ] Finns ett säsongsmönster? Tips: gruppera `O_DATA` på månad (`.dt.month`) och ta
        medelvärdet – vilka månader är arbetslösheten högst/lägst?

#### 2.4 Korrelation vid olika fördröjningar (cellen "Korrelation")
- [ ] Slå ihop export (varor, totalt) och arbetslöshet (`O_DATA`) till en tabell med `pd.merge` på `period`
- [ ] För k = 0, 1, 3, 6, 12: flytta exporten k månader bakåt med `.shift(k)` och räkna
      korrelationen med arbetslösheten (`.corr()`). Spara resultaten i en lista eller dict
- [ ] Skriv ut resultatet som en tabell och gör ett stapeldiagram (k på x-axeln, korrelation på y-axeln)
- [ ] Gör om samma sak med exporten som **procentuell förändring mot samma månad året innan**
      (`.pct_change(12)`). Båda serierna har trender över tid, och två trender kan ge hög
      korrelation utan att ha med varandra att göra – jämför resultaten
- [ ] Svara skriftligt:
  - [ ] Vid vilken fördröjning är sambandet starkast? Är det positivt eller negativt?
  - [ ] Stödjer det `config.LAGS = [1, 3, 6]`, eller bör något läggas till (t.ex. 12)?
- [ ] (Valfritt) Samma analys med import i stället för export

#### 2.5 Nedbrytning per varugrupp (cellen "Nedbrytning per varugrupp")
- [ ] Läs `handel_varor` **utan** totalraden (`grupp != '0-9'`)
- [ ] Rita export över tid per varugrupp (en linje per `grupp_namn`). Tips: `pivot` med
      `period` som index och `grupp_namn` som kolumner, sedan `.plot()`
- [ ] Vilka 2–3 varugrupper är störst? Vilken föll mest 2009 och 2020?

#### 2.6 Avslut
- [ ] Hela filen går att köra uppifrån och ned utan fel
- [ ] Skriv 3–5 meningar med de viktigaste slutsatserna – de används i rapporten och på appens
      Om projektet-sida
- [ ] Uppdatera `config.LAGS` om korrelationen pekar på andra fördröjningar
- [ ] Commit

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
- [ ] Dokumentera resonemanget: varför respektive modell, vilken presterade bäst och varför
- [ ] Var missar modellen (vilken period/bransch är svårast)? Konkreta förbättringsförslag
      (fler features, branschspecifik modell, fler lag-perioder)

### 5. Frontend (`app/streamlit_app.py`)
Förutsättning: steg 1–4 klara. Appen läser **bara** DB + sparad modell – ingen träning, inga
API-anrop, inget som läser `data/*.json`. Kolumnnamn från `config.py`, inte hårdkodade.
Kör lokalt: `streamlit run app/streamlit_app.py`

#### 5.0 Grund
- [ ] Importera `db` och `predict` från `src` (sys.path-raden finns redan)
- [ ] `st.set_page_config` – titel, `layout="wide"`, ev. ikon
- [ ] Sidomeny med `st.sidebar.radio` (finns) – sidordning Data / Historik / Modell / Vad-om / Om projektet
- [ ] Felhantering: om `config.DB_PATH` eller `config.MODEL_PATH` saknas → `st.error` med vilket skript som ska köras, `st.stop()`

#### 5.1 Cachade laddare (överst i filen)
- [ ] `@st.cache_data` `load_table(name)` → `db.read_table(name)`
- [ ] `@st.cache_data` `load_metrics()` → `predict.load_metrics()`
- [ ] `@st.cache_resource` `load_model()` → `predict.load_model()` (modellen är inte serialiserbar → resource, inte data)
- [ ] Knapp i sidomenyn "Rensa cache" (`st.cache_data.clear()`) – praktiskt när DB byggts om

#### 5.2 Sidan Data
- [ ] Dropdown över tabeller från `db.list_tables()`
- [ ] Visa vald tabell med `st.dataframe` (`use_container_width=True`)
- [ ] Nyckeltal ovanför: antal rader, antal perioder, första/sista period, antal grupper
- [ ] Filter: grupp (`grupp_namn`) och periodintervall (slider eller två selectbox)
- [ ] Kort text per tabell: SCB-tabell-ID, frekvens, enhet (mnkr / %) – från `data/README.md`
- [ ] Knapp "Ladda ner CSV" (`st.download_button`)

#### 5.3 Sidan Historik
- [ ] Läs `merged_monthly`
- [ ] Tidsintervall-filter (delas med Data-sidan via en hjälpfunktion)
- [ ] Graf 1 (plotly): export_varor & import_varor över tid, ev. handelsnetto_varor som egen kurva/stapel
- [ ] Graf 2: arbetsloshet vs arbetsloshet_sa (visa att säsongrensning tar bort svängningarna)
- [ ] Graf 3: export & arbetslöshet i samma figur med två y-axlar (motiverar sambandet – 2008/2009, 2020)
- [ ] Nedbrytning per varugrupp: läs `handel_varor`, filtrera bort totalraden
      (`config.SCB_DATASETS["handel_varor"]["total_code"]`), multiselect på `grupp_namn`, linje- eller staplad areagraf
- [ ] Nedbrytning per tjänsteslag på samma sätt från `handel_tjanster` (kvartal)
- [ ] Alla figurer: axeltitlar med enhet, "Källa: SCB" som caption

#### 5.4 Sidan Modell
- [ ] Läs `metrics.json` → tabell: rad per modell (inkl. baseline), kolumner MAE / RMSE / R² test + R² träning
- [ ] Markera bästa modellen (den i `model.pkl`) och ange målvariabel + split-datum (`config.TARGET_SERIES`, `config.TRAIN_END`)
- [ ] Kort text: slår modellen baseline? tecken på överanpassning (R² träning >> test)?
- [ ] Läs `predictions_test` → graf faktiskt vs prediktion över testperioden (välj modell i selectbox)
- [ ] Residualgraf (faktiskt − prediktion) eller scatter faktiskt/prediktion
- [ ] Feature importance / koefficienter från den laddade pipelinen:
      feature-namn efter preprocessorn (`get_feature_names_out`); linjära → `coef_`, RandomForest → `feature_importances_`; sorterat stapeldiagram
- [ ] Lista features som modellen använder (numeric_cols + categorical_cols från model-bundeln)

#### 5.5 Sidan Vad-om
- [ ] Ladda modell-bundeln (`load_model`) och senaste raden i `model_features` som standardvärden
- [ ] `st.form` med ett `st.number_input` per numerisk feature (label = kolumnnamn, standard = senaste värdet,
      rimligt steg) och `st.selectbox` för `config.SEASON_FEATURE` (01–12)
- [ ] Ev. gruppera fälten i kolumner: handel varor / handel tjänster / arbetslöshet t-1 / säsong
- [ ] Vid submit: `predict.predict_one(bundle, features)` → visa med `st.metric` (delta mot senaste faktiska värdet)
- [ ] Knapp "Spara prediktion" → `db.save_prediction(features, prediction, model_name)`
- [ ] Visa tidigare sparade prediktioner från `config.PREDICTIONS_TABLE` (om tabellen finns – `db.table_exists`)
- [ ] Rensa cache för `load_table` efter sparning så listan uppdateras
- [ ] Varningstext: modellen extrapolerar dåligt utanför träningsintervallet (visa min/max per feature)
- [ ] (Valfritt) "Scenario"-knappar: t.ex. export −20 % → fyll formuläret automatiskt

#### 5.6 Sidan Om projektet
- [ ] Syfte och frågeställning (påverkar utrikeshandeln arbetslösheten med fördröjning?)
- [ ] Datakällor: tabell-ID:n, urval, frekvens, licens CC0, "Källa: SCB"
- [ ] Metod: SQLite → lag-features → kronologisk split → sklearn Pipeline; varför baseline
- [ ] Begränsningar: kvartalsdata kopplad till senast avslutade kvartal, korrelation ≠ kausalitet, kort testperiod
- [ ] Länk till repo
- [ ] Teknikstack (tabellen nedan)

### 6. Kvalitet, deploy och avslut
- [ ] Kör igenom alla sidor utan fel med tom `predictions`-tabell
- [ ] Inga absoluta sökvägar (använd `config.*_PATH`)
- [ ] `requirements.txt` innehåller allt appen behöver (streamlit, plotly, joblib, scikit-learn, pandas)
- [ ] Bekräfta att `database/app.db` och `models/` är commitade (se `.gitignore`)
- [ ] Deploy på share.streamlit.io, startfil `app/streamlit_app.py`; ange Python-version om 3.14 krånglar
- [ ] Testa den publicerade appen, klistra in länken i README
- [ ] Teknisk rapport (~3 sidor): bakgrund, huvudresultat, teknisk specifikation, utvärdering av arbetet
- [ ] README med resultattabell (baseline + alla modeller)
- [ ] Säkerställ att all kod är körd inför inlämning
- [ ] Visa Antonio ett minimalt end-to-end-flöde (PoC): SCB-data → databas → enkel modell → resultat
      i Streamlit. Fokus på att flödet fungerar, inte att modellen är optimerad.
- [ ] Stäm av med Antonio:
  - [ ] Godkännande av dataset (SCB handel + arbetsmarknad) → uppdatera "Godkänt av Antonio" i `data/README.md`
  - [ ] "Regression" avser regressionsalgoritmer generellt (linjär, Ridge/Lasso, trädbaserad), inte bara enkel linjär
  - [ ] Lag-feature-ansatsen är ett giltigt sätt att hantera tiden utan att räknas som tidsseriemodell
  - [ ] Nivå på branschnedbrytning (aggregerat vs. per bransch)

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
