"""Spark job for Iceberg table maintenance in Pure Streaming and OLTP Lakehouse.

Actions:
- rewrite_data_files: Compaction of small Parquet files into optimal sizes (128MB target).
- rewrite_manifests: Manifest file optimization for faster query scan planning.
- expire_snapshots: Purging old metadata snapshots beyond retention policies.
- remove_orphan_files: Cleaning up unreferenced or aborted files on object storage.
"""

from __future__ import annotations


import argparse
from typing import Sequence

from lakehouse.spark import spark_session
from lakehouse.maintenance import maintain_tables

# Standard table profiles across Lakehouse layers


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Iceberg table maintenance")
    parser.add_argument(
        "--profile",
        choices=["streaming", "oltp", "all", "custom"],
        default=None,
        help="Predefined table profile (streaming, oltp, all)",
    )
    parser.add_argument(
        "--tables",
        default=None,
        help="Comma-separated table names (e.g. landing.access_logs,gold.fact_order). Overrides profile.",
    )
    parser.add_argument(
        "--retain-snapshots",
        type=int,
        default=20,
        help="Number of snapshots to retain during expire_snapshots (default: 20)",
    )
    parser.add_argument(
        "--target-file-size-bytes",
        type=int,
        default=134217728,  # 128 MB
        help="Target data file size in bytes for compaction (default: 134217728 = 128MB)",
    )
    parser.add_argument(
        "--older-than-days",
        type=int,
        default=3,
        help="Retention period in days for orphan files cleanup (default: 3 days)",
    )
    parser.add_argument(
        "--catalog",
        default="lakehouse",
        help="Iceberg catalog name (default: lakehouse)",
    )
    parser.add_argument(
        "--action",
        choices=["all", "compact", "expire", "orphan", "quarantine"],
        default="all",
        help="Maintenance action to perform (default: all)",
    )
    parser.add_argument(
        "--quarantine-retention-days",
        type=int,
        default=30,
        help="Delete quarantined records older than this many days (default: 30)",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    spark = spark_session("iceberg_table_maintenance")
    try:
        maintain_tables(spark, args)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
