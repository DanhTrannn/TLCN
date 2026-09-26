# Technical Design Specification: Apache ECharts Visualization Suite with Trino Lakehouse DWH

- **Date:** 2026-09-26
- **Status:** Approved
- **Target Branch:** `dev`
- **Scope:** Full migration from Apache Superset to native Apache ECharts on Next.js Storefront, sourced 100% from Data Engineering (DE) Data Marts and DWH via Trino.

---

## 1. Executive Summary & Goals

### 1.1 Problem Statement
Previously, the project relied on Apache Superset (`http://localhost:8088`) as an external BI portal, with minimal client-side HTML progress bars on `/admin/analytics`. The user has decided to eliminate Apache Superset entirely from the workflow. Instead, the operational and strategic BI dashboards must be natively embedded into the Next.js Storefront using **Apache ECharts** as the primary visualization engine, with 100% of analytical metrics and time-series trends retrieved directly from the **Data Engineering (DE) Lakehouse Data Marts (`lakehouse.gold.*`) via the Trino Distributed SQL Query Engine**.

### 1.2 Key Objectives
1. **Drop Apache Superset**: Remove all Superset launchers, banners, external links, and backend `/superset-config` endpoints.
2. **Native Apache ECharts Suite**: Install `echarts` in `apps/storefront` and build a robust, modular, tree-shakable React 19 Client Component wrapper (`EChart.tsx`) with automatic `ResizeObserver` responsiveness and custom brand theme palette (`ink`, `accent`, `moss`, `sand`).
3. **Pure Trino Lakehouse Query Engine**: Build `TrinoClient` in FastAPI (`services/ecommerce-api`) to execute analytical queries directly against Trino Coordinator (`http://trino:8080/v1/statement`) accessing `lakehouse.gold.*` (e.g. `mart_sales_daily`, `mart_logistics_performance`, `mart_inventory_health`, `mart_product_returns`).
4. **Rich Multi-Role ECharts Dashboards**: Implement specialized, interactive ECharts across all 7 operational roles in `/admin/analytics`:
   - **Executive**: Dual-axis Bar & Line Chart (Revenue + COGS vs Gross Profit) with `dataZoom`, Donut Chart (Order status breakdown).
   - **Sales**: Donut Chart (Category Revenue Share), Horizontal Bar Chart (Top Selling Products), Bar Chart (Store contributions).
   - **Marketing**: Funnel Chart (E-commerce conversion funnel: View -> Add to Cart -> Checkout -> Purchase).
   - **Store**: Gauge Chart (Daily sales target achievement %), Daily store performance Bar Chart.
   - **Inventory**: Stacked Bar Chart (Warehouse vs Store inventory asset allocation).
   - **Operations**: Donut Chart (Delivered vs Boom / Failed Delivery rate), Logistics SLA & COD Bar Chart.
   - **System**: Lakehouse Cluster Health Widget (Trino connectivity, Iceberg freshness, Reconciliation Variance = 0đ).
5. **Gold Mart DDL & Data Population**: Ensure Lakehouse Gold Mart tables exist in Iceberg and have active dimensional data accessible via Trino.

---

## 2. Architecture & Data Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Next.js Storefront                              │
│                  (/admin/analytics & Admin Portal)                     │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                 Apache ECharts React 19 Suite                  │   │
│   │   [Dual-Axis Trend] [Category Donut] [Marketing Funnel]        │   │
│   │   [Target Gauge]   [Inventory Stacked Bar] [Boom Rate Donut]   │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
└────────────────────────────────────┼───────────────────────────────────┘
                                     │ HTTP REST
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend API                               │
│              (/api/v1/admin/analytics/role-metrics & sales-trend)     │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │          Role-Based Access Control (RBAC & RLS) Gate           │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
│                                    │                                   │
│   ┌────────────────────────────────▼───────────────────────────────┐   │
│   │               Trino Lakehouse DWH Client                       │   │
│   │      (HTTP /v1/statement, Catalog: lakehouse, Schema: gold)   │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
└────────────────────────────────────┼───────────────────────────────────┘
                                     │ SQL Queries
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       Trino Query Engine                               │
│                     (Port 8080 / 8084 Coordinator)                     │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                 Apache Iceberg REST Catalog                    │   │
│   │                      (Apache Polaris)                          │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
│                                    │ Storage (S3 API)                  │
│                                    ▼                                   │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │             MinIO Object Storage (`lakehouse/warehouse`)       │   │
│   │                                                                │   │
│   │   Gold Marts:                                                  │   │
│   │   - lakehouse.gold.mart_sales_daily                            │   │
│   │   - lakehouse.gold.mart_logistics_performance                  │   │
│   │   - lakehouse.gold.mart_inventory_health                       │   │
│   │   - lakehouse.gold.mart_product_returns                        │   │
│   │   - lakehouse.gold.fact_order, fact_order_item                 │   │
│   │   - lakehouse.gold.dim_product, dim_store, dim_customer        │   │
│   └────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Component Specifications

### 3.1 Backend DWH Service (`services/ecommerce-api`)

#### File: `app/modules/analytics/trino_client.py`
- Connects to Trino Coordinator via HTTP POST to `/v1/statement`.
- Configuration:
  - `API_TRINO_URL`: defaults to `http://trino:8080` (container network) or `http://localhost:8084` (local).
  - Headers:
    - `X-Trino-User: admin`
    - `X-Trino-Catalog: lakehouse`
    - `X-Trino-Schema: gold`
- Handles Trino query lifecycle:
  1. POST query statement.
  2. Follow `nextUri` asynchronously / synchronously until `state` is `FINISHED` or `FAILED`.
  3. Extract `columns` and `data` rows into Python `list[dict[str, Any]]`.
