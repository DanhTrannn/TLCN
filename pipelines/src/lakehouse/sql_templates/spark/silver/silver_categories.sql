CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_categories (
    category_id                     BIGINT,
    public_id                       BINARY,
    parent_category_id              BIGINT,
    code                            STRING,
    slug                            STRING,
    name                            STRING,
    is_active                       BOOLEAN,
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
