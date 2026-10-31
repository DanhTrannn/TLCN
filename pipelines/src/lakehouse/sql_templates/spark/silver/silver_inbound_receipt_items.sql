CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_inbound_receipt_items (
    item_id                         BIGINT,
    public_id                       BINARY,
    receipt_id                      BIGINT,
    variant_id                      BIGINT,
    quantity                        INT,
    unit_cost_vnd                   BIGINT,
    total_cost_vnd                  BIGINT,
    previous_cost_price_vnd         BIGINT,
    new_cost_price_vnd              BIGINT,
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
