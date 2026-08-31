import argparse
import sys

from lakehouse.logs.bronze import BRONZE_EVENTS_TABLE
from lakehouse.logs.silver import ensure_logs_silver_tables, ingest_logs_to_silver
from lakehouse.spark import spark_session


def parse_args(args):
    parser = argparse.ArgumentParser(description="Ingest Logs Bronze to Silver")
    parser.add_argument("--run-id", required=True, help="Airflow DAG run ID")
    parser.add_argument("--ingest-date", required=True, help="Target date (YYYY-MM-DD)")
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])
    spark = spark_session("ingest_logs_bronze_to_silver")
    try:
        ensure_logs_silver_tables(spark)

        try:
            bronze_df = spark.read.format("iceberg").load(BRONZE_EVENTS_TABLE)
        except Exception:
            print(f"Bronze table {BRONZE_EVENTS_TABLE} not found. Exiting.")
            return

        count = ingest_logs_to_silver(
            spark=spark,
            bronze_df=bronze_df,
            run_id=args.run_id,
            target_path="",
        )

        print(f"Logs Silver: ingested={count} records")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
