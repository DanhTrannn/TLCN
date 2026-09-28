from __future__ import annotations

import pytest
from lakehouse.oltp.gold_ddl import GOLD_TABLE_DDL

# Import the maintenance argument parser and resolver
# (This will fail or be imported from jobs.maintenance.iceberg_table_maintenance)
from jobs.maintenance.iceberg_table_maintenance import (
    TABLE_PROFILES,
    parse_args,
    resolve_tables,
)


def test_table_profiles_definitions():
    """Verify standard profiles contain expected tables."""
    assert "streaming" in TABLE_PROFILES
    assert "oltp" in TABLE_PROFILES
    assert "all" in TABLE_PROFILES

    streaming_tables = TABLE_PROFILES["streaming"]
    assert "landing.access_logs" in streaming_tables
    assert "bronze.web_events" in streaming_tables
    assert "silver.silver_logs" in streaming_tables
    assert "gold.fact_web_events" in streaming_tables

    oltp_tables = TABLE_PROFILES["oltp"]
    assert "gold.fact_order" in oltp_tables
    assert "gold.fact_order_item" in oltp_tables
    assert "gold.fact_shipment" in oltp_tables
    assert "gold.fact_return_exchange" in oltp_tables
    assert "gold.fact_inventory_daily_snapshot" in oltp_tables
    assert "gold.mart_sales_daily" in oltp_tables


def test_resolve_tables_by_profile():
    """Verify table resolution by profile name."""
    args = parse_args(["--profile", "streaming"])
    tables = resolve_tables(args)
    assert tables == TABLE_PROFILES["streaming"]

    args_oltp = parse_args(["--profile", "oltp"])
    tables_oltp = resolve_tables(args_oltp)
    assert "gold.fact_order" in tables_oltp
    assert "gold.fact_order_item" in tables_oltp

    args_all = parse_args(["--profile", "all"])
    tables_all = resolve_tables(args_all)
    for t in TABLE_PROFILES["streaming"]:
        assert t in tables_all
    for t in TABLE_PROFILES["oltp"]:
        assert t in tables_all


def test_resolve_tables_explicit_override():
    """Explicit --tables flag overrides profile setting."""
    args = parse_args(["--tables", "custom.table1, custom.table2", "--profile", "oltp"])
    tables = resolve_tables(args)
    assert tables == ["custom.table1", "custom.table2"]


def test_parse_args_maintenance_options():
    """Verify arguments for compaction target size and retention."""
    args = parse_args([
        "--action", "compact",
        "--profile", "oltp",
        "--target-file-size-bytes", "134217728",
        "--retain-snapshots", "15",
    ])
    assert args.action == "compact"
    assert args.profile == "oltp"
    assert args.target_file_size_bytes == 134217728
    assert args.retain_snapshots == 15


def test_fact_order_item_partitioning_and_properties():
    """fact_order_item DDL must be partitioned by order_date and have 128MB target file size."""
    ddl = GOLD_TABLE_DDL["fact_order_item"]
    assert "order_date                      DATE" in ddl
    assert "PARTITIONED BY (order_date)" in ddl
    assert "'write.target-file-size-bytes' = '134217728'" in ddl
    assert "'history.expire.max-snapshot-age-ms' = '259200000'" in ddl


def test_gold_facts_and_marts_iceberg_properties():
    """Verify all gold facts and marts have optimized Iceberg properties."""
    tables_to_check = [
        "fact_order",
        "fact_order_item",
        "fact_shipment",
        "fact_return_exchange",
        "fact_inventory_daily_snapshot",
        "mart_sales_daily",
        "mart_logistics_performance",
        "mart_product_returns",
        "mart_inventory_health",
    ]
    for table_name in tables_to_check:
        ddl = GOLD_TABLE_DDL[table_name]
        assert "'write.target-file-size-bytes' = '134217728'" in ddl, f"{table_name} missing target file size"
        assert "'history.expire.max-snapshot-age-ms' = '259200000'" in ddl, f"{table_name} missing max snapshot age"
