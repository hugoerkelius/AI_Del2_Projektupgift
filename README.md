# Utrikeshandel och arbetslöshet

Projektuppgift i kursen AI – teori och tillämpning. Projektet undersöker om förändringar i Sveriges
export och import av varor och tjänster kan prediktera arbetslösheten några månader senare.

Flödet är: **SCB:s API → SQLite-databas → regression med scikit-learn → Streamlit-app**.

## Data

All data kommer från SCB:s öppna API (PxWebApi v2), från 2005 och framåt. Licens CC0, källa: SCB.

| Data | SCB-tabell | Frekvens |
|---|---|---|
| Utrikeshandel med varor | TAB1644 | Månad |
| Utrikeshandel med tjänster | TAB5147 | Kvartal |
| Arbetskraftsundersökningen (AKU), arbetslöshet 15–74 år | TAB6387 | Månad |

Mer om tabeller, koder och kolumner finns i [data/README.md](data/README.md).

## Metod

- De tre tabellerna slås ihop till en rad per månad. Tjänstehandeln kopplas till det senast avslutade
  kvartalet, så att modellen inte använder information som ännu inte fanns.
- Features: export och import 1, 3 och 6 månader tidigare, arbetslösheten föregående månad och månaden
  (för säsongsvariation).
- Målvariabel: arbetslösheten (icke säsongrensad) samma månad.
- Datan delas upp i tid: träning till och med 2022-12, test från 2023-01. Hyperparametrar väljs med
  `TimeSeriesSplit`.
- Fyra modeller jämförs med en baseline som gissar samma värde som föregående månad.

## Resultat

Resultat på testdatan (2023-01 – 2026-06). MAE och RMSE anges i procentenheter.

| Modell | MAE | RMSE | R² test | R² träning |
|---|---|---|---|---|
| Baseline | 0,681 | 0,916 | −0,176 | 0,546 |
| LinearRegression | 0,541 | 0,685 | 0,343 | 0,864 |
| Ridge | 0,540 | 0,684 | 0,344 | 0,864 |
| **Lasso** | **0,482** | **0,623** | **0,456** | 0,845 |
| RandomForest | 0,611 | 0,765 | 0,181 | 0,971 |

Lasso gav bäst resultat och används i appen. Lasso sätter nästan alla handelsvariabler till noll, så
prediktionen bygger främst på arbetslösheten föregående månad och månaden.

## Projektstruktur

```
config.py              Inställningar: sökvägar, SCB-tabeller, tabellnamn, lag-perioder, split-datum
data/                  Råa API-svar från SCB (json)
database/app.db        SQLite-databasen
models/                Sparad modell (model.pkl), resultat (metrics.json) och experiment (experiment.csv)
src/scb_api.py         Hämtar och tolkar data från SCB:s API
src/db.py              Läser och skriver till databasen
src/preprocess.py      Sammanslagning och lag-features
src/train.py           Träning och utvärdering av modellerna
src/predict.py         Laddar modellen och gör prediktioner
scripts/               Skript som kör stegen ovan
notebooks/eda.py       Utforskande dataanalys med figurer i notebooks/fig/
streamlit_app.py       Webbappen
```

## Installation

Kräver Python 3.11 eller senare.

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

På macOS och Linux aktiveras miljön med `source .venv/bin/activate`.

## Köra projektet

Databasen och modellen finns redan i repot, så appen kan startas direkt:

```
streamlit run streamlit_app.py
```

Appen har sidorna Prediktera, Historik, Modell, Data och Om projektet.

För att bygga om allt från början:

```
python scripts/load_data.py --offline
python scripts/build_features.py
python scripts/train_model.py
```

`--offline` läser de sparade json-filerna i `data/`. Utan flaggan hämtas data direkt från SCB:s API.

Övriga skript:

- `python scripts/experiment.py` jämför andra inställningar (fler lags, säsongrensad arbetslöshet,
  sysselsättning, längre horisont) och sparar resultatet i `models/experiment.csv`.
- Den utforskande analysen körs från mappen `notebooks` med `python eda.py`.
