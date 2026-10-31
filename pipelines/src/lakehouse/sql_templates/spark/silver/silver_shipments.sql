CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_shipments (
    shipment_id                     BIGINT,
    public_id                       BINARY,
    shipment_code                   STRING,
    order_id                        BIGINT,
    delivery_staff_id               BIGINT,
    status                          STRING,
    attempt_count                   INT,
    cod_amount_vnd                  BIGINT,
    cod_collected_vnd               BIGINT,
    dispatched_at                   TIMESTAMP,
    delivered_at                    TIMESTAMP,
    failed_at                       TIMESTAMP,
    failure_reason                  STRING,
    notes                           STRING,
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
