CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_inventory_transactions (
    transaction_id                  BIGINT,
    public_id                       BINARY,
    variant_id                      BIGINT,
    location_type                   STRING,
    store_id                        BIGINT,
    movement_type                   STRING,
    quantity_delta                  INT,
    reference_code                  STRING,
    notes                           STRING,
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
