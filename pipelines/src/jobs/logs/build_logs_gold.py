import argparse
import sys

from pyspark.sql import functions as F

from lakehouse.logs.gold import (
    FACT_WEB_EVENTS_TABLE,
    MART_DAILY_PRODUCT_DEMAND_TABLE,
    MART_HOURLY_ROUTE_METRICS_TABLE,
    build_mart_daily_product_demand,
    build_mart_hourly_route_metrics,
    ensure_logs_gold_tables,
)
from lakehouse.spark import spark_session


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Gold Data Marts from real-time Fact Web Events")
    parser.add_argument("--run-id", required=True, help="Airflow DAG run ID")
    parser.add_argument("--ingest-date", help="Target date (YYYY-MM-DD), default all recent dates")
    return parser.parse_args(args)


def main() -> None:
    args = parse_args(sys.argv[1:])
    spark = spark_session("build_logs_gold_marts")
    try:
        # 1. Ensure Polaris namespaces and Iceberg Gold tables exist
        ensure_logs_gold_tables(spark)

        # 2. Read streaming Fact table directly
        try:
            fact_df = spark.read.table(FACT_WEB_EVENTS_TABLE)
        except Exception as exc:
            print(f"Fact table {FACT_WEB_EVENTS_TABLE} not found: {exc}. Exiting.")
            return

        if fact_df.limit(1).count() == 0:
            print(f"Fact table {FACT_WEB_EVENTS_TABLE} is empty. No Gold marts to build.")
            return

        if args.ingest_date:
            target_facts = fact_df.filter(F.col("event_date") == args.ingest_date)
        else:
            target_facts = fact_df

        target_count = target_facts.count()
        print(f"[{args.run_id}] Building Gold Data Marts from {target_count} fact records (date={args.ingest_date})...")

        if target_count == 0:
            print("No records for target date. Skipping mart rollup.")
            return

        # 3. Build and write Hourly Route Metrics Mart
        hourly_mart_df = build_mart_hourly_route_metrics(target_facts, args.run_id)
        hourly_count = hourly_mart_df.count()
        if hourly_count > 0:
            hourly_mart_df.writeTo(MART_HOURLY_ROUTE_METRICS_TABLE).overwritePartitions()
            print(f"[{args.run_id}] Written {hourly_count} rows to {MART_HOURLY_ROUTE_METRICS_TABLE}")

        # 4. Build and write Daily Product Demand Mart
        product_demand_df = build_mart_daily_product_demand(target_facts, args.run_id)
        product_count = product_demand_df.count()
        if product_count > 0:
            product_demand_df.writeTo(MART_DAILY_PRODUCT_DEMAND_TABLE).overwritePartitions()
            print(f"[{args.run_id}] Written {product_count} rows to {MART_DAILY_PRODUCT_DEMAND_TABLE}")

        print(f"Logs Gold Marts Rollup Complete: hourly_routes={hourly_count}, product_demand={product_count}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
