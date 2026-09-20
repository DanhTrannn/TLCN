# Kế hoạch Triển khai: Vòng đời Đơn hàng, Thanh toán COD & Giao vận Shipper Nội bộ

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Triển khai trọn vẹn Gói 1 gồm phương thức thanh toán COD, chế tài chặn boom hàng, quản lý giao vận Shipper nội bộ D&K và mở rộng State Machine đơn hàng từ Backend API đến Giao diện Web.

**Architecture:** Mở rộng FastAPI backend với module `logistics` chuyên biệt cho Shipper và Shipments, tích hợp lựa chọn thanh toán COD vào `checkout`, bổ sung các transitions xuất kho/giao hàng/boom hàng trong `orders` và `admin`. Phía Next.js 15 frontend, bổ sung lựa chọn COD trên `/checkout`, tạo trang quản trị `/admin/logistics` và nâng cấp workflow đơn hàng trên `/admin/orders`.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, Pytest, Next.js 15, React 19, TypeScript, Tailwind CSS.

**Spec:** [`docs/superpowers/specs/2026-09-20-order-lifecycle-cod-logistics-design.md`](file:///home/danhtran/TLCN/docs/superpowers/specs/2026-09-20-order-lifecycle-cod-logistics-design.md)

## Global Constraints

- Tuân thủ nghiêm ngặt schema và ràng buộc toàn vẹn của migration `0014_logistics_returns_inbound_cogs.py`.
- Mọi thao tác ghi/chuyển trạng thái đơn hàng đều phải chạy trong Database Transaction và idempotent với `Idempotency-Key`.
- Tuyệt đối không xóa cứng (hard delete) dữ liệu nhân viên giao hàng; chỉ toggle `is_active`.
- Quy tắc hoàn kho boom hàng: Phải khóa row `inventory` bằng `SELECT ... FOR UPDATE` theo thứ tự `variant_id` tăng dần, cộng lại `on_hand`, tăng `version`.
- Tất cả API endpoints mới đều phải được bảo vệ bởi middleware xác thực và phân quyền tương ứng (`get_current_admin` hoặc `get_current_customer`).
- Giữ vững 171 tests hiện có của repo, không gây hồi quy (no regressions).

---

### Task 1: Backend Logistics Module (Delivery Staff & Shipments CRUD)

**Files:**
- Create: `services/ecommerce-api/app/modules/logistics/schemas.py`
- Create: `services/ecommerce-api/app/modules/logistics/service.py`
- Create: `services/ecommerce-api/app/modules/logistics/router.py`
- Modify: `services/ecommerce-api/app/api/router.py`
- Test: `services/ecommerce-api/tests/test_logistics_api.py`

**Interfaces:**
- Consumes: `app.models.logistics.DeliveryStaff`, `app.models.logistics.Shipment`
- Produces: 
  - Router `admin_logistics_router` mounted at `/api/v1/admin` with endpoints:
    - `GET /delivery-staff` -> `list[DeliveryStaffResponse]`
    - `POST /delivery-staff` -> `DeliveryStaffResponse`
    - `PATCH /delivery-staff/{staff_id}` -> `Response(status_code=204)`
    - `GET /shipments` -> `list[ShipmentResponse]`
    - `GET /shipments/{order_number}` -> `ShipmentResponse`

- [ ] **Step 1: Viết test thất bại (Failing Test) cho Logistics API**

```python
# services/ecommerce-api/tests/test_logistics_api.py
import pytest
from fastapi.testclient import TestClient

def test_admin_delivery_staff_crud(client: TestClient, admin_token_headers: dict[str, str]):
    # 1. Create delivery staff
    payload = {
        "full_name": "Nguyễn Văn Shipper",
        "phone": "0987654321",
        "vehicle_plate": "59-X1 12345"
    }
    create_res = client.post("/api/v1/admin/delivery-staff", json=payload, headers=admin_token_headers)
    assert create_res.status_code == 201
    staff_data = create_res.json()
    assert staff_data["full_name"] == "Nguyễn Văn Shipper"
    assert staff_data["is_active"] is True
    staff_id = staff_data["staff_id"]

    # 2. List delivery staff
    list_res = client.get("/api/v1/admin/delivery-staff", headers=admin_token_headers)
    assert list_res.status_code == 200
    staff_list = list_res.json()
    assert any(s["staff_id"] == staff_id for s in staff_list)

    # 3. Patch delivery staff
    patch_res = client.patch(
        f"/api/v1/admin/delivery-staff/{staff_id}",
        json={"is_active": False},
        headers=admin_token_headers
    )
    assert patch_res.status_code == 204

    # Verify updated
    get_res = client.get("/api/v1/admin/delivery-staff", headers=admin_token_headers)
    target = next(s for s in get_res.json() if s["staff_id"] == staff_id)
    assert target["is_active"] is False
```

- [ ] **Step 2: Chạy test để xác nhận thất bại**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_logistics_api.py`  
Expected: FAIL (404 Not Found do endpoint chưa tồn tại).

- [ ] **Step 3: Triển khai Schemas, Service và Router cho Logistics**

Tạo `services/ecommerce-api/app/modules/logistics/schemas.py`:
```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class DeliveryStaffCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    full_name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=8, max_length=20)
    vehicle_plate: str | None = Field(default=None, max_length=30)

class DeliveryStaffUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, min_length=8, max_length=20)
    vehicle_plate: str | None = Field(default=None, max_length=30)
    is_active: bool | None = None

class DeliveryStaffResponse(BaseModel):
    staff_id: int
    public_id: str
    full_name: str
    phone: str
    vehicle_plate: str | None
    is_active: bool
    created_at: datetime

class ShipmentResponse(BaseModel):
    shipment_id: int
    shipment_code: str
    order_id: int
    order_number: str
    delivery_staff_id: int | None
    delivery_staff_name: str | None
    delivery_staff_phone: str | None
    status: str
    attempt_count: int
    cod_amount_vnd: int
    cod_collected_vnd: int
    dispatched_at: datetime | None
    delivered_at: datetime | None
    failed_at: datetime | None
    failure_reason: str | None
    notes: str | None
```

Tạo `services/ecommerce-api/app/modules/logistics/service.py`:
```python
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.errors import not_found
from app.core.ids import uuid7
from app.models.logistics import DeliveryStaff, Shipment
from app.models.order import Order
from app.modules.logistics.schemas import DeliveryStaffCreateRequest, DeliveryStaffUpdateRequest

def list_delivery_staff(db: Session) -> list[DeliveryStaff]:
    return db.execute(select(DeliveryStaff).order_by(DeliveryStaff.staff_id)).scalars().all()

def create_delivery_staff(db: Session, payload: DeliveryStaffCreateRequest) -> DeliveryStaff:
    staff = DeliveryStaff(
        public_id=uuid7(),
        full_name=payload.full_name,
        phone=payload.phone,
        vehicle_plate=payload.vehicle_plate,
        is_active=True,
    )
    db.add(staff)
    db.flush()
    return staff

def update_delivery_staff(db: Session, staff_id: int, payload: DeliveryStaffUpdateRequest) -> None:
    staff = db.execute(select(DeliveryStaff).where(DeliveryStaff.staff_id == staff_id)).scalar_one_or_none()
    if not staff:
        raise not_found("Không tìm thấy nhân viên giao hàng.")
    if payload.full_name is not None:
        staff.full_name = payload.full_name
    if payload.phone is not None:
        staff.phone = payload.phone
    if payload.vehicle_plate is not None:
        staff.vehicle_plate = payload.vehicle_plate
    if payload.is_active is not None:
        staff.is_active = payload.is_active
    db.flush()

