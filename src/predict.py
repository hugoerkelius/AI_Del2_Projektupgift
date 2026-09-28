import json

import joblib
import pandas as pd

import config


def load_model(path=config.MODEL_PATH) -> dict:
    return joblib.load(path)


def load_metrics(path=config.METRICS_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def predict_one(model_bundle: dict, features: dict) -> float:
    X = pd.DataFrame([features])
    return float(predict_frame(model_bundle, X)[0])


def predict_frame(model_bundle: dict, X):
    kolumner = model_bundle["numeric_cols"] + model_bundle["categorical_cols"]
    return model_bundle["pipeline"].predict(X[kolumner])
