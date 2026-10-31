CREATE TABLE IF NOT EXISTS {{quality_results_table}} (
    check_id                       STRING,
    run_id                         STRING,
    batch_date                     DATE,
    phase                          STRING,
    check_name                     STRING,
    dataset                        STRING,
    severity                       STRING,
    observed_value                 STRING,
    expected_value                 STRING,
    variance_percent               DOUBLE,
    failed_rows                    BIGINT,
    status                         STRING,
    details                        STRING,
    checked_at                     TIMESTAMP
)
USING iceberg
PARTITIONED BY (days(checked_at))
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
