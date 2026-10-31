CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_carts (
    cart_id                         BIGINT,
    public_id                       BINARY,
    customer_id                     BIGINT,
    status                          STRING,
    last_activity_at                TIMESTAMP,
    checked_out_at                  TIMESTAMP,
    abandoned_at                    TIMESTAMP,
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
