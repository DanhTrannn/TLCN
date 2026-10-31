CREATE TABLE IF NOT EXISTS {{fact_web_events_table}} (
    event_id                STRING                          COMMENT 'Unique event identifier',
    event_ts                TIMESTAMP                       COMMENT 'Event generation timestamp in UTC',
    event_date              DATE                            COMMENT 'Partition date derived from event_ts',
    actor_key               STRING                          COMMENT 'Identifier for actor (customer_id or anonymous token)',
    actor_type              STRING                          COMMENT 'Actor classification (customer, anonymous, admin)',
    http_request_method     STRING                          COMMENT 'HTTP verb (GET, POST, etc.)',
    http_route              STRING                          COMMENT 'Normalized endpoint route',
    http_status_code        INT                             COMMENT 'HTTP response status code',
    ecommerce_action        STRING                          COMMENT 'High-level business action',
    product_key             STRING                          COMMENT 'Product master key',
    variant_key             STRING                          COMMENT 'Product variant key',
    duration_ms             DOUBLE                          COMMENT 'Request execution duration in milliseconds',
    is_success              BOOLEAN                         COMMENT 'True if HTTP status is 2xx/3xx',
    is_client_error         BOOLEAN                         COMMENT 'True if HTTP status is 4xx',
    is_server_error         BOOLEAN                         COMMENT 'True if HTTP status is 5xx',
    is_slow_request         BOOLEAN                         COMMENT 'True if duration_ms >= 1000ms',
    _gold_ingested_at       TIMESTAMP                       COMMENT 'UTC timestamp when record was written to Gold',
    _source_run_id          STRING                          COMMENT 'Airflow/Spark execution batch run ID'
)
USING iceberg
PARTITIONED BY (days(event_ts))
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
