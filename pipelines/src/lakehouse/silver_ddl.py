from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

SILVER_QUARANTINE_TABLE = "lakehouse.quarantine.silver_oltp_violations"

SILVER_TABLE_DDL: dict[str, str] = {}


SILVER_TABLE_DDL["silver_customers"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_customers (
    customer_id                     BIGINT,
    public_id                       BINARY(16),
    email_normalized                STRING,
    email_pseudonymized             STRING,
    phone                           STRING,
    phone_pseudonymized             STRING,
    full_name                       STRING,
    full_name_pseudonymized         STRING,
    role                            STRING,
    status                          STRING,
    data_origin                     STRING,
    generation_run_id               STRING,
    _pii_pseudonymized_at           TIMESTAMP,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_categories"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_categories (
    category_id                     BIGINT,
    public_id                       BINARY(16),
    parent_category_id              BIGINT,
    code                            STRING,
    slug                            STRING,
    name                            STRING,
    is_active                       BOOLEAN,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_products"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_products (
    product_id                      BIGINT,
    public_id                       BINARY(16),
    category_id                     BIGINT,
    slug                            STRING,
    name                            STRING,
    description                     STRING,
    image_url                       STRING,
    is_active                       BOOLEAN,
    archived_at                     TIMESTAMP,
    archived_by_customer_id         BIGINT,
    archive_reason                  STRING,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_product_variants"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_product_variants (
    variant_id                      BIGINT,
    public_id                       BINARY(16),
    product_id                      BIGINT,
    sku                             STRING,
    size_code                       STRING,
    color_code                      STRING,
    price_vnd                       BIGINT,
    is_active                       BOOLEAN,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_carts"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_carts (
    cart_id                         BIGINT,
    public_id                       BINARY(16),
    customer_id                     BIGINT,
    status                          STRING,
    last_activity_at                TIMESTAMP,
    checked_out_at                  TIMESTAMP,
    abandoned_at                    TIMESTAMP,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_cart_items"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_cart_items (
    cart_item_id                    BIGINT,
    cart_id                         BIGINT,
    variant_id                      BIGINT,
    quantity                        INT,
    is_present                      BOOLEAN,
    removed_at                      TIMESTAMP,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_wishlist_items"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_wishlist_items (
    wishlist_item_id                BIGINT,
    customer_id                     BIGINT,
    product_id                      BIGINT,
    is_present                      BOOLEAN,
    added_at                        TIMESTAMP,
    removed_at                      TIMESTAMP,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_orders"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_orders (
    order_id                        BIGINT,
    order_number                    STRING,
    cart_id                         BIGINT,
    customer_id                     BIGINT,
    checkout_idempotency_key        STRING,
    currency_code                   STRING,
    subtotal_vnd                    BIGINT,
    discount_amount_vnd             BIGINT,
    shipping_fee_vnd                BIGINT,
    total_vnd                       BIGINT,
    coupon_id                       BIGINT,
    coupon_code_snapshot            STRING,
    coupon_type_snapshot            STRING,
    coupon_value_snapshot           BIGINT,
    receiver_name                   STRING,
    receiver_phone                  STRING,
    shipping_address_text           STRING,
    status                          STRING,
    paid_at                         TIMESTAMP,
    confirmed_at                    TIMESTAMP,
    completed_at                    TIMESTAMP,
    cancelled_at                    TIMESTAMP,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_order_items"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_order_items (
    order_item_id                   BIGINT,
    public_id                       BINARY(16),
    order_id                        BIGINT,
    variant_id                      BIGINT,
    product_name_snapshot           STRING,
    category_name_snapshot          STRING,
    sku_snapshot                    STRING,
    size_code_snapshot              STRING,
    color_code_snapshot             STRING,
    unit_price_vnd                  BIGINT,
    quantity                        INT,
    line_total_vnd                  BIGINT,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_payments"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_payments (
    payment_id                      BIGINT,
    payment_reference               STRING,
    order_id                        BIGINT,
    payment_idempotency_key         STRING,
    status                          STRING,
    currency_code                   STRING,
    amount_vnd                      BIGINT,
    failure_code                    STRING,
    attempted_at                    TIMESTAMP,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_order_status_history"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_order_status_history (
    order_status_history_id         BIGINT,
    order_id                        BIGINT,
    from_status                     STRING,
    to_status                       STRING,
    transition_source               STRING,
    reason                          STRING,
    transition_idempotency_key      STRING,
    transitioned_at                 TIMESTAMP,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_inventory"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_inventory (
    variant_id                      BIGINT,
    opening_on_hand                 INT,
    on_hand                         INT,
    version                         INT,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_coupons"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_coupons (
    coupon_id                       BIGINT,
    public_id                       BINARY(16),
    code_normalized                 STRING,
    discount_type                   STRING,
    discount_value                  BIGINT,
    minimum_subtotal_vnd            BIGINT,
    starts_at                       TIMESTAMP,
    ends_at                         TIMESTAMP,
    is_active                       BOOLEAN,
    total_usage_limit               INT,
    per_customer_usage_limit        INT,
    archived_at                     TIMESTAMP,
    archived_by_customer_id         BIGINT,
    archive_reason                  STRING,
    used_count                      INT,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_coupon_redemptions"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_coupon_redemptions (
    coupon_redemption_id            BIGINT,
    coupon_id                       BIGINT,
    order_id                        BIGINT,
    customer_id                     BIGINT,
    status                          STRING,
    redeemed_at                     TIMESTAMP,
    released_at                     TIMESTAMP,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_refunds"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_refunds (
    refund_id                       BIGINT,
    public_id                       BINARY(16),
    payment_id                      BIGINT,
    refund_idempotency_key          STRING,
    status                          STRING,
    currency_code                   STRING,
    amount_vnd                      BIGINT,
    reason                          STRING,
    requested_by_customer_id        BIGINT,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    completed_at                    TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_product_reviews"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_product_reviews (
    review_id                       BIGINT,
    public_id                       BINARY(16),
    order_item_id                   BIGINT,
    customer_id                     BIGINT,
    product_id                      BIGINT,
    rating                          INT,
    content                         STRING,
    status                          STRING,
    moderation_reason               STRING,
    moderated_by_customer_id        BIGINT,
    moderated_at                    TIMESTAMP,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_QUARANTINE_DDL = f"""
CREATE TABLE IF NOT EXISTS {SILVER_QUARANTINE_TABLE} (
    record_data                     STRING,
    violation_type                  STRING,
    violation_detail                STRING,
    source_table                    STRING,
    _run_id                         STRING,
    _quarantined_at                 TIMESTAMP
)
USING iceberg
PARTITIONED BY (days(_quarantined_at))
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


def ensure_silver_namespaces(spark: SparkSession) -> None:
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.silver")
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.quarantine")


def ensure_silver_tables(spark: SparkSession) -> None:
    ensure_silver_namespaces(spark)
    for ddl in SILVER_TABLE_DDL.values():
        spark.sql(ddl)
    spark.sql(SILVER_QUARANTINE_DDL)
