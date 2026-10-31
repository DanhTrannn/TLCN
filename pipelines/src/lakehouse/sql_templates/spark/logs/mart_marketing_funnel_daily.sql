CREATE TABLE IF NOT EXISTS {{mart_marketing_funnel_daily_table}} (
    metric_date             DATE                            COMMENT 'Metric observation date',
    product_views           BIGINT                          COMMENT 'Product detail and browsing views count',
    cart_additions          BIGINT                          COMMENT 'Cart item additions count',
    checkout_initiations    BIGINT                          COMMENT 'Checkout initiation count',
    orders_completed        BIGINT                          COMMENT 'Orders completed count',
    view_to_cart_rate_pct   DOUBLE                          COMMENT 'Conversion percentage from view to cart',
    cart_to_checkout_rate_pct DOUBLE                        COMMENT 'Conversion percentage from cart to checkout',
    checkout_to_order_rate_pct DOUBLE                       COMMENT 'Conversion percentage from checkout to order',
    overall_conversion_rate_pct DOUBLE                      COMMENT 'Overall conversion percentage from view to order',
    unique_visitors         BIGINT                          COMMENT 'Unique actor count',
    _gold_ingested_at       TIMESTAMP                       COMMENT 'UTC timestamp when record was written to Gold',
    _source_run_id          STRING                          COMMENT 'Airflow/Spark execution batch run ID'
)
USING iceberg
PARTITIONED BY (metric_date)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
