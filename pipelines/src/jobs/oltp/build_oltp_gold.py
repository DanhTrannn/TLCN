from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

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


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build OLTP Gold layer tables (Star Schema & Marts)")
    parser.add_argument("--run-id", required=True, help="Batch or DAG run ID")
    parser.add_argument(
        "--snapshot-date",
        default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        help="Inventory snapshot date (YYYY-MM-DD)",
    )
    return parser.parse_args(args)


def main() -> None:
    args = parse_args(sys.argv[1:])
    spark = spark_session("build_oltp_gold")

    try:
        print(f"[{args.run_id}] Ensuring Gold tables DDL...")
        ensure_oltp_gold_tables(spark)

        # 1. Load Silver tables
        print(f"[{args.run_id}] Loading Silver tables...")
        silver_products = spark.read.format("iceberg").load("lakehouse.silver.silver_products")
        silver_categories = spark.read.format("iceberg").load("lakehouse.silver.silver_categories")
        silver_product_variants = spark.read.format("iceberg").load("lakehouse.silver.silver_product_variants")
        silver_stores = spark.read.format("iceberg").load("lakehouse.silver.silver_stores")
        silver_cities = spark.read.format("iceberg").load("lakehouse.silver.silver_cities")
        silver_delivery_staff = spark.read.format("iceberg").load("lakehouse.silver.silver_delivery_staff")
        silver_customers = spark.read.format("iceberg").load("lakehouse.silver.silver_customers")
        silver_orders = spark.read.format("iceberg").load("lakehouse.silver.silver_orders")
        silver_order_items = spark.read.format("iceberg").load("lakehouse.silver.silver_order_items")
        silver_shipments = spark.read.format("iceberg").load("lakehouse.silver.silver_shipments")
        silver_return_requests = spark.read.format("iceberg").load("lakehouse.silver.silver_return_requests")
        silver_return_items = spark.read.format("iceberg").load("lakehouse.silver.silver_return_items")
        silver_inventory = spark.read.format("iceberg").load("lakehouse.silver.silver_inventory")
        silver_store_inventory = spark.read.format("iceberg").load("lakehouse.silver.silver_store_inventory")

        # 2. Build and persist Dimensions
        print(f"[{args.run_id}] Building dim_date...")
        dim_date = build_dim_date(spark)
        dim_date.writeTo("lakehouse.gold.dim_date").overwritePartitions()

        print(f"[{args.run_id}] Building dim_product...")
        dim_product = build_dim_product(silver_products, silver_categories, args.run_id)
        dim_product.writeTo("lakehouse.gold.dim_product").overwrite(F.lit(True))

        print(f"[{args.run_id}] Building dim_variant...")
        dim_variant = build_dim_variant(silver_product_variants, silver_products, args.run_id)
        dim_variant.writeTo("lakehouse.gold.dim_variant").overwrite(F.lit(True))

        print(f"[{args.run_id}] Building dim_store...")
        dim_store = build_dim_store(silver_stores, silver_cities, args.run_id)
        dim_store.writeTo("lakehouse.gold.dim_store").overwrite(F.lit(True))

        print(f"[{args.run_id}] Building dim_delivery_staff...")
        dim_delivery_staff = build_dim_delivery_staff(silver_delivery_staff, silver_cities, args.run_id)
        dim_delivery_staff.writeTo("lakehouse.gold.dim_delivery_staff").overwrite(F.lit(True))

        print(f"[{args.run_id}] Building dim_customer...")
        dim_customer = build_dim_customer(silver_customers, silver_cities, args.run_id)
        dim_customer.writeTo("lakehouse.gold.dim_customer").overwrite(F.lit(True))

        # 3. Build and persist Facts
        print(f"[{args.run_id}] Building fact_order...")
        fact_order = build_fact_order(silver_orders, silver_order_items, args.run_id, silver_product_variants)
        fact_order.writeTo("lakehouse.gold.fact_order").overwritePartitions()

        print(f"[{args.run_id}] Building fact_order_item...")
        fact_order_item = build_fact_order_item(
            silver_order_items, silver_orders, args.run_id, silver_product_variants
        )
        fact_order_item.writeTo("lakehouse.gold.fact_order_item").overwrite(F.lit(True))

        print(f"[{args.run_id}] Building fact_shipment...")
        fact_shipment = build_fact_shipment(silver_shipments, args.run_id)
        fact_shipment.writeTo("lakehouse.gold.fact_shipment").overwritePartitions()

        print(f"[{args.run_id}] Building fact_return_exchange...")
        fact_return_exchange = build_fact_return_exchange(silver_return_requests, silver_return_items, args.run_id)
        fact_return_exchange.writeTo("lakehouse.gold.fact_return_exchange").overwritePartitions()

        print(f"[{args.run_id}] Building fact_inventory_daily_snapshot...")
        fact_inventory_daily_snapshot = build_fact_inventory_daily_snapshot(
            silver_inventory, silver_store_inventory, silver_product_variants, args.snapshot_date, args.run_id
        )
        fact_inventory_daily_snapshot.writeTo("lakehouse.gold.fact_inventory_daily_snapshot").overwritePartitions()

        # 4. Build and persist Data Marts
        print(f"[{args.run_id}] Building mart_sales_daily...")
        mart_sales_daily = build_mart_sales_daily(fact_order, fact_order_item, dim_product, args.run_id)
        mart_sales_daily.writeTo("lakehouse.gold.mart_sales_daily").overwritePartitions()

        print(f"[{args.run_id}] Building mart_logistics_performance...")
        mart_logistics_performance = build_mart_logistics_performance(fact_shipment, dim_delivery_staff, args.run_id)
        mart_logistics_performance.writeTo("lakehouse.gold.mart_logistics_performance").overwritePartitions()

        print(f"[{args.run_id}] Building mart_product_returns...")
        mart_product_returns = build_mart_product_returns(fact_return_exchange, dim_variant, args.run_id)
        mart_product_returns.writeTo("lakehouse.gold.mart_product_returns").overwritePartitions()

        print(f"[{args.run_id}] Building mart_inventory_health...")
        mart_inventory_health = build_mart_inventory_health(fact_inventory_daily_snapshot, dim_product, args.run_id)
        mart_inventory_health.writeTo("lakehouse.gold.mart_inventory_health").overwritePartitions()

        print(f"[{args.run_id}] All OLTP Gold tables and Marts successfully built!")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
