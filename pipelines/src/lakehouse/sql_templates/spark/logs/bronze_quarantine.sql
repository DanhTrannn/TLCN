CREATE TABLE IF NOT EXISTS {{bronze_quarantine_table}} (
    raw_corrupt_record    STRING                          COMMENT 'Raw unparseable line or malformed JSON text',
    error_message         STRING                          COMMENT 'Diagnostic error description',
    quarantine_stage      STRING                          COMMENT 'Pipeline isolation stage',
    _run_id               STRING                          COMMENT 'Batch execution run ID',
    _source_system        STRING                          COMMENT 'Source system identifier',
    _source_file          STRING                          COMMENT 'Source .jsonl.gz S3 URI containing corrupt line',
    _quarantined_at       TIMESTAMP                       COMMENT 'UTC timestamp when record was routed to quarantine'
)
USING iceberg
PARTITIONED BY (days(_quarantined_at))
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
