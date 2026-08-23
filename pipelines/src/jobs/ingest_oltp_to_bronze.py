import argparse
import os
import sys

from lakehouse.bronze import ingest_to_bronze
from lakehouse.config import load_config
from lakehouse.spark import spark_session


def build_landing_path(bucket: str, table: str, extract_date: str, run_id: str) -> str:
    return f"s3a://{bucket}/landing/oltp/{table}/extract_date={extract_date}/run_id={run_id}/data/*.parquet"


def build_target_table(table: str) -> str:
    return f"lakehouse.bronze.{table}"


def build_quarantine_table(table: str) -> str:
    return f"lakehouse.quarantine.{table}_errors"


def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Ingest OLTP Landing data to Bronze Iceberg tables"
    )
    parser.add_argument("--run-id", required=True, help="Airflow DAG run ID")
    parser.add_argument("--extract-date", required=True, help="Extract date (YYYY-MM-DD)")
    parser.add_argument("--tables", nargs="*", help="Specific tables to ingest (default: all)")
    parser.add_argument(
        "--bucket",
        default=os.environ.get("MINIO_LAKEHOUSE_BUCKET", "lakehouse"),
        help="MinIO S3 bucket name",
    )
    parser.add_argument("--error-threshold", type=float, default=0.01)
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])
    cfg = load_config()
    spark = spark_session("ingest_oltp_to_bronze")

    tables_to_ingest = args.tables if args.tables else [t.name for t in cfg.tables]
    total_tables = len(tables_to_ingest)
    success_count = 0
    skip_count = 0

    for idx, table_name in enumerate(tables_to_ingest, 1):
        table_spec = cfg.table(table_name)
        if table_spec is None:
            print(f"[{idx}/{total_tables}] WARNING: Table '{table_name}' not found in config, skipping.")
            skip_count += 1
            continue

        source_path = build_landing_path(args.bucket, table_name, args.extract_date, args.run_id)
        target_table = build_target_table(table_name)
        quarantine_table = build_quarantine_table(table_name)

        print(f"[{idx}/{total_tables}] Ingesting '{table_name}' from Landing to Bronze...")
        print(f"  Source: {source_path}")
        print(f"  Target: {target_table}")

        try:
            ingest_to_bronze(
                spark=spark,
                run_id=args.run_id,
                source_path=source_path,
                source_format="parquet",
                target_table=target_table,
                quarantine_table=quarantine_table,
                error_threshold=args.error_threshold,
            )
            success_count += 1
            print(f"[{idx}/{total_tables}] OK: '{table_name}' ingested successfully.")
        except Exception as exc:
            print(f"[{idx}/{total_tables}] FAILED: '{table_name}' - {exc}")
            raise

    spark.stop()
    print(f"\nBronze OLTP ingestion completed: {success_count} success, {skip_count} skipped, {total_tables} total.")


if __name__ == "__main__":
    main()
