CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_stores (
    store_id                        BIGINT,
    city_id                         BIGINT,
    code                            STRING,
    name                            STRING,
    address                         STRING,
    phone                           STRING,
    is_active                       BOOLEAN,
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
