import argparse
import json

import _path
import config
from src import db, scb_api


def main(offline=False):
    for dataset_key in config.SCB_DATASETS:
        table_id = config.SCB_DATASETS[dataset_key]["table_id"]
        json_path = config.DATA_RAW_DIR / (dataset_key + "_" + table_id + ".json")

        if offline:
            print("Läser in", json_path.name)
            with open(json_path, encoding="utf-8") as f:
                payload = json.load(f)
        else:
            print("Hämtar", dataset_key, "från SCB.")
            payload = scb_api.get_data(dataset_key)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)

        df_long = scb_api.parse_jsonstat2(payload)
        df = scb_api.tidy_dataframe(df_long, dataset_key)
        db.write_table(df, dataset_key)

        print(f"  {len(df)} rader, {df['period'].nunique()} perioder "
              f"({df['period'].min()} till {df['period'].max()}), "
              f"{df['grupp'].nunique()} grupper, saknade värden: {df.isna().sum().sum()}")

    print("Inläsningen är klar. Tabeller i databasen:", db.list_tables())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    main(offline=args.offline)
