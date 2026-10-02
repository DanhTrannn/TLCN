-- Initialize and Seed Lakehouse Gold Marts in Apache Iceberg via Polaris

CREATE NAMESPACE IF NOT EXISTS lakehouse.gold;

-- 1. mart_sales_daily
CREATE TABLE IF NOT EXISTS lakehouse.gold.mart_sales_daily (
    order_date                      DATE,
    channel                         STRING,
    store_key                       BIGINT,
    category_id                     BIGINT,
    category_name                   STRING,
    total_orders                    BIGINT,
    successful_orders               BIGINT,
    boom_orders                     BIGINT,
    items_sold                      BIGINT,
    gross_revenue_vnd               BIGINT,
    cogs_vnd                        BIGINT,
    gross_profit_vnd                BIGINT,
    gross_profit_margin_pct         DOUBLE,
    _gold_ingested_at               TIMESTAMP,
    _source_run_id                  STRING
)
USING iceberg
PARTITIONED BY (order_date);

-- 2. mart_logistics_performance
CREATE TABLE IF NOT EXISTS lakehouse.gold.mart_logistics_performance (
    shipment_date                   DATE,
    staff_key                       BIGINT,
    staff_code                      STRING,
    assigned_city_id                BIGINT,
    assigned_city_name              STRING,
    total_shipments                 BIGINT,
    delivered_count                 BIGINT,
    boom_count                      BIGINT,
    boom_rate_pct                   DOUBLE,
    on_time_count                   BIGINT,
    on_time_rate_pct                DOUBLE,
    avg_duration_minutes            DOUBLE,
    total_cod_collected_vnd         BIGINT,
    _gold_ingested_at               TIMESTAMP,
    _source_run_id                  STRING
)
USING iceberg
PARTITIONED BY (shipment_date);

-- 3. mart_inventory_health
CREATE TABLE IF NOT EXISTS lakehouse.gold.mart_inventory_health (
    snapshot_date                   DATE,
    location_type                   STRING,
    location_id                     BIGINT,
    category_id                     BIGINT,
    category_name                   STRING,
    total_variants                  BIGINT,
    out_of_stock_count              BIGINT,
    low_stock_count                 BIGINT,
    total_on_hand_units             BIGINT,
    total_inventory_value_vnd       BIGINT,
    _gold_ingested_at               TIMESTAMP,
    _source_run_id                  STRING
)
USING iceberg
PARTITIONED BY (snapshot_date);

-- 4. mart_product_returns
CREATE TABLE IF NOT EXISTS lakehouse.gold.mart_product_returns (
    return_date                     DATE,
    returned_variant_key            BIGINT,
    product_id                      BIGINT,
    product_name                    STRING,
    sku                             STRING,
    size                            STRING,
    color                           STRING,
    action_type                     STRING,
    reason                          STRING,
    total_return_requests           BIGINT,
    total_returned_quantity         BIGINT,
    total_refund_amount_vnd         BIGINT,
    _gold_ingested_at               TIMESTAMP,
    _source_run_id                  STRING
)
USING iceberg
PARTITIONED BY (return_date);

-- 5. dim_product
CREATE TABLE IF NOT EXISTS lakehouse.gold.dim_product (
    product_key                     BIGINT,
    product_id                      BIGINT,
    product_name                    STRING,
    slug                            STRING,
    category_id                     BIGINT,
    category_name                   STRING,
    base_price_vnd                  BIGINT,
    is_active                       BOOLEAN,
    created_at                      TIMESTAMP,
    _gold_ingested_at               TIMESTAMP,
    _source_run_id                  STRING
)
USING iceberg;

-- 6. fact_order_item
CREATE TABLE IF NOT EXISTS lakehouse.gold.fact_order_item (
    order_item_id                   BIGINT,
    order_id                        BIGINT,
    order_date_key                  INT,
    customer_key                    BIGINT,
    product_key                     BIGINT,
    variant_key                     BIGINT,
    store_key                       BIGINT,
    channel                         STRING,
    order_status                    STRING,
    quantity                        INT,
    unit_price_vnd                  BIGINT,
    unit_cost_vnd                   BIGINT,
    item_total_vnd                  BIGINT,
    item_cost_vnd                   BIGINT,
    item_profit_vnd                 BIGINT,
    _gold_ingested_at               TIMESTAMP,
    _source_run_id                  STRING
)
USING iceberg;

-- 7. mart_marketing_funnel_daily
CREATE TABLE IF NOT EXISTS lakehouse.gold.mart_marketing_funnel_daily (
    metric_date                     DATE,
    product_views                   BIGINT,
    cart_additions                  BIGINT,
    checkout_initiations            BIGINT,
    orders_completed                BIGINT,
    view_to_cart_rate_pct           DOUBLE,
    cart_to_checkout_rate_pct       DOUBLE,
    checkout_to_order_rate_pct      DOUBLE,
    overall_conversion_rate_pct     DOUBLE,
    unique_visitors                 BIGINT,
    _gold_ingested_at               TIMESTAMP,
    _source_run_id                  STRING
)
USING iceberg
PARTITIONED BY (metric_date);

