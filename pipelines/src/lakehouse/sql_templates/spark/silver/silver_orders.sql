CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_orders (
    order_id                        BIGINT,
    order_number                    STRING,
    cart_id                         BIGINT,
    customer_id                     BIGINT,
    checkout_idempotency_key        STRING,
    currency_code                   STRING,
    subtotal_vnd                    BIGINT,
    discount_amount_vnd             BIGINT,
    shipping_fee_vnd                BIGINT,
    total_vnd                       BIGINT,
    coupon_id                       BIGINT,
    coupon_code_snapshot            STRING,
    coupon_type_snapshot            STRING,
    coupon_value_snapshot           BIGINT,
    receiver_name_pseudonymized     STRING,
    receiver_phone_pseudonymized    STRING,
    shipping_address_text_pseudonymized STRING,
    status                          STRING,
    payment_method                  STRING,
    store_id                        BIGINT,
    channel                         STRING,
    staff_id                        BIGINT,
    paid_at                         TIMESTAMP,
    confirmed_at                    TIMESTAMP,
    completed_at                    TIMESTAMP,
    cancelled_at                    TIMESTAMP,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _pii_pseudonymized_at           TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
