from __future__ import annotations

from lakehouse.sql import identifier, load_sql, render_sql


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

SILVER_QUARANTINE_TABLE = "lakehouse.quarantine.silver_oltp_violations"

SILVER_TABLE_DDL: dict[str, str] = {}


SILVER_TABLE_DDL["silver_customers"] = load_sql("spark/silver/silver_customers.sql")


SILVER_TABLE_DDL["silver_categories"] = load_sql("spark/silver/silver_categories.sql")


SILVER_TABLE_DDL["silver_products"] = load_sql("spark/silver/silver_products.sql")


SILVER_TABLE_DDL["silver_product_variants"] = load_sql("spark/silver/silver_product_variants.sql")


SILVER_TABLE_DDL["silver_carts"] = load_sql("spark/silver/silver_carts.sql")


SILVER_TABLE_DDL["silver_cart_items"] = load_sql("spark/silver/silver_cart_items.sql")


SILVER_TABLE_DDL["silver_wishlist_items"] = load_sql("spark/silver/silver_wishlist_items.sql")


SILVER_TABLE_DDL["silver_orders"] = load_sql("spark/silver/silver_orders.sql")


SILVER_TABLE_DDL["silver_order_items"] = load_sql("spark/silver/silver_order_items.sql")


SILVER_TABLE_DDL["silver_payments"] = load_sql("spark/silver/silver_payments.sql")


SILVER_TABLE_DDL["silver_order_status_history"] = load_sql("spark/silver/silver_order_status_history.sql")


SILVER_TABLE_DDL["silver_inventory"] = load_sql("spark/silver/silver_inventory.sql")


SILVER_TABLE_DDL["silver_coupons"] = load_sql("spark/silver/silver_coupons.sql")


SILVER_TABLE_DDL["silver_coupon_redemptions"] = load_sql("spark/silver/silver_coupon_redemptions.sql")


SILVER_TABLE_DDL["silver_refunds"] = load_sql("spark/silver/silver_refunds.sql")


SILVER_TABLE_DDL["silver_product_reviews"] = load_sql("spark/silver/silver_product_reviews.sql")


SILVER_TABLE_DDL["silver_cities"] = load_sql("spark/silver/silver_cities.sql")


SILVER_TABLE_DDL["silver_stores"] = load_sql("spark/silver/silver_stores.sql")


SILVER_TABLE_DDL["silver_store_inventory"] = load_sql("spark/silver/silver_store_inventory.sql")


SILVER_TABLE_DDL["silver_delivery_staff"] = load_sql("spark/silver/silver_delivery_staff.sql")


SILVER_TABLE_DDL["silver_shipments"] = load_sql("spark/silver/silver_shipments.sql")


SILVER_TABLE_DDL["silver_shipment_attempts"] = load_sql("spark/silver/silver_shipment_attempts.sql")


SILVER_TABLE_DDL["silver_return_requests"] = load_sql("spark/silver/silver_return_requests.sql")


SILVER_TABLE_DDL["silver_return_items"] = load_sql("spark/silver/silver_return_items.sql")


SILVER_TABLE_DDL["silver_inventory_transactions"] = load_sql("spark/silver/silver_inventory_transactions.sql")


SILVER_TABLE_DDL["silver_inbound_receipts"] = load_sql("spark/silver/silver_inbound_receipts.sql")


SILVER_TABLE_DDL["silver_inbound_receipt_items"] = load_sql("spark/silver/silver_inbound_receipt_items.sql")


SILVER_QUARANTINE_DDL = render_sql(
    "spark/silver/silver_quarantine.sql", silver_quarantine_table=identifier(SILVER_QUARANTINE_TABLE)
)


def ensure_silver_namespaces(spark: SparkSession) -> None:
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.silver")
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.quarantine")


def ensure_silver_tables(spark: SparkSession) -> None:
    ensure_silver_namespaces(spark)
    for ddl in SILVER_TABLE_DDL.values():
        spark.sql(ddl)
    spark.sql(SILVER_QUARANTINE_DDL)

    # Existing local environments may have created the quarantine table before
    # multi-violation reporting was introduced. Iceberg schema evolution keeps
    # the migration idempotent while preserving historical records.
    quarantine_columns = {field.name.lower() for field in spark.table(SILVER_QUARANTINE_TABLE).schema.fields}
    if "violation_types" not in quarantine_columns:
        spark.sql(
            render_sql(
                "spark/silver/add_quarantine_violation_types.sql",
                silver_quarantine_table=identifier(SILVER_QUARANTINE_TABLE),
            )
        )
