# Access-log contract and Lakehouse mapping

## Contents

1. Source contract
2. Field semantics
3. Commerce context
4. Privacy
5. Collection and file identity
6. Medallion mapping
7. Quality, reconciliation, and replay

## 1. Source contract

Use one JSON object per completed HTTP request. Align naming with OpenTelemetry and ECS
where practical, but keep the project contract stable instead of copying either model
wholesale.

```json
{
  "schema": {"name": "ecommerce.access", "version": "1.0.0"},
  "timestamp": "2026-08-10T08:53:00.123456Z",
  "observed_timestamp": "2026-08-10T08:53:00.125000Z",
  "severity_text": "INFO",
  "severity_number": 9,
  "request": {"id": "01989a4f62f77a23a874a235818ba625"},
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "service": {
    "name": "ecommerce-api",
    "version": "0.1.0",
    "environment": "local",
    "instance_id": "ecommerce-api-1"
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
  "actor": {"type": "customer", "key": "customer-public-id"},
  "client": {"user_agent": "bounded raw user agent"},
  "ecommerce": {
    "action": "product_detail",
    "product_key": "dam-linen-dk-001",
    "search_query": null,
    "filters": {}
  },
  "error": {"code": null, "type": null}
}
```

Omit optional fields or set them to null consistently within one schema version. Do not
emit arbitrary dynamic keys outside a bounded `filters` map.

## 2. Field semantics

| Field | Rule |
|---|---|
| `schema.name` | Stable dataset identity, normally `ecommerce.access` |
| `schema.version` | Semantic schema version; reject unsupported major versions |
| `timestamp` | UTC request completion time with microsecond precision |
| `observed_timestamp` | UTC time the log record is emitted; must not precede request start materially |
| `severity_*` | OpenTelemetry severity; normal requests are INFO/9, failures ERROR/17 |
| `request.id` | Unique request identity; primary Silver deduplication key |
| `trace_id`, `span_id` | Optional lowercase W3C hexadecimal identifiers |
| `service.*` | Producer identity; environment and instance must be bounded dimensions |
| `event.duration_ns` | Integer monotonic duration in nanoseconds |
| `event.outcome` | `success`, `failure`, or `unknown`; define status mapping centrally |
| `http.request_method` | Uppercase allowlisted HTTP method |
| `http.route` | Framework route template or bounded `__unmatched__` sentinel |
| `http.status_code` | Integer 100–599 |
| `actor.type` | `anonymous`, `customer`, `admin`, or `system` |
| `actor.key` | Nullable stable server-resolved key; hash/HMAC before trusted Silver |
| `client.user_agent` | Optional bounded raw value; parse to family/device in Silver |
| `error.code` | Safe application error code, never an exception message |
| `error.type` | Bounded exception class for operational grouping |

Do not use `(instance_id, timestamp, trace_id)` as a logical key: timestamps collide,
trace IDs span multiple requests, and trace context may be absent. Use `request.id`.

## 3. Commerce context

Only emit context with a named analytical use. Resolve values server-side when possible.

| Request class | Allowed context | Analytical use |
|---|---|---|
| Catalog list/search | normalized `search_query`; category, size, color, price band, in-stock and sort filters | search demand and filter usage |
| Product detail | product public ID or stable slug | product request demand |
| Wishlist mutation | product key and bounded action | request reliability; OLTP remains wishlist truth |
| Cart mutation | variant/product key and bounded action | request reliability; OLTP remains cart truth |
| Checkout quote/submit | bounded action and coupon-present boolean | checkout traffic and failure rate |
| Order lifecycle/review | bounded action only unless a stable analytical key is required | operational traffic; OLTP remains lifecycle truth |
| Admin route | bounded admin action | admin workload and reliability |

Normalize search text with trim, whitespace collapse, Unicode normalization, lowercase
policy, maximum length, and a PII sanitizer. Reject or redact strings matching email,
phone, token, card, or address patterns. Prefer product/category keys that Silver can
left join to OLTP-derived dimensions; retain unresolved rows and measure the unresolved
rate.

Never log raw path parameters such as order numbers, customer IDs, review IDs, cart IDs,
or idempotency keys. Never log the raw query string.

## 4. Privacy

Block these values at the producer and scan again at the agent/Silver boundary:

- password/hash, JWT, cookie, session or CSRF token;
- `Authorization`, `Set-Cookie`, internal secret, idempotency key;
- email, phone, receiver name, shipping address;
- checkout/request/response body and payment detail;
- raw exception message/stack trace in the analytical access dataset;
- raw IP unless an approved operational use and retention policy exists.

Do not use IP as customer identity. If IP is retained in raw operational storage, make it
nullable, tightly retained, inaccessible to Gold, and HMAC/mask it before Silver.

## 5. Collection and file identity

Use UTC event paths and fixed half-open windows `[window_start, window_end)`:

```text
s3://<bucket>/landing/logs/
  date=YYYY-MM-DD/hour=HH/window_start=YYYYMMDDTHHMMSSZ/
  service=<service>/instance=<instance>/part-<immutable-id>.jsonl.gz
```

Publish a manifest only after the gzip file is closed. Include:

- immutable object path, SHA-256, compressed bytes, and line count;
- window start/end and min/max event timestamp;
- service/instance and encountered schema versions;
- agent version, emitted timestamp, and delivery attempt identity.

Treat `(object_path, sha256)` as file identity. A repeated identity is a delivery replay,
not new data. A reused path with a different checksum is a source integrity violation.

## 6. Medallion mapping

### Landing

Keep closed `jsonl.gz` objects immutable. Use a short but sufficient replay retention;
do not delete until Bronze commit and reconciliation are durable.

### Bronze Iceberg

Store raw payload or typed raw columns plus `_run_id`, `_source_file`,
`_source_file_checksum`, `_source_line_number`, `_ingested_at_utc`, `_parser_version`,
and `_schema_version`. Keep source duplicates. Partition initially by bounded UTC event
date; add service only after measuring file counts and query pruning.

### Silver Iceberg

Flatten stable analytical columns, validate types, deduplicate by `request_id`, normalize
route/search/filter values, pseudonymize actor, parse client family, and left join safe
product references. Route semantic violations to quarantine with Bronze lineage.

Recommended grain: one accepted completed request. Recommended key: `request_id`.

### Gold Iceberg

Prefer a narrow `fact_web_request` and small aggregate marts:

- hourly service/route volume, 4xx/5xx rate, and latency p50/p95/p99;
- daily product-detail request demand;
- daily normalized search demand and filter usage;
- daily authenticated actor coverage and activity.

Do not calculate revenue, payment success, order state, inventory, coupon redemption, or
review truth from access logs.

## 7. Quality, reconciliation, and replay

Validate syntax and supported schema major version before Bronze. In Silver check request
ID, timestamps/clock skew, route/method allowlist, status range, duration sanity, actor
consistency, PII scan, and bounded field lengths.

Reconcile each file/window:

```text
manifest line count
= Bronze parsed rows + technical rejects

Bronze parsed rows
= Silver accepted pre-dedup rows + semantic quarantine rows

Silver accepted unique request IDs
= Gold fact rows for the same published interval
```

Commit file identity and publication state only after the relevant quality gate. Rebuild
Silver/Gold from fixed Bronze snapshots; reprocess Landing only for Bronze parser defects.
Audit input/output snapshot IDs and prove reruns preserve logical counts and KPIs.
