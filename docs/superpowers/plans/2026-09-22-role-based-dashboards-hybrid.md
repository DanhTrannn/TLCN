# Hybrid Role-Based Dashboards & Lakehouse Reporting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Triển khai Gói 4: Hệ thống Báo cáo Quản trị Theo Vai Trò (Hybrid Role-Based Dashboards) kết hợp Headless API truy vấn Data Marts tức thời và Trung tâm Báo cáo BI Chuyên sâu 7 Roles, đồng bộ hóa Lakehouse Data Pipeline và script sinh dữ liệu demo đồ án.

**Architecture:** Kiến trúc 2 tầng (Hybrid): Tầng 1 phục vụ các thẻ KPI tài chính và vận hành thời gian thực trên Web (`/admin`, `/store`) thông qua FastAPIs truy vấn pre-aggregated Gold Marts / OLTP fallback; Tầng 2 là Trung tâm Báo cáo BI `/admin/analytics` gồm 7 Tabs theo 7 Roles nghiệp vụ chuẩn hóa từ `BUSINESS_DOMAIN.md`, áp dụng phân quyền RBAC 2 lớp (chặn 403 ở Backend và ẩn tab trái phép ở Frontend), tích hợp nút mở Apache Superset Studio.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0, PySpark 3.5, Apache Iceberg, Next.js 15 (App Router), Tailwind CSS, TypeScript.

**Spec:** `docs/superpowers/specs/2026-09-22-role-based-dashboards-hybrid-design.md`

## Global Constraints

- Backend APIs under `/api/v1/admin/analytics/` and `/api/v1/admin/overview`.
- RBAC enforcement: `admin` has full access across all 7 roles and stores; department roles (`store_manager`, `marketing_manager`, `inventory_manager`, `operations_manager`, `sales_manager`, `system_admin`) can only access their authorized domain; unauthorized requests return HTTP 403 Forbidden.
- Row-Level Security for `store_manager`: queries are strictly scoped to `actor.store_id`.
- Data Pipeline: `pipelines/config/default.yml` ingests `inbound_receipts` and `inbound_receipt_items`.
- Gold Mart `mart_sales_daily` includes `cogs_vnd`, `gross_profit_vnd`, `gross_profit_margin_pct`.
- Zero regression on existing 161 backend tests and 26 storefront routes.

---

### Task 1: Backend Financial Metrics Extension in `get_overview`

**Files:**
- Modify: `services/ecommerce-api/app/modules/admin/schemas.py:15-32`
- Modify: `services/ecommerce-api/app/modules/admin/service.py:75-115`
- Test: `services/ecommerce-api/tests/test_admin_financial_overview.py`

**Interfaces:**
- Consumes: `OrderItem.cost_price_vnd`, `OrderItem.quantity`, `Order.status`, `Payment`, `Refund`.
- Produces: `AdminOverviewResponse` extended with `cogs_vnd: int`, `gross_profit_vnd: int`, `gross_margin_percent: float`, `boom_orders_count: int`, `return_orders_count: int`.

- [ ] **Step 1: Write integration tests in `services/ecommerce-api/tests/test_admin_financial_overview.py`**

Test scenarios:
1. `GET /api/v1/admin/overview` returns `cogs_vnd`, `gross_profit_vnd`, `gross_margin_percent`, `boom_orders_count`, `return_orders_count`.
2. Verifies that `cogs_vnd` sums `quantity * cost_price_vnd` for orders with status `delivered` or `completed`.
3. Verifies that orders with status `cancelled` or `payment_failed` are excluded from COGS.
4. Verifies that `gross_profit_vnd = net_revenue_vnd - cogs_vnd`.
5. Verifies that `boom_orders_count` accurately counts orders with status `failed_delivery`.

```python
from datetime import datetime, timezone
import pytest
from sqlalchemy import select
from app.models.catalog import Product, ProductVariant
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.payment import Payment

def test_admin_overview_financial_metrics(admin_client, test_db):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # Verify response schema contains new financial metrics
    res = admin_client.get("/api/v1/admin/overview")
    assert res.status_code == 200
    data = res.json()
    assert "cogs_vnd" in data
    assert "gross_profit_vnd" in data
    assert "gross_margin_percent" in data
    assert "boom_orders_count" in data
    assert "return_orders_count" in data
```

