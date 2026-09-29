from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pyspark.sql import functions as F

from lakehouse.oltp.gold import (
    build_dim_customer,
    build_dim_date,
    build_dim_delivery_staff,
    build_dim_product,
    build_dim_store,
    build_dim_variant,
    build_fact_inventory_daily_snapshot,
    build_fact_order,
    build_fact_order_item,
    build_fact_return_exchange,
    build_fact_shipment,
    build_mart_inventory_health,
    build_mart_logistics_performance,
    build_mart_product_returns,
    build_mart_sales_daily,
)
from lakehouse.oltp.gold_ddl import ensure_oltp_gold_tables
from lakehouse.spark import spark_session

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

VALID_STAGES = ("all", "dimensions", "facts", "marts")


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build OLTP Gold layer tables (Star Schema & Marts)")
    parser.add_argument("--run-id", required=True, help="Batch or DAG run ID")
    parser.add_argument(
        "--snapshot-date",
        default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        help="Inventory snapshot date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--stage",
        choices=VALID_STAGES,
        default="all",
        help="Gold stage to build: dimensions, facts, marts, or all (default: all)",
    )
    return parser.parse_args(args)


def run_gold_dimensions(spark: SparkSession, run_id: str) -> None:
    """Load Silver dependencies and build Gold conformed dimensions."""
    print(f"[{run_id}] [Dimensions] Loading Silver tables...")
    silver_products = spark.read.format("iceberg").load("lakehouse.silver.silver_products")
    silver_categories = spark.read.format("iceberg").load("lakehouse.silver.silver_categories")
    silver_product_variants = spark.read.format("iceberg").load("lakehouse.silver.silver_product_variants")
    silver_stores = spark.read.format("iceberg").load("lakehouse.silver.silver_stores")
    silver_cities = spark.read.format("iceberg").load("lakehouse.silver.silver_cities")
    silver_delivery_staff = spark.read.format("iceberg").load("lakehouse.silver.silver_delivery_staff")
    silver_customers = spark.read.format("iceberg").load("lakehouse.silver.silver_customers")

    print(f"[{run_id}] [Dimensions] Building dim_date...")
    dim_date = build_dim_date(spark)
    dim_date.writeTo("lakehouse.gold.dim_date").overwritePartitions()

    print(f"[{run_id}] [Dimensions] Building dim_product...")
    dim_product = build_dim_product(silver_products, silver_categories, run_id)
    dim_product.writeTo("lakehouse.gold.dim_product").overwrite(F.lit(True))

    print(f"[{run_id}] [Dimensions] Building dim_variant...")
    dim_variant = build_dim_variant(silver_product_variants, silver_products, run_id)
    dim_variant.writeTo("lakehouse.gold.dim_variant").overwrite(F.lit(True))

    print(f"[{run_id}] [Dimensions] Building dim_store...")
    dim_store = build_dim_store(silver_stores, silver_cities, run_id)
    dim_store.writeTo("lakehouse.gold.dim_store").overwrite(F.lit(True))

    print(f"[{run_id}] [Dimensions] Building dim_delivery_staff...")
    dim_delivery_staff = build_dim_delivery_staff(silver_delivery_staff, silver_cities, run_id)
    dim_delivery_staff.writeTo("lakehouse.gold.dim_delivery_staff").overwrite(F.lit(True))

    print(f"[{run_id}] [Dimensions] Building dim_customer...")
    dim_customer = build_dim_customer(silver_customers, silver_cities, run_id)
    dim_customer.writeTo("lakehouse.gold.dim_customer").overwrite(F.lit(True))

    print(f"[{run_id}] [Dimensions] All 6 Gold Dimensions successfully built!")


