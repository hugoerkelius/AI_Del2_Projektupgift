import config


def naive_baseline(X_test, y_test) -> dict:
    raise NotImplementedError


def get_models() -> dict:
    raise NotImplementedError


def make_pipeline(preprocessor, model):
    raise NotImplementedError


def evaluate(y_true, y_pred) -> dict:
    raise NotImplementedError


def train_and_evaluate(X_train, X_test, y_train, y_test, preprocessor) -> tuple[dict, dict, dict]:
    raise NotImplementedError


def select_best(metrics: dict, key: str = "mae") -> str:
    raise NotImplementedError


def save_model(pipeline, numeric_cols, categorical_cols, model_name: str, path=config.MODEL_PATH) -> None:
    raise NotImplementedError


def save_metrics(metrics: dict, path=config.METRICS_PATH) -> None:
    raise NotImplementedError
