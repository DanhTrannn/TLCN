INSERT INTO lakehouse.gold.fact_web_events
        SELECT
            event_id  as event_id,
            CAST(event_ts AS TIMESTAMP_LTZ(6)) as event_ts,
            CAST(event_date AS DATE) as event_date,
            CASE WHEN actor_key = '' THEN CAST(NULL AS STRING) ELSE actor_key END as actor_key,
            actor_type as actor_type,
            http_method as http_request_method,
            http_route as http_route,
            http_status as http_status_code,
            action as ecommerce_action,
            CASE WHEN product_key = '' THEN CAST(NULL AS STRING) ELSE product_key END as product_key,
            CASE WHEN variant_key = '' THEN CAST(NULL AS STRING) ELSE variant_key END as variant_key,
            duration_ms as duration_ms,
            is_success as is_success,
            is_client_error as is_client_error,
            is_server_error as is_server_error,
            is_slow_request as is_slow_request,
            CAST(ingest_ts AS TIMESTAMP_LTZ(6)) as _gold_ingested_at,
            'flink-streaming-job' as _source_run_id
        FROM raw_events_view
