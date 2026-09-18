# Data Plan – Handel & Arbetsmarknad
**Projekt:** Prediktion av arbetsmarknadsutveckling utifrån utrikeshandel (varor & tjänster)
**Kurs:** AI - teori och tillämpning, del 1 (MAI24HA/MAI25HA)
**Metod:** Regression (klassisk ML, inga tidsseriemodeller — tidsberoende hanteras via lag-features)

---

## 1. Syfte och hypotes

Vi undersöker om förändringar i Sveriges export/import av varor och tjänster kan användas
för att förklara/prediktera arbetsmarknadsutveckling (t.ex. arbetslöshet, sysselsättningsgrad)
några månader senare. Detta testas som ett rent regressionsproblem: kontinuerligt utfall,
med historisk handelsdata (inklusive fördröjda/lag-värden) som förklarande variabler.

---

## 2. Data som krävs

### 2.1 Källa
Samtliga datakällor hämtas via **SCB:s öppna API, PxWebApi v2** (lanserades okt 2025,
ersätter v1 som stängs vid årsskiftet 2026/2027):
- API-rot (verifiera exakt URL via en tabells "API för denna tabell"-länk i
  Statistikdatabasen innan den hårdkodas): `https://api.scb.se/OV0104/v2beta/api/v2/`
- Statistikdatabasen (för att hitta tabeller och testa frågor i gränssnittet):
  `https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/`
- Nyckel-endpoints: `tables?query=...` (sök tabell), `tables/{id}/metadata` (variabler/koder),
  `tables/{id}/data` (själva datan, stödjer GET med `valueCodes[variabel]=...`)
- Output-format: `json-stat2` (default) — parsas enklast till pandas med biblioteket `pyjstat`
- Rate limits: max 150 000 dataceller per uttag, max 30 anrop per 10 sekunder (per IP)

> OBS: exakta tabellkoder ska verifieras i Statistikdatabasens gränssnitt innan de hårdkodas,
> eftersom SCB ibland byter tabell-ID vid metodikförändringar (t.ex. AKU:s brott 2021).
> PxWebApi v2 är inte bakåtkompatibelt med v1 — gamla v1-exempel/kod går inte att återanvända rakt av.

### 2.2 Datamängd 1 – Utrikeshandel med varor
- **Ämnesområde i SCB:** Handel med varor och tjänster → Utrikeshandel med varor
- **Innehåll:** export- och importvärden per månad, gärna nedbrutet per varugrupp
  (SITC/SPIN-kod) om vi vill göra branschanalys
- **Frekvens:** månadsvis
- **Variabler att hämta:** period, varugrupp (valfritt), export (mnkr), import (mnkr)

### 2.3 Datamängd 2 – Utrikeshandel med tjänster
- **Ämnesområde i SCB:** Handel med varor och tjänster → Utrikeshandel med tjänster
- **Innehåll:** export/import av tjänster, t.ex. per tjänstetyp
- **Frekvens:** kvartalsvis (lägre upplösning än varuhandeln — hanteras i steg 4)
- **Variabler att hämta:** period, tjänstetyp (valfritt), export (mnkr), import (mnkr)

### 2.4 Datamängd 3 – Arbetsmarknad (AKU)
- **Ämnesområde i SCB:** Arbetsmarknad → Arbetskraftsundersökningarna (AKU)
- **Bekräftad tabellväg:** `START/AM/AM0401/AM0401I` (Sysselsatta 15–74 år, månad, 2001–pågående)
- **Innehåll:** arbetslöshet (%), sysselsättningsgrad (%), ev. nedbrutet på kön/ålder/bransch
- **Frekvens:** månadsvis
- **Variabler att hämta:** period, (kön/ålder om relevant), arbetslöshet, sysselsättningsgrad

### 2.5 Tidsomfång
Minst **10 år bakåt** (helst 2010–idag) för att få tillräckligt med observationer för
regression med lag-features utan att datamängden blir för liten efter `dropna()`.

---

## 3. Steg för hela arbetet

### Steg 1 – Datainsamling (backend, rådata)
1. Hitta rätt tabell-ID för respektive datamängd via Statistikdatabasens webbgränssnitt
   och klicka "API för denna tabell" för att få den exakta v2-URL:en.
2. Läs `tables/{id}/metadata` för varje tabell för att identifiera rätt variabelnamn
   och koder (t.ex. vilken kod som motsvarar "arbetslösa" eller en viss varugrupp).
3. Skriv Python-funktioner (`requests`, GET) som anropar `tables/{id}/data` med
   `valueCodes[...]`-parametrar för respektive tabell.
4. Parsa JSON-stat2-svaret till en pandas DataFrame, t.ex. med biblioteket `pyjstat`.
5. Lägg in en kort delay mellan anrop (rate limit: 30 anrop/10 sek per IP).
6. Spara resultaten rått (t.ex. som JSON eller direkt till databastabeller) utan transformation.
7. Skapa databastabeller: `handel_varor`, `handel_tjanster`, `arbetsmarknad`
   (se kolumnschema i avsnitt 4).
