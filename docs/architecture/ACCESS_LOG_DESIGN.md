# Structured Access Logs

This document defines the structured access log contract, Kafka + Flink real-time streaming pipeline, Landing Zone layout, and Medallion transformation mapping for the D&K E-Commerce Data Platform.

## Architectural Overview

The access logging pipeline captures HTTP server requests at the FastAPI boundary, serializes each event into a compact JSON record on container stdout, and streams events in real-time through Apache Kafka to Apache Flink for continuous Iceberg lakehouse ingestion.

```text
Browser Client
      │ HTTP Request
      ▼
FastAPI Boundary (Middleware)
      │ Publishes structured JSON event
      ▼
Apache Kafka (Event Bus)
      │ Topic: ecommerce.access_logs (partitioned, KRaft)
      ▼
Apache Flink (Streaming Ingestion Engine)
      │ Real-time checkpointing & Iceberg streaming sink
      ▼
Apache Iceberg Tables (Landing & Bronze)
      │ landing.access_logs -> bronze.web_events
      ▼
Streaming Maintenance & Spark Rollups
      │ Silver (silver_logs deduplication & typing)
      │ Gold (fact_web_events, hourly route metrics, product demand)
      ▼
Trino Query Layer & Admin BI Analytics Hub
```

---

## Schema Contract (v1.0.0)

The formal schema definition is located at [`../contracts/ecommerce-access-v1.schema.json`](../contracts/ecommerce-access-v1.schema.json).

### Example JSON Record

```json
{
  "schema": {
    "name": "ecommerce.access",
    "version": "1.0.0"
  },
  "timestamp": "2026-08-19T12:00:00.123456Z",
  "observed_timestamp": "2026-08-19T12:00:00.125000Z",
  "severity_text": "INFO",
  "severity_number": 9,
  "request": {
    "id": "01989a4f62f77a23a874a235818ba625"
  },
  "trace_id": null,
  "span_id": null,
  "service": {
    "name": "ecommerce-api",
    "version": "0.1.0",
    "environment": "local",
    "instance_id": "450ce87085c1"
  },
  "event": {
    "name": "http.server.request",
    "category": "web",
    "kind": "event",
    "outcome": "success",
    "duration_ns": 18425000
  },
  "http": {
    "request_method": "GET",
    "route": "/api/v1/products/{slug}",
    "status_code": 200
  },
  "actor": {
    "type": "customer",
    "key": "01989a4f-62f7-7a23-a874-a235818ba625"
  },
  "client": {
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)..."
  },
  "ecommerce": {
    "action": "product_detail",
    "product_key": "dam-linen-dk-001",
    "variant_key": null,
    "search_query": null,
    "filters": {}
  },
  "error": {
    "code": null,
    "type": null
  },
  "data_origin": "observed"
}
```

### Field Reference Table

