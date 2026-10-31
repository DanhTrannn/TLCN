# Structured Access Logs

This document describes the access-event contract and the current Kafka/Flink implementation. Sources: [middleware](../../services/ecommerce-api/app/core/middleware.py), [event builder](../../services/ecommerce-api/app/core/access_logging.py), [producer](../../services/ecommerce-api/app/core/kafka_producer.py), [streaming job](../../pipelines/src/jobs/logs/kafka_to_lakehouse.py).

## 1. Capture boundary

FastAPI middleware assigns a server-generated 32-character hexadecimal request ID and returns it as `X-Request-ID`. Completed requests and handled/unhandled errors produce structured JSON events on stdout and are enqueued asynchronously to Kafka. `GET /health/live` and `GET /health/ready` are excluded. Canonical FastAPI route templates are logged; unmatched paths use `__unmatched__`.

The source is HTTP requests reaching FastAPI, not browser clicks or every Next.js page view. CORS middleware may handle requests before they reach the access middleware. Actor identity is populated by authentication dependencies on the routes that resolve a user; it is not inferred from every request automatically.

## 2. Contract

The [JSON Schema](../contracts/ecommerce-access-v1.schema.json) identifies `ecommerce.access:1.0.0`. It documents the payload shape; the current Kafka job does not run a full JSON Schema validator per event.

| Field | Current meaning |
|---|---|
| `schema.name`, `schema.version` | Contract identity/version |
| `timestamp`, `observed_timestamp` | UTC ISO timestamps for completion and event construction |
| `severity_text`, `severity_number` | INFO/9 below 400, WARN/13 for 4xx, ERROR/17 for 5xx |
| `request.id` | Server-generated request identity; not a trusted caller-supplied ID |
| `trace_id`, `span_id` | Nullable trace fields; no distributed tracing integration is implied |
| `service.*` | Configured name/version/environment; instance from HOSTNAME or service name, up to 128 characters |
| `event.*` | `http.server.request`, category web, kind event, outcome and monotonic duration in ns |
| `http.*` | Uppercase request method, canonical route and response status |
| `actor.type`, `actor.key` | Anonymous, customer, one of seven staff roles, or system; nullable user/system key |
| `client.user_agent` | Optional bounded/sanitized user agent |
| `ecommerce.action` | Action derived from method and route |
| `ecommerce.product_key`, `variant_key` | Allowlisted route identifiers when available |
| `ecommerce.search_query`, `search_redacted` | Normalized/bounded search term or redaction marker |
| `ecommerce.filters` | Allowlisted bounded catalog filters; optional |
| `error.code`, `error.type` | Safe application error metadata; nullable |
| `data_origin` | Contract allows observed/synthetic; runtime builder emits observed |

Optional commerce keys are omitted when unavailable, rather than emitted as JSON null. `actor.key`, trace/span and error values may be null. Service/environment values are configurable, not fixed to a 12-character container ID or a closed list of deployment names. The contract accepts uppercase methods, including HEAD, instead of limiting logs to business endpoint methods.

## 3. Privacy boundary

The event builder does not copy request/response bodies, raw IP, authorization/cookie headers, passwords, JWTs or internal API secrets. Commerce context uses allowlisted fields. Search text is normalized and bounded; email/phone-like values are redacted. User-agent handling removes control characters, limits length and checks PII patterns.

These rules reduce accidental disclosure; pattern sanitization does not prove that every arbitrary input string is free of PII. Actor public IDs remain identifiers. Raw OLTP/CDC privacy is a separate concern and must not be inferred from the access-log schema.

## 4. Producer and failure handling

