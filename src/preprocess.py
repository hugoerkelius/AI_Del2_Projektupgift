import config


def build_merged_monthly():
    raise NotImplementedError


def build_model_features(merged):
    raise NotImplementedError


def get_feature_columns(features_df) -> tuple[list[str], list[str]]:
    raise NotImplementedError


def make_preprocessor(numeric_cols: list[str], categorical_cols: list[str]):
    raise NotImplementedError


def chronological_split(features_df, train_end: str = config.TRAIN_END):
    raise NotImplementedError
