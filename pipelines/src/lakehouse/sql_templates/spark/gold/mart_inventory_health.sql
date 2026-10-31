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
    'write.parquet.compression-codec' = 'zstd',
    'write.target-file-size-bytes' = '134217728',
    'history.expire.max-snapshot-age-ms' = '259200000',
    'history.expire.min-snapshots-to-keep' = '10'
)
