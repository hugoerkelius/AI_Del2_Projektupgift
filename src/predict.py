import config


def load_model(path=config.MODEL_PATH) -> dict:
    raise NotImplementedError


def load_metrics(path=config.METRICS_PATH) -> dict:
    raise NotImplementedError


def predict_one(model_bundle: dict, features: dict) -> float:
    raise NotImplementedError


def predict_frame(model_bundle: dict, X):
    raise NotImplementedError
