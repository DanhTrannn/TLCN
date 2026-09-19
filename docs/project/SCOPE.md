# System Scope and Specifications

This document defines the technical scope, boundaries, and acceptance criteria for the D&K E-Commerce Data Platform. The platform is a batch-oriented Data Lakehouse designed to process operational data and web access logs for Business Intelligence (BI) and machine learning (ML).

## 1. System Goals

The primary objective is to build a batch data lakehouse that extracts data from a MySQL OLTP database and structured access logs from an e-commerce API. This prevents analytical workloads from impacting operational performance. 

Key capabilities include:
- Incremental extraction using composite cursors `(cursor_field, pk)`.
- Micro-batch ingestion of rotated access logs (15-minute intervals).
- Medallion architecture (Bronze, Silver, Gold) using Apache Iceberg.
- Strict data quality, quarantine, and reconciliation gates.
- Idempotent pipelines supporting safe rerun, replay, and backfill.
- Dimensional modeling for Superset BI dashboards via Trino.
- Point-in-time feature engineering for customer repurchase prediction.

---

## 2. Data Sources and Boundaries

The platform ingests data from two official sources. Real-time event streaming (e.g., Kafka/Flink) and client-side telemetry are explicitly out of scope for the batch architecture.

### 2.1. MySQL OLTP Database
The system extracts data from **24 operational tables** (excludes `customer_credentials` which is strictly excluded):

**Core e-commerce tables (19):**
- `customers`, `categories`, `products`, `product_variants`
- `carts`, `cart_items`, `wishlist_items`
- `orders`, `order_items`, `order_status_history`
- `payments`, `refunds`
- `inventory`, `coupons`, `coupon_redemptions`, `product_reviews`
- `cities`, `stores`, `store_inventory`

**Omnichannel extension tables (5) — added in migration 0014:**
- `delivery_staff` — In-house shipper registry (D&K internal logistics team)
- `shipments` — Shipment lifecycle tracking per order
- `return_requests` — Customer return/exchange request headers
- `return_items` — Line-item detail for each return request
- `inventory_transactions` — Full inbound/outbound ledger for the central warehouse

**Strict Exclusion:** The `customer_credentials` table is strictly excluded to prevent password hashes and authentication secrets from entering the analytical environment.


### 2.2. Structured Access Logs
The backend API emits structured JSON logs on container stdout for every completed HTTP request.
- **Included Fields:** `request_id`, `timestamp`, `service`, `event.duration_ns`, `http.method`, `http.route`, `http.status_code`, `actor.type`, `actor.key`, `client.user_agent`, `ecommerce.action`, and sanitized `ecommerce.search_query`.
- **Ingestion Pattern:** Logs are buffered by Fluent Bit, flushed every 15 minutes, gzip-compressed, and uploaded to the MinIO Landing zone.
- **Privacy Rules:** Plaintext passwords, tokens, cookies, authorization headers, and raw IP addresses are stripped before ingestion.

---

## 3. Architecture Principles

1. **Source of Truth:** MySQL is the system of record for business transactions. Access logs are the system of record for HTTP request behavior.
2. **Read-Only Extraction:** The extraction process uses read-only accounts and short transaction cutoffs.
3. **Immutable Landing:** Landing zone files and Bronze tables are append-only.
4. **Idempotency:** Silver layer pipelines handle deduplication and state merging. Rerunning a pipeline with the same input yields the exact same logical state.
5. **Quality Gates:** Data is only published to the Gold layer after passing exact-match reconciliation checks (e.g., row counts, monetary amounts).
6. **Separation of Compute:** Spark handles all Iceberg writes. Trino handles all read queries from Apache Superset and LibreDB Studio. Transactional web APIs never communicate with Spark or Trino.

---

## 4. Lakehouse Design (Medallion Architecture)

### 4.1. Bronze Layer
- Acts as an immutable historical archive.
- Appends raw rows and log entries exactly as extracted from Landing.
- Enriches every row with technical lineage metadata: `_run_id`, `_source_file`, `_source_checksum`, `_ingested_at_utc`.
- Routes corrupt or unparseable files into a technical quarantine namespace.

### 4.2. Silver Layer
- Parses, types, and standardizes timestamps to UTC.
- Deduplicates rows based on primary keys or `request_id`.
- Performs UPSERT (`MERGE`) operations for mutable OLTP tables.
- Pseudonymizes customer identifiers and sensitive attributes.
- Isolates records violating business logic into semantic quarantine tables (`lakehouse.quarantine`).

### 4.3. Gold Layer
- Implements Star Schema dimensional modeling (Dimensions, Facts, and Marts).
- **Dimensions (6):** `dim_date`, `dim_customer`, `dim_product`, `dim_variant`, `dim_store`, `dim_delivery_staff`
- **Facts (5):** `fact_order`, `fact_order_item`, `fact_shipment`, `fact_return_exchange`, `fact_inventory_daily_snapshot`
- **Marts (4):** `mart_sales_daily`, `mart_logistics_performance`, `mart_product_returns`, `mart_inventory_health`

---

## 5. Key Performance Indicators (KPIs)

The BI dashboards report the following core metrics directly from the Gold layer:

- **Revenue Metrics:** Gross revenue, net revenue (after boom/returns), average order value (AOV), refund amounts.
- **Order Metrics:** Order counts by status (`paid`, `confirmed`, `shipping`, `delivered`, `completed`, `failed_delivery`, `returned`, `cancelled`), units sold per category.
- **Logistics Metrics:** Delivery success rate by shipper, average delivery time, COD boom rate by region.
- **Returns Metrics:** Return rate by product/size/reason, net revenue impact of returns.
- **Customer Metrics:** New customer acquisition, conversion rates, and historical repurchase rates.
- **Inventory Metrics:** Current on-hand quantity per variant per store, low-stock alerts, slow-moving items, days-of-inventory.
- **Traffic Metrics:** Total request volume, latency percentiles (p50/p95/p99), error rates (4xx/5xx), and top product search keywords.


---

## 6. Machine Learning (Repurchase Prediction)

The platform generates features and labels for predicting whether a returning customer will make at least one successful purchase within the next 30 days.

- **Data Boundaries:** The model only uses features derived from the OLTP Gold layer. Access logs are excluded from the primary model to avoid identity resolution bias.
- **Features:** RFM (Recency, Frequency, Monetary), average basket value, category diversity, customer tenure, and wishlist/cart engagement.
- **Point-in-Time Correctness:** Features are strictly computed using data available at or before the cutoff timestamp (`as_of_time`) to eliminate target leakage.

---

## 7. Operations and Maintenance

### 7.1. Reconciliation Gates
The pipeline enforces strict reconciliation checks at each layer transition:
- Source row counts must match Bronze accepted rows.
- Source monetary totals must exactly match Gold revenue facts.
- Bronze distinct `request_id` counts must match Silver log deduplicated counts.

### 7.2. Table Maintenance
Airflow runs scheduled DAGs to maintain Iceberg table health:
- Tracks small-file metrics, average file sizes, and snapshot counts.
- Triggers compaction (data file rewrites) only when configurable thresholds are exceeded.
- Removes orphan files and expires snapshots older than the required backfill window.
- Guarantees that maintenance operations never alter logical row counts or checksums.
