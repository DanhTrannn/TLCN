CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_coupon_redemptions (
    coupon_redemption_id            BIGINT,
    coupon_id                       BIGINT,
    order_id                        BIGINT,
    customer_id                     BIGINT,
    status                          STRING,
    redeemed_at                     TIMESTAMP,
    released_at                     TIMESTAMP,
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
