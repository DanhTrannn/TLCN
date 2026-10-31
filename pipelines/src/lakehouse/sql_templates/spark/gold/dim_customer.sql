CREATE TABLE IF NOT EXISTS lakehouse.gold.dim_customer (
    customer_key                    BIGINT                          COMMENT 'Customer key (customer_id)',
    customer_id                     BIGINT                          COMMENT 'Original OLTP customer id',
    email                           STRING                          COMMENT 'Pseudonymized email address',
    phone                           STRING                          COMMENT 'Pseudonymized phone number',
    full_name                       STRING                          COMMENT 'Pseudonymized customer full name',
    role                            STRING                          COMMENT 'Account role (customer, admin, etc.)',
    status                          STRING                          COMMENT 'Account status (active, suspended)',
    city_id                         BIGINT                          COMMENT 'Registered city id',
    city_name                       STRING                          COMMENT 'Registered city name',
    store_id                        BIGINT                          COMMENT 'Preferred/registered store id',
    is_cod_blocked                  BOOLEAN                         COMMENT 'True if COD payment is blocked due to excessive booms',
    boom_count                      INT                             COMMENT 'Total count of failed COD deliveries',
    created_at                      TIMESTAMP                       COMMENT 'Registration timestamp',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold',
    _source_run_id                  STRING                          COMMENT 'Batch run ID'
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
