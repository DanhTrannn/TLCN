"""CLI entrypoint for validated, retry-safe Landing-to-Bronze ingestion."""

import argparse
import os
import sys

from lakehouse.config import load_config
from lakehouse.oltp.ingestion import ingest_bronze_tables
from lakehouse.spark import spark_session


def parse_args(args):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-path")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--extract-date", required=True)
    parser.add_argument("--tables", nargs="*")
    parser.add_argument("--bucket", default=os.environ.get("MINIO_LAKEHOUSE_BUCKET", "lakehouse"))
    parser.add_argument("--error-threshold", type=float, default=0.01)
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])
    cfg = load_config(args.config_path)
    os.environ["MINIO_LAKEHOUSE_BUCKET"] = args.bucket
    spark = spark_session("ingest_oltp_to_bronze")
    try:
        ingest_bronze_tables(spark, cfg, args.run_id, args.extract_date, args.tables, args.error_threshold)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
