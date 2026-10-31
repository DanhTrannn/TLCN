CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_payments (
    payment_id                      BIGINT,
    payment_reference               STRING,
    order_id                        BIGINT,
    payment_idempotency_key         STRING,
    status                          STRING,
    currency_code                   STRING,
    amount_vnd                      BIGINT,
    failure_code                    STRING,
    attempted_at                    TIMESTAMP,
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
