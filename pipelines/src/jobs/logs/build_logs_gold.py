import argparse
import sys

from lakehouse.logs.gold import (
    FACT_WEB_EVENTS_TABLE,
    MART_DAILY_PRODUCT_DEMAND_TABLE,
    MART_HOURLY_ROUTE_METRICS_TABLE,
    build_fact_web_events,
    build_mart_daily_product_demand,
    build_mart_hourly_route_metrics,
    ensure_logs_gold_tables,
)
from lakehouse.logs.silver import LOGS_SILVER_TABLE
from lakehouse.spark import spark_session


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Gold layer tables from Silver logs")
    parser.add_argument("--run-id", required=True, help="Airflow DAG run ID")
    parser.add_argument("--ingest-date", required=True, help="Target date (YYYY-MM-DD)")
    return parser.parse_args(args)


def main() -> None:
    args = parse_args(sys.argv[1:])
    spark = spark_session("build_logs_gold")
    try:
        # 1. Ensure Polaris namespaces and Iceberg Gold tables exist
        ensure_logs_gold_tables(spark)

        # 2. Read Silver logs
        try:
            silver_df = spark.read.format("iceberg").load(LOGS_SILVER_TABLE)
        except Exception:
            print(f"Silver table {LOGS_SILVER_TABLE} not found. Exiting.")
            return

        if silver_df.limit(1).count() == 0:
            print("Silver table is empty. No Gold records to build.")
            return

        # 3. Build and write Fact table
        fact_df = build_fact_web_events(silver_df, args.run_id)
        fact_count = fact_df.count()
        if fact_count == 0:
            print("No Fact records generated.")
            return

        fact_df.writeTo(FACT_WEB_EVENTS_TABLE).append()
        print(f"[{args.run_id}] Written {fact_count} rows to {FACT_WEB_EVENTS_TABLE}")

        # 4. Build and write Hourly Route Metrics Mart
        hourly_mart_df = build_mart_hourly_route_metrics(fact_df, args.run_id)
        hourly_count = hourly_mart_df.count()
        if hourly_count > 0:
            hourly_mart_df.writeTo(MART_HOURLY_ROUTE_METRICS_TABLE).overwritePartitions()
            print(f"[{args.run_id}] Written {hourly_count} rows to {MART_HOURLY_ROUTE_METRICS_TABLE}")

        # 5. Build and write Daily Product Demand Mart
        product_demand_df = build_mart_daily_product_demand(fact_df, args.run_id)
        product_count = product_demand_df.count()
        if product_count > 0:
            product_demand_df.writeTo(MART_DAILY_PRODUCT_DEMAND_TABLE).overwritePartitions()
            print(f"[{args.run_id}] Written {product_count} rows to {MART_DAILY_PRODUCT_DEMAND_TABLE}")

        print(f"Logs Gold Build Complete: facts={fact_count}, hourly_routes={hourly_count}, product_demand={product_count}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
