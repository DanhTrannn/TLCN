# Inbound Production & Inventory Costing (Gói 3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Triển khai quy trình Nhập kho thành phẩm từ xưởng may nội bộ, tự động tính toán giá vốn hàng bán theo phương pháp Bình quân gia quyền di động (Moving Weighted Average Costing), đóng băng giá vốn khi bán hàng qua Online & POS, và xây dựng giao diện quản trị nhập kho trên Storefront.

**Architecture:** Tạo bảng `inbound_receipts` và `inbound_receipt_items` trong `services/ecommerce-api/app/models/inbound.py`. Xây dựng module `app/modules/inbound/` xử lý nhập kho nguyên tử với khóa dòng `with_for_update()` trên `Inventory` và `ProductVariant`. Snapshot `cost_price_vnd` trong `checkout/service.py` và `pos/service.py`. Trên storefront `apps/storefront`, thêm trang quản trị `/admin/inbound`, modal tạo phiếu nhập có Live Costing Preview và bổ sung cột Giá vốn trên `/admin/products`.

**Tech Stack:** Python 3.11/3.13, FastAPI, SQLAlchemy 2.0, Pydantic v2, Pytest, TypeScript, Next.js 15, Tailwind CSS.

**Spec:** [`docs/superpowers/specs/2026-09-21-inbound-inventory-costing-design.md`](file:///home/danhtran/TLCN/docs/superpowers/specs/2026-09-21-inbound-inventory-costing-design.md)

## Global Constraints

- Backend framework: FastAPI, SQLAlchemy 2.0, Pydantic v2.
- 0 regression: Toàn bộ 146 backend tests hiện có (`services/ecommerce-api/tests`) phải tiếp tục pass 100%.
- Inbound destination: Luôn nhập thành phẩm vào Kho tổng trung tâm (`central_warehouse` / bảng `inventory`).
- Database constraint compliance: Khi tăng tồn kho `on_hand += quantity`, bắt buộc phải tăng đồng thời `opening_on_hand += quantity` để thỏa mãn check constraint `on_hand <= opening_on_hand` của bảng `inventory`.
- Concurrency & Row locking: Mọi thao tác nhập kho và cập nhật giá vốn phải sử dụng `with_for_update()` trên các dòng `Inventory` và `ProductVariant`.
- Moving Weighted Average Formula:
  $$C_{\text{new}} = \text{round}\left(\frac{(Q_{\text{current}} \times C_{\text{current}}) + (Q_{\text{inbound}} \times C_{\text{inbound}})}{Q_{\text{current}} + Q_{\text{inbound}}}\right)$$
  Nếu $Q_{\text{current}} == 0$, $C_{\text{new}} = C_{\text{inbound}}$.
- COGS Snapshotting: Cả Online Checkout và POS Checkout phải lưu đúng `OrderItem.cost_price_vnd = variant.cost_price_vnd`.
- Frontend: TypeScript `tsc --noEmit` pass với 0 lỗi, Next.js production build pass 100%.

---

### Task 1: Database Models for Inbound Receipts

**Files:**
- Create: `services/ecommerce-api/app/models/inbound.py`
- Modify: `services/ecommerce-api/app/models/__init__.py`
- Test: `services/ecommerce-api/tests/test_inbound_models.py`

**Interfaces:**
- Consumes: `Base`, `GUID`, `ProductVariant`, `Customer`.
- Produces: SQLAlchemy models `InboundReceipt` and `InboundReceiptItem`.

- [ ] **Step 1: Write failing test in `services/ecommerce-api/tests/test_inbound_models.py`**

```python
import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select
from app.models.catalog import Category, Product, ProductVariant
from app.models.customer import Customer
from app.models.inbound import InboundReceipt, InboundReceiptItem

def test_inbound_receipt_and_item_creation(db_session, test_staff_user, test_variant):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    receipt = InboundReceipt(
        public_id=uuid.uuid4(),
        receipt_code="INB-20260921-000001",
        batch_name="Lô đầm Thu Đông đợt 1",
        status="completed",
        total_items_count=100,
        total_cost_vnd=12000000,
        notes="Kiểm đếm đầy đủ",
        created_by_customer_id=test_staff_user.customer_id,
        created_at=now,
        updated_at=now,
    )
    db_session.add(receipt)
    db_session.flush()

    item = InboundReceiptItem(
        public_id=uuid.uuid4(),
        receipt_id=receipt.receipt_id,
        variant_id=test_variant.variant_id,
        quantity=100,
        unit_cost_vnd=120000,
        total_cost_vnd=12000000,
        previous_cost_price_vnd=0,
        new_cost_price_vnd=120000,
        created_at=now,
    )
    db_session.add(item)
    db_session.commit()

    saved = db_session.scalar(
        select(InboundReceipt).where(InboundReceipt.receipt_id == receipt.receipt_id)
    )
    assert saved is not None
    assert saved.receipt_code == "INB-20260921-000001"
    assert len(saved.items) == 1
    assert saved.items[0].quantity == 100
    assert saved.items[0].new_cost_price_vnd == 120000
```

- [ ] **Step 2: Run test to verify it fails (RED)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_inbound_models.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'app.models.inbound').

