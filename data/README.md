# Data

`*.json` är råa API-svar från SCB (json-stat2), ett per datamängd, hämtade 2026-09-18.
Ändra aldrig filerna; all transformation sker i kod. De är bra att bygga json-stat2-parsern
mot innan du anropar API:t live, och gör att databasen kan byggas om utan nätverk.

## Datakälla

| | |
|---|---|
| Källa | SCB, Statistikdatabasen via PxWebApi v2 – `https://api.scb.se/OV0104/v2beta/api/v2/` |
| Licens | CC0 (enligt API:ts `/config`), ange "Källa: SCB" |
| Hämtat | 2026-09-18, fr.o.m. 2005 (`config.START_YEAR`) |
| Uppgiftstyp | Regression |
| Målkolumn | `target` = arbetslöshetstal 15–74 år (%, icke säsongrensat) vid månad t |
| Godkänt av Antonio | TODO |

## Tabeller från SCB

| DB-tabell | SCB-tabell | Rubrik | Frekvens | Urval |
|---|---|---|---|---|
| `handel_varor` | TAB1644 | Varuimport och varuexport efter varugrupp SITC rev3/rev4, bortfallsjusterat | Månad 1998M01– | SITC 1-siffernivå 0–9 + totalt (`0-9`); import `HA0201Y3`, export `HA0201Y4`; tkr → mnkr |
| `handel_tjanster` | TAB5147 | Tjänstehandel i miljoner kronor, export och import efter tjänsteslag | Kvartal 1982K1– | Huvudposter D1–D12 + totalt (`D0`); export `X1`, import `X2` |
| `arbetsmarknad` | TAB6387 | Befolkningen 15–74 år (AKU) efter arbetskraftstillhörighet, typ av data, kön och ålder | Månad 2001M01– | `ALÖSP` arbetslöshetstal %, `SYSP` sysselsättningsgrad %; `O_DATA` (rå) och `SR_DATA` (säsongrensad); kön 1, 2, 1+2; ålder tot15-74 |

Alla koder är verifierade mot `GET tables/{id}/metadata` 2026-09-18. Alternativa tabeller som övervägdes:
TAB5391 (total varuhandel utan varugrupp, 1975–), TAB4751 (varor per SPIN 2015).

### Exakta API-parametrar (variabelnamn = `valueCodes[<namn>]`)

| Tabell | Variabel | Koder |
|---|---|---|
| TAB1644 | `VarugruppSITCrev3` | `0-9` (totalt), `0`, `1`, … `9` |
| TAB1644 | `ContentsCode` | `HA0201Y3` (import, tkr), `HA0201Y4` (export, tkr) |
| TAB5147 | `ExpImp` | `X1` (export), `X2` (import) |
| TAB5147 | `Kontopost` | `D0` (totalt), `D1` … `D12` |
| TAB5147 | `ContentsCode` | `000002WX` (mnkr) |
| TAB6387 | `Arbetskraftstillh` | `ALÖSP` (arbetslöshetstal %), `SYSP` (sysselsättningsgrad %) |
| TAB6387 | `TypData` | `O_DATA` (icke säsongrensad), `SR_DATA` (säsongrensad) |
| TAB6387 | `Kon` | `1+2` (totalt), `1` (män), `2` (kvinnor) |
| TAB6387 | `Alder` | `tot15-74` |
| TAB6387 | `ContentsCode` | `000007L9` |
| alla | `Tid` | `FROM(2005M01)` resp. `FROM(2005K1)` – att lista alla koder ger för lång URL (404) |

Bas-URL: `https://api.scb.se/OV0104/v2beta/api/v2/`. Lägg alltid till `lang=sv&outputFormat=json-stat2`.
`ContentsCode` måste alltid anges. Rate limit: 30 anrop / 10 s, max 150 000 celler per anrop.
Skalning: varor är i tkr → dela med 1000 för mnkr så varor och tjänster får samma enhet.

## Kolumnbeskrivning

### Rådata (gemensamt schema)
| Kolumn | Typ | Beskrivning |
|---|---|---|
| `period` | text | `YYYY-MM` (månad) eller `YYYY-Qn` (kvartal) |
| `grupp` | text | SCB-kod för varugrupp / tjänsteslag / kön |
| `grupp_namn` | text | Klartext för `grupp` |
| `typ_data` | text | Endast `arbetsmarknad`: `O_DATA` eller `SR_DATA` |
| `export_varde`, `import_varde` | real | mnkr |
| `arbetsloshet_procent`, `sysselsattning_procent` | real | procent av befolkningen 15–74 år |

### `merged_monthly` (en rad per månad)
`period, export_varor, import_varor, arbetsloshet, sysselsattning, arbetsloshet_sa,
kvartal, export_tjanster, import_tjanster`

Tjänstehandel (kvartal) kopplas till varje månad som **senast avslutade kvartal**
(`kvartal`), dvs. den information som fanns vid tidpunkten.

### `model_features` (datasetet modellen tränar på)
- `<serie>_t1`, `_t3`, `_t6` – värdet 1/3/6 månader tidigare, för export/import av varor och tjänster
- `arbetsloshet_t1` – arbetslösheten månaden innan (autoregressiv)
- `manad` – månad `01`–`12` (kategorisk säsongsvariabel)
- `target` – målvariabel

### Övriga tabeller
- `predictions_test` – faktiskt utfall och varje modells prediktion för testperioden
- `predictions` – prediktioner sparade från appens Vad-om-sida
