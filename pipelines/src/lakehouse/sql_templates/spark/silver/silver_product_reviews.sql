CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_product_reviews (
    review_id                       BIGINT,
    public_id                       BINARY,
    order_item_id                   BIGINT,
    customer_id                     BIGINT,
    product_id                      BIGINT,
    rating                          INT,
    content                         STRING,
    status                          STRING,
    moderation_reason               STRING,
    moderated_by_customer_id        BIGINT,
    moderated_at                    TIMESTAMP,
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
