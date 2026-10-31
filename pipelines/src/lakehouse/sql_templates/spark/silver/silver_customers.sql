CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_customers (
    customer_id                     BIGINT,
    public_id                       BINARY,
    display_name_pseudonymized      STRING,
    email_pseudonymized             STRING,
    phone_pseudonymized             STRING,
    full_name_pseudonymized         STRING,
    role                            STRING,
    status                          STRING,
    city_id                         BIGINT,
    store_id                        BIGINT,
    is_cod_blocked                  BOOLEAN,
    boom_count                      INT,
    data_origin                     STRING,
    generation_run_id               STRING,
    anonymized_at                   TIMESTAMP,
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
