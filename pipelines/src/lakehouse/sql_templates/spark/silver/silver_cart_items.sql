CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_cart_items (
    cart_item_id                    BIGINT,
    cart_id                         BIGINT,
    variant_id                      BIGINT,
    quantity                        INT,
    is_present                      BOOLEAN,
    first_added_at                  TIMESTAMP,
    removed_at                      TIMESTAMP,
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
