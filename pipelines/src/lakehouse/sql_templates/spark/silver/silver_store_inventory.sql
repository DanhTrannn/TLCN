CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_store_inventory (
    store_inventory_id              BIGINT,
    store_id                        BIGINT,
    variant_id                      BIGINT,
    on_hand                         BIGINT,
    opening_on_hand                 BIGINT,
    version                         BIGINT,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
