import argparse
import os
import sys

from pyspark.sql.functions import col, input_file_name, lit

from lakehouse.logs.bronze import (
    BRONZE_EVENTS_TABLE,
    BRONZE_QUARANTINE_TABLE,
    OTEL_LOG_SCHEMA,
    ensure_bronze_tables,
    get_committed_landing_files,
    transform_corrupt_logs,
    transform_valid_logs,
)
from lakehouse.spark import spark_session


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest access logs from MinIO Landing Zone to Iceberg Bronze layer"
    )
    parser.add_argument("--run-id", required=True, help="Batch run identifier")
    parser.add_argument("--ingest-date", help="Target UTC date (YYYY-MM-DD)")
    parser.add_argument("--ingest-hour", help="Target UTC hour (HH)")
    parser.add_argument("--replay-date", help="Replay entire target date (YYYY-MM-DD)")
    parser.add_argument(
        "--bucket",
        default=os.environ.get("MINIO_LAKEHOUSE_BUCKET", "lakehouse"),
        help="MinIO S3 bucket name (default: lakehouse)",
    )
    args = parser.parse_args()

    if not args.replay_date and not args.ingest_date:
        parser.error("Either --ingest-date or --replay-date must be provided.")

    return args


def main() -> None:
    args = parse_arguments()
    bucket = args.bucket
    spark = spark_session("ingest_logs_to_bronze")

    # 1. Ensure Polaris namespaces and Iceberg tables exist
    ensure_bronze_tables(spark)

    # 2. Resolve Landing Source Path
    if args.replay_date:
        query_date = args.replay_date
        landing_glob = f"s3a://{bucket}/landing/logs/ingest_date={args.replay_date}/*/*/*.jsonl.gz"
    else:
        query_date = args.ingest_date
        if args.ingest_hour:
            landing_glob = (
                f"s3a://{bucket}/landing/logs/"
                f"ingest_date={args.ingest_date}/ingest_hour={args.ingest_hour}/service=ecommerce-api/*.jsonl.gz"
            )
        else:
            landing_glob = f"s3a://{bucket}/landing/logs/ingest_date={args.ingest_date}/*/*/*.jsonl.gz"

    print(f"[{args.run_id}] Scanning landing path: {landing_glob}")

    # 3. Read landing files with explicit OTel schema and capture source file
    try:
        raw_df = (
            spark.read.schema(OTEL_LOG_SCHEMA)
            .json(landing_glob)
            .withColumn("_source_file", input_file_name())
            .cache()
        )
    except Exception as exc:
        print(f"[{args.run_id}] No files found or unable to read {landing_glob}: {exc}")
        spark.stop()
        sys.exit(0)

    # 4. Anti-Join: Query committed files for target date partition (Partition + Column Pruning)
    if not args.replay_date:
        committed_files = get_committed_landing_files(spark, query_date)
        if committed_files:
            print(f"[{args.run_id}] Found {len(committed_files)} already-committed files for date {query_date}.")
            unprocessed_df = raw_df.filter(~col("_source_file").isin(list(committed_files)))
        else:
            unprocessed_df = raw_df
    else:
        unprocessed_df = raw_df

    # 5. Separate corrupt and valid records
    corrupt_raw_df = unprocessed_df.filter(col("_corrupt_record").isNotNull())
    valid_raw_df = unprocessed_df.filter(col("_corrupt_record").isNull())

    valid_count = valid_raw_df.count()
    corrupt_count = corrupt_raw_df.count()

    if valid_count == 0 and corrupt_count == 0:
        print(f"[{args.run_id}] All files in {landing_glob} have already been ingested. Zero-cost No-Op.")
        raw_df.unpersist()
        spark.stop()
        sys.exit(0)

    print(f"[{args.run_id}] Processing: {valid_count} valid records, {corrupt_count} corrupt records.")

    # 7. Commit valid records to Bronze table
    if valid_count > 0:
        enriched_valid_df = transform_valid_logs(valid_raw_df, args.run_id)
        if args.replay_date:
            enriched_valid_df.writeTo(BRONZE_EVENTS_TABLE).overwrite(
                col("event_ts").cast("date") == lit(args.replay_date)
            )
            print(f"[{args.run_id}] Atomically overwritten partition {args.replay_date} in {BRONZE_EVENTS_TABLE}.")
        else:
            enriched_valid_df.writeTo(BRONZE_EVENTS_TABLE).append()
            print(f"[{args.run_id}] Successfully appended {valid_count} records to {BRONZE_EVENTS_TABLE}.")

    # 8. Commit corrupt records to Quarantine table
    if corrupt_count > 0:
        enriched_corrupt_df = transform_corrupt_logs(corrupt_raw_df, args.run_id)
        enriched_corrupt_df.writeTo(BRONZE_QUARANTINE_TABLE).append()
        print(f"[{args.run_id}] Routed {corrupt_count} corrupt records to {BRONZE_QUARANTINE_TABLE}.")

    raw_df.unpersist()
    spark.stop()
    print(f"[{args.run_id}] Bronze log ingestion completed successfully.")


if __name__ == "__main__":
    main()