def list_shipments(db: Session, status: str | None = None) -> list[tuple[Shipment, str, str | None, str | None]]:
    stmt = (
        select(
            Shipment,
            Order.order_number,
            DeliveryStaff.full_name,
            DeliveryStaff.phone,
        )
        .join(Order, Order.order_id == Shipment.order_id)
        .outerjoin(DeliveryStaff, DeliveryStaff.staff_id == Shipment.delivery_staff_id)
        .order_by(Shipment.shipment_id.desc())
    )
    if status:
        stmt = stmt.where(Shipment.status == status)
    return db.execute(stmt).all()
```

Tạo `services/ecommerce-api/app/modules/logistics/router.py`:
```python
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.db.deps import get_current_admin, get_db, verify_csrf
from app.models.customer import Customer
from app.modules.logistics.schemas import (
    DeliveryStaffCreateRequest,
    DeliveryStaffResponse,
    DeliveryStaffUpdateRequest,
    ShipmentResponse,
)
from app.modules.logistics.service import (
    create_delivery_staff,
    list_delivery_staff,
    list_shipments,
    update_delivery_staff,
)

admin_router = APIRouter(prefix="/logistics", tags=["admin-logistics"])

@admin_router.get("/delivery-staff", response_model=list[DeliveryStaffResponse])
def get_staff_list(_: Customer = Depends(get_current_admin), db: Session = Depends(get_db)):
    rows = list_delivery_staff(db)
    return [
        DeliveryStaffResponse(
            staff_id=r.staff_id,
            public_id=r.public_id.hex(),
            full_name=r.full_name,
            phone=r.phone,
            vehicle_plate=r.vehicle_plate,
            is_active=r.is_active,
            created_at=r.created_at,
        )
        for r in rows
    ]

@admin_router.post("/delivery-staff", response_model=DeliveryStaffResponse, status_code=201)
def add_staff(
    payload: DeliveryStaffCreateRequest,
    _: Customer = Depends(get_current_admin),
    __: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
):
    staff = create_delivery_staff(db, payload)
    return DeliveryStaffResponse(
        staff_id=staff.staff_id,
        public_id=staff.public_id.hex(),
        full_name=staff.full_name,
        phone=staff.phone,
        vehicle_plate=staff.vehicle_plate,
        is_active=staff.is_active,
        created_at=staff.created_at,
    )

@admin_router.patch("/delivery-staff/{staff_id}", status_code=204)
def patch_staff(
    staff_id: int,
    payload: DeliveryStaffUpdateRequest,
    _: Customer = Depends(get_current_admin),
    __: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
):
    update_delivery_staff(db, staff_id, payload)
    return Response(status_code=204)

@admin_router.get("/shipments", response_model=list[ShipmentResponse])
def get_shipments(status: str | None = None, _: Customer = Depends(get_current_admin), db: Session = Depends(get_db)):
    rows = list_shipments(db, status)
    return [
        ShipmentResponse(
            shipment_id=shipment.shipment_id,
            shipment_code=shipment.shipment_code,
            order_id=shipment.order_id,
            order_number=order_number,
            delivery_staff_id=shipment.delivery_staff_id,
            delivery_staff_name=staff_name,
            delivery_staff_phone=staff_phone,
            status=shipment.status,
            attempt_count=shipment.attempt_count,
            cod_amount_vnd=shipment.cod_amount_vnd,
            cod_collected_vnd=shipment.cod_collected_vnd,
            dispatched_at=shipment.dispatched_at,
            delivered_at=shipment.delivered_at,
            failed_at=shipment.failed_at,
            failure_reason=shipment.failure_reason,
            notes=shipment.notes,
        )
        for shipment, order_number, staff_name, staff_phone in rows
    ]
