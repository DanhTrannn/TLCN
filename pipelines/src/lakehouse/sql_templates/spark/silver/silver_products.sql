CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_products (
    product_id                      BIGINT,
    public_id                       BINARY,
    category_id                     BIGINT,
    slug                            STRING,
    name                            STRING,
    description                     STRING,
    image_url                       STRING,
    is_active                       BOOLEAN,
    archived_at                     TIMESTAMP,
    archived_by_customer_id         BIGINT,
    archive_reason                  STRING,
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
