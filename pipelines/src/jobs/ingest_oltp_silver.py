import argparse
import sys

from lakehouse.config import load_config
from lakehouse.silver import merge_oltp_table
from lakehouse.silver_ddl import ensure_silver_tables
from lakehouse.spark import spark_session


def parse_args(args):
    parser = argparse.ArgumentParser(description="Ingest OLTP Bronze to Silver")
    parser.add_argument("--config-path", required=True, help="Path to pipeline config YAML")
    parser.add_argument("--run-id", required=True, help="Airflow DAG run ID")
    parser.add_argument("--bronze-date", required=True, help="Bronze date to process (YYYY-MM-DD)")
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])
    spark = spark_session("ingest_oltp_bronze_to_silver")
    try:
        cfg = load_config(args.config_path)
        ensure_silver_tables(spark)

        for table in cfg.tables:
            bronze_table = f"lakehouse.bronze.{table.name}"
            silver_path = f"s3a://{cfg.bucket}/warehouse/silver/{table.silver_table}"

            try:
                bronze_df = spark.read.format("iceberg").load(bronze_table)
            except Exception:
                print(f"Bronze table {bronze_table} not found, skipping.")
                continue

            result = merge_oltp_table(
                spark=spark,
                table=table,
                bronze_df=bronze_df,
                run_id=args.run_id,
                target_path=silver_path,
            )

            print(f"{table.name}: inserted={result.inserted}, updated={result.updated}, quarantined={result.quarantined}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
