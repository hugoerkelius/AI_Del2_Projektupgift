from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DATA_RAW_DIR = ROOT_DIR / "data"
DB_PATH = ROOT_DIR / "database" / "app.db"
MODEL_DIR = ROOT_DIR / "models"
MODEL_PATH = MODEL_DIR / "model.pkl"
METRICS_PATH = MODEL_DIR / "metrics.json"

SCB_BASE_URL = "https://api.scb.se/OV0104/v2beta/api/v2/"
SCB_LANG = "sv"
SCB_MIN_SECONDS_BETWEEN_CALLS = 0.5

START_YEAR = 2005

SCB_DATASETS = {
    "handel_varor": {
        "table_id": "TAB1644",
        "selection": {
            "VarugruppSITCrev3": ["0-9", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
            "ContentsCode": ["HA0201Y3", "HA0201Y4"],
        },
        "group_dim": "VarugruppSITCrev3",
        "measure_dim": "ContentsCode",
        "measure_map": {"HA0201Y3": "import_varde", "HA0201Y4": "export_varde"},
        "scale": 0.001,
        "total_code": "0-9",
    },
    "handel_tjanster": {
        "table_id": "TAB5147",
        "selection": {
            "ExpImp": ["X1", "X2"],
            "Kontopost": ["D0", "D1", "D2", "D3", "D4", "D5", "D6",
                          "D7", "D8", "D9", "D10", "D11", "D12"],
            "ContentsCode": ["000002WX"],
        },
        "group_dim": "Kontopost",
        "measure_dim": "ExpImp",
        "measure_map": {"X1": "export_varde", "X2": "import_varde"},
        "scale": 1.0,
        "total_code": "D0",
    },
    "arbetsmarknad": {
        "table_id": "TAB6387",
        "selection": {
            "Arbetskraftstillh": ["ALÖSP", "SYSP"],
            "TypData": ["O_DATA", "SR_DATA"],
            "Kon": ["1+2", "1", "2"],
            "Alder": ["tot15-74"],
            "ContentsCode": ["000007L9"],
        },
        "group_dim": "Kon",
        "measure_dim": "Arbetskraftstillh",
        "measure_map": {"ALÖSP": "arbetsloshet_procent", "SYSP": "sysselsattning_procent"},
        "scale": 1.0,
        "total_code": "1+2",
        "extra_dims": {"TypData": "typ_data"},
    },
}

MERGED_TABLE = "merged_monthly"
FEATURES_TABLE = "model_features"
PREDICTIONS_TABLE = "predictions"
TEST_PREDICTIONS_TABLE = "predictions_test"

TASK_TYPE = "regression"

TARGET_SERIES = "arbetsloshet"
TARGET_COLUMN = "target"
HORIZON = 0

LAG_SOURCE_COLUMNS = ["export_varor", "import_varor", "export_tjanster", "import_tjanster"]
LAGS = [1, 3, 6]
AUTOREGRESSIVE_LAGS = [1]
SEASON_FEATURE = "manad"

TRAIN_END = "2022-12"
RANDOM_STATE = 42
