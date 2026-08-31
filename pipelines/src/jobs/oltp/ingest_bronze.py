import argparse
import sys
from lakehouse.spark import spark_session
from lakehouse.oltp.bronze import ingest_to_bronze

def parse_args(args):
    parser = argparse.ArgumentParser(description="Ingest Landing data to Bronze")
    parser.add_argument("--job-name", required=True, help="Spark application name")
    parser.add_argument("--run-id", required=True, help="Airflow DAG run ID or unique identifier")
    parser.add_argument("--source-path", required=True, help="S3 path to the landing directory")
    parser.add_argument("--source-format", required=True, choices=["parquet", "json"], help="Source data format")
    parser.add_argument("--target-table", required=True, help="Iceberg target table (e.g., lakehouse.bronze.orders)")
    parser.add_argument("--quarantine-table", required=True, help="Iceberg quarantine table")
    parser.add_argument("--error-threshold", type=float, default=0.01, help="Fraction of allowed corrupt records")
    return parser.parse_args(args)

def main():
    args = parse_args(sys.argv[1:])
    spark = spark_session(args.job_name)
    try:
        ingest_to_bronze(
            spark=spark,
            run_id=args.run_id,
            source_path=args.source_path,
            source_format=args.source_format,
            target_table=args.target_table,
            quarantine_table=args.quarantine_table,
            error_threshold=args.error_threshold
        )
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
