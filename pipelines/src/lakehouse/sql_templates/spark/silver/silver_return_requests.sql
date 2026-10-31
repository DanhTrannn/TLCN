CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_return_requests (
    return_id                       BIGINT,
    public_id                       BINARY,
    return_code                     STRING,
    order_id                        BIGINT,
    customer_id                     BIGINT,
    action_type                     STRING,
    status                          STRING,
    customer_reason                 STRING,
    image_urls                      STRING,
    admin_note                      STRING,
    reviewed_at                     TIMESTAMP,
    resolved_at                     TIMESTAMP,
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