- [ ] **Step 3: Implement `InboundReceipt` and `InboundReceiptItem` in `services/ecommerce-api/app/models/inbound.py`**

```python
from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import GUID


class InboundReceipt(Base):
    __tablename__ = "inbound_receipts"

    receipt_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    public_id: Mapped[UUID] = mapped_column(GUID(), nullable=False)
    receipt_code: Mapped[str] = mapped_column(String(64), nullable=False)
    batch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="completed")
    total_items_count: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False, default=0)
    total_cost_vnd: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_customer_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("customers.customer_id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        server_onupdate=text("CURRENT_TIMESTAMP(6)"),
    )

    items: Mapped[list["InboundReceiptItem"]] = relationship(
        back_populates="receipt", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("status = 'completed'", name="ck_inbound_receipts_status"),
        CheckConstraint("total_items_count >= 0", name="ck_inbound_receipts_items_count"),
        CheckConstraint("total_cost_vnd >= 0", name="ck_inbound_receipts_total_cost"),
        Index("uq_inbound_receipts_public_id", "public_id", unique=True),
        Index("uq_inbound_receipts_code", "receipt_code", unique=True),
        Index("ix_inbound_receipts_created_at_id", "created_at", "receipt_id"),
    )


class InboundReceiptItem(Base):
    __tablename__ = "inbound_receipt_items"

    item_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    public_id: Mapped[UUID] = mapped_column(GUID(), nullable=False)
    receipt_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("inbound_receipts.receipt_id", ondelete="CASCADE"), nullable=False
    )
    variant_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("product_variants.variant_id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False)
    unit_cost_vnd: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False, default=0)
    total_cost_vnd: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False, default=0)
    previous_cost_price_vnd: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False, default=0)
    new_cost_price_vnd: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )

    receipt: Mapped["InboundReceipt"] = relationship(back_populates="items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inbound_items_quantity"),
        CheckConstraint("unit_cost_vnd >= 0", name="ck_inbound_items_unit_cost"),
        CheckConstraint("total_cost_vnd >= 0", name="ck_inbound_items_total_cost"),
        Index("uq_inbound_items_public_id", "public_id", unique=True),
        Index("ix_inbound_items_receipt_id", "receipt_id"),
        Index("ix_inbound_items_variant_id", "variant_id"),
    )
```

Update `services/ecommerce-api/app/models/__init__.py` to import `InboundReceipt` and `InboundReceiptItem`.

- [ ] **Step 4: Run test to verify it passes (GREEN)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_inbound_models.py -v`
Expected: PASS

- [ ] **Step 5: Run full test suite to ensure 0 regression**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests`
Expected: 147 passed.

- [ ] **Step 6: Commit**

```bash
git add services/ecommerce-api/app/models/inbound.py services/ecommerce-api/app/models/__init__.py services/ecommerce-api/tests/test_inbound_models.py
git commit -m "feat(inbound): add InboundReceipt and InboundReceiptItem models"
```

---

### Task 2: Online & POS Checkout COGS Snapshotting

**Files:**
- Modify: `services/ecommerce-api/app/modules/checkout/service.py:196-200`
- Modify: `services/ecommerce-api/app/modules/pos/service.py:164-168`
- Test: `services/ecommerce-api/tests/test_cogs_snapshot.py`