- [ ] **Step 2: Run test to verify failure (RED)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_admin_financial_overview.py -v`
Expected: FAIL (KeyError or missing fields in `AdminOverviewResponse`).

- [ ] **Step 3: Implement financial metric aggregation in `schemas.py` and `service.py`**

In `services/ecommerce-api/app/modules/admin/schemas.py`:
```python
class AdminOverviewResponse(BaseModel):
    active_products: int
    active_variants: int
    low_stock_variants: int
    customers: int
    paid_orders: int
    confirmed_orders: int
    completed_orders: int
    cancelled_orders: int
    total_reviews: int
    active_coupons: int
    gross_revenue_vnd: int
    refunded_amount_vnd: int
    net_revenue_vnd: int
    cogs_vnd: int = 0
    gross_profit_vnd: int = 0
    gross_margin_percent: float = 0.0
    boom_orders_count: int = 0
    return_orders_count: int = 0
```

In `services/ecommerce-api/app/modules/admin/service.py`:
```python
    # COGS for fulfilled/delivered orders
    cogs_vnd = db.scalar(
        select(func.coalesce(func.sum(OrderItem.quantity * OrderItem.cost_price_vnd), 0))
        .join(Order, Order.order_id == OrderItem.order_id)
        .where(Order.status.in_(("delivered", "completed")))
    ) or 0

    net_rev = int(gross_revenue) - int(refunded_amount)
    gross_profit = net_rev - int(cogs_vnd)
    gross_margin = round((gross_profit / net_rev) * 100, 1) if net_rev > 0 else 0.0

    boom_count = order_counts.get("failed_delivery", 0)
    return_count = order_counts.get("returned", 0)
```

- [ ] **Step 4: Run test to verify it passes (GREEN)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_admin_financial_overview.py -v`
Expected: PASS

- [ ] **Step 5: Run full backend test suite to ensure 0 regression**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests`
Expected: All 162+ tests pass.

- [ ] **Step 6: Commit**

```bash
git add services/ecommerce-api/app/modules/admin/schemas.py services/ecommerce-api/app/modules/admin/service.py services/ecommerce-api/tests/test_admin_financial_overview.py
git commit -m "feat(admin): extend overview API with COGS, gross profit, and margin metrics"
```

---

### Task 2: Backend Analytics Module with RBAC & Role Metrics

**Files:**
- Create: `services/ecommerce-api/app/modules/analytics/__init__.py`
- Create: `services/ecommerce-api/app/modules/analytics/schemas.py`
- Create: `services/ecommerce-api/app/modules/analytics/service.py`
- Create: `services/ecommerce-api/app/modules/analytics/router.py`
- Modify: `services/ecommerce-api/app/api/router.py`
- Test: `services/ecommerce-api/tests/test_analytics_rbac_api.py`

**Interfaces:**
- Consumes: `Customer.role`, `Customer.store_id`, `Order`, `OrderItem`, `InboundReceipt`, `Inventory`.
- Produces:
  - `GET /api/v1/admin/analytics/overview`
  - `GET /api/v1/admin/analytics/role-metrics?target_role=...&store_id=...`
  - `GET /api/v1/admin/analytics/sales-trend?days=30`
  - `GET /api/v1/admin/analytics/superset-config`

- [ ] **Step 1: Write integration tests in `services/ecommerce-api/tests/test_analytics_rbac_api.py`**

Test scenarios:
1. `admin` can access `GET /api/v1/admin/analytics/role-metrics?target_role=executive` (200 OK).
2. `admin` can access any role (`sales`, `marketing`, `store`, `inventory`, `operations`, `system`).
3. Non-admin user (e.g. `store_manager`) accessing `target_role=executive` receives HTTP 403 Forbidden.
4. `store_manager` accessing their assigned `store_id` receives 200 OK.
5. `store_manager` attempting to query a different `store_id` receives HTTP 403 Forbidden.
6. `GET /api/v1/admin/analytics/sales-trend` returns daily time series of revenue, cogs, and profit.
7. `GET /api/v1/admin/analytics/superset-config` returns Superset status and URL.

- [ ] **Step 2: Run test to verify failure (RED)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_analytics_rbac_api.py -v`
Expected: FAIL (404 Not Found / module not implemented).

- [ ] **Step 3: Implement `schemas.py`, `service.py`, and `router.py` in `modules/analytics/`**

