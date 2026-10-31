CREATE TABLE IF NOT EXISTS lakehouse.bronze.oltp_cdc_events (
    event_id STRING,
    topic STRING,
    database_name STRING,
    table_name STRING,
    operation STRING,
    event_ts TIMESTAMP_LTZ(3),
    source_ts TIMESTAMP_LTZ(3),
    transaction_id STRING,
    mysql_server_id STRING,
    binlog_file STRING,
    binlog_position BIGINT,
    binlog_row INT,
    kafka_partition INT,
    kafka_offset BIGINT,
    record_key STRING,
    before_payload STRING,
    after_payload STRING,
    raw_payload STRING,
    ingested_at TIMESTAMP_LTZ(3),
    event_date DATE
) PARTITIONED BY (event_date) WITH (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
