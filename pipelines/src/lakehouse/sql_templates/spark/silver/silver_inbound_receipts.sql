CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_inbound_receipts (
    receipt_id                      BIGINT,
    public_id                       BINARY,
    receipt_code                    STRING,
    batch_name                      STRING,
    status                          STRING,
    total_items_count               INT,
    total_cost_vnd                  BIGINT,
    notes                           STRING,
    created_by_customer_id          BIGINT,
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
