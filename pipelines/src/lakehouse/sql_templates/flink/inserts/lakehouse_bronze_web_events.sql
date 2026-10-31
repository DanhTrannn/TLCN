INSERT INTO lakehouse.bronze.web_events
        SELECT
            event_id as event_id,
            CAST(event_ts AS TIMESTAMP_LTZ(6)) as event_ts,
            CAST(observed_timestamp AS TIMESTAMP_LTZ(6)) as observed_timestamp,
            ROW(schema_name, schema_version) as `schema`,
            ROW(service_name, service_version, service_env, service_instance_id) as service,
            severity_number as severity_number,
            severity_text as severity_text,
            CASE WHEN trace_id = '' THEN CAST(NULL AS STRING) ELSE trace_id END as trace_id,
            CASE WHEN span_id = '' THEN CAST(NULL AS STRING) ELSE span_id END as span_id,
            ROW(event_name, event_category, event_kind, event_outcome, duration_ns) as `event`,
            ROW(http_method, http_route, http_status) as http,
            ROW(event_id) as request,
            ROW(actor_type, CASE WHEN actor_key = '' THEN CAST(NULL AS STRING) ELSE actor_key END) as actor,
            ROW(client_user_agent) as client,
            ROW(
                action,
                CASE WHEN product_key = '' THEN CAST(NULL AS STRING) ELSE product_key END,
                CASE WHEN variant_key = '' THEN CAST(NULL AS STRING) ELSE variant_key END,
                CASE WHEN search_query = '' THEN CAST(NULL AS STRING) ELSE search_query END,
                search_redacted,
                CAST(NULL AS MAP<STRING, STRING>)
            ) as ecommerce,
            ROW(
                CASE WHEN error_code = '' THEN CAST(NULL AS STRING) ELSE error_code END,
                CASE WHEN error_type = '' THEN CAST(NULL AS STRING) ELSE error_type END
            ) as error,
            data_origin as data_origin,
            'flink-streaming-job' as _run_id,
            'ecommerce-api-access-log' as _source_system,
            'kafka://ecommerce.access_logs' as _source_file,
            CAST(ingest_ts AS TIMESTAMP_LTZ(6)) as _ingested_at
        FROM raw_events_view
