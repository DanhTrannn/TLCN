CREATE TABLE IF NOT EXISTS lakehouse.gold.mart_logistics_performance (
    shipment_date                   DATE                            COMMENT 'Shipment date',
    staff_key                       BIGINT                          COMMENT 'Delivery staff key',
    staff_code                      STRING                          COMMENT 'Delivery staff code',
    assigned_city_id                BIGINT                          COMMENT 'City assigned to shipper',
    assigned_city_name              STRING                          COMMENT 'City name',
    total_shipments                 BIGINT                          COMMENT 'Total shipments handled',
    delivered_count                 BIGINT                          COMMENT 'Successfully delivered shipments count',
    boom_count                      BIGINT                          COMMENT 'Boom / failed delivery shipments count',
    boom_rate_pct                   DOUBLE                          COMMENT 'Boom rate percentage (boom_count / total * 100)',
    on_time_count                   BIGINT                          COMMENT 'Delivered on or before estimated time',
    on_time_rate_pct                DOUBLE                          COMMENT 'On-time delivery percentage',
    avg_duration_minutes            DOUBLE                          COMMENT 'Average transit duration in minutes',
    total_cod_collected_vnd         BIGINT                          COMMENT 'Total COD cash collected in VND',
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
