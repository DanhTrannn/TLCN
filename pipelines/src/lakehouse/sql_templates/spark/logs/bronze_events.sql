CREATE TABLE IF NOT EXISTS {{bronze_events_table}} (
    event_id            STRING                          COMMENT 'Unique event identifier mapped from request.id',
    event_ts            TIMESTAMP                       COMMENT 'Event generation timestamp in UTC',
    observed_timestamp  TIMESTAMP                       COMMENT 'Timestamp when event was recorded by container',
    schema              STRUCT<name: STRING, version: STRING>,
    service             STRUCT<name: STRING, version: STRING, environment: STRING, instance_id: STRING>,
    severity_number     INT,
    severity_text       STRING,
    trace_id            STRING,
    span_id             STRING,
    event               STRUCT<name: STRING, category: STRING, kind: STRING, outcome: STRING, duration_ns: BIGINT>,
    http                STRUCT<request_method: STRING, route: STRING, status_code: INT>,
    request             STRUCT<id: STRING>,
    actor               STRUCT<type: STRING, key: STRING>,
    client              STRUCT<user_agent: STRING>,
    ecommerce           STRUCT<action: STRING, product_key: STRING, variant_key: STRING, search_query: STRING, search_redacted: BOOLEAN, filters: MAP<STRING, STRING>>,
    error               STRUCT<code: STRING, type: STRING>,
    data_origin         STRING,
    _run_id             STRING                          COMMENT 'Airflow/Spark batch execution run ID',
    _source_system      STRING                          COMMENT 'Source system identifier',
    _source_file        STRING                          COMMENT 'Source .jsonl.gz S3 URI',
    _ingested_at        TIMESTAMP                       COMMENT 'UTC timestamp when record was committed to Bronze'
)
USING iceberg
PARTITIONED BY (days(event_ts))
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
