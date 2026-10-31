CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_coupons (
    coupon_id                       BIGINT,
    public_id                       BINARY,
    code_normalized                 STRING,
    discount_type                   STRING,
    discount_value                  BIGINT,
    minimum_subtotal_vnd            BIGINT,
    starts_at                       TIMESTAMP,
    ends_at                         TIMESTAMP,
    is_active                       BOOLEAN,
    total_usage_limit               INT,
    per_customer_usage_limit        INT,
    archived_at                     TIMESTAMP,
    archived_by_customer_id         BIGINT,
    archive_reason                  STRING,
    used_count                      INT,
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
