# MySQL CDC Architecture and Operations

## 1. Implemented data path

The transactional CDC path is deployed independently from access-log streaming:

```text
MySQL 8.4 row binlog
  -> Debezium MySQL Connector / Kafka Connect
  -> ecommerce.ecommerce.<table> Kafka topics
  -> PyFlink oltp_cdc_to_bronze
  -> lakehouse.bronze.oltp_cdc_events (Iceberg v2)
  -> Trino replay, audit, and downstream processing
```

The existing Spark incremental batch pipeline remains in place for historical
backfills, Silver/Gold construction, and source-to-target reconciliation. CDC is
the continuous change log; no measured end-to-end latency is asserted here.

Access logs continue through their separate
`ecommerce.access_logs -> Flink -> Landing/Bronze/Silver/Gold` pipeline.

## 2. Capture contract

Debezium captures the 27 analytical OLTP tables. `customer_credentials` is
intentionally excluded because it contains authentication secrets and is not an
analytical source.

The immutable `lakehouse.bronze.oltp_cdc_events` table stores one row per Kafka
record with:

- `operation`: source envelope `op`, normally `r` (snapshot), `c` (create),
  `u` (update), or `d` (delete). The local sink maps a NULL Kafka payload to
  `t`; this is its tombstone convention, not a general definition of Debezium
  `t` (which can also represent a truncate event).
- `before_payload` and `after_payload`: row images from the Debezium envelope.
- `binlog_file`, `binlog_position`, and `binlog_row`: source replay ordering.
- `topic`, `kafka_partition`, and `kafka_offset`: transport replay coordinates.
- `event_id`: deterministic `<topic>:<partition>:<offset>` identity.
- `source_ts`, `event_ts`, and `ingested_at`: source, connector, and sink timing.
- `record_key` and `raw_payload`: the original Kafka key and Debezium envelope.

The table is append-only and partitioned by `event_date`. `event_id` is a replay
identity, not a physically enforced UNIQUE constraint; consumers must account
for possible replay duplicates. The table deliberately does
not overwrite deletes or collapse updates, so audits can reconstruct state at a
specific offset. Consumers must use the latest event per primary key when they
need a current-state projection.

## 3. MySQL and connector guarantees

MySQL runs with row-based binlog, full row images, GTID, and seven-day binlog
retention. A dedicated `debezium` account receives `SELECT`, `RELOAD`,
`SHOW DATABASES`, `REPLICATION SLAVE`, and `REPLICATION CLIENT` privileges
**on `*.*`**. The connector's table allowlist restricts capture, not this
account's SQL visibility to just those 27 tables.

The connector is registered idempotently by `debezium-init` with:

- initial consistent snapshot followed by continuous binlog capture;
- one topic per captured table;
- transaction metadata and schema history topics;
- delete events plus Kafka tombstones;
- JSON envelopes without embedded Connect schemas;
- fail-fast conversion/error handling.

The job configures 10-second exactly-once checkpoints and checkpoint-driven
Iceberg commits. Checkpoints use `file:///opt/flink/checkpoints` on a Docker
volume. These settings do not establish exactly-once delivery across MySQL,
Connect, Kafka, manual job resubmission and all downstream consumers. Kafka
coordinates and deterministic event IDs support replay inspection.

## 4. Run and inspect

Start the complete stack:

```bash
docker compose --profile core --profile batch --profile streaming up -d --build
```

Prepare `.env` using [SETUP](../runbook/SETUP.md) first. The connector endpoint
below uses the default host port; adjust for `CDC_CONNECT_PORT` overrides.

Inspect the connector:

```bash
curl -fsS http://127.0.0.1:8086/connectors/mysql-ecommerce-cdc/status
```

Query captured operations:

```sql
SELECT table_name, operation, count(*) AS events
FROM lakehouse.bronze.oltp_cdc_events
GROUP BY table_name, operation
ORDER BY table_name, operation;
```

## 5. Recovery and operational rules

- Never delete the Kafka Connect offset or schema-history topics during normal
  operation.
- A connector normally resumes from its stored binlog offset while that offset
  and the binlogs remain available. The CDC Kafka source uses group offsets,
  with earliest fallback. The submission script does not supply a checkpoint
  or savepoint restore argument; a newly submitted job must not be assumed to
  restore the prior job's state automatically. Verify the actual restore point
  and committed Kafka offsets before accepting a recovery as complete.
- If binlogs have expired before the connector resumes, stop the connector,
  perform a controlled new snapshot, and reconcile with the Spark batch path.
- Changing `CDC_TOPIC_PREFIX` or `CDC_FLINK_GROUP_ID` creates a new logical
  stream; treat that as a migration, not an ordinary restart.
- Keep Bronze CDC access restricted because raw row images may contain PII.
  Pseudonymization remains mandatory before exposing customer data downstream.
- Use the Spark reconciliation and Gold quality gates after recovery or replay.

## 6. Current boundary

CDC capture through Iceberg Bronze is implemented. Automatic CDC materialization
into every typed Silver table and incremental Gold mart refresh is not yet part
of this path; those layers continue to be built and verified by the scheduled
Spark pipeline. Operational dashboard endpoints still query MySQL for current
transactional actions, while Trino serves analytical history.

Implementation references: [connector configuration](../../infrastructure/debezium/register-connector.sh),
[MySQL account](../../infrastructure/mysql/create-cdc-user.sh),
[Flink job](../../pipelines/src/jobs/cdc/mysql_cdc_to_bronze.py),
[sink DDL/checkpoint factory](../../pipelines/src/lakehouse/flink.py),
[submission script](../../infrastructure/flink/bin/submit-job.sh).