| Variable | Default in producer |
|---|---|
| `KAFKA_ENABLED` | `true` |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` |
| `KAFKA_ACCESS_LOG_TOPIC` | `ecommerce.access_logs` |
| `KAFKA_DLQ_FILE_PATH` | `data/events/dlq_access_logs.jsonl` |

`send_access_event` schedules background enqueueing. If the producer is offline, enqueueing raises or the event loop is unavailable, the code increments a process-local counter and attempts a local JSONL DLQ write. The producer awaits `send`, without awaiting each broker-delivery future; it does not establish confirmed delivery for every HTTP event. DLQ writing may also fail and is logged. There is no automatic DLQ replay job, durable outbox, or end-to-end exactly-once guarantee. Compose does not currently mount a dedicated persistent volume for this API-local DLQ path.

Compose forwards the producer topic variable, but the Flink access job currently uses the literal `ecommerce.access_logs`. Changing only the producer topic would disconnect ingestion; keep them aligned.

## 5. Flink processing and tables

One PyFlink job reads Kafka using group `flink-lakehouse-pure-stream`, with earliest startup for a new submission and configured 10-second exactly-once checkpointing. Checkpoints use the mounted local Flink checkpoint directory. A new submission is not automatically a restore from a previous job's checkpoint.

A single StatementSet writes four sinks from the same parsed source. These are parallel inserts, not four sequential jobs or a requirement that Spark constructs log Silver/Gold fact:

| Sink | Current transformation |
|---|---|
| `landing.access_logs` | Routing fields, duration and original raw JSON |
| `bronze.web_events` | Nested source representation and lineage |
| `silver.silver_logs` | Flattened typed fields; event_id identifier/upsert configuration |
| `gold.fact_web_events` | Event facts, duration_ms, HTTP success/error/slow flags; event_id identifier/upsert configuration |

The job uses `request.id` as event_id, generating a UUID if missing. Silver/Gold tables are configured with an identifier and upsert; existing table metadata still matters. `ecommerce.filters` is currently set to NULL in the typed inserts, while raw Landing retains the original payload. Invalid JSON is logged and filtered out; this path does not route every malformed event to an Iceberg quarantine table. Other parsing/type failures are not a complete per-record recovery workflow.

The parser converts timestamps to Asia/Ho_Chi_Minh and formats timestamp strings before SQL casts; `event_date` comes from that local date. Spark sessions use UTC. Avoid describing all log date/hour buckets as UTC without checking stored values and engine timezone behavior. A checkpoint interval is not a measured end-to-end latency SLA.

## 6. Spark marts and historical files

[build_logs_gold](../../pipelines/src/jobs/logs/build_logs_gold.py) reads `gold.fact_web_events` and writes `mart_hourly_route_metrics`, `mart_daily_product_demand`, and `mart_marketing_funnel_daily`. The streaming maintenance DAG rolls up the current VN date every two hours; the CLI can omit `--ingest-date` to process all available facts. Counts, percentiles and event-funnel limits are in [Metrics Catalog](METRICS_CATALOG.md).

Generator output can be uploaded to this raw prefix:

```text
s3://lakehouse/landing/logs/ingest_date=YYYY-MM-DD/ingest_hour=HH/service=ecommerce-api/<uuid>.jsonl.gz
```

These uploaded historical JSONL files are not consumed automatically by the Kafka job. A configured 30-day generation window is not a storage deletion/retention policy. `data_origin=observed` alone does not prove real user activity: generator exports and simulated API traffic must be identified separately when reporting results.

## 7. Inspect and feed the stream

```bash
# From the repository root, after configuring .env and starting the stack
docker compose --profile streaming logs --tail=200 flink-jobmanager
docker compose exec trino trino --execute "SELECT count(*) FROM lakehouse.gold.fact_web_events;"

# Exercise actual API requests after importing the matching SQL dataset
uv run --locked --package data-generator -- python scripts/simulate_web_traffic.py \
  --config generator/configs/small.yml --duration 300 --concurrency 5

# Historical file upload only; does not populate Kafka/Gold
./scripts/backfill_data.sh --mode logs
```

Use [SETUP](../runbook/SETUP.md) for startup/dependencies and [generator guide](../../generator/README.md) for matched SQL/log datasets.
