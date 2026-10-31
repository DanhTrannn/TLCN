"""Iceberg maintenance operations; CLI owns the Spark lifecycle."""

from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
from lakehouse.sql import identifier, literal, render_sql

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


def resolve_tables(args: argparse.Namespace) -> list[str]:
    """Resolve target tables based on explicit list, profile, or defaults."""
    if args.tables:
        return [t.strip() for t in args.tables.split(",") if t.strip()]
    if args.profile and args.profile in TABLE_PROFILES:
        return TABLE_PROFILES[args.profile]
    return TABLE_PROFILES["streaming"]


def maintain_tables(spark, args):
    catalog = args.catalog
    tables = resolve_tables(args)
    if args.action == "quarantine":
        if args.quarantine_retention_days < 1:
            raise ValueError("--quarantine-retention-days must be at least 1")
        cutoff = datetime.now(timezone.utc) - timedelta(days=args.quarantine_retention_days)
        cutoff_sql = cutoff.strftime("%Y-%m-%d %H:%M:%S")
        print(
            "Deleting quarantined OLTP rows older than "
            f"{args.quarantine_retention_days} days (before {cutoff_sql} UTC)..."
        )
        spark.sql(render_sql("spark/operations/delete_expired_quarantine.sql", cutoff_sql=literal(cutoff_sql)))
        return

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
                            render_sql(
                                "spark/operations/compact_with_options.sql",
                                catalog=identifier(catalog),
                                full_tbl=literal(full_tbl),
                                args_target_file_size_bytes=literal(args.target_file_size_bytes),
                            )
                        )
                        compact_res.show(truncate=False)
                    except Exception as inner_exc:
                        print(f"[{full_tbl}] Map options rewrite failed ({inner_exc}), retrying default procedure...")
                        compact_res = spark.sql(
                            render_sql(
                                "spark/operations/compact.sql", catalog=identifier(catalog), full_tbl=literal(full_tbl)
                            )
                        )
                        compact_res.show(truncate=False)
                else:
                    compact_res = spark.sql(
                        render_sql(
                            "spark/operations/compact.sql", catalog=identifier(catalog), full_tbl=literal(full_tbl)
                        )
                    )
                    compact_res.show(truncate=False)
            except Exception as exc:
                print(f"[{full_tbl}] Error compacting data files: {exc}")
                error_count += 1

            print(f"[{full_tbl}] Running rewrite_manifests...")
            try:
                spark.sql(
                    render_sql(
                        "spark/operations/rewrite_manifests.sql",
                        catalog=identifier(catalog),
                        full_tbl=literal(full_tbl),
                    )
                )
            except Exception as exc:
                print(f"[{full_tbl}] Error rewriting manifests: {exc}")
                error_count += 1

        if args.action in ("all", "expire"):
            print(f"[{full_tbl}] Running expire_snapshots (retain_last = {args.retain_snapshots})...")
            try:
                expire_res = spark.sql(
                    render_sql(
                        "spark/operations/expire_snapshots.sql",
                        catalog=identifier(catalog),
                        full_tbl=literal(full_tbl),
                        args_retain_snapshots=literal(args.retain_snapshots),
                    )
                )
                expire_res.show(truncate=False)
            except Exception as exc:
                print(f"[{full_tbl}] Error expiring snapshots: {exc}")
                error_count += 1

        if args.action in ("all", "orphan"):
            print(f"[{full_tbl}] Running remove_orphan_files...")
            try:
                if args.older_than_days < 1:
                    raise ValueError("--older-than-days must be at least 1")
                orphan_cutoff = datetime.now(timezone.utc) - timedelta(days=args.older_than_days)
                orphan_cutoff_sql = orphan_cutoff.strftime("%Y-%m-%d %H:%M:%S")
                orphan_res = spark.sql(
                    render_sql(
                        "spark/operations/remove_orphans.sql",
                        catalog=identifier(catalog),
                        full_tbl=literal(full_tbl),
                        orphan_cutoff_sql=literal(orphan_cutoff_sql),
                    )
                )
                orphan_res.show(truncate=False)
            except Exception as exc:
                print(f"[{full_tbl}] Error removing orphan files: {exc}")
                error_count += 1

        success_count += 1

    print(f"\nIceberg maintenance completed. Processed: {success_count} tables, Errors encountered: {error_count}.")
    if error_count > 0:
        raise RuntimeError(f"Iceberg maintenance encountered {error_count} errors across {len(tables)} tables.")
