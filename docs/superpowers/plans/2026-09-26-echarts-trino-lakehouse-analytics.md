# Native Apache ECharts Suite with Trino Lakehouse DWH Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Completely replace Apache Superset with native Apache ECharts in the Next.js Storefront, sourcing 100% of analytical metrics and visualizations directly from the Data Engineering (DE) Lakehouse Data Marts via the Trino query engine.

**Architecture:** A FastAPI Trino client (`app/modules/analytics/trino_client.py`) executes SQL statements against the Trino Coordinator (`http://trino:8080/v1/statement` with catalog `lakehouse`, schema `gold`). The analytics service queries `lakehouse.gold.mart_sales_daily`, `mart_logistics_performance`, `mart_inventory_health`, and `mart_product_returns`. On the frontend, a responsive React 19 Client Component (`EChart.tsx`) powers high-performance Canvas/SVG visualizations across all 7 operational roles in `/admin/analytics`. All Superset configurations, endpoints, and banners are removed.

**Tech Stack:** Next.js 15, React 19, TypeScript, Apache ECharts 5, FastAPI, Trino 483, Apache Iceberg, Apache Polaris REST Catalog, MinIO.

**Spec:** `docs/superpowers/specs/2026-09-26-echarts-trino-lakehouse-analytics-design.md`

## Global Constraints

- 100% pure Trino Lakehouse DWH query pipeline for `/admin/analytics` endpoints (no OLTP fallback).
- ECharts integration must be compatible with React 19 and Next.js App Router SSR (using `"use client"`, `useRef`, and `ResizeObserver`).
- Zero remnants of Apache Superset in code (remove `/superset-config` route, schemas, and UI banners).
- Preserve strict RBAC: non-admin roles can only access their authorized domain data; `store_manager` is scoped to their assigned `store_id`.
- Zero regressions across existing backend and frontend test suites.

---

### Task 1: Lakehouse Gold Mart DDL & Seed Provisioning for Trino

**Files:**
- Create: `pipelines/src/jobs/oltp/init_and_seed_gold.py`
- Test: `pipelines/tests/test_gold_marts_provisioning.py`

**Interfaces:**
- Produces: Lakehouse Iceberg Gold tables (`mart_sales_daily`, `mart_logistics_performance`, `mart_inventory_health`, `mart_product_returns`) populated with initial rows accessible by Trino SQL queries.

- [ ] **Step 1: Write integration test verifying Trino can query Gold Marts**
- [ ] **Step 2: Run test to verify failure before tables are populated**
- [ ] **Step 3: Implement `init_and_seed_gold.py` to ensure Gold DDL in Iceberg and insert representative seed rows**
- [ ] **Step 4: Execute `init_and_seed_gold.py` via Spark/Trino and verify query results with `docker compose exec trino trino --execute "SELECT COUNT(*) FROM lakehouse.gold.mart_sales_daily;"`**
- [ ] **Step 5: Run tests to verify PASS**
- [ ] **Step 6: Commit:** `feat(pipelines): provision and seed lakehouse gold data marts for trino queries`

---

### Task 2: Backend Trino DWH Client (`trino_client.py`) & Unit Tests

**Files:**
- Create: `services/ecommerce-api/app/modules/analytics/trino_client.py`
- Test: `services/ecommerce-api/tests/test_trino_client.py`

**Interfaces:**
- Produces: `TrinoClient.execute_query(sql: str, params: dict | None = None) -> list[dict[str, Any]]` and `TrinoClient.execute_scalar(sql: str) -> Any`
- Consumes: `API_TRINO_URL` env config (default: `http://trino:8080`, fallback for local test: `http://localhost:8084`)

- [ ] **Step 1: Write unit and mock integration tests in `test_trino_client.py`**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement `TrinoClient` using `httpx` to POST statements to `/v1/statement` with headers `X-Trino-User: admin`, `X-Trino-Catalog: lakehouse`, `X-Trino-Schema: gold` and resolve `nextUri` polling**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit:** `feat(analytics): implement Trino REST query client for lakehouse DWH access`

---

### Task 3: Backend Analytics Service Pure Trino Migration & Remove Superset

