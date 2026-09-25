import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import config
from src import db


def forra_kvartalet(period):
    ar = int(period[0:4])
    manad = int(period[5:7])
    kvartal = (manad - 1) // 3 + 1

    kvartal = kvartal - 1
    if kvartal == 0:
        kvartal = 4
        ar = ar - 1

    return str(ar) + "-Q" + str(kvartal)


def build_merged_monthly():
    varor = db.read_table("handel_varor", "grupp='0-9'")
    varor["export_varor"] = varor["export_varde"]
    varor["import_varor"] = varor["import_varde"]
    varor = varor[["period", "export_varor", "import_varor"]]

    tjanster = db.read_table("handel_tjanster", "grupp='D0'")
    tjanster["kvartal"] = tjanster["period"]
    tjanster["export_tjanster"] = tjanster["export_varde"]
    tjanster["import_tjanster"] = tjanster["import_varde"]
    tjanster = tjanster[["kvartal", "export_tjanster", "import_tjanster"]]

    o_data = db.read_table("arbetsmarknad", "grupp='1+2' AND typ_data='O_DATA'")
    o_data["arbetsloshet"] = o_data["arbetsloshet_procent"]
    o_data["sysselsattning"] = o_data["sysselsattning_procent"]
    o_data = o_data[["period", "arbetsloshet", "sysselsattning"]]

    sr_data = db.read_table("arbetsmarknad", "grupp='1+2' AND typ_data='SR_DATA'")
    sr_data["arbetsloshet_sa"] = sr_data["arbetsloshet_procent"]
    sr_data = sr_data[["period", "arbetsloshet_sa"]]

    merged = pd.merge(varor, o_data, on="period")
    merged = pd.merge(merged, sr_data, on="period")

    kvartal_lista = []
    for period in merged["period"]:
        kvartal_lista.append(forra_kvartalet(period))
    merged["kvartal"] = kvartal_lista

    merged = pd.merge(merged, tjanster, on="kvartal", how="left")
    return merged


def build_model_features(merged, target_series=config.TARGET_SERIES, lags=config.LAGS, horizon=config.HORIZON):
    features = pd.DataFrame()
    features["period"] = merged["period"]

    for kolumn in config.LAG_SOURCE_COLUMNS:
        for lag in lags:
            ny_kolumn = kolumn + "_t" + str(lag)
            features[ny_kolumn] = merged[kolumn].shift(lag)

    features[target_series + "_t1"] = merged[target_series].shift(1)
    features["manad"] = merged["period"].str[5:7]
    features[config.TARGET_COLUMN] = merged[target_series].shift(-horizon)

    features = features.dropna()
    features = features.reset_index(drop=True)
    return features


def get_feature_columns(features_df):
    numeric_cols = []
    for kolumn in features_df.columns:
        if kolumn not in ["period", "manad", config.TARGET_COLUMN]:
            numeric_cols.append(kolumn)

    categorical_cols = ["manad"]
    return numeric_cols, categorical_cols


def make_preprocessor(numeric_cols, categorical_cols):
    preprocessor = ColumnTransformer([
        ("numeriska", StandardScaler(), numeric_cols),
        ("kategoriska", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
    ])
    return preprocessor


def chronological_split(features_df, train_end=config.TRAIN_END, horizon=config.HORIZON):
    train = features_df[features_df["period"] <= train_end]
    test = features_df[features_df["period"] > train_end]

    train = train.head(len(train) - horizon)
    return train, test
