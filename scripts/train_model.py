import _path
import pandas as pd

import config
from src import db, preprocess, train


def main():
    features = db.read_table(config.FEATURES_TABLE)
    numeric_cols, categorical_cols = preprocess.get_feature_columns(features)
    feature_cols = numeric_cols + categorical_cols

    train_df, test_df = preprocess.chronological_split(features)
    X_train = train_df[feature_cols]
    y_train = train_df[config.TARGET_COLUMN]
    X_test = test_df[feature_cols]
    y_test = test_df[config.TARGET_COLUMN]
    print("Träningsdata:", len(train_df), "rader")
    print("Testdata:", len(test_df), "rader")

    metrics, pipelines, predictions = train.train_and_evaluate(
        X_train, X_test, y_train, y_test, numeric_cols, categorical_cols
    )

    best_name = train.select_best(metrics)

    baseline_pred = train.naive_baseline(X_test)
    metrics["Baseline"] = train.evaluate(y_test, baseline_pred)
    baseline_train = train.naive_baseline(X_train)
    metrics["Baseline"]["r2_train"] = train.evaluate(y_train, baseline_train)["r2"]
    metrics["Baseline"]["mae_cv"] = train.baseline_cv(X_train, y_train)
    metrics["Baseline"]["basta_parametrar"] = {}
    predictions["Baseline"] = baseline_pred

    print("Resultat på testdata:")
    for name in metrics:
        print(name, "MAE:", round(metrics[name]["mae"], 3),
              "RMSE:", round(metrics[name]["rmse"], 3),
              "R2:", round(metrics[name]["r2"], 3))
    print("Bästa modell:", best_name)
    print("Bästa parametrar:", metrics[best_name]["basta_parametrar"])

    train.save_model(pipelines[best_name], numeric_cols, categorical_cols, best_name)
    train.save_metrics(metrics)

    tabeller = []
    for name in predictions:
        tabell = pd.DataFrame()
        tabell["period"] = test_df["period"]
        tabell["modell"] = name
        tabell["faktiskt"] = y_test
        tabell["prediktion"] = list(predictions[name])
        tabeller.append(tabell)

    alla_prediktioner = pd.concat(tabeller)
    db.write_table(alla_prediktioner, config.TEST_PREDICTIONS_TABLE)
    print("Modellen är sparad.")


if __name__ == "__main__":
    main()
