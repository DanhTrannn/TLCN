CREATE TABLE IF NOT EXISTS lakehouse.gold.fact_order (
    order_id                        BIGINT                          COMMENT 'Order ID',
    order_number                    STRING                          COMMENT 'Human-friendly order reference',
    customer_key                    BIGINT                          COMMENT 'Foreign key to dim_customer',
    store_key                       BIGINT                          COMMENT 'Foreign key to dim_store (0 if online)',
    order_date_key                  INT                             COMMENT 'Date key YYYYMMDD',
    order_date                      DATE                            COMMENT 'Order placement date',
    channel                         STRING                          COMMENT 'Sales channel (online or pos)',
    status                          STRING                          COMMENT 'Final or current order status',
    payment_method                  STRING                          COMMENT 'Payment method (cod, vietqr, momo, zalopay)',
    payment_status                  STRING                          COMMENT 'Payment status (succeeded, pending, failed)',
    coupon_id                       BIGINT                          COMMENT 'Coupon ID if applied',
    subtotal_vnd                    BIGINT                          COMMENT 'Order items gross sum in VND',
    discount_vnd                    BIGINT                          COMMENT 'Discount amount in VND',
    shipping_fee_vnd                BIGINT                          COMMENT 'Shipping fee in VND',
    gross_revenue_vnd               BIGINT                          COMMENT 'Total order value (total_vnd) in VND',
    total_cost_vnd                  BIGINT                          COMMENT 'Total cost of goods sold (COGS) in VND',
    gross_profit_vnd                BIGINT                          COMMENT 'Gross profit in VND (gross_revenue - total_cost)',
    net_revenue_vnd                 BIGINT                          COMMENT 'Recognized revenue (0 if failed_delivery/returned/cancelled)',
    net_profit_vnd                  BIGINT                          COMMENT 'Recognized gross profit (0 if failed_delivery/returned/cancelled)',
    is_boom                         BOOLEAN                         COMMENT 'True if delivery failed (boom hàng)',
    is_delivered                    BOOLEAN                         COMMENT 'True if successfully delivered or completed',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
PARTITIONED BY (order_date)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd',
    'write.target-file-size-bytes' = '134217728',
    'history.expire.max-snapshot-age-ms' = '259200000',
    'history.expire.min-snapshots-to-keep' = '10'
)