**Interfaces:**
- Consumes: `ProductVariant.cost_price_vnd`, `OrderItem`.
- Produces: `OrderItem.cost_price_vnd` snapshotting at time of purchase.

- [ ] **Step 1: Write integration tests in `services/ecommerce-api/tests/test_cogs_snapshot.py`**

Test scenarios:
1. Online Checkout snapshots `variant.cost_price_vnd` into `OrderItem.cost_price_vnd`.
2. POS Checkout snapshots `variant.cost_price_vnd` into `OrderItem.cost_price_vnd`.
3. Verify that changing `variant.cost_price_vnd` afterwards does not mutate previously created `OrderItem.cost_price_vnd`.

- [ ] **Step 2: Run test to verify failure (RED)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_cogs_snapshot.py -v`
Expected: FAIL (OrderItem.cost_price_vnd is 0 instead of variant.cost_price_vnd).

- [ ] **Step 3: Update `checkout/service.py` and `pos/service.py` to pass `cost_price_vnd`**

In `services/ecommerce-api/app/modules/checkout/service.py`:
```python
            order_items.append(
                OrderItem(
                    public_id=uuid7(),
                    variant_id=variant_id,
                    product_public_id_snapshot=product.public_id,
                    category_code_snapshot=category.code,
                    category_name_snapshot=category.name,
                    product_name_snapshot=product.name,
                    sku_snapshot=variant.sku,
                    size_code_snapshot=variant.size_code,
                    color_code_snapshot=variant.color_code,
                    unit_price_vnd=variant.price_vnd,
                    cost_price_vnd=variant.cost_price_vnd,
                    quantity=quantity,
                    line_total_vnd=line_total,
                    created_at=now,
                )
            )
```

In `services/ecommerce-api/app/modules/pos/service.py`:
```python
            # Fetch cost_price_vnd from variant in store_items
            variant_cost = variant.cost_price_vnd if hasattr(variant, "cost_price_vnd") else 0
            order_item = OrderItem(
                public_id=uuid7(),
                order_id=order.order_id,
                variant_id=item_data["variant_id"],
                product_public_id_snapshot=uuid7(),
                category_code_snapshot="",
                category_name_snapshot="",
                product_name_snapshot=item_data["product_name"],
                sku_snapshot=item_data["sku"],
                size_code_snapshot=item_data["size_code"],
                color_code_snapshot=item_data["color_code"],
                unit_price_vnd=item_data["unit_price_vnd"],
                cost_price_vnd=item_data.get("cost_price_vnd", 0),
                quantity=item_data["quantity"],
                line_total_vnd=item_data["line_total_vnd"],
                created_at=now,
            )
```

- [ ] **Step 4: Run test to verify it passes (GREEN)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_cogs_snapshot.py -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests`
Expected: All tests pass (0 regression).

- [ ] **Step 6: Commit**

```bash
git add services/ecommerce-api/app/modules/checkout/service.py services/ecommerce-api/app/modules/pos/service.py services/ecommerce-api/tests/test_cogs_snapshot.py
git commit -m "feat(cogs): snapshot variant cost_price_vnd on online and POS checkout"
```

---

### Task 3: Backend Inbound API & Moving Weighted Average Costing

**Files:**
- Create: `services/ecommerce-api/app/modules/inbound/__init__.py`
- Create: `services/ecommerce-api/app/modules/inbound/schemas.py`
- Create: `services/ecommerce-api/app/modules/inbound/service.py`
- Create: `services/ecommerce-api/app/modules/inbound/router.py`
- Modify: `services/ecommerce-api/app/modules/admin/schemas.py` (ensure `AdminVariantResponse.cost_price_vnd`)
- Modify: `services/ecommerce-api/app/api/router.py` (mount inbound router)
- Test: `services/ecommerce-api/tests/test_inbound_costing_api.py`

**Interfaces:**
- Consumes: `InboundReceipt`, `InboundReceiptItem`, `Inventory`, `InventoryTransaction`, `ProductVariant`.
- Produces:
  - `POST /api/v1/admin/inbound/receipts`
  - `GET /api/v1/admin/inbound/receipts`
  - `GET /api/v1/admin/inbound/receipts/{receipt_code}`

- [ ] **Step 1: Write integration tests in `services/ecommerce-api/tests/test_inbound_costing_api.py`**

