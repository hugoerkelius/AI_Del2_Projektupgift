import _path
import config
from src import db, preprocess


def main():
    merged = preprocess.build_merged_monthly()
    db.write_table(merged, config.MERGED_TABLE)
    print("merged_monthly:", len(merged), "rader")

    features = preprocess.build_model_features(merged)
    db.write_table(features, config.FEATURES_TABLE)
    print("model_features:", len(features), "rader")
    print("Första period:", features["period"].min())
    print("Sista period:", features["period"].max())

    lag_kolumn = config.TARGET_SERIES + "_t1"
    steg = 1 + config.HORIZON
    fel = 0
    for i in range(steg, len(features)):
        if features[lag_kolumn][i] != features[config.TARGET_COLUMN][i - steg]:
            fel = fel + 1
    print("Kontroll av", lag_kolumn + ":", fel, "fel")


if __name__ == "__main__":
    main()
