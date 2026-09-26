import json

import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline

import config
from src import preprocess


def naive_baseline(X_test, target_series=config.TARGET_SERIES):
    return X_test[target_series + "_t1"]


def baseline_cv(X_train, y_train, target_series=config.TARGET_SERIES):
    cv = TimeSeriesSplit(n_splits=config.CV_SPLITS)
    maes = []
    for train_index, val_index in cv.split(X_train):
        pred = naive_baseline(X_train.iloc[val_index], target_series)
        maes.append(mean_absolute_error(y_train.iloc[val_index], pred))
    return sum(maes) / len(maes)


def get_models():
    models = {
        "LinearRegression": LinearRegression(),
        "Ridge": Ridge(),
        "Lasso": Lasso(max_iter=10000),
        "RandomForest": RandomForestRegressor(random_state=config.RANDOM_STATE),
    }
    return models


def get_param_grids():
    param_grids = {
        "LinearRegression": {},
        "Ridge": {"model__alpha": [0.01, 0.1, 1, 10, 100]},
        "Lasso": {"model__alpha": [0.001, 0.01, 0.1, 1]},
        "RandomForest": {
            "model__n_estimators": [100, 300],
            "model__max_depth": [3, 5, None],
            "model__min_samples_leaf": [1, 5],
        },
    }
    return param_grids


def make_pipeline(numeric_cols, categorical_cols, model):
    preprocessor = preprocess.make_preprocessor(numeric_cols, categorical_cols)
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", model),
    ])
    return pipeline


def evaluate(y_true, y_pred):
    result = {
        "mae": mean_absolute_error(y_true, y_pred),
        "rmse": root_mean_squared_error(y_true, y_pred),
        "r2": r2_score(y_true, y_pred),
    }
    return result


def train_and_evaluate(X_train, X_test, y_train, y_test, numeric_cols, categorical_cols):
    metrics = {}
    pipelines = {}
    predictions = {}

    models = get_models()
    param_grids = get_param_grids()
    for name in models:
        pipeline = make_pipeline(numeric_cols, categorical_cols, models[name])

        search = GridSearchCV(
            pipeline,
            param_grids[name],
            cv=TimeSeriesSplit(n_splits=config.CV_SPLITS),
            scoring="neg_mean_absolute_error",
        )
        search.fit(X_train, y_train)
        best_pipeline = search.best_estimator_

        y_pred_test = best_pipeline.predict(X_test)
        y_pred_train = best_pipeline.predict(X_train)

        result = evaluate(y_test, y_pred_test)
        result["r2_train"] = r2_score(y_train, y_pred_train)
        result["mae_cv"] = -search.best_score_
        result["basta_parametrar"] = search.best_params_

        metrics[name] = result
        pipelines[name] = best_pipeline
        predictions[name] = y_pred_test

    return metrics, pipelines, predictions


def select_best(metrics):
    best_name = None
    best_mae = None
    for name in metrics:
        mae = metrics[name]["mae_cv"]
        if best_mae is None or mae < best_mae:
            best_name = name
            best_mae = mae
    return best_name


def save_model(pipeline, numeric_cols, categorical_cols, model_name, path=config.MODEL_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "pipeline": pipeline,
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols,
        "model_name": model_name,
    }
    joblib.dump(bundle, path)


def save_metrics(metrics, path=config.METRICS_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
