CREATE TABLE IF NOT EXISTS {{silver_quarantine_table}} (
    record_data                     STRING,
    violation_type                  STRING,
    violation_types                 ARRAY<STRING>,
    violation_detail                STRING,
    source_table                    STRING,
    _run_id                         STRING,
    _quarantined_at                 TIMESTAMP
)
USING iceberg
PARTITIONED BY (days(_quarantined_at))
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
