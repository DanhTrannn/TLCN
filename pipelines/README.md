# Lakehouse Pipelines

The `batch-pipeline` workspace package contains Spark OLTP extraction/transformation/quality jobs, PyFlink access-log and CDC jobs, and Iceberg maintenance helpers. Spark/Flink execution runs in the corresponding Docker images; the Python workspace alone is not their complete runtime.

## Source map

| Path | Responsibility |
|---|---|
| [config/default.yml](config/default.yml) | 27 source tables, PK/cursor, mutability, PII fields and lookback |
| [src/jobs/oltp](src/jobs/oltp) | Extract, Landing-to-Bronze, Silver, Gold and gates |
| [src/jobs/logs/kafka_to_lakehouse.py](src/jobs/logs/kafka_to_lakehouse.py) | Kafka access stream to four Iceberg sinks |
| [src/jobs/logs/build_logs_gold.py](src/jobs/logs/build_logs_gold.py) | Three log marts from fact_web_events |
| [src/jobs/cdc/mysql_cdc_to_bronze.py](src/jobs/cdc/mysql_cdc_to_bronze.py) | Debezium table topics to append-only Bronze events |
| [src/jobs/maintenance](src/jobs/maintenance) | Compaction, manifest rewrite, expiry, orphan and quarantine cleanup |
| [src/lakehouse/oltp](src/lakehouse/oltp) | SQL predicates, extract, cursor, Bronze/Silver/Gold DDL/transform, reconciliation/quality |
| [src/lakehouse/logs](src/lakehouse/logs) | Log schemas and Spark rollup transformations |
| [src/lakehouse/flink.py](src/lakehouse/flink.py) | Active Flink table DDL, upsert/checkpoint/catalog configuration |
| [src/lakehouse/spark.py](src/lakehouse/spark.py) | Spark session, UTC timezone, S3 and REST catalog configuration |
| [Airflow DAGs](../airflow/dags) | Batch and separate maintenance orchestration |

## Batch OLTP

The `lakehouse_oltp_pipeline` DAG runs daily at 02:00 Asia/Ho_Chi_Minh, with catchup disabled and one active run. Compose creates DAGs paused.

1. Capture per-table high watermarks; Spark reads composite cursor windows with a default 10-minute lookback.
2. Write Landing Parquet/manifests; validate listed objects and MD5 integrity metadata. MD5 here is an integrity check, not authentication of an untrusted source.
3. Append source data/lineage to Bronze; **commit cursors after Bronze succeeds**.
4. Type, deduplicate, pseudonymize configured PII and MERGE Silver; quarantine violations.
5. Reconcile MySQL against Silver at a 0.05% tolerance before Gold.
6. Build Gold dimensions and facts in parallel, then marts.
7. Run post-Gold quality checks and write evidence to `lakehouse.system.data_quality_results`.

Gold OLTP defines 6 dimensions, 5 facts and 4 marts. Counts/keys/financial checks are separate from the dashboard's display thresholds. Each table commits independently; a post-Gold failure does not roll back every previously written table. Watermarks are not a single consistent snapshot across all source tables.

Batch does not propagate all hard deletes. Payments use created_at even though COD completion updates status, so old updates outside lookback can be missed. CDC retains updates/deletes separately but does not automatically apply them to Silver/Gold. Inspect run lineage and audit results when recovering after a Silver/Gold failure with already-advanced cursors.

## Access-log streaming and CDC

| Job | Source | Sinks / boundary |
|---|---|---|
| `kafka_to_lakehouse_pure_streaming` | Kafka ecommerce.access_logs | One StatementSet inserts Landing access_logs, Bronze web_events, Silver silver_logs and Gold fact_web_events |
| `oltp_cdc_to_bronze` | Debezium per-table Kafka topics | Bronze oltp_cdc_events, including raw payload/key, operation, images, binlog and Kafka coordinates |

Both jobs configure 10-second checkpoints on the mounted Flink checkpoint directory. This is not a measured latency SLA or an end-to-end exactly-once guarantee. The submit script does not automatically specify a prior checkpoint/savepoint for a new submission. CDC event_id is deterministic, but the append-only sink does not enforce physical uniqueness.

The access job uses request identity/upsert configuration for Silver/Gold. Invalid JSON is logged and dropped; a full schema/quarantine path is not enforced for every message. Timestamp parsing uses VN local time before SQL casts, whereas Spark sessions use UTC. Historical JSONL uploaded under landing/logs is not read by this Kafka job. See [access logs](../docs/architecture/ACCESS_LOG_DESIGN.md) and [CDC](../docs/architecture/CDC_DASHBOARD_DATA_SPEC.md).

## Maintenance and mart rollups

| DAG | Schedule (VN) | Current scope |
|---|---|---|
| `lakehouse_oltp_maintenance` | 03:00 daily | 15 Gold + 8 listed Silver tables; separate quarantine cleanup |
| `lakehouse_streaming_maintenance` | Every 2 hours | Four log tables, then three log mart rollups for the current VN date |

Maintenance does not yet cover all 27 Silver tables, batch Bronze or Bronze CDC. Refer to TABLE_PROFILES in the maintenance job. OLTP compaction targets 128 MiB, snapshot expiry retains at least the configured last 10 snapshots (20 for logs), orphan cleanup defaults to a 3-day cutoff. Quarantine retention deletes rows older than 30 days in quarantine.silver_oltp_violations; it is not a bucket-wide retention policy.

The streaming health task checks for a RUNNING job, not independently for both required streams. Maintenance DAGs have no cross-DAG dependency waiting for batch completion. The log rollup CLI can omit --ingest-date to process all available fact dates; the scheduled DAG supplies today's VN date.

## Run and inspect

After configuring and starting the stack, load the source history and use:

```bash
docker compose exec -T airflow-scheduler airflow dags unpause lakehouse_oltp_pipeline
docker compose exec -T airflow-scheduler airflow dags trigger lakehouse_oltp_pipeline
docker compose exec trino trino --execute "SHOW TABLES FROM lakehouse.gold;"
docker compose exec trino trino --execute "SELECT * FROM lakehouse.system.data_quality_results LIMIT 20;"
```

A successful schema bootstrap only creates tables; it does not populate analytical results. Full startup, other DAGs and recovery checks are in [SETUP](../docs/runbook/SETUP.md). Model grains and KPI formulas are in [Lakehouse Design](../docs/project/LAKEHOUSE_DESIGN_PLAN.md) and [Metrics Catalog](../docs/architecture/METRICS_CATALOG.md).
