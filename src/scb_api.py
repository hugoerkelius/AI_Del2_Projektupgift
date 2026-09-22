import config


def normalize_period(period_code: str) -> str:
    raise NotImplementedError


def first_period_code(table_id: str) -> str:
    raise NotImplementedError


def parse_jsonstat2(payload: dict):
    raise NotImplementedError


def tidy_dataframe(df_long, dataset_key: str):
    raise NotImplementedError


def _get(url: str, params: dict | None = None) -> dict:
    raise NotImplementedError


def get_metadata(table_id: str) -> dict:
    raise NotImplementedError


def get_data(dataset_key: str) -> dict:
    raise NotImplementedError
