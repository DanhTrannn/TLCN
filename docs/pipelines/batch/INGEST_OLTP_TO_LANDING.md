# OLTP Extraction to Landing Zone (`ingest_oltp_batch`)

This document describes the Spark batch pipeline for extracting 16 OLTP tables from MySQL into the MinIO Landing Zone as Parquet files with cryptographic MD5 manifests and composite state cursors.

---

## 1. Pipeline Overview

* **DAG:** `ingest_oltp_batch`
* **Schedule:** On-demand / Triggered (`None`)
* **Timezone:** `Asia/Ho_Chi_Minh`
* **Spark Job:** [`pipelines/src/jobs/oltp/extract_oltp.py`](file:///home/leekhoa/Code/TLCN/pipelines/src/jobs/oltp/extract_oltp.py)
* **Core Modules:**
  * [`pipelines/src/lakehouse/oltp/extract.py`](file:///home/leekhoa/Code/TLCN/pipelines/src/lakehouse/oltp/extract.py) — Multi-threaded extraction engine
  * [`pipelines/src/lakehouse/oltp/cursor.py`](file:///home/leekhoa/Code/TLCN/pipelines/src/lakehouse/oltp/cursor.py) — Composite cursor state serialization
  * [`pipelines/src/lakehouse/oltp/query.py`](file:///home/leekhoa/Code/TLCN/pipelines/src/lakehouse/oltp/query.py) — SQL incremental predicate builder
  * [`pipelines/src/lakehouse/landing.py`](file:///home/leekhoa/Code/TLCN/pipelines/src/lakehouse/landing.py) — Landing path builder & manifest writer

---

## 2. Airflow Workflow DAG

```text
check_mysql
    │
    ▼
begin_run
    │
    ▼
capture_high_watermarks
    │
    ▼
extract_tables_to_landing (SparkSubmitOperator -> extract_oltp.py)
    │
    ▼
validate_landing_manifests
    │
    ▼
commit_cursors
```

### Task Descriptions
1. **`check_mysql`**: Validates MySQL connectivity and credentials via SQLAlchemy.
2. **`begin_run`**: Generates execution `run_id` (UUID4) and resolves `extract_date`.
3. **`capture_high_watermarks`**: Reads `MAX(cursor_field)` and `MAX(pk)` from MySQL for all tables to lock the extraction upper bound.
4. **`extract_tables_to_landing`**: Submits Spark job to read data in parallel, write Snappy Parquet files to S3, and serialize MD5 manifests.
5. **`validate_landing_manifests`**: Verifies file count, byte size, and MD5 hashes across all 16 landing folders.
6. **`commit_cursors`**: Atomically advances `state/cursor/<table_name>.json` in MinIO to the new watermark.

---

## 3. Storage Layout

Data files are written to the Landing Zone under the partition hierarchy:

```text
s3a://lakehouse/landing/oltp/<table_name>/extract_date=YYYY-MM-DD/run_id=<run_id>/
├── data_0000.parquet
├── data_0001.parquet
└── _manifest.json
```

### Manifest Schema (`_manifest.json`)
```json
{
  "manifest_version": "1.0",
  "table_name": "orders",
  "run_id": "9f7b1945-8176-47b2-bd75-385038c92a95",
  "extract_date": "2026-08-31",
  "row_count": 1250,
  "files": [
    {
      "path": "s3a://lakehouse/landing/oltp/orders/extract_date=2026-08-31/run_id=9f7b1945.../data_0000.parquet",
      "bytes": 45120,
      "md5": "d41d8cd98f00b204e9800998ecf8427e"
    }
  ],
  "high_watermark": {
    "cursor_field": "updated_at",
    "cursor_at": "2026-08-31T14:38:22.000000",
    "cursor_pk": 1250
  }
}
```

---

## 4. Manual CLI Execution

```bash
docker compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  /opt/project/pipelines/src/jobs/oltp/extract_oltp.py \
  --config-path /opt/project/pipelines/config/default.yml \
  --run-id manual-extract-01 \
  --extract-date 2026-08-31
```
