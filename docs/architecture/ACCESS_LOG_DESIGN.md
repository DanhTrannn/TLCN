# Structured Access Logs

This document defines the structured access log contract, Fluent Bit ingestion pipeline, Landing Zone layout, and Medallion transformation mapping for the D&K E-Commerce Data Platform.

## Architectural Overview

The access logging pipeline captures HTTP server requests at the FastAPI boundary, serializes each event into a compact JSON record on container stdout, and delivers compressed micro-batches to MinIO S3 object storage via Fluent Bit.

```text
Browser Client
      │ HTTP Request
      ▼
FastAPI Boundary (Middleware)
      │ Emits JSON to Docker stdout
      ▼
Fluent Bit Collector (v4.2.3)
      │ Memory buffer + persistent disk buffer
      │ Flushes 15-minute micro-batches
      ▼
MinIO S3 Landing Zone
      │ s3://lakehouse/landing/logs/ingest_date=YYYY-MM-DD/ingest_hour=HH/service=ecommerce-api/<uuid>.jsonl.gz
      ▼
Spark Batch ETL Pipeline
      │ Bronze (Raw deduplication, metadata enrichment)
      │ Silver (Validation, pseudonymization, quarantine)
      ▼
Iceberg Tables (Gold Aggregates)
      │ Hourly route metrics, product demand, search keywords
      ▼
Trino Query Layer & Superset Dashboards
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

### 15-Minute Micro-Batch Mechanism

- Fluent Bit is configured with `upload_timeout: 15m`.
- Files are rotated and uploaded to S3 after 15 minutes or when the uncompressed buffer reaches 128 MiB.
- Objects in S3 Landing Zone are immutable. Re-transmissions from buffer retries do not overwrite closed objects.

### S3 Storage Layout

All access log files follow Hive-style partitioning:

```text
s3://lakehouse/landing/logs/ingest_date=YYYY-MM-DD/ingest_hour=HH/service=ecommerce-api/<uuid>.jsonl.gz
```

- **File Format:** Gzip-compressed newline-delimited JSON (`.jsonl.gz`).
- **Retention Buffer:** Operational landing files are staged with a 30-day retention window.

---

## Medallion Architecture Mapping

| Layer | Responsibility | Primary Deduplication Key |
|---|---|---|
| **Landing** | Immutable gzip files delivered by Fluent Bit or historical generator. | S3 Key |
| **Bronze** | Raw Iceberg table preserving full lineage, file path, line numbers, and ingestion timestamps. Retains source duplicates. | `(_source_file, _source_line_number)` |
| **Silver** | Typed Iceberg table with JSON parsing, schema validation, actor pseudonymization, user-agent parsing, and deduplication. Bad records are routed to `quarantine.access_logs_quarantine`. | `request_id` |
| **Gold** | Curated dimensional facts and aggregate marts: `fact_web_requests`, `mart_hourly_route_metrics`, `mart_daily_product_demand`, `mart_daily_search_keywords`. | Composite dimensional grain |

---

## Local Verification Commands

### Check Live Fluent Bit Logs

```bash
docker compose --profile batch logs -f fluent-bit
```

### Inspect MinIO S3 Objects

Access the MinIO Web Console at `http://localhost:9001` (Bucket: `lakehouse`, Prefix: `landing/logs/`).

### Backfill Historical Access Logs

```bash
# Automated zero-footprint backfill to MinIO
./scripts/backfill_data.sh --mode logs
```
