from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

GOLD_TABLE_DDL: dict[str, str] = {}

# ==========================================
# 1. CONFORMED DIMENSIONS
# ==========================================

GOLD_TABLE_DDL["dim_date"] = """
CREATE TABLE IF NOT EXISTS lakehouse.gold.dim_date (
    date_key                        INT                             COMMENT 'Date surrogate key YYYYMMDD',
    full_date                       DATE                            COMMENT 'Standard calendar date',
    day_of_week                     INT                             COMMENT 'Day of week (1=Sunday, 7=Saturday)',
    day_name                        STRING                          COMMENT 'Day name (Monday, etc.)',
    day_of_month                    INT                             COMMENT 'Day of month (1-31)',
    day_of_year                     INT                             COMMENT 'Day of year (1-366)',
    week_of_year                    INT                             COMMENT 'ISO week of year (1-53)',
    month                           INT                             COMMENT 'Month number (1-12)',
    month_name                      STRING                          COMMENT 'Month name (January, etc.)',
    quarter                         INT                             COMMENT 'Quarter of year (1-4)',
    year                            INT                             COMMENT 'Calendar year',
    is_weekend                      BOOLEAN                         COMMENT 'True if Saturday or Sunday',
    is_holiday                      BOOLEAN                         COMMENT 'True if recognized public holiday',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold'
)
USING iceberg
PARTITIONED BY (year)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

GOLD_TABLE_DDL["dim_product"] = """
CREATE TABLE IF NOT EXISTS lakehouse.gold.dim_product (
    product_key                     BIGINT                          COMMENT 'Product key (product_id)',
    product_id                      BIGINT                          COMMENT 'Original OLTP product id',
    product_name                    STRING                          COMMENT 'Product display name',
    slug                            STRING                          COMMENT 'URL friendly slug',
    category_id                     BIGINT                          COMMENT 'Category id',
    category_name                   STRING                          COMMENT 'Category display name',
    base_price_vnd                  BIGINT                          COMMENT 'Base listed price in VND',
    is_active                       BOOLEAN                         COMMENT 'Product active status',
    created_at                      TIMESTAMP                       COMMENT 'Product creation timestamp',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

GOLD_TABLE_DDL["dim_variant"] = """
CREATE TABLE IF NOT EXISTS lakehouse.gold.dim_variant (
    variant_key                     BIGINT                          COMMENT 'Variant key (variant_id)',
    variant_id                      BIGINT                          COMMENT 'Original OLTP variant id',
    product_id                      BIGINT                          COMMENT 'Foreign key to product',
    product_name                    STRING                          COMMENT 'Product display name',
    sku                             STRING                          COMMENT 'Stock keeping unit code',
    color                           STRING                          COMMENT 'Variant color',
    size                            STRING                          COMMENT 'Variant size (S/M/L/XL)',
    price_vnd                       BIGINT                          COMMENT 'Variant selling price in VND',
    cost_price_vnd                  BIGINT                          COMMENT 'Cost price / COGS in VND',
    margin_pct                      DOUBLE                          COMMENT 'Gross margin percentage ((price - cost)/price * 100)',
    is_active                       BOOLEAN                         COMMENT 'Variant active status',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

GOLD_TABLE_DDL["dim_store"] = """
CREATE TABLE IF NOT EXISTS lakehouse.gold.dim_store (
    store_key                       BIGINT                          COMMENT 'Store key (store_id)',
    store_id                        BIGINT                          COMMENT 'Original OLTP store id',
    store_code                      STRING                          COMMENT 'Store unique code',
    store_name                      STRING                          COMMENT 'Store display name',
    city_id                         BIGINT                          COMMENT 'City ID',
    city_name                       STRING                          COMMENT 'City name',
    address                         STRING                          COMMENT 'Street address',
    phone                           STRING                          COMMENT 'Store hotline',
    is_active                       BOOLEAN                         COMMENT 'Store active status',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

GOLD_TABLE_DDL["dim_delivery_staff"] = """
CREATE TABLE IF NOT EXISTS lakehouse.gold.dim_delivery_staff (
    staff_key                       BIGINT                          COMMENT 'Staff key (staff_id)',
    staff_id                        BIGINT                          COMMENT 'Original OLTP staff id',
    staff_code                      STRING                          COMMENT 'Internal staff code',
    full_name                       STRING                          COMMENT 'Pseudonymized staff name',
    phone                           STRING                          COMMENT 'Pseudonymized phone number',
    assigned_city_id                BIGINT                          COMMENT 'Assigned city ID',
    assigned_city_name              STRING                          COMMENT 'Assigned city name',
    vehicle_type                    STRING                          COMMENT 'Vehicle type (motorbike, van)',
    is_active                       BOOLEAN                         COMMENT 'Employment active status',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

GOLD_TABLE_DDL["dim_customer"] = """
CREATE TABLE IF NOT EXISTS lakehouse.gold.dim_customer (
    customer_key                    BIGINT                          COMMENT 'Customer key (customer_id)',
    customer_id                     BIGINT                          COMMENT 'Original OLTP customer id',
    email                           STRING                          COMMENT 'Pseudonymized email address',
    phone                           STRING                          COMMENT 'Pseudonymized phone number',
    full_name                       STRING                          COMMENT 'Pseudonymized customer full name',
    role                            STRING                          COMMENT 'Account role (customer, admin, etc.)',
    status                          STRING                          COMMENT 'Account status (active, suspended)',
    city_id                         BIGINT                          COMMENT 'Registered city id',
    city_name                       STRING                          COMMENT 'Registered city name',
    store_id                        BIGINT                          COMMENT 'Preferred/registered store id',
    is_cod_blocked                  BOOLEAN                         COMMENT 'True if COD payment is blocked due to excessive booms',
    boom_count                      INT                             COMMENT 'Total count of failed COD deliveries',
    created_at                      TIMESTAMP                       COMMENT 'Registration timestamp',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

# ==========================================
# 2. CORE FACTS
# ==========================================

GOLD_TABLE_DDL["fact_order"] = """
CREATE TABLE IF NOT EXISTS lakehouse.gold.fact_order (
    order_id                        BIGINT                          COMMENT 'Order ID',
    order_number                    STRING                          COMMENT 'Human-friendly order reference',
    customer_key                    BIGINT                          COMMENT 'Foreign key to dim_customer',
    store_key                       BIGINT                          COMMENT 'Foreign key to dim_store (0 if online)',
    order_date_key                  INT                             COMMENT 'Date key YYYYMMDD',
    order_date                      DATE                            COMMENT 'Order placement date',
    channel                         STRING                          COMMENT 'Sales channel (online or pos)',
    status                          STRING                          COMMENT 'Final or current order status',
    payment_method                  STRING                          COMMENT 'Payment method (cod, vietqr, momo, zalopay)',
    payment_status                  STRING                          COMMENT 'Payment status (succeeded, pending, failed)',
    coupon_id                       BIGINT                          COMMENT 'Coupon ID if applied',
    subtotal_vnd                    BIGINT                          COMMENT 'Order items gross sum in VND',
    discount_vnd                    BIGINT                          COMMENT 'Discount amount in VND',
    shipping_fee_vnd                BIGINT                          COMMENT 'Shipping fee in VND',
    gross_revenue_vnd               BIGINT                          COMMENT 'Total order value (total_vnd) in VND',
    total_cost_vnd                  BIGINT                          COMMENT 'Total cost of goods sold (COGS) in VND',
    gross_profit_vnd                BIGINT                          COMMENT 'Gross profit in VND (gross_revenue - total_cost)',
    net_revenue_vnd                 BIGINT                          COMMENT 'Recognized revenue (0 if failed_delivery/returned/cancelled)',
    net_profit_vnd                  BIGINT                          COMMENT 'Recognized gross profit (0 if failed_delivery/returned/cancelled)',
    is_boom                         BOOLEAN                         COMMENT 'True if delivery failed (boom hàng)',
    is_delivered                    BOOLEAN                         COMMENT 'True if successfully delivered or completed',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
PARTITIONED BY (order_date)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

GOLD_TABLE_DDL["fact_order_item"] = """
CREATE TABLE IF NOT EXISTS lakehouse.gold.fact_order_item (
    order_item_id                   BIGINT                          COMMENT 'Order item ID',
    order_id                        BIGINT                          COMMENT 'Foreign key to order',
    order_date_key                  INT                             COMMENT 'Date key YYYYMMDD',
    customer_key                    BIGINT                          COMMENT 'Foreign key to dim_customer',
    product_key                     BIGINT                          COMMENT 'Foreign key to dim_product',
    variant_key                     BIGINT                          COMMENT 'Foreign key to dim_variant',
    store_key                       BIGINT                          COMMENT 'Foreign key to dim_store (0 if online)',
    channel                         STRING                          COMMENT 'Sales channel (online or pos)',
    order_status                    STRING                          COMMENT 'Order status at snapshot',
    quantity                        INT                             COMMENT 'Quantity sold',
    unit_price_vnd                  BIGINT                          COMMENT 'Sale unit price in VND',
    unit_cost_vnd                   BIGINT                          COMMENT 'Unit cost price (COGS) in VND',
    item_total_vnd                  BIGINT                          COMMENT 'Line revenue (quantity * unit_price) in VND',
    item_cost_vnd                   BIGINT                          COMMENT 'Line cost (quantity * unit_cost) in VND',
    item_profit_vnd                 BIGINT                          COMMENT 'Line profit (item_total - item_cost) in VND',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

GOLD_TABLE_DDL["fact_shipment"] = """
CREATE TABLE IF NOT EXISTS lakehouse.gold.fact_shipment (
    shipment_id                     BIGINT                          COMMENT 'Shipment ID',
    shipment_code                   STRING                          COMMENT 'Tracking number',
    order_id                        BIGINT                          COMMENT 'Foreign key to order',
    staff_key                       BIGINT                          COMMENT 'Foreign key to dim_delivery_staff',
    shipment_date_key               INT                             COMMENT 'Date key YYYYMMDD',
    shipment_date                   DATE                            COMMENT 'Shipment date',
    status                          STRING                          COMMENT 'Shipment status (assigned, picked_up, delivered, failed)',
    attempt_count                   INT                             COMMENT 'Number of delivery attempts made',
    is_boom                         BOOLEAN                         COMMENT 'True if shipment marked failed (boom)',
    is_delivered                    BOOLEAN                         COMMENT 'True if successfully delivered',
    cod_amount_expected_vnd         BIGINT                          COMMENT 'COD collection target in VND',
    cod_amount_collected_vnd        BIGINT                          COMMENT 'Actual COD collected in VND',
    delivery_duration_minutes       DOUBLE                          COMMENT 'Transit duration in minutes',
    is_on_time                      BOOLEAN                         COMMENT 'True if delivered at or before estimated_delivery_at',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
PARTITIONED BY (shipment_date)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

GOLD_TABLE_DDL["fact_return_exchange"] = """
CREATE TABLE IF NOT EXISTS lakehouse.gold.fact_return_exchange (
    return_item_id                  BIGINT                          COMMENT 'Return item ID',
    return_id                       BIGINT                          COMMENT 'Foreign key to return request',
    return_number                   STRING                          COMMENT 'Return request tracking code',
    order_id                        BIGINT                          COMMENT 'Foreign key to order',
    order_item_id                   BIGINT                          COMMENT 'Foreign key to original order item',
    return_date_key                 INT                             COMMENT 'Date key YYYYMMDD',
    return_date                     DATE                            COMMENT 'Return creation date',
    action_type                     STRING                          COMMENT 'Return action (exchange or refund)',
    return_status                   STRING                          COMMENT 'Return status (requested, approved, received, completed, rejected)',
    reason                          STRING                          COMMENT 'Customer return reason',
    returned_variant_key            BIGINT                          COMMENT 'Foreign key to dim_variant being returned',
    exchanged_variant_key           BIGINT                          COMMENT 'Foreign key to new dim_variant if exchange',
    returned_quantity               INT                             COMMENT 'Quantity returned',
    refund_amount_vnd               BIGINT                          COMMENT 'Total refund amount in VND (0 if exchange)',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
PARTITIONED BY (return_date)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

GOLD_TABLE_DDL["fact_inventory_daily_snapshot"] = """
CREATE TABLE IF NOT EXISTS lakehouse.gold.fact_inventory_daily_snapshot (
    snapshot_date_key               INT                             COMMENT 'Date key YYYYMMDD',
    snapshot_date                   DATE                            COMMENT 'Snapshot observation date',
    location_type                   STRING                          COMMENT 'Location classification (warehouse or store)',
    location_id                     BIGINT                          COMMENT 'Warehouse (0) or store_id',
    variant_key                     BIGINT                          COMMENT 'Foreign key to dim_variant',
    product_key                     BIGINT                          COMMENT 'Foreign key to dim_product',
    on_hand_quantity                INT                             COMMENT 'Units physically in stock',
    reserved_quantity               INT                             COMMENT 'Units reserved for pending orders',
    unit_cost_vnd                   BIGINT                          COMMENT 'COGS unit price in VND',
    inventory_value_cost_vnd        BIGINT                          COMMENT 'Stock valuation at cost (on_hand * unit_cost)',
    is_low_stock                    BOOLEAN                         COMMENT 'True if on_hand < 10 units',
    is_out_of_stock                 BOOLEAN                         COMMENT 'True if on_hand == 0',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
PARTITIONED BY (snapshot_date)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

# ==========================================
# 3. DATA MARTS
# ==========================================

GOLD_TABLE_DDL["mart_sales_daily"] = """
CREATE TABLE IF NOT EXISTS lakehouse.gold.mart_sales_daily (
    order_date                      DATE                            COMMENT 'Sales observation date',
    channel                         STRING                          COMMENT 'Channel (online or pos)',
    store_key                       BIGINT                          COMMENT 'Store key (0 if online)',
    category_id                     BIGINT                          COMMENT 'Product category ID',
    category_name                   STRING                          COMMENT 'Product category name',
    total_orders                    BIGINT                          COMMENT 'Total distinct orders placed',
    successful_orders               BIGINT                          COMMENT 'Distinct delivered/completed orders',
    boom_orders                     BIGINT                          COMMENT 'Distinct failed delivery (boom) orders',
    items_sold                      BIGINT                          COMMENT 'Total units delivered to customers',
    gross_revenue_vnd               BIGINT                          COMMENT 'Gross revenue of delivered units in VND',
    cogs_vnd                        BIGINT                          COMMENT 'Cost of goods sold of delivered units in VND',
    gross_profit_vnd                BIGINT                          COMMENT 'Gross profit in VND (gross_revenue - cogs)',
    gross_profit_margin_pct         DOUBLE                          COMMENT 'Gross profit percentage',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
PARTITIONED BY (order_date)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

GOLD_TABLE_DDL["mart_logistics_performance"] = """
CREATE TABLE IF NOT EXISTS lakehouse.gold.mart_logistics_performance (
    shipment_date                   DATE                            COMMENT 'Shipment date',
    staff_key                       BIGINT                          COMMENT 'Delivery staff key',
    staff_code                      STRING                          COMMENT 'Delivery staff code',
    assigned_city_id                BIGINT                          COMMENT 'City assigned to shipper',
    assigned_city_name              STRING                          COMMENT 'City name',
    total_shipments                 BIGINT                          COMMENT 'Total shipments handled',
    delivered_count                 BIGINT                          COMMENT 'Successfully delivered shipments count',
    boom_count                      BIGINT                          COMMENT 'Boom / failed delivery shipments count',
    boom_rate_pct                   DOUBLE                          COMMENT 'Boom rate percentage (boom_count / total * 100)',
    on_time_count                   BIGINT                          COMMENT 'Delivered on or before estimated time',
    on_time_rate_pct                DOUBLE                          COMMENT 'On-time delivery percentage',
    avg_duration_minutes            DOUBLE                          COMMENT 'Average transit duration in minutes',
    total_cod_collected_vnd         BIGINT                          COMMENT 'Total COD cash collected in VND',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
PARTITIONED BY (shipment_date)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

GOLD_TABLE_DDL["mart_product_returns"] = """
CREATE TABLE IF NOT EXISTS lakehouse.gold.mart_product_returns (
    return_date                     DATE                            COMMENT 'Return date',
    returned_variant_key            BIGINT                          COMMENT 'Variant key returned',
    product_id                      BIGINT                          COMMENT 'Product ID',
    product_name                    STRING                          COMMENT 'Product name',
    sku                             STRING                          COMMENT 'Variant SKU',
    size                            STRING                          COMMENT 'Variant size (S/M/L/XL)',
    color                           STRING                          COMMENT 'Variant color',
    action_type                     STRING                          COMMENT 'Return action (exchange or refund)',
    reason                          STRING                          COMMENT 'Customer reason',
    total_return_requests           BIGINT                          COMMENT 'Number of return requests',
    total_returned_quantity         BIGINT                          COMMENT 'Total units returned',
    total_refund_amount_vnd         BIGINT                          COMMENT 'Total refund payout in VND',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
PARTITIONED BY (return_date)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

GOLD_TABLE_DDL["mart_inventory_health"] = """
CREATE TABLE IF NOT EXISTS lakehouse.gold.mart_inventory_health (
    snapshot_date                   DATE                            COMMENT 'Snapshot date',
    location_type                   STRING                          COMMENT 'Location type (warehouse or store)',
    location_id                     BIGINT                          COMMENT 'Location ID (0 or store_id)',
    category_id                     BIGINT                          COMMENT 'Product category ID',
    category_name                   STRING                          COMMENT 'Product category name',
    total_variants                  BIGINT                          COMMENT 'Total distinct variants tracked',
    out_of_stock_count              BIGINT                          COMMENT 'Count of variants with zero stock',
    low_stock_count                 BIGINT                          COMMENT 'Count of variants with on_hand < 10',
    total_on_hand_units             BIGINT                          COMMENT 'Total physical inventory units',
    total_inventory_value_vnd       BIGINT                          COMMENT 'Total inventory asset value at cost',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
PARTITIONED BY (snapshot_date)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


def ensure_oltp_gold_tables(spark: SparkSession) -> None:
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.gold")
    for table_name, ddl in GOLD_TABLE_DDL.items():
        spark.sql(ddl)
