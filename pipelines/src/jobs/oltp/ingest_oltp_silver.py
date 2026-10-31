import argparse
import sys

from lakehouse.config import load_config
from lakehouse.oltp.ingestion import ingest_silver_tables
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
        ingest_silver_tables(spark, cfg, args.run_id, args.bronze_date)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
