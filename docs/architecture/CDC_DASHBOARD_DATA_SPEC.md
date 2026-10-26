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
the low-latency change log; batch is the correctness and recovery path.

Access logs continue through their separate
`ecommerce.access_logs -> Flink -> Landing/Bronze/Silver/Gold` pipeline.

## 2. Capture contract

Debezium captures the 27 analytical OLTP tables. `customer_credentials` is
intentionally excluded because it contains authentication secrets and is not an
analytical source.

The immutable `lakehouse.bronze.oltp_cdc_events` table stores one row per Kafka
record with:

- `operation`: Debezium `r` (snapshot), `c` (create), `u` (update), `d`
  (delete), or `t` (Kafka tombstone).
- `before_payload` and `after_payload`: row images from the Debezium envelope.
- `binlog_file`, `binlog_position`, and `binlog_row`: source replay ordering.
- `topic`, `kafka_partition`, and `kafka_offset`: transport replay coordinates.
- `event_id`: deterministic `<topic>:<partition>:<offset>` identity.
- `source_ts`, `event_ts`, and `ingested_at`: source, connector, and sink timing.
- `record_key` and `raw_payload`: the original Kafka key and Debezium envelope.

The table is append-only and partitioned by `event_date`. It deliberately does
not overwrite deletes or collapse updates, so audits can reconstruct state at a
specific offset. Consumers must use the latest event per primary key when they
need a current-state projection.

## 3. MySQL and connector guarantees

MySQL runs with row-based binlog, full row images, GTID, and seven-day binlog
retention. A dedicated `debezium` account receives only `SELECT`, `RELOAD`,
`SHOW DATABASES`, `REPLICATION SLAVE`, and `REPLICATION CLIENT` privileges.

The connector is registered idempotently by `debezium-init` with:

- initial consistent snapshot followed by continuous binlog capture;
- one topic per captured table;
- transaction metadata and schema history topics;
- delete events plus Kafka tombstones;
- JSON envelopes without embedded Connect schemas;
- fail-fast conversion/error handling.

Flink checkpoints every 10 seconds in exactly-once mode. Iceberg commits happen
on successful checkpoints. Kafka offsets and deterministic `event_id` values
provide a second line of defence for replay and duplicate detection.

## 4. Run and inspect

Start the complete stack:

```bash
docker compose --profile core --profile batch --profile streaming up -d --build
```

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
- A connector restart resumes from its stored binlog offset. A Flink restart
  resumes from its latest checkpoint and Kafka offsets.
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