1. `schemas.py`:
   - `ExecutiveMetricsResponse`: GMV, Net Revenue, COGS, Gross Profit, Gross Margin, Orders, AOV, Boom Rate, Return Rate.
   - `SalesMetricsResponse`: Store Contributions, Top Selling Products, Category Share.
   - `MarketingMetricsResponse`: Funnel Steps (Views, Add to Cart, Checkout, Purchase), Conversion Rate.
   - `StoreMetricsResponse`: Store Revenue Today, Store Orders, Target Achievement, Low Stock at Store.
   - `InventoryMetricsResponse`: Total Inventory Value, Warehouse vs Store Stock, Inbound Batches Count, Stockout Count.
   - `OperationsMetricsResponse`: Pending Fulfillment, Shipping SLA Violations, Boom Orders, Return Requests.
   - `SystemMetricsResponse`: Pipeline Status, Data Freshness SLA, Reconciliation Variance.
   - `DailySalesTrendPoint`: Date, Revenue, COGS, Profit, Orders Count.
   - `SupersetConfigResponse`: Superset URL, Enabled status, Guest token support.

2. `service.py`:
   - Enforce RBAC validation:
     ```python
     def validate_role_access(actor: Customer, target_role: str, store_id: int | None = None) -> None:
         if actor.role == "admin":
             return
         if actor.role != target_role:
             raise AppError(FORBIDDEN, "Bạn không có quyền truy cập dữ liệu của vai trò này.", status_code=403)
         if actor.role == "store_manager":
             if store_id is not None and store_id != actor.store_id:
                 raise AppError(FORBIDDEN, "Bạn chỉ được phép xem dữ liệu cửa hàng do mình phụ trách.", status_code=403)
     ```
   - Implement queries for role metrics with OLTP fallback (and Trino hook when active).

3. `router.py`:
   - Mount endpoints under `/admin/analytics` with `get_current_admin` / `get_current_staff` dependencies.

4. Mount in `services/ecommerce-api/app/api/router.py`.

- [ ] **Step 4: Run test to verify it passes (GREEN)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_analytics_rbac_api.py -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests`
Expected: All tests pass cleanly.

- [ ] **Step 6: Commit**

```bash
git add services/ecommerce-api/app/modules/analytics/ services/ecommerce-api/app/api/router.py services/ecommerce-api/tests/test_analytics_rbac_api.py
git commit -m "feat(analytics): implement role-based analytics API with strict RBAC security gate"
```

---

### Task 3: Data Pipeline Lakehouse Ingestion Configuration & Marts Verification

**Files:**
- Modify: `pipelines/config/default.yml`
- Modify: `pipelines/src/lakehouse/oltp/gold.py` (ensure COGS & profit calculation parity)
- Test: `pipelines/tests/test_financial_gold_marts.py`

**Interfaces:**
- Consumes: MySQL tables (`inbound_receipts`, `inbound_receipt_items`), Silver tables (`silver_orders`, `silver_order_items`, `silver_product_variants`).
- Produces: `mart_sales_daily` with validated `cogs_vnd`, `gross_profit_vnd`, `gross_profit_margin_pct`.

- [ ] **Step 1: Write unit test in `pipelines/tests/test_financial_gold_marts.py`**

Test scenario:
- Creates mock DataFrames for `silver_orders`, `silver_order_items`, `silver_product_variants`.
- Runs `build_fact_order`, `build_fact_order_item`, and `build_mart_sales_daily`.
- Verifies that:
  - `fact_order.total_cost_vnd` equals sum of `quantity * cost_price_vnd`.
  - `fact_order.gross_profit_vnd = gross_revenue_vnd - total_cost_vnd`.
  - `mart_sales_daily.cogs_vnd` and `gross_profit_margin_pct` calculate correctly.

- [ ] **Step 2: Run test to verify status**

Run: `pytest pipelines/tests/test_financial_gold_marts.py -v`
Expected: PASS or FAIL if mock fields are missing.

- [ ] **Step 3: Update `pipelines/config/default.yml`**

Add `inbound_receipts` and `inbound_receipt_items` configuration blocks:
```yaml
  - name: inbound_receipts
    cursor_field: updated_at
    pk: receipt_id
    mutability: mutable
    silver_table: silver_inbound_receipts
  - name: inbound_receipt_items
    cursor_field: created_at
    pk: item_id
    mutability: append_only
    silver_table: silver_inbound_receipt_items