Test scenarios:
1. Inbound receipt successfully creates receipt, increases `inventory.on_hand` and `inventory.opening_on_hand`, creates `InventoryTransaction(movement_type='inbound')`.
2. Cost price updates according to moving weighted average formula:
   - Existing: 10 units @ 100,000 VND
   - Inbound: 20 units @ 130,000 VND
   - New cost price: round((10*100000 + 20*130000) / 30) = 120,000 VND.
3. Edge case: Existing inventory is 0:
   - New cost price = Inbound unit cost.
4. Validation:
   - Reject duplicate `variant_id` in items payload with 422.
   - Reject `quantity <= 0` with 422.
   - Reject non-existent `variant_id` with 404.
5. List and Detail retrieval endpoints work as expected.

- [ ] **Step 2: Run test to verify it fails (RED)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_inbound_costing_api.py -v`
Expected: FAIL (404 Not Found / router not mounted).

- [ ] **Step 3: Implement Schemas, Service & Router for Inbound Receipts**

1. `schemas.py`:
```python
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class InboundReceiptItemPayload(BaseModel):
    variant_id: int
    quantity: int = Field(ge=1)
    unit_cost_vnd: int = Field(ge=0)

class CreateInboundReceiptPayload(BaseModel):
    batch_name: str = Field(min_length=3, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)
    items: list[InboundReceiptItemPayload] = Field(min_length=1, max_length=200)

    @field_validator("items")
    @classmethod
    def validate_unique_variants(cls, v: list[InboundReceiptItemPayload]):
        ids = [item.variant_id for item in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Danh sách sản phẩm nhập không được chứa mã variant trùng lặp.")
        return v

class InboundReceiptItemDetailResponse(BaseModel):
    item_id: int
    variant_id: int
    product_name: str
    sku: str
    size_code: str
    color_code: str
    quantity: int
    unit_cost_vnd: int
    total_cost_vnd: int
    previous_cost_price_vnd: int
    new_cost_price_vnd: int

class InboundReceiptDetailResponse(BaseModel):
    receipt_id: int
    receipt_code: str
    batch_name: str
    status: str
    total_items_count: int
    total_cost_vnd: int
    notes: str | None = None
    created_by_name: str | None = None
    created_at: datetime
    items: list[InboundReceiptItemDetailResponse]

class InboundReceiptSummaryResponse(BaseModel):
    receipt_id: int
    receipt_code: str
    batch_name: str
    status: str
    total_items_count: int
    total_cost_vnd: int
    created_by_name: str | None = None
    created_at: datetime

class InboundReceiptListResponse(BaseModel):
    items: list[InboundReceiptSummaryResponse]
    total: int
```

2. `service.py`:
Implement:
- `create_inbound_receipt(db, admin_customer_id, payload, idempotency_key)`:
  - Generate receipt_code `INB-YYYYMMDD-XXXXXX`.
  - For each item:
    - Lock `Inventory` (`with_for_update()`) and `ProductVariant` (`with_for_update()`).
    - If `Inventory` does not exist: create `Inventory(variant_id=..., opening_on_hand=0, on_hand=0)`.
    - Current qty = `inv.on_hand`, Current cost = `variant.cost_price_vnd`.
    - New cost = `round((current_qty * current_cost + item.quantity * item.unit_cost_vnd) / (current_qty + item.quantity))` if `current_qty + item.quantity > 0` else `item.unit_cost_vnd`.
    - Update `variant.cost_price_vnd = new_cost`.
    - Update `inv.on_hand += item.quantity`, `inv.opening_on_hand += item.quantity`, `inv.version += 1`.
    - Create `InventoryTransaction(public_id=uuid4(), variant_id=variant.variant_id, location_type='central_warehouse', movement_type='inbound', quantity_delta=item.quantity, reference_code=receipt_code, notes=f"Nhập kho thành phẩm: {payload.batch_name}")`.
    - Record `InboundReceiptItem(...)`.
  - Save `InboundReceipt(...)`.
- `list_inbound_receipts(db, search, limit, offset)`
- `get_inbound_receipt_detail(db, receipt_code)`

3. `router.py`:
Mount under `/admin/inbound` with `get_current_admin`, `verify_csrf`, `_require_idempotency_key`.

4. Update `services/ecommerce-api/app/api/router.py`.
5. Update `AdminVariantResponse` in `admin/schemas.py` and `admin/service.py` to include `cost_price_vnd: int = 0`.

- [ ] **Step 4: Run test to verify it passes (GREEN)**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests/test_inbound_costing_api.py -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests`
Expected: All tests pass (0 regression).

- [ ] **Step 6: Commit**

```bash
git add services/ecommerce-api/app/modules/inbound/ services/ecommerce-api/app/modules/admin/ services/ecommerce-api/app/api/router.py services/ecommerce-api/tests/test_inbound_costing_api.py
git commit -m "feat(inbound): implement admin inbound receipts and moving weighted average costing"
```

---

### Task 4: Frontend API Client Types & Admin Navigation

**Files:**
- Modify: `apps/storefront/src/lib/commerce.ts`
- Modify: `apps/storefront/src/lib/api.ts`
- Modify: `apps/storefront/src/components/AdminNav.tsx`

**Interfaces:**
- Consumes: Backend Inbound API endpoints.
- Produces:
  - TypeScript interfaces: `InboundReceiptSummary`, `InboundReceiptItemDetail`, `InboundReceiptDetail`, `CreateInboundReceiptInput`.
  - Client functions: `getAdminInboundReceipts`, `getAdminInboundReceiptDetail`, `createAdminInboundReceipt`.
  - AdminNav with `/admin/inbound` tab.

- [ ] **Step 1: Add types and functions to `commerce.ts` & `api.ts`**

Interfaces:
```typescript
export interface InboundReceiptItemDetail {
  item_id: number;
  variant_id: number;
  product_name: string;
  sku: string;
  size_code: string;
  color_code: string;
  quantity: number;
  unit_cost_vnd: number;
  total_cost_vnd: number;
  previous_cost_price_vnd: number;
  new_cost_price_vnd: number;
}

export interface InboundReceiptDetail {
  receipt_id: number;
  receipt_code: string;
  batch_name: string;
  status: string;
  total_items_count: number;
  total_cost_vnd: number;
  notes?: string | null;
  created_by_name?: string | null;
  created_at: string;
  items: InboundReceiptItemDetail[];
}

export interface InboundReceiptSummary {
  receipt_id: number;
  receipt_code: string;
  batch_name: string;
  status: string;
  total_items_count: number;
  total_cost_vnd: number;
  created_by_name?: string | null;
  created_at: string;
}

export interface CreateInboundReceiptItemInput {
  variant_id: number;
  quantity: number;
  unit_cost_vnd: number;
}

export interface CreateInboundReceiptInput {
  batch_name: string;
  notes?: string | null;
  items: CreateInboundReceiptItemInput[];
}
```

Functions:
- `getAdminInboundReceipts(params?: { search?: string; limit?: number; offset?: number })`
- `getAdminInboundReceiptDetail(receiptCode: string)`
- `createAdminInboundReceipt(input: CreateInboundReceiptInput, idempotencyKey: string)`
Update `AdminProductVariant` / `variant` types in storefront to include `cost_price_vnd?: number`.

- [ ] **Step 2: Update `AdminNav.tsx`**

Add `{ href: "/admin/inbound", label: "Nhập kho sản xuất", icon: "box" }` to `links`.

- [ ] **Step 3: Run typecheck to verify**

Run: `npm --prefix apps/storefront run typecheck`
Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
git add apps/storefront/src/lib/commerce.ts apps/storefront/src/lib/api.ts apps/storefront/src/components/AdminNav.tsx
git commit -m "feat(storefront): add inbound API client functions, types and AdminNav tab"
```

---

### Task 5: Frontend Admin Inbound Management Pages & Modal

**Files:**
- Create: `apps/storefront/src/components/admin/CreateInboundModal.tsx`
- Create: `apps/storefront/src/app/admin/inbound/page.tsx`
- Create: `apps/storefront/src/app/admin/inbound/[receiptCode]/page.tsx`

**Interfaces:**
- Consumes: `getAdminInboundReceipts`, `getAdminInboundReceiptDetail`, `createAdminInboundReceipt`, `getAdminProducts`.
- Produces:
  - Trang `/admin/inbound`: Danh sách các đợt nhập kho xưởng, thẻ thống kê, tìm kiếm và nút mở modal tạo phiếu.
  - `CreateInboundModal.tsx`: Chọn sản phẩm, nhập số lượng & chi phí, có **Live Costing Preview** (xem trước giá vốn mới tự động).
  - Trang `/admin/inbound/[receiptCode]`: Chi tiết phiếu nhập, bảng đối soát giá vốn cũ $\rightarrow$ giá vốn mới.

- [ ] **Step 1: Implement `CreateInboundModal.tsx`**

Build modal:
- Input: Tên đợt sản xuất / xưởng may (`batch_name`, required).
- Textarea: Ghi chú (`notes`).
- Product variant selector:
  - Load products list from `getAdminProducts()`.
  - Dropdown / search selector to pick a variant.
  - Displays: Tồn kho hiện tại (`on_hand`), Giá vốn hiện tại (`cost_price_vnd`).
  - Inputs for selected variant:
    - Số lượng xuất xưởng ($quantity > 0$).
    - Chi phí sản xuất xuất xưởng ($unit\_cost\_vnd \ge 0$).
  - **Live Costing Preview badge**:
    $$\text{Dự kiến giá vốn mới} = \text{round}\left(\frac{on\_hand \times cost\_price + qty \times unit\_cost}{on\_hand + qty}\right)$$
- Total receipt summary: Tổng số lượng, Tổng chi phí sản xuất.
- Submit: calls `createAdminInboundReceipt(payload, idempotencyKey)`.

- [ ] **Step 2: Implement `apps/storefront/src/app/admin/inbound/page.tsx`**

- Thẻ thống kê: Tổng số đợt nhập xưởng, Tổng sản phẩm đã nhập, Tổng chi phí sản xuất tích lũy.
- Ô tìm kiếm theo mã phiếu, tên đợt sản xuất.
- Nút "Tạo phiếu nhập mới" mở `CreateInboundModal`.
- Bảng danh sách phiếu nhập:
  - Mã phiếu (link to `/admin/inbound/[receiptCode]`)
  - Tên đợt sản xuất
  - Số lượng sản phẩm
  - Tổng chi phí sản xuất (`formatVnd`)
  - Người thực hiện
  - Thời gian (`formatVietnamDateTime`)
  - Nút "Chi tiết"

- [ ] **Step 3: Implement `apps/storefront/src/app/admin/inbound/[receiptCode]/page.tsx`**

- Fetch detail via `getAdminInboundReceiptDetail(receiptCode)`.
- Card thông tin phiếu: Mã phiếu, Tên đợt sản xuất, Người nhập, Ngày nhập, Ghi chú, Tổng tiền.
- Bảng chi tiết sản phẩm: Tên sản phẩm, SKU, Size, Màu, Số lượng, Đơn giá xuất xưởng, Cột biến động **Giá vốn cũ $\rightarrow$ Giá vốn mới**, Thành tiền.

- [ ] **Step 4: Verify typecheck & build**

Run: `npm --prefix apps/storefront run typecheck`
Run: `npm --prefix apps/storefront run build`
Expected: 0 errors, build thành công.

- [ ] **Step 5: Commit**

```bash
git add apps/storefront/src/components/admin/CreateInboundModal.tsx apps/storefront/src/app/admin/inbound/
git commit -m "feat(storefront): implement admin inbound receipts listing, creation modal and detail page"
```

---

### Task 6: Frontend Product Management COGS Display & End-to-End Verification

**Files:**
- Modify: `apps/storefront/src/app/admin/products/page.tsx`
- Test: Full backend test suite & Next.js production build

- [ ] **Step 1: Update `apps/storefront/src/app/admin/products/page.tsx`**

- In the variants subtable of each product:
  Add column: **Giá vốn (COGS)** displaying `formatVnd(variant.cost_price_vnd ?? 0)` with a subtle badge or muted text right next to Giá bán.

- [ ] **Step 2: Run full backend test suite**

Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests -v`
Expected: All 148+ tests pass cleanly (0 regression).

- [ ] **Step 3: Run storefront typecheck and build**

Run: `npm --prefix apps/storefront run typecheck`
Run: `npm --prefix apps/storefront run build`
Expected: 0 errors, all 26 routes build pass.

- [ ] **Step 4: Commit**

```bash
git add apps/storefront/src/app/admin/products/page.tsx
git commit -m "feat(storefront): display COGS in admin product variants table"
```
