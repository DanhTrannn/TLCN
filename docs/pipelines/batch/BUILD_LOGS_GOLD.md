# Batch Pipeline: Access Logs Silver to Gold (Fact & Data Marts)

**Goal:** Build a Spark analytical transformation pipeline that reads cleansed access logs from the Iceberg Silver table (`lakehouse.silver.silver_logs`), models detailed request events into a Kimball Star Schema Fact table (`lakehouse.gold.fact_web_events`), and aggregates operational and product analytics into two Gold Data Marts:
1. `lakehouse.gold.mart_hourly_route_metrics`: API traffic, error rates, and p50/p95/p99 latency distributions per route/hour.
2. `lakehouse.gold.mart_daily_product_demand`: Daily product view count, cart additions, wishlist adds, checkout intent, and conversion funnel metrics.

**Architecture:** The pipeline is embedded within the unified Airflow master DAG (`lakehouse_logs_pipeline`) in the `gold_layer` TaskGroup. Each scheduled run reads Silver logs, transforms and appends to `fact_web_events`, and performs dynamic partition overwrites (`overwritePartitions`) on the two Gold Data Marts for idempotent reruns.

**Tech Stack:** PySpark 3.5, Apache Iceberg (v2 format, ZSTD parquet), Apache Polaris REST catalog, Python 3.11, Apache Airflow 2.10.5 (with `pendulum` Asia/Ho_Chi_Minh timezone).

---

## 1. Table Definitions & Schemas

### 1.1. Fact Table: `lakehouse.gold.fact_web_events`

* **Table:** `lakehouse.gold.fact_web_events`
* **Grain:** 1 record per HTTP request/event.
* **Partitioning:** `PARTITIONED BY (days(event_ts))`
* **Columns:**

| Column | Type | Description |
|---|---|---|
| `event_id` | STRING | Unique event identifier (UUID hex) |
| `event_ts` | TIMESTAMP | Event timestamp in UTC |
| `event_date` | DATE | Derived date from event_ts |
| `actor_key` | STRING | Customer ID or anonymous visitor token |
| `actor_type` | STRING | Actor classification (`customer`, `anonymous`, `admin`) |
| `http_request_method` | STRING | HTTP verb (`GET`, `POST`, `PUT`, `DELETE`) |
| `http_route` | STRING | Normalized endpoint route (e.g. `/api/v1/products/{slug}`) |
| `http_status_code` | INT | HTTP response status code |
| `ecommerce_action` | STRING | Business action (`product_detail`, `cart_add`, `checkout_quote`, etc.) |
| `product_key` | STRING | Product master identifier |
| `variant_key` | STRING | Product variant identifier |
| `duration_ms` | DOUBLE | Request duration in milliseconds (`event_duration_ns / 1e6`) |
| `is_success` | BOOLEAN | True if HTTP status code < 400 |
| `is_client_error` | BOOLEAN | True if HTTP status code in [400, 499] |
| `is_server_error` | BOOLEAN | True if HTTP status code >= 500 |
| `is_slow_request` | BOOLEAN | True if duration_ms >= 1000.0 ms |
| `_gold_ingested_at` | TIMESTAMP | Processing timestamp in UTC |
| `_source_run_id` | STRING | Airflow DAG run ID |

---

### 1.2. Data Mart 1: `lakehouse.gold.mart_hourly_route_metrics`

* **Table:** `lakehouse.gold.mart_hourly_route_metrics`
* **Grain:** 1 record per `(metric_date, metric_hour, http_route, http_request_method)`.
* **Partitioning:** `PARTITIONED BY (metric_date)`
* **Columns:**

| Column | Type | Description |
|---|---|---|
| `metric_date` | DATE | Observation date |
| `metric_hour` | INT | Hour of day (0-23) |
| `http_route` | STRING | Normalized API endpoint route |
| `http_request_method` | STRING | HTTP method |
| `total_requests` | BIGINT | Total request count in hourly window |
| `success_2xx_count` | BIGINT | 2xx/3xx response count |
| `client_error_4xx_count` | BIGINT | 4xx response count |
| `server_error_5xx_count` | BIGINT | 5xx response count |
| `error_rate_pct` | DOUBLE | Overall error percentage: `(4xx + 5xx) / total * 100` |
| `avg_duration_ms` | DOUBLE | Average response duration in ms |
| `p50_duration_ms` | DOUBLE | 50th percentile (median) response duration in ms |
| `p95_duration_ms` | DOUBLE | 95th percentile response duration in ms |
| `p99_duration_ms` | DOUBLE | 99th percentile response duration in ms |
| `_gold_ingested_at` | TIMESTAMP | Ingestion timestamp |
| `_source_run_id` | STRING | Batch run ID |

---

### 1.3. Data Mart 2: `lakehouse.gold.mart_daily_product_demand`

* **Table:** `lakehouse.gold.mart_daily_product_demand`
* **Grain:** 1 record per `(metric_date, product_key)`.
* **Partitioning:** `PARTITIONED BY (metric_date)`
* **Columns:**

| Column | Type | Description |
|---|---|---|
| `metric_date` | DATE | Observation date |
| `product_key` | STRING | Product master key |
| `detail_view_count` | BIGINT | Product detail page views (`product_detail`) |
| `cart_add_count` | BIGINT | Add to cart events (`cart_add`) |
| `cart_remove_count` | BIGINT | Remove from cart events (`cart_remove`) |
| `wishlist_add_count` | BIGINT | Add to wishlist events (`wishlist_add`) |
| `checkout_quote_count` | BIGINT | Checkout quote events (`checkout_quote`) |
| `unique_visitors_count` | BIGINT | Count of distinct `actor_key`s interacting with product |
| `cart_to_view_rate_pct` | DOUBLE | `cart_add_count / detail_view_count * 100.0` (0 if view count is 0) |
| `_gold_ingested_at` | TIMESTAMP | Ingestion timestamp |
| `_source_run_id` | STRING | Batch run ID |

---

## 2. Airflow Orchestration

The pipeline runs inside `airflow/dags/lakehouse_logs_pipeline.py`:

```text
begin_run
   │
   ▼
[TaskGroup: staging_layer]
   ├── check_minio_landing
   └── discover_landing_logs
   │
   ▼
[TaskGroup: bronze_layer]
   └── ingest_logs_to_bronze (SparkSubmitOperator -> ingest_logs_to_bronze.py)
   │
   ▼
[TaskGroup: silver_layer]
   └── ingest_logs_to_silver (SparkSubmitOperator -> ingest_logs_silver.py)
   │
   ▼
[TaskGroup: gold_layer]
   └── build_logs_gold (SparkSubmitOperator -> build_logs_gold.py)
```

## 3. Spark CLI Execution

To run manually or backfill via Spark CLI:

```bash
docker compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  /opt/project/pipelines/src/jobs/logs/build_logs_gold.py \
  --run-id manual-gold-test-01 \
  --ingest-date 2026-08-31
```
