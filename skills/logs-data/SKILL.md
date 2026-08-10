---
name: logs-data
description: Design, implement, or review structured e-commerce access logs, log collection, batch ingestion into a Lakehouse, and deterministic synthetic web traffic. Use for backend/frontend request logging, OpenTelemetry/ECS-compatible JSON contracts, privacy-safe enrichment, 15–30 minute JSONL.gz Landing files, Bronze–Silver–Gold modeling, access-log DQ/replay, or traffic generation with Vietnamese e-commerce seasonality such as Tết and monthly double-day campaigns.
---

# E-commerce log data

Build an auditable access-log source that supports operations and analytics without
turning access logs into transaction truth or an implicit clickstream platform.

## Start with repository context

1. Read the authoritative scope, architecture, routes, authentication flow, current
   logger, runtime topology, OLTP schema, and generator configuration.
2. State what is implemented, what is only planned, and which log producer owns each
   request boundary.
3. Preserve repository decisions such as table format, catalog, object storage,
   orchestration, batch interval, timezone, and excluded sources. Do not introduce
   Delta, Kafka, Kubernetes, a telemetry gateway, or browser clickstream when the
   repository has chosen Iceberg, Docker Compose, and batch access logs.
4. Resolve document conflicts using the repository's declared source-of-truth order.

## Keep source semantics separate

Classify every proposed record before designing fields:

- **Access log:** one completed HTTP request. This is the analytical source for
  traffic, route, status, latency, search/filter demand, and authenticated coverage.
- **Application log:** diagnostic state or exception. Keep it out of request facts
  unless it shares a clearly defined event contract.
- **Business transaction:** order, payment, refund, inventory, coupon, review, cart,
  or wishlist state. Keep OLTP as truth; use logs only as request context.
- **Clickstream:** browser interaction such as impression, click, scroll, or session.
  Do not add it unless the active project scope explicitly includes it.

Do not claim an access-log route sequence is a conversion funnel. Reconcile business
milestones from OLTP and use access logs only to add traffic and reliability context.

## Design contract before code

Define these items explicitly:

1. Grain: one completed request at one service boundary.
2. Identity: globally unique `request_id`; keep W3C `trace_id` and `span_id` optional
   for cross-service correlation, never as the deduplication key.
3. Time: UTC event/emission timestamps and integer `duration_ns`.
4. Route: low-cardinality route template, not a raw path containing IDs or PII.
5. Actor: `anonymous`, `customer`, `admin`, or `system`; nullable stable actor key
   that must be pseudonymized before trusted Silver.
6. Outcome: HTTP status, event outcome, safe application error code, and no response
   body.
7. Commerce context: only allowlisted product/search/filter/action fields that answer
   named analytical questions.
8. Evolution: explicit schema name/version and parser compatibility policy.

Read [references/access-log-contract.md](references/access-log-contract.md) whenever
designing producers, schemas, privacy rules, Landing/Bronze/Silver/Gold tables, DQ,
or replay behavior.

## Implement producers safely

- Emit one compact JSON object to stdout/stderr after the request finishes, including
  handled 4xx/5xx responses and unhandled exceptions.
- Generate or validate request identity at ingress and return it to callers.
- Resolve the framework route template after routing. Map unmatched paths to a bounded
  sentinel instead of preserving arbitrary raw paths.
- Enrich from trusted server-side context. Never trust a client-supplied actor ID,
  role, product ID, error code, or latency.
- Allowlist query-derived fields. Normalize and bound search text before logging; never
  log the raw query string.
- Keep browser telemetry opt-in and separate. A frontend API client may propagate
  request/trace context, but must not fabricate server status or server latency.
- Prefer native structured logging and framework middleware over hand-built string
  templates.

## Collect and ingest in closed batches

Use this boundary:

```text
web/API stdout -> log agent + disk buffer -> immutable closed JSONL.gz Landing file
-> manifest/checksum -> Bronze Iceberg -> Silver -> Gold
```

- Let the log agent own buffering, redaction defense, rotation, compression, retry,
  and upload. Applications must not write Iceberg tables.
- Use one configured interval per environment, normally 15 minutes. Close files before
  discovery and never append after publication.
- Identify source files by immutable path plus checksum. Record line count, byte size,
  min/max event time, schema versions, and producer instances in a manifest.
- Keep Bronze append-only and replayable. Deduplicate trusted rows by `request_id` in
  Silver; do not discard raw duplicates from Bronze.
- Use Spark as writer when the repository makes Spark the only Iceberg writer.

## Generate synthetic request data

Read [references/synthetic-traffic.md](references/synthetic-traffic.md) whenever adding
or reviewing a traffic generator, scenario configuration, generated log fixtures, or
campaign/seasonality behavior.

Require generated logs to be:

- deterministic from seed, anchor time, generator version, scenario, and distribution;
- referentially consistent with generated actors, products, routes, and OLTP timing;
- shaped by local business time but persisted in UTC;
- bursty around configured campaigns while preserving normal weekday/hour patterns;
- explicit synthetic data, never presented as observed Vietnamese market statistics;
- emitted in the same schema and closed-file layout as real logs.

## Validate before handoff

Check at minimum:

- every output line passes the supported schema version;
- required IDs and timestamps are valid and `request_id` is unique after Silver dedup;
- route/method combinations are bounded and plausible;
- status is 100–599 and duration is non-negative and below a documented sanity limit;
- secret/PII scanning finds no token, cookie, authorization, password, email, phone,
  address, checkout body, or payment detail;
- file manifest counts/checksum/time bounds match the closed file;
- replay/rerun does not change logical request counts or KPI results;
- campaign lift, hourly shape, actor coverage, error rate, and latency stay within
  scenario tolerances;
- Gold aggregates reconcile to accepted Silver rows by interval.

Report assumptions and analytical limitations next to the implementation. Prefer a
small meaningful contract over fields collected without a defined consumer.
