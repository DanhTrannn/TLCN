CREATE TABLE IF NOT EXISTS lakehouse.landing.access_logs (
    event_id STRING,
    event_ts TIMESTAMP(6),
    ingest_ts TIMESTAMP(6),
    service_name STRING,
    http_method STRING,
    http_route STRING,
    http_status_code INT,
    duration_ns BIGINT,
    actor_type STRING,
    ecommerce_action STRING,
    raw_payload STRING
) WITH (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
