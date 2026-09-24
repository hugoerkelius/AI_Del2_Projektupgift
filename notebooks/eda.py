# %%
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
from src import db
import pandas as pd
import matplotlib.pyplot as plt


#%% Läs handel med varor
varor = db.read_table("handel_varor", "grupp='0-9'")
print("Handel med varor:")
print(varor.head())
print(varor.shape)

#%% Läs handel med tjänster
tjanster = db.read_table("handel_tjanster", "grupp='D0'")
print("Data handel med tjänster:")
print(tjanster.head())
print(tjanster.shape)

# %% Läs arbetsmarknad
arbete = db.read_table("arbetsmarknad","grupp='1+2'")
print("Data arbetsmarknad:")
print(arbete.head())
print(arbete.shape)

# %% Kontroll mot load_data.py
print("Period varor:")
print("Första period:", varor["period"].min())
print("Sista period:", varor["period"].max())

print("Period tjänster:")
print("Första period:", tjanster["period"].min())
print("Sista period:", tjanster["period"].max())

print("Period arbetsmarknad:")
print("Första period:", arbete["period"].min())
print("Sista period:", arbete["period"].max())

# %% Datumkolumn
varor["datum"] = pd.to_datetime(varor["period"])
arbete["datum"] = pd.to_datetime(arbete["period"])
tjanster["datum"] = pd.PeriodIndex(tjanster["period"], freq="Q").to_timestamp()

print("Datum varor:")
print(varor[["period", "datum"]].head())
print(varor.dtypes)

print("Datum tjänster:")
print(tjanster[["period", "datum"]].head())
print(tjanster.dtypes)

print("Datum arbetsmarknad:")
print(arbete[["period", "datum"]].head())
print(arbete.dtypes)

# %% Tidsserier

# %% Korrelation vid olika fördröjningar

# %% Nedbrytning per varugrupp
