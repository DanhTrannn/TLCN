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

# Standard table profiles across Lakehouse layers
TABLE_PROFILES: dict[str, list[str]] = {
    "streaming": [
        "landing.access_logs",
        "bronze.web_events",
        "silver.silver_logs",
        "gold.fact_web_events",
    ],
    "oltp": [
        # Gold Facts
        "gold.fact_order",
        "gold.fact_order_item",
        "gold.fact_shipment",
        "gold.fact_return_exchange",
        "gold.fact_inventory_daily_snapshot",
        # Gold Data Marts
        "gold.mart_sales_daily",
        "gold.mart_logistics_performance",
        "gold.mart_product_returns",
        "gold.mart_inventory_health",
        # Gold Conformed Dimensions
        "gold.dim_customer",
        "gold.dim_product",
        "gold.dim_variant",
        "gold.dim_store",
        "gold.dim_delivery_staff",
        "gold.dim_date",
        # Core Silver Tables
        "silver.silver_orders",
        "silver.silver_order_items",
        "silver.silver_product_variants",
        "silver.silver_inventory",
        "silver.silver_shipments",
        "silver.silver_return_requests",
        "silver.silver_inbound_receipts",
        "silver.silver_inbound_receipt_items",
    ],
}
TABLE_PROFILES["all"] = TABLE_PROFILES["streaming"] + TABLE_PROFILES["oltp"]


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
        choices=["all", "compact", "expire", "orphan"],
        default="all",
        help="Maintenance action to perform (default: all)",
    )
    return parser.parse_args(argv)


def resolve_tables(args: argparse.Namespace) -> list[str]:
    """Resolve target tables based on explicit list, profile, or defaults."""
    if args.tables:
        return [t.strip() for t in args.tables.split(",") if t.strip()]
    if args.profile and args.profile in TABLE_PROFILES:
        return TABLE_PROFILES[args.profile]
    return TABLE_PROFILES["streaming"]


def main() -> None:
    args = parse_args()
    catalog = args.catalog
    tables = resolve_tables(args)

    spark = spark_session("iceberg_table_maintenance")
    try:
        print(f"=== Starting Iceberg Table Maintenance (Action: {args.action}, Target Tables: {len(tables)}) ===")
        success_count = 0
        error_count = 0

        for tbl in tables:
            full_tbl = f"{catalog}.{tbl}" if not tbl.startswith(f"{catalog}.") else tbl
            print(f"\n--- Maintenance on {full_tbl} ---")

            if args.action in ("all", "compact"):
                print(f"[{full_tbl}] Running rewrite_data_files (target_size={args.target_file_size_bytes}B)...")
                try:
                    if args.target_file_size_bytes:
                        try:
                            compact_res = spark.sql(
                                f"CALL {catalog}.system.rewrite_data_files("
                                f"table => '{full_tbl}', "
                                f"options => map('target-file-size-bytes', '{args.target_file_size_bytes}')"
                                f")"
                            )
                            compact_res.show(truncate=False)
                        except Exception as inner_exc:
                            print(f"[{full_tbl}] Map options rewrite failed ({inner_exc}), retrying default procedure...")
                            compact_res = spark.sql(f"CALL {catalog}.system.rewrite_data_files(table => '{full_tbl}')")
                            compact_res.show(truncate=False)
                    else:
                        compact_res = spark.sql(f"CALL {catalog}.system.rewrite_data_files(table => '{full_tbl}')")
                        compact_res.show(truncate=False)
                except Exception as exc:
                    print(f"[{full_tbl}] Error compacting data files: {exc}")
                    error_count += 1

                print(f"[{full_tbl}] Running rewrite_manifests...")
                try:
                    spark.sql(f"CALL {catalog}.system.rewrite_manifests(table => '{full_tbl}')")
                except Exception as exc:
                    print(f"[{full_tbl}] Error rewriting manifests: {exc}")
                    error_count += 1

            if args.action in ("all", "expire"):
                print(f"[{full_tbl}] Running expire_snapshots (retain_last = {args.retain_snapshots})...")
                try:
                    expire_res = spark.sql(
                        f"CALL {catalog}.system.expire_snapshots("
                        f"table => '{full_tbl}', "
                        f"retain_last => {args.retain_snapshots}"
                        f")"
                    )
                    expire_res.show(truncate=False)
                except Exception as exc:
                    print(f"[{full_tbl}] Error expiring snapshots: {exc}")
                    error_count += 1

            if args.action in ("all", "orphan"):
                print(f"[{full_tbl}] Running remove_orphan_files...")
                try:
                    orphan_res = spark.sql(f"CALL {catalog}.system.remove_orphan_files(table => '{full_tbl}')")
                    orphan_res.show(truncate=False)
                except Exception as exc:
                    print(f"[{full_tbl}] Error removing orphan files: {exc}")
                    error_count += 1

            success_count += 1

        print(f"\nIceberg maintenance completed. Processed: {success_count} tables, Errors encountered: {error_count}.")
        if error_count > 0:
            raise RuntimeError(f"Iceberg maintenance encountered {error_count} errors across {len(tables)} tables.")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