**Files:**
- Modify: `services/ecommerce-api/app/modules/analytics/service.py`
- Modify: `services/ecommerce-api/app/modules/analytics/schemas.py`
- Modify: `services/ecommerce-api/app/modules/analytics/router.py`
- Modify: `services/ecommerce-api/tests/test_analytics_rbac_api.py`

**Interfaces:**
- Produces: `get_role_metrics(actor, target_role, store_id)` and `get_sales_trend(actor, days)` backed 100% by Trino SQL queries.
- Removes: `SupersetConfigResponse` schema and `GET /superset-config` endpoint.

- [ ] **Step 1: Write integration tests asserting metrics are sourced from Trino Gold Marts and 404 for removed Superset endpoint**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Update `service.py` to execute Trino SQL against `mart_sales_daily`, `mart_logistics_performance`, `mart_inventory_health`, and `mart_product_returns`**
- [ ] **Step 4: Remove `SupersetConfigResponse` and `/superset-config` endpoint from `schemas.py` and `router.py`**
- [ ] **Step 5: Run tests and full pytest suite to verify all pass**
- [ ] **Step 6: Commit:** `feat(analytics): migrate role metrics service to pure Trino queries and remove Superset`

---

### Task 4: Frontend Apache ECharts Package & Base Component (`EChart.tsx`)

**Files:**
- Modify: `apps/storefront/package.json`
- Create: `apps/storefront/src/components/ui/EChart.tsx`
- Test: Storefront typecheck `npm --prefix apps/storefront run typecheck`

**Interfaces:**
- Produces: `<EChart option={EChartsOption} height={number | string} loading={boolean} className={string} />`

- [ ] **Step 1: Install `echarts` in `apps/storefront`**
- [ ] **Step 2: Implement `apps/storefront/src/components/ui/EChart.tsx` with `"use client"`, tree-shaking `echarts/core`, `ResizeObserver`, and brand palette**
- [ ] **Step 3: Run `npm --prefix apps/storefront run typecheck` to verify 0 errors**
- [ ] **Step 4: Commit:** `feat(storefront): add EChart wrapper component with React 19 and ResizeObserver support`

---

### Task 5: Frontend Role-Based BI Hub ECharts Suite (`/admin/analytics`)

**Files:**
- Modify: `apps/storefront/src/app/admin/analytics/page.tsx`
- Modify: `apps/storefront/src/lib/api.ts` & `commerce.ts`

**Interfaces:**
- Consumes: `<EChart />`, `getAdminRoleMetrics()`, `getAdminSalesTrend()`
- Produces: Interactive ECharts across all 7 role tabs:
  1. Executive: Dual-Axis Bar & Line Chart + Donut Status Breakdown.
  2. Sales: Category Donut + Top Products Horizontal Bar + Store Revenue Bar.
  3. Marketing: Funnel Conversion Chart.
  4. Store: Daily Target Gauge Chart + Sales Volume Bar.
  5. Inventory: Warehouse vs Store Stacked Bar.
  6. Operations: Shipper Boom Rate Donut + Logistics SLA Bar.
  7. System: Trino & Lakehouse Health Status.
- Removes: Superset launcher banner and client `getSupersetConfig()` call.

- [ ] **Step 1: Clean up Superset types and API functions from `commerce.ts` and `api.ts`**
- [ ] **Step 2: Replace Superset banner and static progress bars in `/admin/analytics/page.tsx` with specialized ECharts for all 7 role tabs**
- [ ] **Step 3: Run `npm --prefix apps/storefront run typecheck` and `npm --prefix apps/storefront run build`**
- [ ] **Step 4: Commit:** `feat(storefront): implement interactive ECharts visualizer suite across all 7 role dashboards`

---

### Task 6: End-to-End System Verification & Final Polish

**Files:**
- Test: Full system test across backend and frontend

- [ ] **Step 1: Restart `tlcn-ecommerce-api-1` and verify live and ready health endpoints**
- [ ] **Step 2: Run full backend pytest suite (`uv run ... pytest services/ecommerce-api/tests`)**
- [ ] **Step 3: Run storefront production build (`npm --prefix apps/storefront run build`)**
- [ ] **Step 4: Test live query against Trino and verify charts render properly in browser**
- [ ] **Step 5: Commit any final refinements:** `chore(analytics): finalize Trino ECharts integration and verification`
