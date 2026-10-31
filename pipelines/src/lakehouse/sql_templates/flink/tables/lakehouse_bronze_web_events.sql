CREATE TABLE IF NOT EXISTS lakehouse.bronze.web_events (
    event_id STRING,
    event_ts TIMESTAMP_LTZ(6),
    observed_timestamp TIMESTAMP_LTZ(6),
    `schema` ROW<`name` STRING, `version` STRING>,
    service ROW<`name` STRING, `version` STRING, `environment` STRING, `instance_id` STRING>,
    severity_number INT,
    severity_text STRING,
    trace_id STRING,
    span_id STRING,
    `event` ROW<`name` STRING, `category` STRING, `kind` STRING, `outcome` STRING, `duration_ns` BIGINT>,
    http ROW<`request_method` STRING, `route` STRING, `status_code` INT>,
    request ROW<`id` STRING>,
    actor ROW<`type` STRING, `key` STRING>,
    client ROW<`user_agent` STRING>,
    ecommerce ROW<`action` STRING, `product_key` STRING, `variant_key` STRING, `search_query` STRING, `search_redacted` BOOLEAN, `filters` MAP<STRING, STRING>>,
    error ROW<`code` STRING, `type` STRING>,
    data_origin STRING,
    _run_id STRING,
    _source_system STRING,
    _source_file STRING,
    _ingested_at TIMESTAMP_LTZ(6)
) WITH (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
