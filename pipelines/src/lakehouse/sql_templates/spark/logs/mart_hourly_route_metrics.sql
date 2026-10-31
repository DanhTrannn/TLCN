CREATE TABLE IF NOT EXISTS {{mart_hourly_route_metrics_table}} (
    metric_date             DATE                            COMMENT 'Metric observation date',
    metric_hour             INT                             COMMENT 'Hour of day (0-23)',
    http_route              STRING                          COMMENT 'Normalized API endpoint route',
    http_request_method     STRING                          COMMENT 'HTTP method',
    total_requests          BIGINT                          COMMENT 'Total request count in this hourly window',
    success_2xx_count       BIGINT                          COMMENT 'Successful 2xx request count',
    client_error_4xx_count  BIGINT                          COMMENT 'Client error 4xx request count',
    server_error_5xx_count  BIGINT                          COMMENT 'Server error 5xx request count',
    error_rate_pct          DOUBLE                          COMMENT 'Overall error rate percentage ((4xx+5xx)/total * 100)',
    avg_duration_ms         DOUBLE                          COMMENT 'Average duration in milliseconds',
    p50_duration_ms         DOUBLE                          COMMENT 'Median duration in milliseconds',
    p95_duration_ms         DOUBLE                          COMMENT '95th percentile duration in milliseconds',
    p99_duration_ms         DOUBLE                          COMMENT '99th percentile duration in milliseconds',
    _gold_ingested_at       TIMESTAMP                       COMMENT 'UTC timestamp when aggregation was recorded',
    _source_run_id          STRING                          COMMENT 'Airflow/Spark execution batch run ID'
)
USING iceberg
PARTITIONED BY (metric_date)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
