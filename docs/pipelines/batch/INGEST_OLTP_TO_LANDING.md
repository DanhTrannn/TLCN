# Batch Pipeline: OLTP Extract to MinIO Landing

This document specifies the design, architecture, and operational mechanics of the `ingest_oltp_batch` Airflow DAG, which extracts transactional data from the 16 allowed MySQL OLTP tables and writes immutable Parquet files with cryptographic manifests to the MinIO Landing Zone.

---

## 1. Architecture and Data Flow

```text
Airflow DAG: ingest_oltp_batch
 ├── 1. check_mysql (PythonOperator)
 ├── 2. begin_run (PythonOperator: generates run_id, extract_date)
 ├── 3. capture_high_watermarks (PythonOperator: captures MAX cursor per table)
 ├── 4. extract_tables_to_landing (SparkSubmitOperator -> jobs/extract_oltp.py)
 │      ├── Multi-threaded read (ThreadPoolExecutor, 4 parallel tables)
 │      ├── Incremental extraction via composite cursor (cursor_field, pk)
 │      ├── Lineage metadata column enrichment (_run_id, _source_*, _ingested_at_utc)
 │      ├── Parquet write to s3a://lakehouse/landing/oltp/<table>/extract_date=.../run_id=.../
 │      └── Cryptographic manifest write (manifest.json with MD5 checksums)
 └── 5. validate_landing_manifests (PythonOperator: validates Parquet row counts and S3 objects)
```

---

## 2. Storage Layout and Partitioning

Landing data is organized under Hive-style UTC date partitions:

```text
landing/oltp/<table>/extract_date=YYYY-MM-DD/run_id=<run_id>/
  ├── data/
  │   ├── part-00000-<uuid>.parquet
  │   └── part-00001-<uuid>.parquet
  └── manifest.json
```

### Storage Properties
- **Immutability:** Once written, Parquet files in the Landing Zone are strictly immutable and append-only.
- **Run Isolation:** Every DAG run generates a unique `run_id` (`uuid4().hex`), preventing file collisions during retries or replays.
- **Manifest Finalization:** The `manifest.json` file is written last, serving as the atomicity marker for each extracted table.

---

## 3. Incremental Extraction Mechanics

Incremental ingestion relies on composite cursors `(cursor_field, pk)` to guarantee exact and deterministic boundary queries without data loss.

### Incremental SQL Predicate
When a committed cursor exists in `s3://lakehouse/state/cursor/<table>.json`:

```sql
WHERE (`cursor_field` > :committed_at 
   OR (`cursor_field` = :committed_at AND `pk` > :committed_pk))
```

### High Watermark Capture
Before extraction starts, Airflow captures the instantaneous high watermark in MySQL:

```sql
SELECT MAX(`cursor_field`) AS at, MAX(`pk`) AS pk_at_max
FROM `<table>`
WHERE `cursor_field` = (SELECT MAX(`cursor_field`) FROM `<table>`);
```

---

## 4. Metadata Column Enrichment

Every row written to Parquet includes standardized source audit columns:

| Column | Type | Description | Example |
|---|---|---|---|
| `_run_id` | string | Unique extraction execution ID | `a3b8c2f1...` |
| `_source_system` | string | Source origin identifier | `mysql_ecommerce` |
| `_source_schema` | string | Origin database schema | `ecommerce` |
| `_source_table` | string | Source table name | `orders` |
| `_source_primary_key` | string | Cast string of row PK value | `1001` |
| `_source_cursor_at` | string / datetime | Timestamp value of the cursor field | `2026-08-19 12:00:00` |
| `_source_high_watermark` | string | Target extraction upper bound | `2026-08-19 14:00:00` |
| `_ingested_at_utc` | string | ISO 8601 UTC ingestion timestamp | `2026-08-19T14:05:00Z` |

---

## 5. Manifest Specification (`v1.0.0`)

Each completed table run outputs a `manifest.json`:

```json
{
  "manifest_version": "1.0.0",
  "run_id": "9f3b7c2a1e...",
  "table": "orders",
  "source": {
    "system": "mysql_ecommerce",
    "schema": "ecommerce"
  },
  "cursor": {
    "field": "updated_at",
    "committed_at": "2026-08-19T10:00:00.000000",
    "committed_pk": 1050,
    "high_watermark_at": "2026-08-19T14:00:00.000000",
    "high_watermark_pk": 1280,
    "min_at": "2026-08-19T10:05:00.000000",
    "max_at": "2026-08-19T13:58:30.000000"
  },
  "rows": 230,
  "empty": false,
  "files": [
    {
      "path": "landing/oltp/orders/extract_date=2026-08-19/run_id=9f3b.../data/part-00000.parquet",
      "rows": 115,
      "md5": "d41d8cd98f00b204e9800998ecf8427e"
    },
    {
      "path": "landing/oltp/orders/extract_date=2026-08-19/run_id=9f3b.../data/part-00001.parquet",
      "rows": 115,
      "md5": "79cfeb94595de33b3326c06ab1abefd2"
    }
  ],
  "generated_at_utc": "2026-08-19T14:06:12Z"
}
```

---

## 6. Manifest Validation Gate

The final DAG step (`validate_landing_manifests`) uses Boto3 and PyArrow to inspect Parquet metadata footers without starting a Spark cluster:
- Verifies that all files listed in `manifest.json` physically exist in MinIO.
- Ensures object sizes are non-zero.
- Computes the sum of row counts from Parquet footers and verifies exact match with `manifest.rows`.
- Verifies boundary constraints (`min_at >= committed_at` and `max_at <= high_watermark_at`).

---

## 7. Automated Testing and Verification

Run the pipeline unit test suite:

```bash
PYTHONPATH=pipelines/src uv run --locked --package batch-pipeline --extra dev -- pytest pipelines/tests
```

### Test Coverage (32 Tests)
- `test_config.py`: Verifies loading and validation of table specs, cursor mappings, and mutability configurations.
- `test_cursor.py`: Tests JSON round-tripping and error handling for `CursorState`.
- `test_landing.py`: Verifies `RunPaths` path builders, manifest serialization, and edge-case validation rules.
- `test_validate.py`: Tests S3 manifest validation logic and failure detection.