def run_gold_facts(spark: SparkSession, run_id: str, snapshot_date: str) -> None:
    """Load Silver dependencies and build Gold fact tables."""
    print(f"[{run_id}] [Facts] Loading Silver tables...")
    silver_orders = spark.read.format("iceberg").load("lakehouse.silver.silver_orders")
    silver_order_items = spark.read.format("iceberg").load("lakehouse.silver.silver_order_items")
    silver_product_variants = spark.read.format("iceberg").load("lakehouse.silver.silver_product_variants")
    silver_shipments = spark.read.format("iceberg").load("lakehouse.silver.silver_shipments")
    silver_return_requests = spark.read.format("iceberg").load("lakehouse.silver.silver_return_requests")
    silver_return_items = spark.read.format("iceberg").load("lakehouse.silver.silver_return_items")
    silver_inventory = spark.read.format("iceberg").load("lakehouse.silver.silver_inventory")
    silver_store_inventory = spark.read.format("iceberg").load("lakehouse.silver.silver_store_inventory")

    print(f"[{run_id}] [Facts] Building fact_order...")
    fact_order = build_fact_order(silver_orders, silver_order_items, run_id, silver_product_variants)
    fact_order.writeTo("lakehouse.gold.fact_order").overwritePartitions()

    print(f"[{run_id}] [Facts] Building fact_order_item...")
    fact_order_item = build_fact_order_item(
        silver_order_items, silver_orders, run_id, silver_product_variants
    )
    fact_order_item.writeTo("lakehouse.gold.fact_order_item").overwritePartitions()

    print(f"[{run_id}] [Facts] Building fact_shipment...")
    fact_shipment = build_fact_shipment(silver_shipments, run_id)
    fact_shipment.writeTo("lakehouse.gold.fact_shipment").overwritePartitions()

    print(f"[{run_id}] [Facts] Building fact_return_exchange...")
    fact_return_exchange = build_fact_return_exchange(silver_return_requests, silver_return_items, run_id)
    fact_return_exchange.writeTo("lakehouse.gold.fact_return_exchange").overwritePartitions()

    print(f"[{run_id}] [Facts] Building fact_inventory_daily_snapshot...")
    fact_inventory_daily_snapshot = build_fact_inventory_daily_snapshot(
        silver_inventory, silver_store_inventory, silver_product_variants, snapshot_date, run_id
    )
    fact_inventory_daily_snapshot.writeTo("lakehouse.gold.fact_inventory_daily_snapshot").overwritePartitions()

    print(f"[{run_id}] [Facts] All 5 Gold Facts successfully built!")


def run_gold_marts(spark: SparkSession, run_id: str) -> None:
    """Load Gold Facts and Dimensions to rollup Data Marts."""
    print(f"[{run_id}] [Marts] Loading Gold Facts & Dimensions...")
    fact_order = spark.read.format("iceberg").load("lakehouse.gold.fact_order")
    fact_order_item = spark.read.format("iceberg").load("lakehouse.gold.fact_order_item")
    dim_product = spark.read.format("iceberg").load("lakehouse.gold.dim_product")
    fact_shipment = spark.read.format("iceberg").load("lakehouse.gold.fact_shipment")
    dim_delivery_staff = spark.read.format("iceberg").load("lakehouse.gold.dim_delivery_staff")
    fact_return_exchange = spark.read.format("iceberg").load("lakehouse.gold.fact_return_exchange")
    dim_variant = spark.read.format("iceberg").load("lakehouse.gold.dim_variant")
    fact_inventory_daily_snapshot = spark.read.format("iceberg").load("lakehouse.gold.fact_inventory_daily_snapshot")

    print(f"[{run_id}] [Marts] Building mart_sales_daily...")
    mart_sales_daily = build_mart_sales_daily(fact_order, fact_order_item, dim_product, run_id)
    mart_sales_daily.writeTo("lakehouse.gold.mart_sales_daily").overwritePartitions()

    print(f"[{run_id}] [Marts] Building mart_logistics_performance...")
    mart_logistics_performance = build_mart_logistics_performance(fact_shipment, dim_delivery_staff, run_id)
    mart_logistics_performance.writeTo("lakehouse.gold.mart_logistics_performance").overwritePartitions()

    print(f"[{run_id}] [Marts] Building mart_product_returns...")
    mart_product_returns = build_mart_product_returns(fact_return_exchange, dim_variant, run_id)
    mart_product_returns.writeTo("lakehouse.gold.mart_product_returns").overwritePartitions()

    print(f"[{run_id}] [Marts] Building mart_inventory_health...")
    mart_inventory_health = build_mart_inventory_health(fact_inventory_daily_snapshot, dim_product, run_id)
    mart_inventory_health.writeTo("lakehouse.gold.mart_inventory_health").overwritePartitions()

    print(f"[{run_id}] [Marts] All 4 Gold Data Marts successfully built!")


def main() -> None:
    args = parse_args(sys.argv[1:])
    app_name = f"build_oltp_gold_{args.stage}" if args.stage != "all" else "build_oltp_gold"
    spark = spark_session(app_name)

    try:
        print(f"[{args.run_id}] Ensuring Gold tables DDL...")
        ensure_oltp_gold_tables(spark)

        if args.stage in ("all", "dimensions"):
            run_gold_dimensions(spark, args.run_id)

        if args.stage in ("all", "facts"):
            run_gold_facts(spark, args.run_id, args.snapshot_date)

        if args.stage in ("all", "marts"):
            run_gold_marts(spark, args.run_id)

        print(f"[{args.run_id}] Gold stage '{args.stage}' successfully finished!")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
