CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_order_status_history (
    order_status_history_id         BIGINT,
    order_id                        BIGINT,
    from_status                     STRING,
    to_status                       STRING,
    transition_source               STRING,
    reason                          STRING,
    transition_idempotency_key      STRING,
    transitioned_at                 TIMESTAMP,
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
