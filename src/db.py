import sqlite3
from datetime import datetime

import pandas as pd

import config


def get_connection(db_path=config.DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def write_table(df, table_name, if_exists="replace", index_cols=("period",)):
    conn = get_connection()
    df.to_sql(table_name, conn, if_exists=if_exists, index=False)
    for col in index_cols:
        if col in df.columns:
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_{col} ON {table_name} ({col})")
    conn.commit()
    conn.close()


def read_table(table_name, where=None):
    sql = "SELECT * FROM " + table_name
    if where is not None:
        sql = sql + " WHERE " + where

    conn = get_connection()
    df = pd.read_sql(sql, conn)
    conn.close()

    if "period" in df.columns:
        df = df.sort_values("period").reset_index(drop=True)
    return df


def table_exists(table_name):
    conn = get_connection()
    result = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    ).fetchone()
    conn.close()
    return result is not None


def list_tables():
    conn = get_connection()
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    conn.close()

    names = []
    for row in rows:
        names.append(row[0])
    return names


def save_prediction(features, prediction, model_name):
    row = {
        "tidpunkt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "modell": model_name,
        "prediktion": prediction,
    }
    for name in features:
        row[name] = features[name]

    df = pd.DataFrame([row])
    write_table(df, config.PREDICTIONS_TABLE, if_exists="append", index_cols=())
