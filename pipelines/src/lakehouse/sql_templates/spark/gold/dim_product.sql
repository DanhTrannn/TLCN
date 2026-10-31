CREATE TABLE IF NOT EXISTS lakehouse.gold.dim_product (
    product_key                     BIGINT                          COMMENT 'Product key (product_id)',
    product_id                      BIGINT                          COMMENT 'Original OLTP product id',
    product_name                    STRING                          COMMENT 'Product display name',
    slug                            STRING                          COMMENT 'URL friendly slug',
    category_id                     BIGINT                          COMMENT 'Category id',
    category_name                   STRING                          COMMENT 'Category display name',
    base_price_vnd                  BIGINT                          COMMENT 'Base listed price in VND',
    is_active                       BOOLEAN                         COMMENT 'Product active status',
    created_at                      TIMESTAMP                       COMMENT 'Product creation timestamp',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
