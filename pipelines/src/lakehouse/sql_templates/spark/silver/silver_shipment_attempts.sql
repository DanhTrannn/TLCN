CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_shipment_attempts (
    attempt_id                      BIGINT,
    public_id                       BINARY,
    shipment_id                     BIGINT,
    attempt_number                  INT,
    delivery_staff_id               BIGINT,
    status                          STRING,
    failure_reason                  STRING,
    is_buyer_fault                  BOOLEAN,
    idempotency_key                 STRING,
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
