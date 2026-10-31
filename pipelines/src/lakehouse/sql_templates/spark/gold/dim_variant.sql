CREATE TABLE IF NOT EXISTS lakehouse.gold.dim_variant (
    variant_key                     BIGINT                          COMMENT 'Variant key (variant_id)',
    variant_id                      BIGINT                          COMMENT 'Original OLTP variant id',
    product_id                      BIGINT                          COMMENT 'Foreign key to product',
    product_name                    STRING                          COMMENT 'Product display name',
    sku                             STRING                          COMMENT 'Stock keeping unit code',
    color                           STRING                          COMMENT 'Variant color',
    size                            STRING                          COMMENT 'Variant size (S/M/L/XL)',
    price_vnd                       BIGINT                          COMMENT 'Variant selling price in VND',
    cost_price_vnd                  BIGINT                          COMMENT 'Cost price / COGS in VND',
    margin_pct                      DOUBLE                          COMMENT 'Gross margin percentage ((price - cost)/price * 100)',
    is_active                       BOOLEAN                         COMMENT 'Variant active status',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