8. Verifiera manuellt att datan ser rimlig ut (stickprov, saknade värden, tidsspann).

### Steg 2 – Databasuppsättning
1. Välj databas: **SQLite** för utveckling/PoC (enkelt, ingen server).
2. Skriv insättningsskript (`INSERT`) som läser från API-anropen i steg 1.
3. Lägg till index på `period`-kolumnen för snabbare joins senare.

### Steg 3 – Sammanslagning av datakällor
1. Läs alla tre rådatatabeller till pandas DataFrames.
2. Hantera frekvens-mismatch: tjänstehandel är kvartalsvis — antingen
   a) forward-fill till varje månad, eller
   b) aggregera allt till kvartalsnivå (enklare, rekommenderas för PoC).
3. Slå ihop till en tabell `merged_monthly` (eller `merged_quarterly`) med en rad per period.
4. Spara denna mellantabell i databasen.

### Steg 4 – Feature engineering (lag-features)
1. Skapa lag-variabler för handelsdata: t-1, t-3, t-6 perioder bakåt.
2. Skapa ev. autoregressiv feature: arbetslöshet t-1 (fångar trögrörlighet).
3. Lägg till säsongsvariabel (månad/kvartal som kategori) om relevant.
4. Definiera målvariabel `y` (t.ex. arbetslöshet vid tidpunkt t).
5. Ta bort rader med saknade värden (`dropna()`), som uppstår i början av serien pga lag.
6. Spara som `model_features`-tabell — detta är datasetet modellen faktiskt tränar på.

### Steg 5 – Train/test-split
1. **Kronologisk split** (ej slumpmässig) — träna på äldre data, testa på nyare.
2. Exempel: träna på 2010–2022, testa på 2023–idag.

### Steg 6 – Modellering (regression)
1. Baseline: `LinearRegression` (scikit-learn).
2. Jämförelsemodell 1: `Ridge`/`Lasso` (regularisering, motiveras av flera korrelerade
   handelsvariabler).
3. Jämförelsemodell 2: `RandomForestRegressor` (icke-linjära samband, ger feature importance).
4. Utvärdera samtliga med MAE, RMSE, R².
5. Dokumentera resonemang: varför valdes respektive modell, vilken presterade bäst och varför.

### Steg 7 – PoC-avstämning med Antonio
1. Visa ett minimalt end-to-end-flöde: SCB-data → databas → enkel modell → resultat i Streamlit.
2. Fokus: att flödet fungerar, inte att modellen är optimerad.

### Steg 8 – Frontend (Streamlit)
1. Sida 1: visa historisk data (graf export/import vs. arbetslöshet).
2. Sida 2: visa modellens prediktion vs. faktiskt utfall (test-perioden).
3. Interaktivt: låt användaren välja bransch/tidsperiod, ev. en "vad-om"-slider.

### Steg 9 – Utvärdering och förbättringsförslag
1. Sammanställ modellresultat i tabellform.
2. Diskutera var modellen missar (vilken period/bransch är svårast).
3. Föreslå konkreta förbättringar (fler features, branschspecifik modell, fler lag-perioder).

### Steg 10 – Dokumentation
1. Skriv teknisk rapport (~3 sidor): bakgrund, huvudresultat, teknisk specifikation,
   utvärdering av gruppens arbete.
2. Färdigställ README på GitHub.
3. Säkerställ att koden är körd/exekverad inför inlämning.

---

## 4. Databasschema (sammanfattning)

**Rådata:**
- `handel_varor(id, period, varugrupp, export_varde, import_varde)`
- `handel_tjanster(id, period, tjanstetyp, export_varde, import_varde)`
- `arbetsmarknad(id, period, bransch, arbetsloshet_procent, sysselsattning_procent)`

**Mellanlager:**
- `merged_monthly(period, export_varor, import_varor, export_tjanster, import_tjanster,
  arbetsloshet, sysselsattning)`

**Modell-features:**
- `model_features(period, export_varor_t1, export_varor_t3, export_varor_t6,
  import_varor_t1, arbetsloshet_t1, manad, target_arbetsloshet)`

---

## 5. Att stämma av med Antonio

- [ ] Godkännande av dataset (SCB handel + arbetsmarknad)
- [ ] Bekräfta att "regression" avser regressionsalgoritmer generellt (linjär, Ridge/Lasso,
      trädbaserad) och inte enbart enkel linjär regression
- [ ] Bekräfta att lag-feature-ansatsen är ett giltigt sätt att hantera tidsdimensionen
      utan att räknas som en "tidsseriemodell"
- [ ] Nivå på branschnedbrytning (aggregerat vs. per bransch) — påverkar datamängdens storlek
