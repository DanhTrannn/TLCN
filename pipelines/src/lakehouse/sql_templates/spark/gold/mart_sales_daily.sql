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
    'write.parquet.compression-codec' = 'zstd',
    'write.target-file-size-bytes' = '134217728',
    'history.expire.max-snapshot-age-ms' = '259200000',
    'history.expire.min-snapshots-to-keep' = '10'
)
