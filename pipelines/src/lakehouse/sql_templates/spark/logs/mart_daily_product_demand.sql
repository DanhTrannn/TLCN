CREATE TABLE IF NOT EXISTS {{mart_daily_product_demand_table}} (
    metric_date             DATE                            COMMENT 'Metric observation date',
    product_key             STRING                          COMMENT 'Product master key',
    detail_view_count       BIGINT                          COMMENT 'Product detail page view count',
    cart_add_count          BIGINT                          COMMENT 'Add to cart interaction count',
    cart_remove_count       BIGINT                          COMMENT 'Remove from cart interaction count',
    wishlist_add_count      BIGINT                          COMMENT 'Add to wishlist interaction count',
    checkout_quote_count    BIGINT                          COMMENT 'Checkout quote interaction count',
    unique_visitors_count   BIGINT                          COMMENT 'Distinct actor count interacting with product',
    cart_to_view_rate_pct   DOUBLE                          COMMENT 'Conversion percentage from view to cart add',
    _gold_ingested_at       TIMESTAMP                       COMMENT 'UTC timestamp when aggregation was recorded',
    _source_run_id          STRING                          COMMENT 'Airflow/Spark execution batch run ID'
)
USING iceberg
PARTITIONED BY (metric_date)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