- Error handling: raises clear `AppError(INTERNAL_SERVER_ERROR, "Trino query execution failed")` if SQL fails or Trino is unreachable.

#### File: `app/modules/analytics/service.py`
Refactor all analytics aggregations to execute Trino SQL queries against `lakehouse.gold.*`:

1. `get_executive_metrics()`:
   - Queries `lakehouse.gold.mart_sales_daily` for GMV, Net Revenue, COGS, Gross Profit, and Gross Margin %.
   - Queries `lakehouse.gold.mart_logistics_performance` for Boom rate % and count.
2. `get_sales_metrics()`:
   - Queries `lakehouse.gold.mart_sales_daily` for Category Shares (`category_name`, revenue).
   - Queries `lakehouse.gold.mart_sales_daily` for Store Contributions (`store_key`, revenue).
   - Queries `lakehouse.gold.fact_order_item` joined with `lakehouse.gold.dim_product` for Top 5 Selling Products.
3. `get_store_metrics(store_id)`:
   - Queries `lakehouse.gold.mart_sales_daily` filtered by `store_key = :store_id` and `order_date = current_date`.
4. `get_inventory_metrics()`:
   - Queries `lakehouse.gold.mart_inventory_health` for total valuation, warehouse vs store units, out of stock, and low stock counts.
5. `get_operations_metrics()`:
   - Queries `lakehouse.gold.mart_logistics_performance` and `lakehouse.gold.mart_product_returns` for delivery rate, boom rate, return requests, and total COD collected.
6. `get_marketing_metrics()`:
   - Computes funnel steps (Views -> Cart -> Checkout -> Purchase) using customer and order counts.
7. `get_system_metrics()`:
   - Validates Trino coordinator status (`/v1/info`), Lakehouse gold tables presence, and reports reconciliation variance.
8. `get_sales_trend(days)`:
   - Queries `lakehouse.gold.mart_sales_daily` grouped by `order_date` for the requested time window.

#### Removal of Superset:
- Remove `SupersetConfigResponse` from `app/modules/analytics/schemas.py`.
- Remove `/superset-config` route from `app/modules/analytics/router.py`.

### 3.2 Frontend Apache ECharts Integration (`apps/storefront`)

#### Dependency:
- `echarts`: installed via `npm --prefix apps/storefront install echarts`.

#### File: `apps/storefront/src/components/ui/EChart.tsx`
- Client Component (`"use client"`).
- Tree-shaking imports from `echarts/core`:
  - Charts: `BarChart`, `LineChart`, `PieChart`, `FunnelChart`, `GaugeChart`.
  - Components: `TitleComponent`, `TooltipComponent`, `GridComponent`, `LegendComponent`, `ToolboxComponent`, `DataZoomComponent`.
  - Renderer: `CanvasRenderer`.
- Features:
  - Wrapped with `ResizeObserver` for zero-flicker dynamic resizing.
  - Native cleanup on unmount with `chartInstance.dispose()`.
  - Supports loading state overlay.
  - Custom color palette: `#152722` (ink), `#a94728` (accent), `#315b4f` (moss), `#8b5b16` (warning), `#a63f3b` (danger), `#dcd8cf` (line).

#### File: `apps/storefront/src/app/admin/analytics/page.tsx`
- Delete the Apache Superset Studio banner and launcher button.
- Integrate interactive ECharts for all 7 role tabs:
  1. **Executive Tab**:
     - Dual-Axis Bar & Line Chart: Bar 1 (Net Revenue), Bar 2 (COGS), Line (Gross Profit) with dynamic `dataZoom` slider and formatted tooltip in VND.
     - Donut Chart: Order fulfillment status breakdown (Delivered vs Shipping vs Boom).
  2. **Sales Tab**:
     - Donut Chart: Category Revenue Share with rich legends and hover percentages.
     - Horizontal Bar Chart: Top 5 products by revenue.
     - Column Bar Chart: Store revenue contributions.
  3. **Marketing Tab**:
     - Funnel Chart: Visual drop-off funnel from Product Page View -> Add to Cart -> Checkout -> Order Complete.
  4. **Store Tab**:
     - Gauge Chart: Store daily sales target achievement % with color gradations (rose < 50%, amber 50-80%, emerald > 80%).
     - Bar Chart: Daily store sales and order volume.
  5. **Inventory Tab**:
     - Stacked Bar Chart: Stock allocation across Central Warehouse vs Store Locations, highlighting Low Stock & Stockout items.
  6. **Operations Tab**:
     - Donut Chart: Shipper Delivery Success vs Boom Rate %.
     - Bar Chart: COD Collections and transit metrics.
  7. **System Tab**:
     - Lakehouse Data Pipeline Health & Trino SLA Status Widget.

---

## 4. Lakehouse Gold Marts Data Provisioning

To enable Trino to execute queries immediately without waiting for overnight batch schedules:
- Run DDL script `ensure_oltp_gold_tables` to define all tables in `lakehouse.gold.*`.
- Execute a Python seeding script or batch run populating initial representative data into `mart_sales_daily`, `mart_logistics_performance`, and `mart_inventory_health`.

---

## 5. Testing & Verification Plan

1. **Backend Tests**:
   - Write unit and integration tests in `services/ecommerce-api/tests/test_analytics_trino_dwh.py`.
   - Test Trino query generation, statement polling, and result transformation.
   - Run full pytest suite (192+ tests) ensuring 0 regressions.
2. **Frontend Typecheck & Build**:
   - `npm --prefix apps/storefront run typecheck` (0 errors).
   - `npm --prefix apps/storefront run build` (all 27 routes compiled cleanly).
3. **End-to-End Visual Verification**:
   - Open `/admin/analytics` and verify all 7 role tabs render interactive ECharts with live data fetched via Trino.
