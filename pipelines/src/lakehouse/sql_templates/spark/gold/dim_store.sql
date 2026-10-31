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