```

Cập nhật `services/ecommerce-api/app/api/router.py`: Include `admin_logistics_router` dưới `v1_router.include_router(admin_logistics_router, prefix="/admin")`.

- [ ] **Step 4: Chạy test để xác nhận vượt qua**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_logistics_api.py`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add services/ecommerce-api/app/modules/logistics services/ecommerce-api/app/api/router.py services/ecommerce-api/tests/test_logistics_api.py
git commit -m "feat(api): add delivery staff and shipments logistics module"
```

---

### Task 2: Backend Checkout Hỗ trợ COD & Chặn Boom Hàng

**Files:**
- Modify: `services/ecommerce-api/app/modules/checkout/schemas.py`
- Modify: `services/ecommerce-api/app/modules/checkout/service.py`
- Test: `services/ecommerce-api/tests/test_checkout_cod.py`

**Interfaces:**
- Consumes: `CheckoutRequest.payment_method` (`'vietqr' | 'cod'`)
- Produces: `CheckoutResultResponse` containing `payment_method`, creates order with `status='confirmed'` for COD or `status='paid'` for VietQR. Enforces `is_cod_blocked`.

- [ ] **Step 1: Viết test cho Checkout COD và chế tài chặn**

```python
# services/ecommerce-api/tests/test_checkout_cod.py
import pytest
from fastapi.testclient import TestClient

