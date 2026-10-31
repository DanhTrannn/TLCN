CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_refunds (
    refund_id                       BIGINT,
    public_id                       BINARY,
    payment_id                      BIGINT,
    refund_idempotency_key          STRING,
    status                          STRING,
    currency_code                   STRING,
    amount_vnd                      BIGINT,
    reason                          STRING,
    requested_by_customer_id        BIGINT,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    completed_at                    TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
