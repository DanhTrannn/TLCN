"""Spark job for Iceberg table maintenance in Pure Streaming Lakehouse.

Actions:
- rewrite_data_files: Compaction of small Parquet files produced by streaming checkpoints.
- rewrite_manifests: Manifest file optimization for faster scan planning.
- expire_snapshots: Purging old metadata snapshots to control metadata volume.
- remove_orphan_files: Cleaning up unreferenced or aborted files.
"""

import argparse
import sys
from lakehouse.spark import spark_session


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Iceberg table maintenance")
    parser.add_argument(
        "--tables",
        default="landing.access_logs,bronze.web_events,silver.silver_logs,gold.fact_web_events",
        help="Comma-separated table names (e.g. landing.access_logs,...)",
    )
    parser.add_argument(
        "--retain-snapshots",
        type=int,
        default=20,
        help="Number of snapshots to retain",
    )
    parser.add_argument(
        "--action",
        choices=["all", "compact", "expire", "orphan"],
        default="all",
        help="Maintenance action to perform",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spark = spark_session("iceberg_table_maintenance")
    try:
        tables = [t.strip() for t in args.tables.split(",") if t.strip()]
        for tbl in tables:
            full_tbl = f"lakehouse.{tbl}" if not tbl.startswith("lakehouse.") else tbl
            print(f"=== Starting maintenance on {full_tbl} ===")

            if args.action in ("all", "compact"):
                print(f"[{full_tbl}] Running rewrite_data_files (compaction)...")
                try:
                    compact_res = spark.sql(f"CALL lakehouse.system.rewrite_data_files(table => '{full_tbl}')")
                    compact_res.show(truncate=False)
                except Exception as exc:
                    print(f"[{full_tbl}] Error compacting: {exc}")

                print(f"[{full_tbl}] Running rewrite_manifests...")
                try:
                    spark.sql(f"CALL lakehouse.system.rewrite_manifests(table => '{full_tbl}')")
                except Exception as exc:
                    print(f"[{full_tbl}] Error rewriting manifests: {exc}")

            if args.action in ("all", "expire"):
                print(f"[{full_tbl}] Running expire_snapshots (retain_last = {args.retain_snapshots})...")
                try:
                    expire_res = spark.sql(
                        f"CALL lakehouse.system.expire_snapshots(table => '{full_tbl}', retain_last => {args.retain_snapshots})"
                    )
                    expire_res.show(truncate=False)
                except Exception as exc:
                    print(f"[{full_tbl}] Error expiring snapshots: {exc}")

            if args.action in ("all", "orphan"):
                print(f"[{full_tbl}] Running remove_orphan_files...")
                try:
                    orphan_res = spark.sql(f"CALL lakehouse.system.remove_orphan_files(table => '{full_tbl}')")
                    orphan_res.show(truncate=False)
                except Exception as exc:
                    print(f"[{full_tbl}] Error removing orphan files: {exc}")

        print("Iceberg maintenance completed successfully.")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
