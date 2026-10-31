CREATE TABLE IF NOT EXISTS lakehouse.gold.fact_return_exchange (
    return_item_id                  BIGINT                          COMMENT 'Return item ID',
    return_id                       BIGINT                          COMMENT 'Foreign key to return request',
    return_number                   STRING                          COMMENT 'Return request tracking code',
    order_id                        BIGINT                          COMMENT 'Foreign key to order',
    order_item_id                   BIGINT                          COMMENT 'Foreign key to original order item',
    return_date_key                 INT                             COMMENT 'Date key YYYYMMDD',
    return_date                     DATE                            COMMENT 'Return creation date',
    action_type                     STRING                          COMMENT 'Return action (exchange or refund)',
    return_status                   STRING                          COMMENT 'Return status (requested, approved, received, completed, rejected)',
    reason                          STRING                          COMMENT 'Customer return reason',
    returned_variant_key            BIGINT                          COMMENT 'Foreign key to dim_variant being returned',
    exchanged_variant_key           BIGINT                          COMMENT 'Foreign key to new dim_variant if exchange',
    returned_quantity               INT                             COMMENT 'Quantity returned',
    refund_amount_vnd               BIGINT                          COMMENT 'Total refund amount in VND (0 if exchange)',
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
