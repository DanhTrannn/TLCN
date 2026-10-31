CREATE TABLE IF NOT EXISTS lakehouse.gold.fact_shipment (
    shipment_id                     BIGINT                          COMMENT 'Shipment ID',
    shipment_code                   STRING                          COMMENT 'Tracking number',
    order_id                        BIGINT                          COMMENT 'Foreign key to order',
    staff_key                       BIGINT                          COMMENT 'Foreign key to dim_delivery_staff',
    shipment_date_key               INT                             COMMENT 'Date key YYYYMMDD',
    shipment_date                   DATE                            COMMENT 'Shipment date',
    status                          STRING                          COMMENT 'Shipment status (assigned, picked_up, delivered, failed)',
    attempt_count                   INT                             COMMENT 'Number of delivery attempts made',
    is_boom                         BOOLEAN                         COMMENT 'True if shipment marked failed (boom)',
    is_delivered                    BOOLEAN                         COMMENT 'True if successfully delivered',
    cod_amount_expected_vnd         BIGINT                          COMMENT 'COD collection target in VND',
    cod_amount_collected_vnd        BIGINT                          COMMENT 'Actual COD collected in VND',
    delivery_duration_minutes       DOUBLE                          COMMENT 'Transit duration in minutes',
    is_on_time                      BOOLEAN                         COMMENT 'True if delivered at or before estimated_delivery_at',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
PARTITIONED BY (shipment_date)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd',
    'write.target-file-size-bytes' = '134217728',
    'history.expire.max-snapshot-age-ms' = '259200000',
    'history.expire.min-snapshots-to-keep' = '10'
)
