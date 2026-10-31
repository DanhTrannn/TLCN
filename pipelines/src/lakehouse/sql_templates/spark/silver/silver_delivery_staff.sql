CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_delivery_staff (
    staff_id                        BIGINT,
    public_id                       BINARY,
    full_name_pseudonymized         STRING,
    phone_pseudonymized             STRING,
    vehicle_plate                   STRING,
    is_active                       BOOLEAN,
    _pii_pseudonymized_at           TIMESTAMP,
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
