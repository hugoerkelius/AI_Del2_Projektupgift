import config


def get_connection(db_path=config.DB_PATH):
    raise NotImplementedError


def write_table(df, table_name: str, if_exists: str = "replace", index_cols=("period",)) -> None:
    raise NotImplementedError


def read_table(table_name: str, where: str | None = None):
    raise NotImplementedError


def table_exists(table_name: str) -> bool:
    raise NotImplementedError


def list_tables() -> list[str]:
    raise NotImplementedError


def save_prediction(features: dict, prediction: float, model_name: str) -> None:
    raise NotImplementedError
