# %%
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
from src import db
import numpy as np
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
plt.figure()
plt.plot(varor["datum"], varor["export_varde"], label="Export")
plt.plot(varor["datum"], varor["import_varde"], label="Import")
plt.title("Handel med varor per månad (Källa: SCB)")
plt.xlabel("År")
plt.ylabel("Värde (mnkr)")
plt.legend()
plt.savefig("fig/graf1_varor.png")
plt.show()

plt.figure()
plt.plot(tjanster["datum"], tjanster["export_varde"], label="Export")
plt.plot(tjanster["datum"], tjanster["import_varde"], label="Import")
plt.title("Handel med tjänster per kvartal (Källa: SCB)")
plt.xlabel("År")
plt.ylabel("Värde (mnkr)")
plt.legend()
plt.savefig("fig/graf2_tjanster.png")
plt.show()

o_data = arbete[arbete["typ_data"] == "O_DATA"]
sr_data = arbete[arbete["typ_data"] == "SR_DATA"]

plt.figure()
plt.plot(o_data["datum"], o_data["arbetsloshet_procent"], label="Ej säsongrensad")
plt.plot(sr_data["datum"], sr_data["arbetsloshet_procent"], label="Säsongrensad")
plt.title("Arbetslöshet per månad (Källa: SCB)")
plt.xlabel("År")
plt.ylabel("Arbetslöshet (%)")
plt.legend()
plt.savefig("fig/graf3_arbetsloshet.png")
plt.show()

# %% Korrelation vid olika fördröjningar
data = pd.merge(varor[["period", "export_varde"]], o_data[["period", "arbetsloshet_procent"]], on="period")
data["export_forandring"] = data["export_varde"].pct_change(12) * 100
data["ar"] = data["period"].str[0:4].astype(int)

fordrojningar = [0, 1, 3, 6, 12]
korr_niva = []
korr_forandring = []

for k in fordrojningar:
    export_niva = data["export_varde"].shift(k)
    korr_niva.append(export_niva.corr(data["arbetsloshet_procent"]))

    export_forandring = data["export_forandring"].shift(k)
    korr_forandring.append(export_forandring.corr(data["arbetsloshet_procent"]))

resultat = pd.DataFrame({
    "fordrojning": fordrojningar,
    "korrelation_niva": korr_niva,
    "korrelation_forandring": korr_forandring
})
print("Korrelation mellan export och arbetslöshet:")
print(resultat)

plt.figure(figsize=(20, 5))
for i in range(len(fordrojningar)):
    k = fordrojningar[i]
    x = data["export_varde"].shift(k)
    y = data["arbetsloshet_procent"]
    finns = x.notna()

    plt.subplot(1, 5, i + 1)
    plt.scatter(x, y, c=data["ar"], cmap="viridis", s=12)
    lutning, start = np.polyfit(x[finns], y[finns], 1)
    plt.plot(x[finns], lutning * x[finns] + start, color="red")
    plt.title(str(k) + " mån tidigare, korrelation " + str(round(korr_niva[i], 2)))
    plt.xlabel("Export (mnkr)")
    plt.ylabel("Arbetslöshet (%)")
    if i == 4:
        plt.colorbar(label="År", ticks=[2005, 2010, 2015, 2020, 2025])
plt.suptitle("Exportens värde och arbetslösheten. En prick = en månad, färgen visar året, röd linje = trendlinje (Källa: SCB)")
plt.tight_layout()
plt.savefig("fig/graf4_korrelation_niva.png")
plt.show()

plt.figure(figsize=(20, 5))
for i in range(len(fordrojningar)):
    k = fordrojningar[i]
    x = data["export_forandring"].shift(k)
    y = data["arbetsloshet_procent"]
    finns = x.notna()

    plt.subplot(1, 5, i + 1)
    plt.scatter(x, y, c=data["ar"], cmap="viridis", s=12)
    lutning, start = np.polyfit(x[finns], y[finns], 1)
    plt.plot(x[finns], lutning * x[finns] + start, color="red")
    plt.axvline(0, color="gray", linestyle="--")
    plt.title(str(k) + " mån tidigare, korrelation " + str(round(korr_forandring[i], 2)))
    plt.xlabel("Exportens förändring mot året innan (%)")
    plt.ylabel("Arbetslöshet (%)")
    if i == 4:
        plt.colorbar(label="År", ticks=[2005, 2010, 2015, 2020, 2025])
plt.suptitle("Exportens förändring och arbetslösheten. En prick = en månad, färgen visar året, röd linje = trendlinje (Källa: SCB)")
plt.tight_layout()
plt.savefig("fig/graf5_korrelation_forandring.png")
plt.show()

# %% Nedbrytning per varugrupp
varugrupper = db.read_table("handel_varor", "grupp != '0-9'")

korta_namn = {
    "0": "Livsmedel",
    "1": "Drycker och tobak",
    "2": "Råvaror (t.ex. trä, malm)",
    "3": "Bränslen och el",
    "4": "Oljor och fetter",
    "5": "Kemikalier och läkemedel",
    "6": "Material (t.ex. stål, papper)",
    "7": "Maskiner och fordon",
    "8": "Övriga färdiga varor",
    "9": "Övrigt",
}
varugrupper["kort_namn"] = varugrupper["grupp"].map(korta_namn)

tabell = varugrupper.pivot(index="period", columns="kort_namn", values="export_varde")
tabell.index = pd.to_datetime(tabell.index)

tabell.plot(figsize=(12, 6))
plt.title("Export per varugrupp (Källa: SCB)")
plt.xlabel("År")
plt.ylabel("Export (mnkr)")
plt.legend(title="Varugrupp", bbox_to_anchor=(1, 1))
plt.tight_layout()
plt.savefig("fig/graf6_export_per_varugrupp.png")
plt.show()