| Field | Type | Required | Description | Constraints & Values |
|---|---|---|---|---|
| `schema.name` | string | Yes | Dataset identity | Fixed value: `ecommerce.access` |
| `schema.version` | string | Yes | Semantic contract version | Fixed value: `1.0.0` |
| `timestamp` | string | Yes | ISO 8601 UTC completion time | Microsecond precision |
| `observed_timestamp` | string | Yes | ISO 8601 UTC emission time | Emitted immediately upon response |
| `severity_text` | string | Yes | OpenTelemetry severity text | `INFO` (2xx/3xx), `WARN` (4xx), `ERROR` (5xx) |
| `severity_number` | integer | Yes | OpenTelemetry severity level | `9` (INFO), `13` (WARN), `17` (ERROR) |
| `request.id` | string | Yes | Unique request ID | 32-character hexadecimal string |
| `service.name` | string | Yes | Emitting service name | `ecommerce-api` |
| `service.version` | string | Yes | Service semantic version | `0.1.0` |
| `service.environment` | string | Yes | Runtime environment | `local`, `staging`, `production` |
| `service.instance_id` | string | Yes | Container or host identity | 12-character hexadecimal container ID |
| `event.name` | string | Yes | Event semantic name | `http.server.request` |
| `event.duration_ns` | integer | Yes | Execution duration | Monotonic clock duration in nanoseconds |
| `http.request_method` | string | Yes | HTTP method | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` |
| `http.route` | string | Yes | Canonical FastAPI route template | e.g. `/api/v1/products/{slug}`, or `__unmatched__` |
| `http.status_code` | integer | Yes | HTTP status code | Integer `100` to `599` |
| `actor.type` | string | Yes | Actor classification | `anonymous`, `customer`, `admin`, `system` |
| `actor.key` | string | No | Actor public ID or system key | UUID string or `null` (for anonymous) |
| `ecommerce.action` | string | No | Commerce action taxonomy | e.g. `catalog_view`, `product_detail`, `checkout_submit` |
| `ecommerce.product_key` | string | No | Product public ID or slug | Sanitized identifier or `null` |
| `ecommerce.variant_key` | string | No | Variant public ID or SKU | Sanitized identifier or `null` |
| `ecommerce.search_query` | string | No | Normalized search term | Trimmed, lowercase, PII-sanitized |
| `ecommerce.filters` | object | No | Applied filter map | Bounded key-value object |
| `error.code` | string | No | Safe application error code | e.g. `INSUFFICIENT_STOCK`, `INVALID_COUPON` |
| `error.type` | string | No | High-level exception category | e.g. `ValidationError`, `NotFoundError` |
| `data_origin` | string | Yes | Record provenance | `observed` |

---

## Privacy and Redaction Rules

To comply with data privacy policies, the following fields are strictly excluded at the API middleware boundary:

1. **Credentials and Tokens:** Passwords, password hashes, JWT tokens, session cookies, and CSRF tokens are never logged.
2. **HTTP Headers:** `Authorization`, `Cookie`, `Set-Cookie`, and internal API secrets are excluded.
3. **Customer PII:** Customer names, email addresses, phone numbers, and shipping street addresses are never logged.
4. **Payment Details:** Credit card numbers, bank accounts, and raw payment payloads are excluded.
5. **Raw Payloads:** Request and response JSON bodies are omitted; only allowlisted parameters (product slug, normalized search text) are extracted.
6. **Raw IP Addresses:** IP addresses are not recorded in the analytical access log schema.

---

## Ingestion and Landing Layout

### Streaming and historical files

FastAPI publishes HTTP events to Kafka `ecommerce.access_logs`. The continuous Flink job writes `landing.access_logs`, `bronze.web_events`, `silver.silver_logs` and `gold.fact_web_events` through a StatementSet, with a configured 10-second checkpoint interval.

The checkpoint interval is not an end-to-end latency guarantee. Delivery and replay behavior must be interpreted with the Kafka offsets, Flink checkpoints and table commits of the running job.

The generator can also upload historical `.jsonl.gz` files to:

```text
s3://lakehouse/landing/logs/ingest_date=YYYY-MM-DD/ingest_hour=HH/service=ecommerce-api/<uuid>.jsonl.gz
```

These files are raw Landing assets. The current Flink job reads Kafka and does not automatically ingest the uploaded JSONL files. A generated 30-day log window is a dataset setting, not proof that object-storage retention is configured to delete files after 30 days.

## Medallion mapping

| Layer | Current tables / processing |
|---|---|
| Landing | Iceberg `landing.access_logs` for the stream; historical JSONL files are a separate raw path |
| Bronze | `bronze.web_events`, source event representation and lineage |
| Silver | `silver.silver_logs`, typed fields and request-key processing |
| Gold fact | `gold.fact_web_events`, event-grain HTTP/business facts |
| Gold marts | `mart_hourly_route_metrics`, `mart_daily_product_demand`, `mart_marketing_funnel_daily`; Spark rollups |

See [Metrics Catalog](METRICS_CATALOG.md) for request duration, error rate, product demand and event-based funnel definitions. Source metadata alone does not prove that a log was produced by real users; record the generator/traffic configuration when reporting synthetic data.

---

## Observe the Pipeline

### Check Live Streaming Logs

```bash
docker compose --profile streaming logs -f flink-jobmanager
docker compose --profile streaming logs -f kafka
```

### Inspect MinIO S3 Objects

Access the MinIO Web Console at `http://localhost:9001` (Bucket: `lakehouse`, Prefix: `landing/logs/`).

### Backfill Historical Access Logs

```bash
# Automated zero-footprint backfill to MinIO
./scripts/backfill_data.sh --mode logs
```
