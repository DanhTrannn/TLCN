# Bronze Ingestion Plan - Landing to Bronze

> **Ngày:** 2026-08-21  
> **Status:** ✅ Complete (Tasks 1-3 done)  
> **Commits:** `5cdd00b..14a6385` (3 commits)

---

## Mục tiêu

Triển khai logic ingest dữ liệu từ **Landing Zone** (MinIO S3) vào **Bronze Layer** (Apache Iceberg) với chiến lược **Dead-Letter (Guarded)** pattern.

---

## Kiến trúc

```
Landing Zone (S3)          Bronze Layer (Iceberg)
┌─────────────────┐       ┌─────────────────────────┐
│ Parquet/JSONL.gz │ ───►  │ Append-only tables       │
│                 │       │ + _run_id                │
│                 │       │ + _source_file           │
│                 │       │ + _ingested_at_utc       │
└─────────────────┘       └─────────────────────────┘
                                   │
                          ┌────────┴────────┐
                          │ Quarantine       │
                          │ (per-table)      │
                          └─────────────────┘
```

---

## Chi tiết triển khai

### Task 1: Implement Bronze Ingestion Core Logic

**Files created:**
- `pipelines/src/lakehouse/bronze.py` - Core logic
- `pipelines/tests/test_bronze.py` - Test suite

**Interface:**
```python
def ingest_to_bronze(
    spark: SparkSession,
    run_id: str,
    source_path: str,
    format: str,
    target_table: str,
    quarantine_table: str,
    error_threshold: float = 0.01,
    _write_format: str = "iceberg"
) -> None
```

**TDD Steps:**
1. ✅ Write failing test
2. ✅ Verify test fails
3. ✅ Write minimal implementation
4. ✅ Verify test passes
5. ✅ Write threshold test & implement
6. ✅ Commit

### Task 2: Create Spark Submit Job

**File created:** `pipelines/src/jobs/ingest_bronze.py`

- CLI wrapper for `ingest_to_bronze()`
- Accepts command-line args for Airflow integration
- Handles Spark session lifecycle

### Task 3: Update Architecture Documentation

**File modified:** `docs/project/LAKEHOUSE_DESIGN_PLAN.md`

- Documented Dead-Letter strategy
- Added Circuit Breaker pattern (1% error threshold)
- Explained Decentralized Quarantine routing

---

## Strategy: Dead-Letter (Guarded)

### Reading Mode
- **PERMISSIVE** - Spark reads corrupt records into `_corrupt_record` column
- Preserves raw data for debugging

### Lineage Metadata
| Column | Description |
|--------|-------------|
| `_run_id` | Airflow DAG Run ID (idempotent reruns) |
| `_source_file` | Absolute S3 path (auditability) |
| `_ingested_at_utc` | Ingest timestamp (incremental Silver) |

### Circuit Breaker
- **Threshold:** 1% corrupt records (configurable)
- **Behavior:** Raise `RuntimeError` → fail fast
- **Purpose:** Prevent silent catastrophic schema changes

### Decentralized Quarantine
- **Routing:** `lakehouse.quarantine.<table_name>_errors`
- **Benefit:** Isolates replay scope, prevents cross-domain contention
- **Replay:** Ad-hoc jobs → Bronze table → Silver MERGE handles late arrival

---

## Test Coverage

| Test Case | Description | Status |
|-----------|-------------|--------|
| `test_ingest_to_bronze_ok` | Valid JSON → 2 rows + metadata columns | ✅ |
| `test_ingest_to_bronze_threshold_exceeded` | Corrupt JSON > threshold → RuntimeError | ✅ |
| `test_ingest_to_bronze_quarantine_within_threshold` | Corrupt JSON < threshold → valid + quarantine separated | ✅ |

---

## Code Review Notes

### Deferred Items
1. **`bronze.py:104`** - `format` shadows Python builtin
   - **Fix:** Rename to `source_format` in next refactor
   - **Risk:** Low

2. **`bronze.py:126`** - `df.cache()` without `unpersist()`
   - **Context:** SparkSession is per-job, so cache is auto-cleaned
   - **Risk:** Low (memory pressure in long-running sessions)

---

## Files Changed

| File | Action | Lines |
|------|--------|-------|
| `pipelines/src/lakehouse/bronze.py` | Created | +59 |
| `pipelines/src/jobs/ingest_bronze.py` | Created | +34 |
| `pipelines/tests/test_bronze.py` | Created | +83 |
| `docs/project/LAKEHOUSE_DESIGN_PLAN.md` | Modified | +10/-4 |
| **Total** | | **+182/-4** |

---

## Commits

```
14a6385 docs: document bronze ingestion dead-letter strategy and metadata columns
67d9625 feat(pipelines): add spark submit job for bronze ingestion
3a0b2de feat(pipelines): implement permissive bronze ingestion logic with quarantine
```

---

## Next Steps

- [ ] Fix `format` shadowing builtin (rename to `source_format`)
- [ ] Add `unpersist()` after count operations
- [ ] Implement Silver layer ingestion (next plan)
- [ ] Add integration tests with real Iceberg tables
