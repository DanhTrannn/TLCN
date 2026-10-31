CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_return_items (
    return_item_id                  BIGINT,
    public_id                       BINARY,
    return_id                       BIGINT,
    order_item_id                   BIGINT,
    variant_id                      BIGINT,
    quantity                        INT,
    exchange_variant_id             BIGINT,
    refund_amount_vnd               BIGINT,
    inspection_status               STRING,
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
