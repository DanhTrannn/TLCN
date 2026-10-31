INSERT INTO lakehouse.landing.access_logs
        SELECT
            event_id  as event_id,
            CAST(event_ts AS TIMESTAMP(6)) as event_ts,
            CAST(ingest_ts AS TIMESTAMP(6)) as ingest_ts,
            service_name  as service_name,
            http_method as http_method,
            http_route as http_route,
            http_status as http_status_code,
            duration_ns as duration_ns,
            actor_type as actor_type,
            action as ecommerce_action,
            raw_payload as raw_payload
        FROM raw_events_view