```

- [ ] **Step 4: Run pipeline tests**

Run: `pytest pipelines/tests/`
Expected: All pipeline tests pass.

- [ ] **Step 5: Commit**

```bash
git add pipelines/config/default.yml pipelines/src/lakehouse/oltp/gold.py pipelines/tests/test_financial_gold_marts.py
git commit -m "feat(pipelines): register inbound tables and verify financial Gold Mart calculations"
```

---

### Task 4: Comprehensive Seed & Demo Scenarios Script

**Files:**
- Create: `database/seeds/seed_demo_scenarios.py`
- Test: `services/ecommerce-api/tests/test_demo_scenarios_seed.py`

**Interfaces:**
- Consumes: MySQL database models (`Customer`, `Product`, `ProductVariant`, `InboundReceipt`, `Order`, `OrderItem`, `Payment`, `Shipment`, `ReturnRequest`).
- Produces: Executable seed script that populates realistic time-series data across all 7 business domains.

- [ ] **Step 1: Write test verifying seed script execution**

In `services/ecommerce-api/tests/test_demo_scenarios_seed.py`:
- Run `seed_demo_data(test_db)`.
- Assert that database contains:
  - Inbound receipts with recalculated variant cost prices.
  - Delivered orders with `cost_price_vnd > 0`.
  - Failed delivery (boom) shipments.
  - Completed returns with refund transactions.
  - Customer review and coupon redemptions.

- [ ] **Step 2: Run test to verify failure (RED)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_demo_scenarios_seed.py -v`
Expected: FAIL (seed function not defined).

- [ ] **Step 3: Implement `seed_demo_scenarios.py`**

Implement deterministic seed function:
- Generates 3 inbound batches (updating moving weighted cost).
- Generates 25+ orders spanning the past 14 days:
  - 15 delivered online orders.
  - 5 completed POS store orders.
  - 3 failed delivery (boom) orders.
  - 2 customer return requests (1 completed with refund).
- Ensures exact mathematical integrity between Order, OrderItem, Payment, Refund, and InventoryTransaction.

