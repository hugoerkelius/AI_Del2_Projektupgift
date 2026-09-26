import _path
import pandas as pd

import config
from src import db, preprocess, train


def run_experiment(merged, namn, target_series, lags, horizon):
    features = preprocess.build_model_features(merged, target_series, lags, horizon)
    numeric_cols, categorical_cols = preprocess.get_feature_columns(features)
    feature_cols = numeric_cols + categorical_cols

    train_df, test_df = preprocess.chronological_split(features, config.TRAIN_END, horizon)
    X_train = train_df[feature_cols]
    y_train = train_df[config.TARGET_COLUMN]
    X_test = test_df[feature_cols]
    y_test = test_df[config.TARGET_COLUMN]

    metrics, pipelines, predictions = train.train_and_evaluate(
        X_train, X_test, y_train, y_test, numeric_cols, categorical_cols
    )
    baseline_pred = train.naive_baseline(X_test, target_series)
    metrics["Baseline"] = train.evaluate(y_test, baseline_pred)

    rader = []
    for modell in metrics:
        rader.append({
            "experiment": namn,
            "modell": modell,
            "mae": round(metrics[modell]["mae"], 3),
            "rmse": round(metrics[modell]["rmse"], 3),
            "r2": round(metrics[modell]["r2"], 3),
        })
    return rader


def main():
    merged = db.read_table(config.MERGED_TABLE)

    experiment = [
        ["Grund", "arbetsloshet", [1, 3, 6], 0],
        ["Lag 12", "arbetsloshet", [1, 3, 6, 12], 0],
        ["Säsongrensad", "arbetsloshet_sa", [1, 3, 6], 0],
        ["Sysselsättning", "sysselsattning", [1, 3, 6], 0],
        ["Horisont t+3", "arbetsloshet", [1, 3, 6], 3],
    ]

    alla_rader = []
    for namn, target_series, lags, horizon in experiment:
        print("Kör experiment:", namn)
        rader = run_experiment(merged, namn, target_series, lags, horizon)
        alla_rader = alla_rader + rader

    resultat = pd.DataFrame(alla_rader)
    print(resultat.to_string(index=False))

    resultat.to_csv(config.MODEL_DIR / "experiment.csv", index=False)
    print("Resultatet är sparat i", config.MODEL_DIR / "experiment.csv")


if __name__ == "__main__":
    main()
