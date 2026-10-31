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
    'write.parquet.compression-codec' = 'zstd',
    'write.target-file-size-bytes' = '134217728',
    'history.expire.max-snapshot-age-ms' = '259200000',
    'history.expire.min-snapshots-to-keep' = '10'
)
