import argparse
import json

from lakehouse.config import load_config
from lakehouse.extract import run_extract
from lakehouse.spark import spark_session


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract OLTP tables to MinIO landing")
    parser.add_argument("--config-path", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--extract-date", required=True)
    parser.add_argument("--high-watermarks", required=True)
    args = parser.parse_args()

    cfg = load_config(args.config_path)
    high_watermarks = json.loads(args.high_watermarks)
    spark = spark_session("extract_oltp_to_landing")
    manifests = run_extract(
        spark, cfg, high_watermarks,
        run_id=args.run_id, extract_date=args.extract_date,
        max_workers=cfg.run.max_parallel_tables,
    )
    for manifest in manifests:
        print(f"EXTRACT OK: {manifest['table']} rows={manifest['rows']} empty={manifest['empty']}")
    spark.stop()


if __name__ == "__main__":
    main()