- [ ] **Step 4: Run test to verify it passes (GREEN)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_demo_scenarios_seed.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add database/seeds/seed_demo_scenarios.py services/ecommerce-api/tests/test_demo_scenarios_seed.py
git commit -m "feat(seeds): add comprehensive demo scenarios seed script for multi-role reporting"
```

---

### Task 5: Storefront Dashboard Enhancements (`/admin` & `/store`)

**Files:**
- Modify: `apps/storefront/src/lib/api.ts` & `commerce.ts`
- Modify: `apps/storefront/src/app/admin/page.tsx`
- Modify: `apps/storefront/src/app/store/page.tsx`

**Interfaces:**
- Consumes: Updated `AdminOverview` with `cogs_vnd`, `gross_profit_vnd`, `gross_margin_percent`, `boom_orders_count`, `return_orders_count`.
- Produces: Enhanced UI cards with compact VND formatting, gross margin badges, and operational alert counters.

- [ ] **Step 1: Update `AdminOverview` in `api.ts` and `commerce.ts`**

```typescript
export interface AdminOverview {
  active_products: number;
  active_variants: number;
  low_stock_variants: number;
  customers: number;
  paid_orders: number;
  confirmed_orders: number;
  completed_orders: number;
  cancelled_orders: number;
  total_reviews: number;
  active_coupons: number;
  gross_revenue_vnd: number;
  refunded_amount_vnd: number;
  net_revenue_vnd: number;
  cogs_vnd?: number;
  gross_profit_vnd?: number;
  gross_margin_percent?: number;
  boom_orders_count?: number;
  return_orders_count?: number;
}
```

- [ ] **Step 2: Update `apps/storefront/src/app/admin/page.tsx`**

- Add **Giá vốn hàng bán (COGS)** card: `formatMetricVnd(data.cogs_vnd ?? 0)` with caption "Bình quân gia quyền di động".
- Add **Lợi nhuận gộp (Gross Profit)** card: `formatMetricVnd(data.gross_profit_vnd ?? 0)` with dynamic margin badge (`Tỷ suất {data.gross_margin_percent}%` in green/emerald or red/rose).
- Add operational alert pill for Boom orders and Return requests in the "Cần xử lý" panel.

- [ ] **Step 3: Update `apps/storefront/src/app/store/page.tsx`**

- Ensure Store Manager overview renders local store metrics cleanly with formatted currency and stock alerts.

- [ ] **Step 4: Run typecheck**

Run: `npm --prefix apps/storefront run typecheck`
Expected: 0 errors.

- [ ] **Step 5: Commit**

```bash
git add apps/storefront/src/lib/api.ts apps/storefront/src/lib/commerce.ts apps/storefront/src/app/admin/page.tsx apps/storefront/src/app/store/page.tsx
git commit -m "feat(storefront): display COGS, gross profit and operational alerts on admin overview"
```

---

### Task 6: Frontend Role-Based BI Hub Page (`/admin/analytics`)

**Files:**
- Create: `apps/storefront/src/app/admin/analytics/page.tsx`
- Modify: `apps/storefront/src/components/AdminNav.tsx`
- Modify: `apps/storefront/src/lib/commerce.ts` & `api.ts`

**Interfaces:**
- Consumes: `GET /api/v1/admin/analytics/role-metrics`, `GET /api/v1/admin/analytics/sales-trend`, `GET /api/v1/admin/analytics/superset-config`.
- Produces: Role-Based Analytics Hub supporting 7 business roles, RBAC tab gating, Role Simulator Switcher for Admin, and Superset studio launcher.

- [ ] **Step 1: Add API client functions in `commerce.ts` & `api.ts`**

Functions:
- `getAdminRoleMetrics(role: string, storeId?: number)`
- `getAdminSalesTrend(days?: number)`
- `getSupersetConfig()`

- [ ] **Step 2: Add navigation link in `AdminNav.tsx`**

Add `{ href: "/admin/analytics", label: "Báo cáo BI Lakehouse", icon: "bar-chart" }`.

- [ ] **Step 3: Implement `apps/storefront/src/app/admin/analytics/page.tsx`**

Build:
- Role Tab Header with 7 Roles:
  1. Ban Giám đốc (CEO)
  2. Kinh doanh & Chiến lược
  3. Quản lý Cửa hàng (RLS Store Selector)
  4. Kho & Chuỗi cung ứng
  5. Vận hành Đơn & Logistics
  6. Marketing & Phễu chuyển đổi
  7. Kỹ thuật & Đối soát dữ liệu
- **RBAC View Gate:**
  - Non-admin users only see their authorized role tab.
  - Unauthorized tabs are completely hidden from the tab bar.
  - Direct URL access to unauthorized tabs renders an "Access Denied" notice.
- **Admin Role Simulator Switcher:**
  - When logged in as `admin`, displays a "Mô phỏng góc nhìn Role" switcher allowing instant preview of each role's dashboard for demo presentations.
- **Interactive Visualizations:**
  - Executive Cards (GMV, COGS, Gross Profit, Gross Margin %).
  - Sales & Profit Trend Bar/Line visualization.
  - Funnel conversion visualization for Marketing.
  - Low-stock and Inbound summary for Inventory.
  - Delivery and Boom rate summary for Operations.
  - Reconciliation Gate delta table for System Admin.
- **Superset Studio Launcher:**
  - Prominent banner linking to Apache Superset portal (`http://localhost:8088`).

- [ ] **Step 4: Run typecheck and production build**

Run: `npm --prefix apps/storefront run typecheck`
Run: `npm --prefix apps/storefront run build`
Expected: 0 errors, 27/27 routes compiled successfully.

- [ ] **Step 5: Run full backend test suite**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests`
Expected: All 162+ tests pass cleanly (0 regression).

- [ ] **Step 6: Commit**

```bash
git add apps/storefront/src/app/admin/analytics/page.tsx apps/storefront/src/components/AdminNav.tsx apps/storefront/src/lib/commerce.ts apps/storefront/src/lib/api.ts
git commit -m "feat(storefront): implement hybrid role-based analytics hub with RBAC tab gating"
```

---

### Task 7: End-to-End Verification & Whole-Branch Review

**Files:**
- Full repository audit across `services/ecommerce-api`, `apps/storefront`, `pipelines`, and `database/seeds`.

- [ ] **Step 1: Execute demo seed scenario**

Run: `python database/seeds/seed_demo_scenarios.py` (or test runner) to populate realistic multi-role data.

- [ ] **Step 2: Run full backend pytest suite**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests -v`
Expected: 100% tests pass.

- [ ] **Step 3: Run pipeline tests**

Run: `pytest pipelines/tests/ -v`
Expected: 100% tests pass.

- [ ] **Step 4: Run storefront typecheck and build**

Run: `npm --prefix apps/storefront run typecheck`
Run: `npm --prefix apps/storefront run build`
Expected: 0 errors, all routes active.

- [ ] **Step 5: Dispatch Whole-Branch Final Reviewer**
