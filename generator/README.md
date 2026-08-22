# OLTP & Access Log Data Generator

The Data Generator (`data-generator` package, v0.6.0) creates deterministic synthetic datasets calibrated to realistic Vietnamese e-commerce behavior. It exports full relational SQL inserts for MySQL OLTP and operational HTTP access logs formatted identically to production runtime logs.

---

## Automated Backfill (Zero-Footprint on Host)

To backfill data without leaving temporary SQL or log files on your host filesystem, use [`scripts/backfill_data.sh`](../../scripts/backfill_data.sh):

```bash
# Backfill both OLTP SQL into MySQL and Access Logs to MinIO S3
./scripts/backfill_data.sh

# Or backfill individually
./scripts/backfill_data.sh --mode oltp  # MySQL database only
./scripts/backfill_data.sh --mode logs  # MinIO Landing Zone only

# With a specific scale configuration
./scripts/backfill_data.sh --config generator/configs/medium.yml
```

---

## Manual Export Workflow

### 1. Export SQL History

```bash
uv run --locked --package data-generator -- generator export-sql \
  --config generator/configs/small.yml \
  --output data/generator/small.sql
```

The output file is written to `data/generator/small.sql`.

### 2. Import into MySQL

Once MySQL is running and Alembic migrations have completed (`0001` through `0009`):

```bash
./scripts/import_generated_sql.sh data/generator/small.sql
```

> [!IMPORTANT]
> The generated SQL runs within a single atomic transaction without disabling foreign key checks. Do not import the same SQL file twice into the same database.

### Demo Customer Credentials
After export, the CLI prints a demo customer account. The demo email uses the first 8 characters of `logical_identity`, and the local password is fixed to `Demo@12345`.

---

### 3. Export Matching Access Logs

```bash
uv run --locked --package data-generator -- generator export-logs \
  --config generator/configs/small.yml \
  --output-directory data/generator/access-logs \
  --expected-requests 60000
```

Output files are structured in Hive-style partition directories under `data/generator/access-logs/landing/logs/`:

```text
landing/logs/ingest_date=YYYY-MM-DD/ingest_hour=HH/service=ecommerce-api/<uuid>.jsonl.gz
```

- **Retention Window:** Generates operational access logs matching the most recent 30-day window.
- **Format:** Gzip-compressed newline-delimited JSON (`.jsonl.gz`).
- **Telemetry Standards:** Standardized to OpenTelemetry-compatible fields (`service.name=ecommerce-api`, `data_origin=observed`, 12-character hex container IDs).

### 4. Upload to MinIO Landing Zone

When MinIO and Docker services are active, upload generated logs to the S3 Landing Zone:

```bash
./scripts/upload_generated_logs.sh data/generator/access-logs
```

---

## 5. Dataset Scale Configurations

The `configs/` directory provides pre-configured scenarios:

| Config | Customers | Products | Variants | Orders | Window |
|---|---|---|---|---|---|
| `small.yml` | 500 | 60 | 240 | ~3,000 | 12 months |
| `medium.yml` | 5,000 | 200 | 800 | ~30,000 | 12 months |
| `large-local.yml` | 50,000 | 500 | 2,000 | ~300,000 | 12 months |
| `large-10m.yml` | 500,000 | 1,000 | 4,000 | ~10,000,000 | 12 months |
| `month-test.yml` | 200 | 30 | 120 | ~250 | 1 month |

---

## 6. Vietnamese E-Commerce Behavioral Distributions

The generator models realistic retail consumption patterns:

- **Timezone & Seasonality:** Calibrated to `Asia/Ho_Chi_Minh` (stored as UTC). Models Lunar New Year (Tet) sales peaks, double-day campaigns (e.g. 9/9, 11/11, 12/12), and Black Friday.
- **Diurnal Rhythm:** Normal day peaks occur at 19:00–22:00. Campaign days feature 00:00–02:00 midnight spikes, lunch rushes (12:00), and evening surges.
- **Customer Segmentation:** Customers are segmented into `loyal`, `regular`, and `one_off` cohorts with distinct purchase intervals, coupon affinity, review propensities, and cancellation rates.
- **Review Behavior:** Reviews originate exclusively from verified `completed` order items. Default synthetic ratio features 94% published immediately and 6% post-moderated (`rejected`) with Vietnamese audit reasons.
- **Soft Archive:** Simulates product and coupon lifecycle archives without breaking historical relational lineage.

---

## 7. Deterministic Identity Strategy

- **Surrogate PKs:** Uses `BIGINT UNSIGNED` keys for internal joins and performant bulk imports.
- **Public Identifiers:** Uses deterministic UUIDv5 for `public_id`, `logical_identity`, `generation_run_id`, and transaction idempotency keys.
- **Business Keys:** Keeps human-readable `order_number`, SKU, slug, and coupon code identifiers.

---

## 8. Unit Testing

Run the generator unit tests (54 tests):

```bash
uv run --locked --package data-generator --extra dev -- pytest generator/tests
```
