import argparse
import os
import sys

from lakehouse.config import load_config
from lakehouse.oltp.bronze import ingest_to_bronze
from lakehouse.spark import spark_session


def discover_latest_run_id(spark, bucket: str, table: str, extract_date: str) -> str | None:
    """Find the latest run_id directory under extract_date that contains data files."""
    hadoop_path = spark._jvm.org.apache.hadoop.fs.Path(
        f"s3a://{bucket}/landing/oltp/{table}/extract_date={extract_date}"
    )
    fs = hadoop_path.getFileSystem(spark._jsc.hadoopConfiguration())

    try:
        if not fs.exists(hadoop_path):
            return None
        run_dirs = fs.listStatus(hadoop_path)
    except Exception:
        return None

    # Collect run_ids that have data files
    candidates = []
    for d in run_dirs:
        if not d.isDirectory():
            continue
        dir_name = d.getPath().getName()
        if not dir_name.startswith("run_id="):
            continue
        rid = dir_name.split("=", 1)[1]
        data_path = spark._jvm.org.apache.hadoop.fs.Path(
            f"s3a://{bucket}/landing/oltp/{table}/extract_date={extract_date}/{dir_name}/data"
        )
        try:
            if fs.exists(data_path) and len(fs.listStatus(data_path)) > 0:
                candidates.append(rid)
        except Exception:
            continue

    if not candidates:
        return None
    # Return the lexicographically last run_id (most recent by UUIDv7 or similar)
    return sorted(candidates)[-1]


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
    parser.add_argument("--run-id", default=None, help="Airflow DAG run ID (auto-discovered if omitted)")
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
    run_id = args.run_id

    for idx, table_name in enumerate(tables_to_ingest, 1):
        table_spec = cfg.table(table_name)
        if table_spec is None:
            print(f"[{idx}/{total_tables}] WARNING: Table '{table_name}' not found in config, skipping.")
            skip_count += 1
            continue

        # Auto-discover run_id if not provided
        effective_run_id = run_id
        if not effective_run_id:
            effective_run_id = discover_latest_run_id(spark, args.bucket, table_name, args.extract_date)
            if not effective_run_id:
                print(f"[{idx}/{total_tables}] SKIP: '{table_name}' - no landing run found.")
                skip_count += 1
                continue

        source_path = build_landing_path(args.bucket, table_name, args.extract_date, effective_run_id)
        target_table = build_target_table(table_name)
        quarantine_table = build_quarantine_table(table_name)

        print(f"[{idx}/{total_tables}] Ingesting '{table_name}' from Landing to Bronze...")
        print(f"  Source: {source_path}")
        print(f"  Target: {target_table}")

        try:
            # Check if landing data dir exists and has parquet files
            try:
                data_dir_path = spark._jvm.org.apache.hadoop.fs.Path(
                    f"s3a://{args.bucket}/landing/oltp/{table_name}/extract_date={args.extract_date}/run_id={effective_run_id}/data"
                )
                fs = data_dir_path.getFileSystem(spark._jsc.hadoopConfiguration())
                has_data = fs.exists(data_dir_path) and len(fs.listStatus(data_dir_path)) > 0
            except Exception:
                has_data = False

            if not has_data:
                print(f"[{idx}/{total_tables}] SKIP: '{table_name}' - no landing data found.")
                skip_count += 1
                continue

            ingest_to_bronze(
                spark=spark,
                run_id=effective_run_id,
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