def test_checkout_cod_success(client: TestClient, customer_token_headers: dict[str, str]):
    # Add to cart first...
    # Checkout with payment_method='cod'
    payload = {
        "receiver_name": "Danh Tran",
        "receiver_phone": "0912345678",
        "shipping_address_text": "123 Le Loi, Ben Nghe, Quan 1, TP HCM",
        "payment_method": "cod"
    }
    res = client.post("/api/v1/checkout", json=payload, headers=customer_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "confirmed"
    assert data["payment_status"] == "pending"

def test_checkout_cod_blocked(client: TestClient, blocked_customer_headers: dict[str, str]):
    payload = {
        "receiver_name": "Boomer",
        "receiver_phone": "0999999999",
        "shipping_address_text": "456 Tran Hung Dao, TP HCM",
        "payment_method": "cod"
    }
    res = client.post("/api/v1/checkout", json=payload, headers=blocked_customer_headers)
    assert res.status_code == 403
    assert "khóa phương thức COD" in res.json()["message"]
```

- [ ] **Step 2: Chạy test để xác nhận thất bại**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_checkout_cod.py`  
Expected: FAIL.

- [ ] **Step 3: Cập nhật Schemas và Service của Checkout**

- Trong `checkout/schemas.py`: Thêm `payment_method: Literal["vietqr", "cod"] = "vietqr"` vào `CheckoutRequest`.
- Trong `checkout/service.py`:
  - Kiểm tra nếu `payload.payment_method == "cod"`:
    - `if customer.is_cod_blocked: raise AppError(VALIDATION_ERROR, "Tài khoản của bạn đã bị khóa phương thức COD do boom hàng. Vui lòng chọn VietQR.", status_code=403)`
    - `order.status = "confirmed"`, `order.paid_at = None`, `order.payment_method = "cod"`
    - `payment.status = "pending"`
    - `OrderStatusHistory(from_status=None, to_status="confirmed", transition_source="checkout")`
  - Nếu `payload.payment_method == "vietqr"`:
    - Giữ nguyên `order.status = "paid"`, `payment.status = "succeeded"`, `order.paid_at = now`.

- [ ] **Step 4: Chạy test để xác nhận vượt qua**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_checkout_cod.py`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add services/ecommerce-api/app/modules/checkout services/ecommerce-api/tests/test_checkout_cod.py
git commit -m "feat(api): support COD checkout and enforce is_cod_blocked"
```

---

### Task 3: Backend Order Transitions (Dispatch, Deliver, Failed Delivery)

**Files:**
- Modify: `services/ecommerce-api/app/modules/orders/service.py`
- Modify: `services/ecommerce-api/app/modules/admin/router.py`
- Test: `services/ecommerce-api/tests/test_order_lifecycle_transitions.py`

**Interfaces:**
- Endpoints:
  - `POST /api/v1/admin/orders/{order_number}/dispatch`: assigns shipper, creates shipment, moves order to `shipping`.
  - `POST /api/v1/admin/orders/{order_number}/deliver`: moves order to `delivered`, marks payment succeeded for COD.
  - `POST /api/v1/admin/orders/{order_number}/failed-delivery`: moves order to `failed_delivery`, restores `inventory.on_hand`, increments `boom_count`.
  - `POST /api/v1/admin/orders/{order_number}/complete`: moves order from `delivered` to `completed`.

- [ ] **Step 1: Viết test cho các transitions của đơn hàng**

```python
# services/ecommerce-api/tests/test_order_lifecycle_transitions.py
def test_full_cod_order_lifecycle(client, admin_headers, customer_headers):
    # 1. Checkout COD -> status='confirmed'
    # 2. Dispatch with staff_id -> status='shipping', shipment created
    # 3. Deliver -> status='delivered', payment='succeeded', order.paid_at set
    # 4. Complete -> status='completed'

def test_cod_order_boom_handling(client, admin_headers):
    # 1. Checkout COD
    # 2. Dispatch
    # 3. Failed delivery with reason -> status='failed_delivery', inventory restored, boom_count += 1
```

- [ ] **Step 2: Chạy test để xác nhận thất bại**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_order_lifecycle_transitions.py`  
Expected: FAIL.

- [ ] **Step 3: Cập nhật `orders/service.py` và `admin/router.py`**

- Triển khai các hàm nghiệp vụ:
  - `dispatch_order(db, order_number, staff_id, notes)`
  - `deliver_order(db, order_number)`
  - `fail_delivery_order(db, order_number, reason)`
- Thêm routes trong `admin/router.py`:
  - `@router.post("/orders/{order_number}/dispatch")`
  - `@router.post("/orders/{order_number}/deliver")`
  - `@router.post("/orders/{order_number}/failed-delivery")`
  - `@router.post("/orders/{order_number}/complete")`
- Cập nhật regex status trong `GET /admin/orders` để hỗ trợ lọc `shipping`, `delivered`, `failed_delivery`, `returned`.

- [ ] **Step 4: Chạy test để xác nhận vượt qua**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_order_lifecycle_transitions.py`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add services/ecommerce-api/app/modules/orders services/ecommerce-api/app/modules/admin services/ecommerce-api/tests/test_order_lifecycle_transitions.py
git commit -m "feat(api): add dispatch, deliver, failed-delivery and complete order transitions"
```

---

### Task 4: Frontend Component OrderStatusBadge & API Client Types

**Files:**
- Modify: `apps/storefront/src/components/OrderStatusBadge.tsx`
- Modify: `apps/storefront/src/lib/api.ts`
- Modify: `apps/storefront/src/lib/commerce.ts`
- Modify: `apps/storefront/src/components/AdminNav.tsx`

**Interfaces:**
- Produces:
  - `OrderStatusBadge` supporting all 9 statuses.
  - TypeScript types: `DeliveryStaff`, `ShipmentDetail`, `payment_method` in `CommerceOrder`.
  - Client functions: `getDeliveryStaffList`, `createDeliveryStaff`, `patchDeliveryStaff`, `getShipmentsList`, `dispatchAdminOrder`, `deliverAdminOrder`, `failDeliveryAdminOrder`.

- [ ] **Step 1: Cập nhật `OrderStatusBadge.tsx`**

Bổ sung cấu hình 9 trạng thái:
- `paid`: "Đã thanh toán · Chờ xuất kho"
- `confirmed`: "Đã xác nhận · Chờ giao hàng"
- `shipping`: "Đang giao hàng" (màu indigo)
- `delivered`: "Đã giao hàng · Chờ hoàn tất" (màu xanh lá)
- `failed_delivery`: "Giao thất bại (Boom COD)" (màu đỏ)
- `returned`: "Đã đổi / trả hàng" (màu hổ phách)
- `completed`: "Hoàn tất"
- `cancelled`: "Đã hủy"
- `payment_failed`: "Thanh toán thất bại"

- [ ] **Step 2: Cập nhật API Client Types và Functions trong `lib/api.ts` và `lib/commerce.ts`**

- Định nghĩa interface `DeliveryStaff` và `ShipmentDetail`.
- Thêm `dispatchAdminOrder(orderNumber, staffId, notes)`, `deliverAdminOrder(orderNumber)`, `failDeliveryAdminOrder(orderNumber, reason)`, `completeAdminOrder(orderNumber)`.
- Cập nhật `checkoutWithCoupon` nhận thêm `payment_method: 'vietqr' | 'cod'`.

- [ ] **Step 3: Cập nhật `AdminNav.tsx`**

Thêm link `{ href: "/admin/logistics", label: "Vận chuyển", icon: "truck" }`.

- [ ] **Step 4: Chạy typecheck**

Run: `npm --prefix apps/storefront run typecheck`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/storefront/src/components/OrderStatusBadge.tsx apps/storefront/src/lib/api.ts apps/storefront/src/lib/commerce.ts apps/storefront/src/components/AdminNav.tsx
git commit -m "feat(storefront): update OrderStatusBadge, API client types and AdminNav"
```

---

### Task 5: Frontend Checkout Page with VietQR / COD Selection & Block Check

**Files:**
- Modify: `apps/storefront/src/app/checkout/page.tsx`

- [ ] **Step 1: Thêm state và giao diện chọn Phương thức thanh toán**

Trong `apps/storefront/src/app/checkout/page.tsx`:
- Thêm state `paymentMethod: 'vietqr' | 'cod' = 'vietqr'`.
- Thêm Bước 3 trong form:
  - Option 1: VietQR (icon QR, tiêu đề "Chuyển khoản VietQR", mô tả "Xác nhận tức thời, chuẩn bị xuất kho ngay").
  - Option 2: COD (icon tiền mặt, tiêu đề "Thanh toán tiền mặt khi nhận hàng (COD)", mô tả "Thanh toán cho Shipper D&K khi nhận bưu phẩm").
- Nếu `customer?.is_cod_blocked`:
  - Disable Option COD.
  - Hiển thị banner cảnh báo: "Tài khoản của bạn đã bị khóa tính năng COD do từng không nhận hàng (boom hàng). Vui lòng thanh toán qua VietQR."
- Gửi `payment_method: paymentMethod` khi gọi `checkoutWithCoupon`.

- [ ] **Step 2: Chạy typecheck và test giao diện**

Run: `npm --prefix apps/storefront run typecheck`  
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add apps/storefront/src/app/checkout/page.tsx
git commit -m "feat(storefront): add VietQR and COD payment selection to checkout"
```

---

### Task 6: Frontend Admin Logistics Management Page (`/admin/logistics`)

**Files:**
- Create: `apps/storefront/src/app/admin/logistics/page.tsx`

- [ ] **Step 1: Xây dựng trang `/admin/logistics/page.tsx`**

- Phần 1: Quản lý Đội ngũ Shipper D&K
  - Bảng danh sách shipper: Mã nhân viên, Họ tên, SĐT, Biển số xe, Công tắc bật/tắt `is_active`.
  - Nút "Thêm Shipper mới" kèm Modal form nhập thông tin.
- Phần 2: Giám sát Vận đơn (Shipments)
  - Bộ lọc trạng thái vận đơn: Tất cả, Đang giao (`in_transit`), Giao thành công (`delivered`), Thất bại (`failed`).
  - Bảng vận đơn: Mã vận đơn (`SHP-...`), Mã đơn hàng, Shipper phụ trách, Trạng thái, Tiền COD, Thời gian xuất kho.

- [ ] **Step 2: Chạy typecheck và kiểm tra render**

Run: `npm --prefix apps/storefront run typecheck`  
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add apps/storefront/src/app/admin/logistics/page.tsx
git commit -m "feat(storefront): add admin logistics and delivery staff management page"
```

---

### Task 7: Frontend Admin Orders & Order Detail Workflow Transitions

**Files:**
- Modify: `apps/storefront/src/app/admin/orders/page.tsx`
- Modify: `apps/storefront/src/app/admin/orders/[orderNumber]/page.tsx`
- Modify: `apps/storefront/src/app/orders/[orderNumber]/page.tsx`

- [ ] **Step 1: Nâng cấp `/admin/orders/page.tsx`**

- Mở rộng dropdown trạng thái: `Tất cả`, `Chờ xác nhận (paid)`, `Đã xác nhận (confirmed)`, `Đang giao hàng (shipping)`, `Đã giao hàng (delivered)`, `Giao thất bại / Boom (failed_delivery)`, `Hoàn tất (completed)`, `Đã hủy (cancelled)`.
- Thao tác theo trạng thái:
  - `confirmed`: Nút "Giao hàng" $\rightarrow$ mở Modal chọn Shipper đang active $\rightarrow$ gọi `dispatchAdminOrder` $\rightarrow$ chuyển sang `shipping`.
  - `shipping`:
    - Nút "Giao thành công" $\rightarrow$ gọi `deliverAdminOrder` $\rightarrow$ chuyển sang `delivered`.
    - Nút "Báo Boom hàng" $\rightarrow$ mở Modal nhập lý do $\rightarrow$ gọi `failDeliveryAdminOrder` $\rightarrow$ chuyển sang `failed_delivery`.
  - `delivered`: Nút "Hoàn tất đơn" $\rightarrow$ gọi `completeAdminOrder`.

- [ ] **Step 2: Nâng cấp `/admin/orders/[orderNumber]/page.tsx`**

- Bổ sung Card "Thông tin Vận chuyển": Hiển thị mã vận đơn, Họ tên & SĐT Shipper, Số tiền COD cần thu/đã thu, và trạng thái vận đơn.

- [ ] **Step 3: Cập nhật trang Khách hàng `/orders/[orderNumber]/page.tsx`**

- Hiển thị thông tin Shipper và mã vận đơn nếu đơn đã chuyển sang `shipping` hoặc `delivered`.
- Nút "Đã nhận hàng" chỉ hiển thị khi đơn hàng đang ở trạng thái `delivered` (hoặc `shipping`).

- [ ] **Step 4: Chạy typecheck**

Run: `npm --prefix apps/storefront run typecheck`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/storefront/src/app/admin/orders apps/storefront/src/app/orders
git commit -m "feat(storefront): implement order status transitions and shipping details"
```

---

### Task 8: End-to-End Verification & Lakehouse Consistency Check

**Files:**
- Verification: toàn bộ test suite và smoke check

- [ ] **Step 1: Chạy toàn bộ test suite của Backend**

Run: `PYTHONPATH=pipelines/src:generator/src:services/ecommerce-api uv run pytest services/ecommerce-api/tests`  
Expected: All tests pass.

- [ ] **Step 2: Chạy Typecheck & Build Production của Frontend**

Run:
```bash
npm --prefix apps/storefront run typecheck
npm --prefix apps/storefront run build
```
Expected: Build production thành công 0 lỗi.

- [ ] **Step 3: Chạy Lakehouse Pipeline Smoke Check**

Run: `PYTHONPATH=pipelines/src uv run pytest pipelines/tests`  
Expected: 54 batch pipeline tests pass.

- [ ] **Step 4: Commit toàn bộ tài liệu hoàn tất**

```bash
git commit --allow-empty -m "chore: complete Package 1 implementation verification"
```
