from __future__ import annotations

from lakehouse.sql import load_sql


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

GOLD_TABLE_DDL: dict[str, str] = {}

# ==========================================
# 1. CONFORMED DIMENSIONS
# ==========================================

GOLD_TABLE_DDL["dim_date"] = load_sql("spark/gold/dim_date.sql")

GOLD_TABLE_DDL["dim_product"] = load_sql("spark/gold/dim_product.sql")

GOLD_TABLE_DDL["dim_variant"] = load_sql("spark/gold/dim_variant.sql")

GOLD_TABLE_DDL["dim_store"] = load_sql("spark/gold/dim_store.sql")

GOLD_TABLE_DDL["dim_delivery_staff"] = load_sql("spark/gold/dim_delivery_staff.sql")

GOLD_TABLE_DDL["dim_customer"] = load_sql("spark/gold/dim_customer.sql")

# ==========================================
# 2. CORE FACTS
# ==========================================

GOLD_TABLE_DDL["fact_order"] = load_sql("spark/gold/fact_order.sql")

GOLD_TABLE_DDL["fact_order_item"] = load_sql("spark/gold/fact_order_item.sql")

GOLD_TABLE_DDL["fact_shipment"] = load_sql("spark/gold/fact_shipment.sql")

GOLD_TABLE_DDL["fact_return_exchange"] = load_sql("spark/gold/fact_return_exchange.sql")

GOLD_TABLE_DDL["fact_inventory_daily_snapshot"] = load_sql("spark/gold/fact_inventory_daily_snapshot.sql")

# ==========================================
# 3. DATA MARTS
# ==========================================

GOLD_TABLE_DDL["mart_sales_daily"] = load_sql("spark/gold/mart_sales_daily.sql")

GOLD_TABLE_DDL["mart_logistics_performance"] = load_sql("spark/gold/mart_logistics_performance.sql")

GOLD_TABLE_DDL["mart_product_returns"] = load_sql("spark/gold/mart_product_returns.sql")

GOLD_TABLE_DDL["mart_inventory_health"] = load_sql("spark/gold/mart_inventory_health.sql")


def ensure_oltp_gold_tables(spark: SparkSession) -> None:
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.gold")
    for table_name, ddl in GOLD_TABLE_DDL.items():
        spark.sql(ddl)
        if table_name == "fact_order_item":
            columns = {field.name.lower() for field in spark.table("lakehouse.gold.fact_order_item").schema.fields}
            if "order_date" not in columns:
                raise RuntimeError(
                    "fact_order_item requires an explicit schema migration; automatic table deletion is disabled"
                )
