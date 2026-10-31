CREATE TABLE IF NOT EXISTS lakehouse.gold.mart_product_returns (
    return_date                     DATE                            COMMENT 'Return date',
    returned_variant_key            BIGINT                          COMMENT 'Variant key returned',
    product_id                      BIGINT                          COMMENT 'Product ID',
    product_name                    STRING                          COMMENT 'Product name',
    sku                             STRING                          COMMENT 'Variant SKU',
    size                            STRING                          COMMENT 'Variant size (S/M/L/XL)',
    color                           STRING                          COMMENT 'Variant color',
    action_type                     STRING                          COMMENT 'Return action (exchange or refund)',
    reason                          STRING                          COMMENT 'Customer reason',
    total_return_requests           BIGINT                          COMMENT 'Number of return requests',
    total_returned_quantity         BIGINT                          COMMENT 'Total units returned',
    total_refund_amount_vnd         BIGINT                          COMMENT 'Total refund payout in VND',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
PARTITIONED BY (return_date)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd',
    'write.target-file-size-bytes' = '134217728',
    'history.expire.max-snapshot-age-ms' = '259200000',
    'history.expire.min-snapshots-to-keep' = '10'
)
