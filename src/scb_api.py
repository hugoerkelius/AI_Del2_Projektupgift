import itertools
import time

import pandas as pd
import requests

import config


def normalize_period(period_code):
    if "M" in period_code:
        year, month = period_code.split("M")
        return year + "-" + month
    if "K" in period_code:
        year, quarter = period_code.split("K")
        return year + "-Q" + quarter
    raise ValueError("Okänt periodformat: " + period_code)


def first_period_code(table_id):
    if table_id == config.SCB_DATASETS["handel_tjanster"]["table_id"]:
        return str(config.START_YEAR) + "K1"
    return str(config.START_YEAR) + "M01"


def parse_jsonstat2(payload):
    dimensions = payload["id"]

    all_codes = []
    for dim in dimensions:
        index = payload["dimension"][dim]["category"]["index"]
        if type(index) == list:
            codes = index
        else:
            codes = [None] * len(index)
            for code, position in index.items():
                codes[position] = code
        all_codes.append(codes)

    expected = 1
    for size in payload["size"]:
        expected = expected * size
    if len(payload["value"]) != expected:
        raise ValueError(f"Felaktigt antal värden: {len(payload['value'])}, förväntat antal är {expected}")

    rows = []
    combinations = itertools.product(*all_codes)
    for combo, value in zip(combinations, payload["value"]):
        row = {}
        for i in range(len(dimensions)):
            row[dimensions[i]] = combo[i]
        row["value"] = value
        rows.append(row)

    df = pd.DataFrame(rows)

    for dim in dimensions:
        labels = payload["dimension"][dim]["category"]["label"]
        df[dim + "_label"] = df[dim].map(labels)

    return df


def tidy_dataframe(df_long, dataset_key):
    settings = config.SCB_DATASETS[dataset_key]
    group_dim = settings["group_dim"]
    measure_dim = settings["measure_dim"]
    extra_dims = settings.get("extra_dims", {})

    df = df_long.copy()
    df["period"] = df["Tid"].apply(normalize_period)
    df["grupp"] = df[group_dim]
    df["grupp_namn"] = df[group_dim + "_label"]
    for dim in extra_dims:
        df[extra_dims[dim]] = df[dim]
    df["matt"] = df[measure_dim].map(settings["measure_map"])
    df["value"] = df["value"] * settings["scale"]

    index_cols = ["period", "grupp", "grupp_namn"]
    for dim in extra_dims:
        index_cols.append(extra_dims[dim])

    wide = df.pivot(index=index_cols, columns="matt", values="value")
    wide = wide.reset_index()
    wide.columns.name = None

    expected_rows = wide["period"].nunique() * wide["grupp"].nunique()
    for dim in extra_dims:
        expected_rows = expected_rows * wide[extra_dims[dim]].nunique()
    if len(wide) != expected_rows:
        raise ValueError(f"{dataset_key}: {len(wide)} rader, förväntat antal är {expected_rows}")

    rows_before = len(wide)
    wide = wide.dropna()
    if len(wide) < rows_before:
        print(f"  {dataset_key}: {rows_before - len(wide)} rader med saknade värden har tagits bort")

    wide = wide.sort_values(["period", "grupp"])
    wide = wide.reset_index(drop=True)
    return wide


def _get(url, params=None):
    if params is None:
        params = {}
    params["lang"] = config.SCB_LANG

    for attempt in range(3):
        time.sleep(config.SCB_MIN_SECONDS_BETWEEN_CALLS)
        response = requests.get(url, params=params, timeout=60)
        if response.status_code == 429:
            print("För många anrop (429). Väntar 10 sekunder.")
            time.sleep(10)
            continue
        response.raise_for_status()
        return response.json()

    raise RuntimeError("SCB svarade med 429 för många gånger: " + url)


def get_data(dataset_key):
    settings = config.SCB_DATASETS[dataset_key]
    table_id = settings["table_id"]

    params = {"outputFormat": "json-stat2"}
    for variable in settings["selection"]:
        codes = settings["selection"][variable]
        params["valueCodes[" + variable + "]"] = ",".join(codes)
    params["valueCodes[Tid]"] = "FROM(" + first_period_code(table_id) + ")"

    url = config.SCB_BASE_URL + "tables/" + table_id + "/data"
    return _get(url, params)
