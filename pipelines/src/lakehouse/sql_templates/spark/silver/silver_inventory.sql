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
