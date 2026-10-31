CREATE TABLE IF NOT EXISTS lakehouse.gold.dim_delivery_staff (
    staff_key                       BIGINT                          COMMENT 'Staff key (staff_id)',
    staff_id                        BIGINT                          COMMENT 'Original OLTP staff id',
    staff_code                      STRING                          COMMENT 'Internal staff code',
    full_name                       STRING                          COMMENT 'Pseudonymized staff name',
    phone                           STRING                          COMMENT 'Pseudonymized phone number',
    assigned_city_id                BIGINT                          COMMENT 'Assigned city ID',
    assigned_city_name              STRING                          COMMENT 'Assigned city name',
    vehicle_type                    STRING                          COMMENT 'Vehicle type (motorbike, van)',
    is_active                       BOOLEAN                         COMMENT 'Employment active status',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
