# Returns & Refunds Flow (Gói 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Triển khai hoàn chỉnh hệ thống Đổi trả & Hoàn tiền (Returns & Refunds Flow) cho nền tảng TMĐT từ khách hàng gửi yêu cầu, duyệt hoàn trả, nhận hàng tại kho, kiểm định chất lượng, tự động cộng lại kho với lock bi quan, cho đến giải ngân hoàn tiền và cập nhật trạng thái đơn hàng.

**Architecture:** Xây dựng module backend `app/modules/returns/` trong `services/ecommerce-api` với các service nguyên tử xử lý state machine (`pending_review` $\rightarrow$ `approved` $\rightarrow$ `goods_received` $\rightarrow$ `completed`). Tích hợp hạch toán hoàn tiền vào bảng `refunds` và tăng tồn kho vào `inventories` & `inventory_transactions`. Trên frontend `apps/storefront`, tạo modal yêu cầu trả hàng, trang theo dõi tiến độ cho khách và trang quản trị toàn diện `/admin/returns`.

**Tech Stack:** Python 3.11/3.13, FastAPI, SQLAlchemy 2.0, Pydantic v2, Pytest, TypeScript, Next.js 14 (App Router), Tailwind CSS.

**Spec:** [`docs/superpowers/specs/2026-09-20-returns-refunds-flow-design.md`](file:///home/danhtran/TLCN/docs/superpowers/specs/2026-09-20-returns-refunds-flow-design.md)

## Global Constraints

- Backend framework: FastAPI, SQLAlchemy 2.0, Pydantic v2.
- 0 regression: Tất cả 125 backend tests hiện có (`services/ecommerce-api/tests`) phải tiếp tục pass 100%.
- Idempotency: Mọi mutation tài chính/trạng thái phải yêu cầu `Idempotency-Key` (1-64 chars) và không được vượt quá 64 chars khi lưu vào DB.
- Atomic row locking: Nhập lại kho phải dùng `with_for_update()` trên bảng `Inventory`.
- Return window: Chỉ cho phép tạo yêu cầu hoàn trả cho đơn hàng ở trạng thái `delivered` hoặc `completed` trong vòng 7 ngày kể từ khi giao hàng thành công.
- Refund proration: Tính toán tiền hoàn phải trừ đi tỷ lệ giảm giá coupon tương ứng, không được vượt quá số tiền thực tế khách đã trả.
- Frontend: TypeScript `tsc --noEmit` pass với 0 lỗi, Next.js production build pass 100%.

---

### Task 1: Database Model Constraints & Model Relationships

**Files:**
- Modify: `services/ecommerce-api/app/models/order.py:238-250`
- Modify: `services/ecommerce-api/app/models/returns.py:40-42`
- Test: `services/ecommerce-api/tests/test_return_models.py`

**Interfaces:**
- Consumes: `OrderStatusHistory`, `Order`, `ReturnRequest`, `ReturnItem`, `Refund`.
- Produces: Cho phép transition `from_status='completed'` $\rightarrow$ `to_status='returned'` với `transition_source='admin_return'` trong `order_status_history`.

- [ ] **Step 1: Write failing test in `services/ecommerce-api/tests/test_return_models.py`**

```python
from datetime import datetime, timezone
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.models.order import Order, OrderStatusHistory, Payment, Refund
from app.models.returns import ReturnRequest, ReturnItem

def test_order_status_history_allows_completed_to_returned(db_session, test_order):
    test_order.status = "completed"
    db_session.commit()

    now = datetime.now(timezone.utc)
    history = OrderStatusHistory(
        order_id=test_order.order_id,
        from_status="completed",
        to_status="returned",
        transition_source="admin_return",
        transition_idempotency_key=f"ret-{uuid.uuid4().hex[:30]}",
        transitioned_at=now,
    )
    db_session.add(history)
    db_session.commit()

    saved = db_session.scalar(
        select(OrderStatusHistory).where(OrderStatusHistory.order_status_history_id == history.order_status_history_id)
    )
    assert saved is not None
    assert saved.to_status == "returned"
    assert saved.transition_source == "admin_return"
```

- [ ] **Step 2: Run test to verify it fails (RED)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_return_models.py -v`
Expected: FAIL due to check constraint `valid_transition` or `transition_source`.

- [ ] **Step 3: Update `valid_transition` and `transition_source` in `services/ecommerce-api/app/models/order.py`**

In `OrderStatusHistory.__table_args__`:
```python
        CheckConstraint(
            "(from_status is null and to_status in ('paid','payment_failed','confirmed')) "
            "or (from_status = 'paid' and to_status in ('confirmed','cancelled')) "
            "or (from_status = 'paid' and to_status = 'shipping') "
            "or (from_status = 'confirmed' and to_status in ('completed','cancelled','shipping')) "
            "or (from_status = 'shipping' and to_status in ('delivered','failed_delivery','returned')) "
            "or (from_status = 'delivered' and to_status in ('completed','returned')) "
            "or (from_status = 'completed' and to_status = 'returned')",
            name="valid_transition",
        ),
        CheckConstraint(
            "transition_source in ('checkout','internal_endpoint','generator','system','admin','customer','admin_dispatch','admin_deliver','admin_failed_delivery','admin_complete','admin_return')",
            name="transition_source",
        ),
```

- [ ] **Step 4: Run test to verify it passes (GREEN)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_return_models.py -v`
Expected: PASS

- [ ] **Step 5: Run full test suite to ensure 0 regression**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests`
Expected: 126 passed.

- [ ] **Step 6: Commit**

```bash
git add services/ecommerce-api/app/models/order.py services/ecommerce-api/tests/test_return_models.py
git commit -m "feat(returns): update order status history constraint to support return transitions"
```

---

### Task 2: Backend Customer Returns API (Schemas, Service, Router)

**Files:**
- Create: `services/ecommerce-api/app/modules/returns/__init__.py`
- Create: `services/ecommerce-api/app/modules/returns/schemas.py`
- Create: `services/ecommerce-api/app/modules/returns/service.py`
- Create: `services/ecommerce-api/app/modules/returns/router.py`
- Modify: `services/ecommerce-api/app/api/router.py`
- Test: `services/ecommerce-api/tests/test_return_customer_api.py`

**Interfaces:**
- Consumes: `Customer`, `Order`, `OrderItem`, `ReturnRequest`, `ReturnItem`.
- Produces:
  - `POST /api/v1/orders/{order_number}/returns`
  - `GET /api/v1/returns`
  - `GET /api/v1/returns/{return_code}`
  - `POST /api/v1/returns/{return_code}/cancel`

- [ ] **Step 1: Write integration tests in `services/ecommerce-api/tests/test_return_customer_api.py`**

Test scenarios:
1. Customer successfully creates a return request for a `completed` order within 7 days.
2. Verify prorated refund amount calculation when order has coupon discount.
3. Reject return request if order is not delivered/completed (e.g. `shipping` or `confirmed`).
4. Reject return request if more than 7 days have passed.
5. Reject return request if another active return request is already open (`pending_review`, `approved`, `goods_received`).
6. Customer can view their return list and return detail.
7. Customer can cancel a return request when in `pending_review`.

- [ ] **Step 2: Run test to verify it fails (RED)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_return_customer_api.py -v`
Expected: FAIL with 404 Not Found (router not mounted / module not existing).

- [ ] **Step 3: Implement Schemas, Service & Router for Customer Returns**

1. `services/ecommerce-api/app/modules/returns/schemas.py`:
```python
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class ReturnItemCreatePayload(BaseModel):
    order_item_id: int
    quantity: int = Field(ge=1)

class CreateReturnRequestPayload(BaseModel):
    customer_reason: str = Field(min_length=5, max_length=1000)
    bank_name: str = Field(min_length=2, max_length=100)
    bank_account_number: str = Field(min_length=4, max_length=50)
    bank_account_holder: str = Field(min_length=2, max_length=150)
    image_urls: list[str] = Field(default_factory=list)
    items: list[ReturnItemCreatePayload] = Field(min_length=1)

class ReturnItemDetailResponse(BaseModel):
    return_item_id: int
    order_item_id: int
    variant_id: int
    product_name: str | None = None
    variant_title: str | None = None
    sku: str | None = None
    quantity: int
    refund_amount_vnd: int
    inspection_status: str

class ReturnRequestDetailResponse(BaseModel):
    return_id: int
    return_code: str
    order_id: int
    order_number: str
    action_type: str
    status: str
    customer_reason: str
    admin_note: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    bank_info: dict | None = None
    total_refund_amount_vnd: int
    created_at: datetime
    reviewed_at: datetime | None = None
    resolved_at: datetime | None = None
    items: list[ReturnItemDetailResponse] = Field(default_factory=list)

class ReturnRequestSummaryResponse(BaseModel):
    return_id: int
    return_code: str
    order_number: str
    action_type: str
    status: str
    total_items_count: int
    total_refund_amount_vnd: int
    created_at: datetime
```

2. `services/ecommerce-api/app/modules/returns/service.py`:
Implement:
- `create_customer_return_request(db, customer_id, order_number, payload, idempotency_key)`:
  - Fetch order, verify ownership.
  - Verify status is in `('delivered', 'completed')`.
  - Verify `now - (order.completed_at or order.updated_at) <= 7 days`.
  - Check no active return request exists with `status in ('pending_review', 'approved', 'goods_received')`.
  - Calculate `prorated_unit_price = round(item.unit_price_vnd * (1 - order.discount_amount_vnd / order.subtotal_vnd))` if `order.subtotal_vnd > 0` else `item.unit_price_vnd`.
  - Store bank info in `image_urls` JSON dictionary or customer_reason/metadata.
  - Create `ReturnRequest` with generated code `RT-YYYYMMDD-XXXXXX`.
  - Create `ReturnItem` for each selected item.
- `list_customer_returns(db, customer_id)`
- `get_customer_return_detail(db, customer_id, return_code)`
- `cancel_customer_return_request(db, customer_id, return_code)`

3. `services/ecommerce-api/app/modules/returns/router.py`:
- `POST /orders/{order_number}/returns` (with `_require_idempotency_key`, `verify_csrf`, `get_current_customer`).
- `GET /returns` (with `get_current_customer`).
- `GET /returns/{return_code}` (with `get_current_customer`).
- `POST /returns/{return_code}/cancel` (with `verify_csrf`, `get_current_customer`).

4. Mount customer router in `services/ecommerce-api/app/api/router.py`.

- [ ] **Step 4: Run test to verify it passes (GREEN)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_return_customer_api.py -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests`
Expected: 0 regression.

- [ ] **Step 6: Commit**

```bash
git add services/ecommerce-api/app/modules/returns/ services/ecommerce-api/app/api/router.py services/ecommerce-api/tests/test_return_customer_api.py
git commit -m "feat(returns): implement customer return request APIs and schemas"
```

---

### Task 3: Backend Admin Returns Management, Inspection & Stock Restock

**Files:**
- Modify: `services/ecommerce-api/app/modules/returns/schemas.py`
- Modify: `services/ecommerce-api/app/modules/returns/service.py`
- Modify: `services/ecommerce-api/app/modules/returns/router.py`
- Modify: `services/ecommerce-api/app/api/router.py`
- Test: `services/ecommerce-api/tests/test_return_admin_api.py`

**Interfaces:**
- Consumes: `Inventory`, `InventoryTransaction`, `Refund`, `Payment`, `OrderStatusHistory`, `get_current_admin`.
- Produces:
  - `GET /api/v1/admin/returns`
  - `GET /api/v1/admin/returns/{return_code}`
  - `POST /api/v1/admin/returns/{return_code}/review`
  - `POST /api/v1/admin/returns/{return_code}/receive`
  - `POST /api/v1/admin/returns/{return_code}/inspect-and-resolve`

- [ ] **Step 1: Write integration tests in `services/ecommerce-api/tests/test_return_admin_api.py`**

Test scenarios:
1. Admin reviews return request: `approved` updates status to `approved`; `rejected` updates status to `rejected` with `admin_note`.
2. Admin receives package: `receive` endpoint moves status to `goods_received`.
3. Admin inspects and resolves with `passed` items:
   - Atomic update on `Inventory.on_hand += quantity`
   - `InventoryTransaction` recorded with `movement_type='return_customer'`
   - `Refund` created with `status='succeeded'`
   - Return status moves to `completed`
   - If all order items returned -> Order moves to `returned` and `OrderStatusHistory` recorded.
4. Admin inspects and resolves with `failed` items:
   - Inventory is NOT restocked.
   - Refund is NOT issued for failed items.
5. Idempotent resolution checks.

- [ ] **Step 2: Run test to verify it fails (RED)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_return_admin_api.py -v`
Expected: FAIL (endpoints not implemented).

- [ ] **Step 3: Implement Admin Schemas, Services & Router**

1. Add Admin schemas to `schemas.py`:
   - `AdminReviewReturnPayload(action: Literal["approved", "rejected"], admin_note: str | None = None)`
   - `AdminInspectItemPayload(return_item_id: int, inspection_status: Literal["passed", "failed"])`
   - `AdminInspectAndResolvePayload(items: list[AdminInspectItemPayload], admin_note: str | None = None)`
   - `AdminReturnListResponse(items: list[ReturnRequestDetailResponse], total: int)`
2. Add Admin services in `service.py`:
   - `list_admin_returns(db, status, search, limit, offset)`
   - `get_admin_return_detail(db, return_code)`
   - `review_admin_return(db, return_code, action, admin_note)`
   - `receive_admin_return(db, return_code)`
   - `inspect_and_resolve_admin_return(db, return_code, payload, idempotency_key)`:
     - Load return request, lock row.
     - Validate status is `goods_received`.
     - For each item in payload:
       - Update `item.inspection_status`.
       - If `passed`:
         - Query `Inventory` with `.with_for_update()` by `variant_id`.
         - If found: `inv.on_hand += item.quantity`.
         - Create `InventoryTransaction(public_id=uuid4(), variant_id=item.variant_id, location_type='central_warehouse', movement_type='return_customer', quantity_delta=item.quantity, reference_code=return_req.return_code, notes=f"Hàng hoàn từ {return_req.return_code}")`.
     - Sum `refund_amount = sum(item.refund_amount_vnd for item in return_req.items if item.inspection_status == 'passed')`.
     - If `refund_amount > 0`:
       - Create `Refund(public_id=uuid4(), payment_id=order.payment.payment_id, refund_idempotency_key=f"ref:{idempotency_key[:58]}", status="succeeded", amount_vnd=refund_amount, reason=f"Hoàn tiền yêu cầu {return_req.return_code}", requested_by_customer_id=return_req.customer_id, completed_at=datetime.now(UTC))`.
     - Set `return_req.status = "completed"`, `return_req.resolved_at = datetime.now(UTC)`.
     - Check if all order items have been returned:
       - If total returned quantity across completed returns >= total order quantity:
         - Set `order.status = "returned"`.
         - Add `OrderStatusHistory(order_id=order.order_id, from_status=order.status, to_status="returned", transition_source="admin_return", transition_idempotency_key=f"ret:{idempotency_key[:58]}", transitioned_at=now)`.
3. Add Admin endpoints to `router.py` (mounted under `/admin/returns` with `get_current_admin`).
4. Include return information in order detail response (`OrderDetailResponse`) for both admin and customer so frontend can detect existing returns.

- [ ] **Step 4: Run test to verify it passes (GREEN)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_return_admin_api.py -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests`
Expected: All tests pass (0 regression).

- [ ] **Step 6: Commit**

```bash
git add services/ecommerce-api/app/modules/returns/ services/ecommerce-api/app/modules/orders/ services/ecommerce-api/tests/test_return_admin_api.py
git commit -m "feat(admin): implement admin return review, receipt, inspection and refund resolution"
```

---

### Task 4: Frontend API Client Types & Status Badges

**Files:**
- Modify: `apps/storefront/src/components/OrderStatusBadge.tsx`
- Modify: `apps/storefront/src/lib/commerce.ts`
- Modify: `apps/storefront/src/lib/api.ts`
- Modify: `apps/storefront/src/components/AdminNav.tsx`

**Interfaces:**
- Consumes: Backend API return endpoints.
- Produces:
  - TypeScript types: `ReturnItemDetail`, `ReturnRequestDetail`, `ReturnRequestSummary`, `CreateReturnRequestInput`.
  - Client functions: `createCustomerReturnRequest`, `getCustomerReturnsList`, `getCustomerReturnDetail`, `cancelCustomerReturnRequest`, `getAdminReturnsList`, `getAdminReturnDetail`, `reviewAdminReturn`, `receiveAdminReturn`, `inspectAndResolveAdminReturn`.
  - `ReturnStatusBadge`: Component hiển thị trạng thái của `ReturnRequest` (`pending_review`, `approved`, `goods_received`, `completed`, `rejected`, `cancelled`).

- [ ] **Step 1: Update `apps/storefront/src/lib/commerce.ts` & `apps/storefront/src/lib/api.ts`**

Add interfaces:
```typescript
export interface ReturnItemDetail {
  return_item_id: number;
  order_item_id: number;
  variant_id: number;
  product_name?: string | null;
  variant_title?: string | null;
  sku?: string | null;
  quantity: number;
  refund_amount_vnd: number;
  inspection_status: "pending" | "passed" | "failed";
}

export interface ReturnRequestDetail {
  return_id: number;
  return_code: string;
  order_id: number;
  order_number: string;
  action_type: string;
  status: "pending_review" | "approved" | "rejected" | "goods_received" | "completed" | "cancelled";
  customer_reason: string;
  admin_note?: string | null;
  image_urls?: string[];
  bank_info?: {
    bank_name: string;
    bank_account_number: string;
    bank_account_holder: string;
  } | null;
  total_refund_amount_vnd: number;
  created_at: string;
  reviewed_at?: string | null;
  resolved_at?: string | null;
  items: ReturnItemDetail[];
}

export interface ReturnRequestSummary {
  return_id: number;
  return_code: string;
  order_number: string;
  action_type: string;
  status: "pending_review" | "approved" | "rejected" | "goods_received" | "completed" | "cancelled";
  total_items_count: number;
  total_refund_amount_vnd: number;
  created_at: string;
}
```

Add API functions for customer and admin returns.
Update `OrderDetail` and `CommerceOrderDetail` to include optional `active_return?: ReturnRequestSummary | null` and `refund?: { amount_vnd: number; status: string } | null`.

- [ ] **Step 2: Update `apps/storefront/src/components/OrderStatusBadge.tsx`**

Add `ReturnStatusBadge` component:
- `pending_review`: "Chờ duyệt đổi trả" (`warning` style)
- `approved`: "Đã duyệt · Chờ nhận hàng" (`info` style)
- `goods_received`: "Đã nhận hàng tại kho" (`primary` style)
- `completed`: "Đã hoàn tất & Hoàn tiền" (`success` style)
- `rejected`: "Bị từ chối" (`danger` style)
- `cancelled`: "Đã hủy" (`muted` style)

Also add helper `FinancialRefundBadge` for orders that have partial refunds:
- "Đã hoàn tiền một phần (Partially Refunded)" (`emerald` / `teal` style with amount).

- [ ] **Step 3: Update `apps/storefront/src/components/AdminNav.tsx`**

Add `{ href: "/admin/returns", label: "Đổi trả & Hoàn tiền", icon: "rotate-ccw" }` to admin navigation.

- [ ] **Step 4: Run typecheck to verify**

Run: `npm --prefix apps/storefront run typecheck`
Expected: 0 errors.

- [ ] **Step 5: Commit**

```bash
git add apps/storefront/src/components/OrderStatusBadge.tsx apps/storefront/src/lib/ apps/storefront/src/components/AdminNav.tsx
git commit -m "feat(storefront): add return API client functions, types and ReturnStatusBadge"
```

---

### Task 5: Frontend Customer Return Flow (Modal & Detail Page)

**Files:**
- Create: `apps/storefront/src/components/returns/CreateReturnModal.tsx`
- Create: `apps/storefront/src/app/orders/returns/[returnCode]/page.tsx`
- Modify: `apps/storefront/src/app/orders/[orderNumber]/page.tsx`

**Interfaces:**
- Consumes: `createCustomerReturnRequest`, `getCustomerReturnDetail`, `cancelCustomerReturnRequest`.
- Produces:
  - Nút "Yêu cầu Đổi / Trả hàng" trên trang chi tiết đơn hàng cho đơn `delivered`/`completed` trong 7 ngày.
  - Card thông tin tiến độ trả hàng trên trang chi tiết đơn hàng nếu đơn có yêu cầu đổi trả.
  - Trang chi tiết yêu cầu trả hàng `/orders/returns/[returnCode]` với Stepper 4 bước và nút Hủy yêu cầu.

- [ ] **Step 1: Implement `CreateReturnModal.tsx`**

Build interactive modal:
- Bảng danh sách `order.items`: checkbox chọn sản phẩm, số lượng trả ($1 \le qty \le item.quantity$).
- Form thông tin nhận hoàn tiền:
  - Tên ngân hàng (`bank_name`, select hoặc input).
  - Số tài khoản (`bank_account_number`).
  - Họ tên chủ tài khoản (`bank_account_holder`).
- Ô nhập lý do (`customer_reason`, required).
- Ô nhập link ảnh minh chứng (`image_urls`).
- Hiển thị ước tính số tiền hoàn lại: $\sum \text{selected\_items} \times \text{prorated\_price}$.
- Submit: gọi `createCustomerReturnRequest`, sinh `Idempotency-Key` ngẫu nhiên, reload/chuyển hướng sang trang chi tiết yêu cầu.

- [ ] **Step 2: Update `apps/storefront/src/app/orders/[orderNumber]/page.tsx`**

- Tính điều kiện: `isEligibleForReturn`:
  - `(order.status === 'delivered' || order.status === 'completed')`
  - Đơn trong vòng 7 ngày kể từ khi giao hàng
  - Không có yêu cầu return nào đang hoạt động
- Hiển thị nút "Yêu cầu Trả hàng / Hoàn tiền" khi `isEligibleForReturn`.
- Nếu đơn đã có yêu cầu return: hiển thị Banner / Card "Tiến độ yêu cầu Đổi / Trả hàng" kèm mã `return_code`, `ReturnStatusBadge` và nút "Xem chi tiết tiến độ".

- [ ] **Step 3: Implement `apps/storefront/src/app/orders/returns/[returnCode]/page.tsx`**

- Fetch return detail via `getCustomerReturnDetail(returnCode)`.
- Status Stepper:
  1. Gửi yêu cầu $\rightarrow$ 2. Duyệt yêu cầu $\rightarrow$ 3. Nhận hàng tại kho $\rightarrow$ 4. Hoàn tất & Hoàn tiền.
- Card thông tin đơn hàng gốc & STK nhận tiền hoàn.
- Bảng chi tiết sản phẩm: tên sản phẩm, số lượng, kết quả kiểm định (`passed` / `failed`), số tiền hoàn.
- Nút "Hủy yêu cầu" khi trạng thái là `pending_review`.

- [ ] **Step 4: Verify typecheck & build**

Run: `npm --prefix apps/storefront run typecheck`
Run: `npm --prefix apps/storefront run build`
Expected: 0 errors, build thành công.

- [ ] **Step 5: Commit**

```bash
git add apps/storefront/src/components/returns/ apps/storefront/src/app/orders/
git commit -m "feat(storefront): add customer return request modal and progress tracking page"
```

---

### Task 6: Frontend Admin Returns Management & Inspection Resolution

**Files:**
- Create: `apps/storefront/src/app/admin/returns/page.tsx`
- Create: `apps/storefront/src/app/admin/returns/[returnCode]/page.tsx`
- Modify: `apps/storefront/src/app/admin/orders/[orderNumber]/page.tsx`

**Interfaces:**
- Consumes: `getAdminReturnsList`, `getAdminReturnDetail`, `reviewAdminReturn`, `receiveAdminReturn`, `inspectAndResolveAdminReturn`.
- Produces:
  - Trang `/admin/returns`: Danh sách yêu cầu hoàn trả toàn hệ thống với tab lọc trạng thái và tìm kiếm.
  - Trang `/admin/returns/[returnCode]`: Thao tác Duyệt / Từ chối, Xác nhận nhận hàng, Form kiểm định từng item và Giải ngân hoàn tất.
  - Trang `/admin/orders/[orderNumber]`: Hiển thị thông tin Return/Refund liên quan.

- [ ] **Step 1: Implement `apps/storefront/src/app/admin/returns/page.tsx`**

- Tab lọc trạng thái: Tất cả (`""`), Chờ duyệt (`pending_review`), Chờ nhận hàng (`approved`), Đã nhận hàng (`goods_received`), Đã hoàn tất (`completed`), Từ chối (`rejected`).
- Ô tìm kiếm: theo mã yêu cầu, mã đơn hàng, SĐT.
- Bảng dữ liệu:
  - Mã yêu cầu (`RT-...`)
  - Mã đơn hàng (link đến `/admin/orders/[orderNumber]`)
  - Khách hàng (Tên & SĐT)
  - Số lượng món
  - Tổng tiền hoàn (VND)
  - Trạng thái (`ReturnStatusBadge`)
  - Thời gian tạo
  - Thao tác: link đến `/admin/returns/[returnCode]`

- [ ] **Step 2: Implement `apps/storefront/src/app/admin/returns/[returnCode]/page.tsx`**

- Fetch chi tiết yêu cầu qua `getAdminReturnDetail(returnCode)`.
- Card 1: Thông tin khách hàng & Thông tin tài khoản ngân hàng nhận tiền hoàn.
- Card 2: Danh sách sản phẩm và form kiểm định:
  - Khi trạng thái là `goods_received`: Radio chọn `passed` hoặc `failed` cho từng sản phẩm.
  - Tự động tính lại tổng số tiền hoàn từ các món `passed`.
- Card 3: Thao tác theo trạng thái:
  - Khi `pending_review`:
    - Nút "Duyệt yêu cầu" (`reviewAdminReturn(returnCode, "approved")`).
    - Nút "Từ chối" mở modal nhập lý do (`reviewAdminReturn(returnCode, "rejected", reason)`).
  - Khi `approved`:
    - Nút "Xác nhận đã nhận hàng về kho" (`receiveAdminReturn(returnCode)`).
  - Khi `goods_received`:
    - Nút "Xác nhận kiểm định & Hoàn tất hoàn tiền" (`inspectAndResolveAdminReturn(...)`).

- [ ] **Step 3: Update `apps/storefront/src/app/admin/orders/[orderNumber]/page.tsx`**

- Bổ sung Card thông tin Đổi trả & Hoàn tiền (nếu đơn có phát sinh hoàn tiền/yêu cầu return).
- Hiển thị link trực tiếp đến trang xử lý yêu cầu đổi trả `/admin/returns/[returnCode]`.

- [ ] **Step 4: Verify typecheck & build**

Run: `npm --prefix apps/storefront run typecheck`
Run: `npm --prefix apps/storefront run build`
Expected: 0 errors, build pass 100%.

- [ ] **Step 5: Commit**

```bash
git add apps/storefront/src/app/admin/returns/ apps/storefront/src/app/admin/orders/
git commit -m "feat(storefront): implement admin returns management and inspection workflow"
```

---

### Task 7: End-to-End Verification & Documentation

**Files:**
- Modify: `docs/superpowers/specs/2026-09-20-returns-refunds-flow-design.md`
- Test: Full backend test suite & Next.js production build

- [ ] **Step 1: Run full backend test suite**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests -v`
Expected: All tests pass.

- [ ] **Step 2: Run storefront typecheck and build**

Run: `npm --prefix apps/storefront run typecheck`
Run: `npm --prefix apps/storefront run build`
Expected: 0 errors, build thành công 100%.

- [ ] **Step 3: Commit and update documentation**

```bash
git commit -m "docs: finalize returns and refunds flow implementation verification"
```
