CREATE TABLE IF NOT EXISTS lakehouse.gold.fact_web_events (
    event_id STRING,
    event_ts TIMESTAMP_LTZ(6),
    event_date DATE,
    actor_key STRING,
    actor_type STRING,
    http_request_method STRING,
    http_route STRING,
    http_status_code INT,
    ecommerce_action STRING,
    product_key STRING,
    variant_key STRING,
    duration_ms DOUBLE,
    is_success BOOLEAN,
    is_client_error BOOLEAN,
    is_server_error BOOLEAN,
    is_slow_request BOOLEAN,
    _gold_ingested_at TIMESTAMP_LTZ(6),
    _source_run_id STRING,
    PRIMARY KEY (event_id) NOT ENFORCED
) WITH (
    'format-version' = '2',
    'write.upsert.enabled' = 'true',
    'write.parquet.compression-codec' = 'zstd'
)
