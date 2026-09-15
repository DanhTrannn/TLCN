# POS & Multi-Store Inventory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng hệ thống POS (bán tại quầy) + phân bổ đơn hàng online theo cửa hàng + đồng bộ tồn kho kép (global + store)

**Architecture:** 
- Bảng `orders` mở rộng thêm `store_id`, `channel`, `staff_id`
- Tồn kho dùng mô hình Allocation: `inventory` = tổng, `store_inventory` = phân bổ theo cửa hàng
- Online order tự động gán cửa hàng theo địa chỉ khách + fallback kho tổng
- POS order trừ cả 2 bảng inventory atomically

**Tech Stack:** Next.js 15, FastAPI, MySQL 8.4, SQLAlchemy, Alembic, React 19, Tailwind CSS

**Spec:** `docs/superpowers/specs/2026-09-15-pos-multi-store-design.md`

---

## Global Constraints

- Python 3.12+, FastAPI, SQLAlchemy 2.0+ (async-style mapped_column)
- MySQL 8.4, charset utf8mb4
- Next.js 15 App Router, React 19, Tailwind CSS
- Frontend: không dùng UI library, custom components
- Backend: `run_in_transaction()` cho mọi write operations
- Models: BIGINT UNSIGNED PK, UUID public_id, datetime(6)
- Validation: Pydantic v2, min/max length
- Tests: pytest, mock DB via `app.dependency_overrides[get_db]`

---

## Thiết Kế Tổng Quan

### Mô Hình Tồn Kho Allocation

**Vấn đề:** Hệ thống hiện tại có 2 bảng tồn kho (`inventory` toàn cục và `store_inventory` theo cửa hàng) nhưng không liên kết với nhau. Khi mua online chỉ trừ `inventory`, `store_inventory` không thay đổi → dữ liệu lệch.

**Giải pháp:** Mô hình Allocation - `inventory.on_hand` là tổng tồn kho thực sự của company, `store_inventory.on_hand` là phần tồn kho được phân bổ cho từng cửa hàng. Tổng tất cả `store_inventory` ≤ `inventory`.

```
inventory.on_hand = 100 (tổng tồn kho company)
    ├── kho_tổng = 40 (chưa phân bổ)
    ├── store_A = 30 (đang ở cửa hàng A)
    ├── store_B = 20 (đang ở cửa hàng B)
    └── store_C = 10 (đang ở cửa hàng C)
```

**Lý do chọn mô hình này:**
1. Phù hợp với thực tế retail Việt Nam (CellphoneS, TGDĐ)
2. Online order có thể fulfill từ cửa hàng gần nhất hoặc kho tổng
3. POS order luôn trừ từ cửa hàng
4. Dễ mở rộng cho chuyển kho giữa các cửa hàng

### Flow Đơn Hàng Online

```
1. Customer nhập địa chỉ giao hàng
2. Hệ thống parse tên Tỉnh/TP từ địa chỉ
3. Tìm cửa hàng trong thành phố có TẤT CẢ items
4. Nếu có 1 cửa hàng có đủ → Gán đơn + trừ store_inventory
5. Nếu không cửa hàng nào có đủ → Fallback toàn bộ về kho tổng
6. Luôn trừ inventory.on_hand
```

**Lý do:** Ưu tiên fulfill từ 1 cửa hàng duy nhất để giảm chi phí vận chuyển. Nếu không cửa hàng nào có đủ tất cả items → fallback toàn bộ về kho tổng (không tách đơn).

### Flow POS

```
1. Nhân viên nhập mã sản phẩm
2. Hệ thống tìm SP + hiển thị tồn kho tại cửa hàng
3. Nhân viên nhập số lượng
4. Thêm vào giỏ POS
5. Khi xong → Click "Thanh toán"
6. Xác nhận → Trừ cả inventory + store_inventory atomically
7. Đơn hàng tự động "completed" (bán tại quầy, không cần ship)
```

**Lý do:** POS bán tại quầy nên đơn hàng hoàn thành ngay lập tức, không cần quy trình confirm như online. Trừ cả 2 bảng để đảm bảo dữ liệu nhất quán.

### Phân Quyền

| Action | Admin | City Planner | Store Manager |
|--------|-------|--------------|---------------|
| Xem tất cả đơn online | ✅ | ❌ | ❌ |
| Xem đơn POS cửa hàng mình | ✅ | ✅ (cùng TP) | ✅ |
| Xác nhận đơn online | ✅ | ✅ (cùng TP) | ✅ |
| Tạo đơn POS | ✅ | ✅ | ✅ |
| Xem tồn kho toàn hệ thống | ✅ | ❌ | ❌ |
| Xem tồn kho thành phố | ✅ | ✅ | ❌ |
| Xem tồn kho cửa hàng | ✅ | ✅ | ✅ |

---

## File Structure

### Backend Files

| File | Action | Mô tả | Lý do |
|------|--------|-------|-------|
| `services/ecommerce-api/app/models/order.py` | Modify | Thêm `store_id`, `channel`, `staff_id` | Đơn hàng cần biết kênh bán (online/POS) và cửa hàng fulfill |
| `services/ecommerce-api/app/modules/pos/__init__.py` | Create | POS module | Tách riêng POS logic thành module độc lập |
| `services/ecommerce-api/app/modules/pos/router.py` | Create | POS endpoints | API endpoints cho POS |
| `services/ecommerce-api/app/modules/pos/service.py` | Create | POS business logic | Business logic tìm SP + tạo đơn POS |
| `services/ecommerce-api/app/modules/pos/schemas.py` | Create | POS schemas | Request/response validation |
| `services/ecommerce-api/app/modules/checkout/service.py` | Modify | Thêm store allocation | Online order cần tự động gán cửa hàng |
| `services/ecommerce-api/app/modules/checkout/allocation.py` | Create | Store allocation logic | Tách riêng logic phân bổ cửa hàng |
| `services/ecommerce-api/app/modules/admin/router.py` | Modify | Thêm POS routes | Đăng ký POS endpoints |
| `services/ecommerce-api/app/db/deps.py` | Modify | Thêm `get_current_store_manager` | Auth cho store manager |
| `database/migrations/versions/0011_pos_order_channel.py` | Create | Migration mới | Schema thay đổi |

### Frontend Files

| File | Action | Mô tả | Lý do |
|------|--------|-------|-------|
| `apps/storefront/src/app/admin/pos/page.tsx` | Create | POS UI | Giao diện bán hàng tại quầy |
| `apps/storefront/src/components/AdminNav.tsx` | Modify | Thêm nav POS | Điều hướng đến POS |
| `apps/storefront/src/app/admin/orders/page.tsx` | Modify | Thêm filter channel/store | Lọc đơn theo kênh và cửa hàng |

---

## Task 1: Database Migration - Thêm fields vào orders

**Files:**
- Create: `database/migrations/versions/0011_pos_order_channel.py`
- Modify: `services/ecommerce-api/app/models/order.py:12-38`

**Interfaces:**
- Consumes: None
- Produces: Order model mới với `store_id`, `channel`, `staff_id`

**Lý do:** Đơn hàng cần lưu thông tin kênh bán (online/POS), cửa hàng fulfill (store_id), và nhân viên tạo đơn (staff_id) để phân quyền và theo dõi.

- [ ] **Step 1: Đọc migration template hiện tại**

Đọc `database/migrations/versions/0001_initial_schema.py` để hiểu format.

- [ ] **Step 2: Tạo migration mới**

```python
# database/migrations/versions/0011_pos_order_channel.py
"""Add POS fields to orders table.

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-15
"""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("orders", sa.Column("store_id", sa.BigInteger(), nullable=True))
    op.add_column("orders", sa.Column("channel", sa.String(16), nullable=False, server_default="online"))
    op.add_column("orders", sa.Column("staff_id", sa.BigInteger(), nullable=True))
    op.create_index("ix_orders_channel", "orders", ["channel"])
    op.create_index("ix_orders_store_id", "orders", ["store_id"])
    op.create_foreign_key("fk_orders_store", "orders", "stores", ["store_id"], ["store_id"])

def downgrade() -> None:
    op.drop_constraint("fk_orders_store", "orders", type_="foreignkey")
    op.drop_index("ix_orders_store_id")
    op.drop_index("ix_orders_channel")
    op.drop_column("orders", "staff_id")
    op.drop_column("orders", "channel")
    op.drop_column("orders", "store_id")
```

- [ ] **Step 3: Cập nhật Order model**

```python
# services/ecommerce-api/app/models/order.py
# Thêm vào class Order:
store_id: Mapped[int | None] = mapped_column(BigInteger(), ForeignKey("stores.store_id"), nullable=True)
channel: Mapped[str] = mapped_column(String(16), nullable=False, default="online")
staff_id: Mapped[int | None] = mapped_column(BigInteger(), ForeignKey("customers.customer_id"), nullable=True)
```

- [ ] **Step 4: Chạy migration**

```bash
docker exec tlcn-ecommerce-api-1 alembic upgrade head
```

- [ ] **Step 5: Verify**

```bash
docker exec tlcn-mysql-1 mysql -u ecommerce_app -ppassword ecommerce -Bse "DESCRIBE orders;" | grep -E "store_id|channel|staff_id"
```

- [ ] **Step 6: Commit**

```bash
git add database/migrations/versions/0011_pos_order_channel.py services/ecommerce-api/app/models/order.py
git commit -m "feat(db): add store_id, channel, staff_id to orders for POS support"
```

---

## Task 2: POS Schemas

**Files:**
- Create: `services/ecommerce-api/app/modules/pos/schemas.py`

**Interfaces:**
- Consumes: None
- Produces: `POSTItemRequest`, `POSTransactionRequest`, `POSTransactionResponse`, `ProductSearchResponse`

**Lý do:** Tách riêng POS schemas để validation rõ ràng, dễ maintain. POS có request/response khác với checkout online.

- [ ] **Step 1: Tạo schemas**

```python
# services/ecommerce-api/app/modules/pos/schemas.py
from pydantic import BaseModel, ConfigDict, Field


class POSTItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    variant_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=999)


class POSTransactionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    store_id: int = Field(gt=0)
    items: list[POSTItemRequest] = Field(min_length=1)
    payment_method: str = Field(pattern=r"^(cash|card)$")
    amount_received_vnd: int | None = Field(default=None, ge=0)


class POSTItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    variant_id: int
    product_name: str
    sku: str
    size_code: str
    color_code: str
    unit_price_vnd: int
    quantity: int
    line_total_vnd: int


class POSTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    order_number: str
    status: str
    channel: str
    store_id: int
    payment_method: str
    items: list[POSTItemResponse]
    subtotal_vnd: int
    total_vnd: int
    created_at: str


class POSProductSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    variant_id: int
    product_name: str
    sku: str
    size_code: str
    color_code: str
    price_vnd: int
    store_stock: int
    global_stock: int
```

- [ ] **Step 2: Verify imports**

```bash
cd services/ecommerce-api && python -c "from app.modules.pos.schemas import POSTransactionRequest; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add services/ecommerce-api/app/modules/pos/schemas.py
git commit -m "feat(pos): add POS request/response schemas"
```

---

## Task 3: POS Service - Tìm sản phẩm

**Files:**
- Create: `services/ecommerce-api/app/modules/pos/service.py`
- Create: `services/ecommerce-api/tests/test_pos_service.py`

**Interfaces:**
- Consumes: Product, ProductVariant, Inventory, StoreInventory models
- Produces: `search_products()`, `create_pos_transaction()`

**Lý do:** POS cần tìm sản phẩm theo SKU hoặc tên để nhân viên nhanh chóng tìm SP cần bán. Hiển thị tồn kho tại cửa hàng để nhân viên biết còn hàng không.

- [ ] **Step 1: Viết test search_products**

```python
# services/ecommerce-api/tests/test_pos_service.py
import pytest
from unittest.mock import MagicMock, patch
from app.modules.pos.service import search_products


def test_search_products_by_sku():
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter([
        MagicMock(
            variant_id=1,
            product_name="Áo Polo Nam",
            sku="APN001",
            size_code="L",
            color_code="DEN",
            price_vnd=300000,
            store_on_hand=5,
            global_on_hand=20,
        )
    ]))
    mock_db.execute.return_value = mock_result
    
    results = search_products(mock_db, store_id=1, query="APN001")
    assert len(results) == 1
    assert results[0].sku == "APN001"


def test_search_products_empty():
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter([]))
    mock_db.execute.return_value = mock_result
    
    results = search_products(mock_db, store_id=1, query="NONEXISTENT")
    assert len(results) == 0
```

- [ ] **Step 2: Chạy test để verify fail**

```bash
cd services/ecommerce-api && python -m pytest tests/test_pos_service.py -v
```
Expected: FAIL (module not found)

- [ ] **Step 3: Viết minimal implementation**

```python
# services/ecommerce-api/app/modules/pos/service.py
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.catalog import Product, ProductVariant
from app.models.inventory import Inventory
from app.models.multicity import StoreInventory


def search_products(db: Session, store_id: int, query: str) -> list[dict]:
    stmt = (
        select(
            ProductVariant.variant_id,
            Product.name.label("product_name"),
            ProductVariant.sku,
            ProductVariant.size_code,
            ProductVariant.color_code,
            ProductVariant.price_vnd,
            func.coalesce(StoreInventory.on_hand, 0).label("store_on_hand"),
            func.coalesce(Inventory.on_hand, 0).label("global_stock"),
        )
        .join(Product, Product.product_id == ProductVariant.product_id)
        .outerjoin(Inventory, Inventory.variant_id == ProductVariant.variant_id)
        .outerjoin(
            StoreInventory,
            (StoreInventory.variant_id == ProductVariant.variant_id)
            & (StoreInventory.store_id == store_id),
        )
        .where(ProductVariant.is_active == True)  # noqa: E712
        .where(Product.is_active == True)  # noqa: E712
        .where(
            (ProductVariant.sku.ilike(f"%{query}%"))
            | (Product.name.ilike(f"%{query}%"))
        )
        .limit(20)
    )
    rows = db.execute(stmt).all()
    return [dict(row._mapping) for row in rows]
```

- [ ] **Step 4: Chạy test để verify pass**

```bash
cd services/ecommerce-api && python -m pytest tests/test_pos_service.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/ecommerce-api/app/modules/pos/service.py services/ecommerce-api/tests/test_pos_service.py
git commit -m "feat(pos): add product search service for POS"
```

---

## Task 4: POS Service - Tạo đơn hàng POS

**Files:**
- Modify: `services/ecommerce-api/app/modules/pos/service.py`
- Modify: `services/ecommerce-api/tests/test_pos_service.py`

**Interfaces:**
- Consumes: POSTransactionRequest
- Produces: `create_pos_transaction()` → order dict

**Lý do:** Tạo đơn POS cần: (1) Validate cửa hàng active, (2) Check tồn kho tại cửa hàng, (3) Trừ cả 2 bảng inventory atomically, (4) Tạo order + payment + history. Đơn POS tự động "completed" vì bán tại quầy.

- [ ] **Step 1: Viết test create_pos_transaction**

```python
# Thêm vào tests/test_pos_service.py
from app.modules.pos.service import create_pos_transaction
from app.modules.pos.schemas import POSTransactionRequest, POSTItemRequest
from app.core.exceptions import OUT_OF_STOCK, StoreNotFound


def test_create_pos_transaction_success():
    mock_db = MagicMock()
    mock_store = MagicMock(is_active=True)
    mock_db.query.return_value.filter_by.return_value.first.return_value = mock_store
    
    # Mock inventory check passes
    mock_inventory = MagicMock(on_hand=10)
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_inventory
    
    request = POSTransactionRequest(
        store_id=1,
        items=[POSTItemRequest(variant_id=10, quantity=2)],
        payment_method="cash",
        amount_received_vnd=1000000,
    )
    
    with patch("app.modules.pos.service.new_order_number", return_value="POS-001"):
        result = create_pos_transaction(mock_db, request, staff_id=1)
    
    assert result["order_number"] == "POS-001"
    assert result["channel"] == "pos"


def test_create_pos_transaction_insufficient_stock():
    mock_db = MagicMock()
    mock_store = MagicMock(is_active=True)
    mock_db.query.return_value.filter_by.return_value.first.return_value = mock_store
    
    # Mock inventory check fails
    mock_inventory = MagicMock(on_hand=1)
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_inventory
    
    request = POSTransactionRequest(
        store_id=1,
        items=[POSTItemRequest(variant_id=10, quantity=5)],
        payment_method="cash",
    )
    
    with pytest.raises(OUT_OF_STOCK):
        create_pos_transaction(mock_db, request, staff_id=1)
```

- [ ] **Step 2: Chạy test để verify fail**

```bash
cd services/ecommerce-api && python -m pytest tests/test_pos_service.py::test_create_pos_transaction_success -v
```
Expected: FAIL

- [ ] **Step 3: Viết implementation**

```python
# Thêm vào services/ecommerce-api/app/modules/pos/service.py
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.core.exceptions import OUT_OF_STOCK, StoreNotFound
from app.core.utils import new_order_number
from app.db.uow import run_in_transaction
from app.models.catalog import ProductVariant
from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.multicity import Store, StoreInventory
from app.models.order import Order, OrderItem, OrderStatusHistory, Payment
from app.modules.pos.schemas import POSTransactionRequest


def create_pos_transaction(
    db: Session, request: POSTransactionRequest, staff_id: int
) -> dict:
    with run_in_transaction(db):
        # Validate store exists and is active
        store = db.execute(
            select(Store).where(Store.store_id == request.store_id, Store.is_active == True)  # noqa: E712
        ).scalar_one_or_none()
        if not store:
            raise StoreNotFound("Cửa hàng không tồn tại hoặc đã ngừng hoạt động")

        now = datetime.now(timezone.utc)
        order_number = new_order_number()

        # Build order items and validate stock
        order_items = []
        subtotal = 0

        for item in request.items:
            # Check variant exists
            variant = db.execute(
                select(ProductVariant).where(
                    ProductVariant.variant_id == item.variant_id,
                    ProductVariant.is_active == True,  # noqa: E712
                )
            ).scalar_one_or_none()
            if not variant:
                raise OUT_OF_STOCK(f"Variant {item.variant_id} không tồn tại")

            # Check store inventory
            store_inv = db.execute(
                select(StoreInventory).where(
                    StoreInventory.store_id == request.store_id,
                    StoreInventory.variant_id == item.variant_id,
                ).with_for_update()
            ).scalar_one_or_none()

            if not store_inv or store_inv.on_hand < item.quantity:
                raise OUT_OF_STOCK(
                    f"{variant.sku} không đủ hàng tại cửa hàng (còn {store_inv.on_hand if store_inv else 0})"
                )

            line_total = variant.price_vnd * item.quantity
            subtotal += line_total

            order_items.append({
                "variant_id": variant.variant_id,
                "product_name": variant.product.name if hasattr(variant, 'product') else "",
                "sku": variant.sku,
                "size_code": variant.size_code,
                "color_code": variant.color_code,
                "unit_price_vnd": variant.price_vnd,
                "quantity": item.quantity,
                "line_total_vnd": line_total,
                "product_public_id": str(variant.product.public_id) if hasattr(variant, 'product') else "",
            })

            # Deduct store inventory
            store_inv.on_hand -= item.quantity
            store_inv.version += 1
            store_inv.updated_at = now

            # Deduct global inventory
            global_inv = db.execute(
                select(Inventory).where(
                    Inventory.variant_id == item.variant_id,
                ).with_for_update()
            ).scalar_one_or_none()
            if global_inv:
                global_inv.on_hand -= item.quantity
                global_inv.version += 1
                global_inv.updated_at = now

        total = subtotal  # POS: no shipping fee

        # Create order
        order = Order(
            order_number=order_number,
            customer_id=staff_id,  # Staff acts as customer for POS
            store_id=request.store_id,
            channel="pos",
            staff_id=staff_id,
            status="completed",
            currency_code="VND",
            subtotal_vnd=subtotal,
            discount_amount_vnd=0,
            shipping_fee_vnd=0,
            total_vnd=total,
            receiver_name="POS Customer",
            receiver_phone="",
            shipping_address_text=store.address or "",
            data_origin="manual",
            paid_at=now,
            completed_at=now,
        )
        db.add(order)
        db.flush()

        # Create order items
        for item_data in order_items:
            order_item = OrderItem(
                order_id=order.order_id,
                variant_id=item_data["variant_id"],
                product_public_id_snapshot=item_data["product_public_id"],
                product_name_snapshot=item_data["product_name"],
                sku_snapshot=item_data["sku"],
                size_code_snapshot=item_data["size_code"],
                color_code_snapshot=item_data["color_code"],
                unit_price_vnd=item_data["unit_price_vnd"],
                quantity=item_data["quantity"],
                line_total_vnd=item_data["line_total_vnd"],
            )
            db.add(order_item)

        # Create payment
        payment = Payment(
            order_id=order.order_id,
            status="succeeded",
            amount_vnd=total,
        )
        db.add(payment)

        # Create status history
        history = OrderStatusHistory(
            order_id=order.order_id,
            from_status=None,
            to_status="completed",
            transition_source="pos",
        )
        db.add(history)

        db.flush()

        return {
            "order_number": order.order_number,
            "status": order.status,
            "channel": order.channel,
            "store_id": order.store_id,
            "payment_method": request.payment_method,
            "items": order_items,
            "subtotal_vnd": subtotal,
            "total_vnd": total,
            "created_at": now.isoformat(),
        }
```

- [ ] **Step 4: Chạy test để verify pass**

```bash
cd services/ecommerce-api && python -m pytest tests/test_pos_service.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/ecommerce-api/app/modules/pos/service.py services/ecommerce-api/tests/test_pos_service.py
git commit -m "feat(pos): add POS transaction creation with dual inventory deduction"
```

---

## Task 5: POS Router

**Files:**
- Create: `services/ecommerce-api/app/modules/pos/router.py`
- Modify: `services/ecommerce-api/app/api/router.py`

**Interfaces:**
- Consumes: `search_products()`, `create_pos_transaction()` from Task 3-4
- Produces: `GET /api/v1/pos/products`, `POST /api/v1/pos/transactions`

**Lý do:** Tách POS router riêng để manage endpoints, dễ maintain và mở rộng. Sử dụng `get_current_staff` dependency để phân quyền staff.

- [ ] **Step 1: Tạo router**

```python
# services/ecommerce-api/app/modules/pos/router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db, get_current_staff
from app.modules.pos.schemas import POSTransactionRequest, POSTransactionResponse, POSProductSearchResponse
from app.modules.pos.service import search_products, create_pos_transaction

router = APIRouter(prefix="/api/v1/pos", tags=["pos"])


@router.get("/products", response_model=list[POSProductSearchResponse])
def list_products(
    store_id: int,
    search: str = "",
    db: Session = Depends(get_db),
    _staff=Depends(get_current_staff),
):
    return search_products(db, store_id=store_id, query=search)


@router.post("/transactions", response_model=POSTransactionResponse)
def create_transaction(
    request: POSTransactionRequest,
    db: Session = Depends(get_db),
    staff=Depends(get_current_staff),
):
    result = create_pos_transaction(db, request, staff_id=staff.customer_id)
    return result
```

- [ ] **Step 2: Đăng ký router**

```python
# services/ecommerce-api/app/api/router.py
# Thêm import và include:
from app.modules.pos.router import router as pos_router
api_router.include_router(pos_router)
```

- [ ] **Step 3: Verify endpoints exist**

```bash
docker exec tlcn-ecommerce-api-1 python -c "from app.modules.pos.router import router; print('OK')"
```

- [ ] **Step 4: Commit**

```bash
git add services/ecommerce-api/app/modules/pos/router.py services/ecommerce-api/app/api/router.py
git commit -m "feat(pos): add POS API endpoints"
```

---

## Task 6: Store Allocation Logic (Online Orders)

**Files:**
- Modify: `services/ecommerce-api/app/modules/checkout/service.py:207-304`
- Create: `services/ecommerce-api/app/modules/checkout/allocation.py`
- Create: `services/ecommerce-api/tests/test_allocation.py`

**Interfaces:**
- Consumes: Order items, StoreInventory, Inventory, address
- Produces: `allocate_order_to_store()`, `find_best_store()`

**Lý do:** Online order cần tự động gán cửa hàng fulfill theo địa chỉ khách. Logic này tách riêng để dễ test và maintain. Ưu tiên cửa hàng có tồn kho cao nhất trong cùng thành phố.

- [ ] **Step 1: Tạo allocation module**

```python
# services/ecommerce-api/app/modules/checkout/allocation.py
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.multicity import City, Store, StoreInventory
from app.models.inventory import Inventory


def parse_city_from_address(address: str) -> str | None:
    """Parse city name from shipping address."""
    # Address format: "street, ward, province"
    parts = [p.strip() for p in address.split(",")]
    if len(parts) >= 3:
        return parts[-1]  # Last part is province/city
    return None


def find_stores_in_city(db: Session, city_name: str) -> list[Store]:
    """Find all active stores in a city."""
    stmt = (
        select(Store)
        .join(City, City.city_id == Store.city_id)
        .where(City.name == city_name)
        .where(Store.is_active == True)  # noqa: E712
        .where(City.is_active == True)  # noqa: E712
    )
    return list(db.execute(stmt).scalars().all())


def find_store_with_all_items(
    db: Session, stores: list[Store], items: list[dict]
) -> Store | None:
    """Find a single store that has ALL items in sufficient quantity."""
    if not stores:
        return None
    
    for store in stores:
        store_has_all = True
        for item in items:
            stmt = (
                select(StoreInventory.on_hand)
                .where(
                    StoreInventory.store_id == store.store_id,
                    StoreInventory.variant_id == item["variant_id"],
                    StoreInventory.on_hand >= item["quantity"],
                )
            )
            row = db.execute(stmt).first()
            if not row:
                store_has_all = False
                break
        
        if store_has_all:
            return store
    
    return None


def allocate_order_to_stores(
    db: Session, order_id: int, shipping_address: str, items: list[dict]
) -> dict:
    """Allocate order to a single store that has ALL items, or fallback to global.
    
    Strategy: Find ONE store that can fulfill the ENTIRE order.
    If no such store exists, fallback entirely to global inventory (kho tổng).
    This is the simplest and most realistic approach for retail.
    """
    city_name = parse_city_from_address(shipping_address)
    
    allocation_result = {"store_id": None, "source": "global", "allocations": []}
    
    if not city_name:
        return allocation_result
    
    stores = find_stores_in_city(db, city_name)
    if not stores:
        return allocation_result
    
    # Find ONE store that has ALL items
    best_store = find_store_with_all_items(db, stores, items)
    
    if best_store:
        allocation_result["store_id"] = best_store.store_id
        allocation_result["source"] = "store"
        for item in items:
            allocation_result["allocations"].append({
                "variant_id": item["variant_id"],
                "store_id": best_store.store_id,
                "quantity": item["quantity"],
                "source": "store",
            })
    else:
        # No store has all items → fallback entirely to global
        for item in items:
            allocation_result["allocations"].append({
                "variant_id": item["variant_id"],
                "store_id": None,
                "quantity": item["quantity"],
                "source": "global",
            })
    
    return allocation_result
```

- [ ] **Step 2: Viết test**

```python
# services/ecommerce-api/tests/test_allocation.py
import pytest
from unittest.mock import MagicMock
from app.modules.checkout.allocation import parse_city_from_address, find_store_with_all_items


def test_parse_city_from_address():
    assert parse_city_from_address("123 Nguyễn Huệ, Bến Nghé, Thành phố Hồ Chí Minh") == "Thành phố Hồ Chí Minh"
    assert parse_city_from_address("456 Lê Lợi, Quận 1, Thành phố Hà Nội") == "Thành phố Hà Nội"
    assert parse_city_from_address("abc") is None


def test_find_store_with_all_items_success():
    """Store has all items → return that store."""
    mock_db = MagicMock()
    mock_stores = [MagicMock(store_id=1), MagicMock(store_id=2)]
    items = [{"variant_id": 10, "quantity": 2}, {"variant_id": 15, "quantity": 1}]
    
    # Store 1 has both items
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter([
        MagicMock(on_hand=5),  # variant 10
    ]))
    mock_db.execute.return_value = mock_result
    
    result = find_store_with_all_items(mock_db, mock_stores, items)
    assert result.store_id == 1


def test_find_store_with_all_items_no_store():
    """No store has all items → return None (fallback to global)."""
    mock_db = MagicMock()
    mock_stores = [MagicMock(store_id=1)]
    items = [{"variant_id": 10, "quantity": 2}, {"variant_id": 15, "quantity": 1}]
    
    # Store 1 doesn't have variant 15
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter([]))
    mock_db.execute.return_value = mock_result
    
    result = find_store_with_all_items(mock_db, mock_stores, items)
    assert result is None
```

- [ ] **Step 3: Chạy test**

```bash
cd services/ecommerce-api && python -m pytest tests/test_allocation.py -v
```
Expected: PASS

- [ ] **Step 4: Tích hợp vào checkout service**

```python
# services/ecommerce-api/app/modules/checkout/service.py
# Trong hàm checkout(), sau khi tạo order items, thêm:

from app.modules.checkout.allocation import allocate_order_to_stores

# Allocate order to stores
allocation = allocate_order_to_stores(
    db, order.order_id, payload.shipping_address_text, order_items_data
)

# Set store_id on order
if allocation["store_id"]:
    order.store_id = allocation["store_id"]

# Handle store inventory deductions
for alloc in allocation["allocations"]:
    if alloc["source"] == "store":
        # Deduct from store inventory
        store_inv = db.execute(
            select(StoreInventory).where(
                StoreInventory.store_id == alloc["store_id"],
                StoreInventory.variant_id == alloc["variant_id"],
            ).with_for_update()
        ).scalar_one_or_none()
        
        if store_inv:
            store_inv.on_hand -= alloc["quantity"]
            store_inv.version += 1
            store_inv.updated_at = now
```

- [ ] **Step 5: Commit**

```bash
git add services/ecommerce-api/app/modules/checkout/allocation.py services/ecommerce-api/tests/test_allocation.py services/ecommerce-api/app/modules/checkout/service.py
git commit -m "feat(checkout): add store allocation logic for online orders"
```

---

## Task 7: POS Frontend Page

**Files:**
- Create: `apps/storefront/src/app/admin/pos/page.tsx`

**Interfaces:**
- Consumes: POS API endpoints (Task 5)
- Produces: POS UI page

**Lý do:** POS UI cần đơn giản, tập trung vào nhập mã SP và xác nhận nhanh. Không cần grid SP phức tạp vì nhân viên quen mã SP.

- [ ] **Step 1: Tạo POS page**

```tsx
// apps/storefront/src/app/admin/pos/page.tsx
"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { Icon } from "@/components/ui/Icon";
import { useAuth } from "@/lib/auth";
import { ApiError, formatVnd } from "@/lib/api";

interface PosItem {
  variant_id: number;
  product_name: string;
  sku: string;
  size_code: string;
  color_code: string;
  price_vnd: number;
  quantity: number;
}

export default function PosPage() {
  const { customer } = useAuth();
  const router = useRouter();
  const [searchCode, setSearchCode] = useState("");
  const [searchResult, setSearchResult] = useState<any>(null);
  const [quantity, setQuantity] = useState(1);
  const [cart, setCart] = useState<PosItem[]>([]);
  const [searching, setSearching] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchProduct = useCallback(async () => {
    if (!searchCode.trim()) return;
    setSearching(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/v1/pos/products?store_id=1&search=${encodeURIComponent(searchCode.trim())}`,
        { credentials: "include" }
      );
      if (!response.ok) throw new ApiError("Không tìm thấy sản phẩm");
      const results = await response.json();
      setSearchResult(results[0] || null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Lỗi tìm kiếm");
    } finally {
      setSearching(false);
    }
  }, [searchCode]);

  const addToCart = useCallback(() => {
    if (!searchResult) return;
    setCart((prev) => {
      const existing = prev.find((i) => i.variant_id === searchResult.variant_id);
      if (existing) {
        return prev.map((i) =>
          i.variant_id === searchResult.variant_id
            ? { ...i, quantity: i.quantity + quantity }
            : i
        );
      }
      return [...prev, { ...searchResult, quantity }];
    });
    setSearchCode("");
    setSearchResult(null);
    setQuantity(1);
  }, [searchResult, quantity]);

  const removeFromCart = useCallback((variantId: number) => {
    setCart((prev) => prev.filter((i) => i.variant_id !== variantId));
  }, []);

  const total = cart.reduce((sum, item) => sum + item.price_vnd * item.quantity, 0);

  const submitTransaction = useCallback(async () => {
    if (cart.length === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      const response = await fetch("/api/v1/pos/transactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          store_id: 1,
          items: cart.map((i) => ({ variant_id: i.variant_id, quantity: i.quantity })),
          payment_method: "cash",
          amount_received_vnd: total,
        }),
      });
      if (!response.ok) throw new ApiError("Tạo đơn thất bại");
      const result = await response.json();
      alert(`Đơn ${result.order_number} đã tạo thành công!`);
      setCart([]);
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Lỗi tạo đơn");
    } finally {
      setSubmitting(false);
    }
  }, [cart, total, router]);

  return (
    <main className="page-shell">
      <header>
        <h1 className="page-heading">Bán hàng tại quầy</h1>
        <p className="mt-2 text-muted">Store: {customer?.store_id || "N/A"}</p>
      </header>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_400px]">
        {/* Left: Search & Results */}
        <section className="surface-card p-5">
          <h2 className="font-semibold">Nhập sản phẩm</h2>
          <div className="mt-4 flex gap-2">
            <input
              className="form-control flex-1"
              placeholder="Nhập mã sản phẩm (SKU)"
              value={searchCode}
              onChange={(e) => setSearchCode(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && searchProduct()}
            />
            <button
              className="button-primary"
              onClick={searchProduct}
              disabled={searching}
            >
              {searching ? "Đang tìm..." : "Tìm"}
            </button>
          </div>

          {searchResult && (
            <div className="mt-4 rounded-xl border p-4">
              <p className="font-medium">{searchResult.product_name}</p>
              <p className="text-sm text-muted">
                SKU: {searchResult.sku} | Size: {searchResult.size_code} | Màu: {searchResult.color_code}
              </p>
              <p className="text-sm text-muted">
                Giá: {formatVnd(searchResult.price_vnd)} | Tồn kho: {searchResult.store_stock}
              </p>
              <div className="mt-3 flex items-center gap-2">
                <input
                  className="form-control w-20"
                  type="number"
                  min="1"
                  value={quantity}
                  onChange={(e) => setQuantity(Number(e.target.value))}
                />
                <button className="button-primary" onClick={addToCart}>
                  Thêm vào giỏ
                </button>
              </div>
            </div>
          )}
        </section>

        {/* Right: Cart */}
        <section className="surface-card p-5">
          <h2 className="font-semibold">Giỏ hàng</h2>
          {cart.length === 0 ? (
            <p className="mt-4 text-muted">Chưa có sản phẩm</p>
          ) : (
            <div className="mt-4 space-y-3">
              {cart.map((item) => (
                <div key={item.variant_id} className="flex items-center justify-between border-b pb-2">
                  <div>
                    <p className="text-sm">{item.product_name}</p>
                    <p className="text-xs text-muted">
                      {item.sku} | {item.quantity} x {formatVnd(item.price_vnd)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>{formatVnd(item.price_vnd * item.quantity)}</span>
                    <button
                      className="text-danger"
                      onClick={() => removeFromCart(item.variant_id)}
                    >
                      <Icon name="trash" size={16} />
                    </button>
                  </div>
                </div>
              ))}
              <div className="border-t pt-3">
                <div className="flex justify-between font-semibold">
                  <span>Tổng cộng</span>
                  <span>{formatVnd(total)}</span>
                </div>
              </div>
            </div>
          )}

          {error && <p className="feedback-error mt-4">{error}</p>}

          <button
            className="button-accent mt-4 w-full"
            onClick={submitTransaction}
            disabled={submitting || cart.length === 0}
          >
            {submitting ? "Đang xử lý..." : "Thanh toán"}
          </button>
        </section>
      </div>
    </main>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd apps/storefront && npx tsc --noEmit
```
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add apps/storefront/src/app/admin/pos/page.tsx
git commit -m "feat(pos): add POS checkout page for staff"
```

---

## Task 8: Admin Orders Page - Thêm Filter Channel

**Files:**
- Modify: `apps/storefront/src/app/admin/orders/page.tsx`

**Interfaces:**
- Consumes: Orders API
- Produces: Filter UI cho channel + store

**Lý do:** Admin cần lọc đơn theo kênh (online/POS) và cửa hàng để quản lý hiệu quả. Store manager chỉ thấy đơn POS của cửa hàng mình.

- [ ] **Step 1: Đọc orders page hiện tại**

Đọc `apps/storefront/src/app/admin/orders/page.tsx` để hiểu structure.

- [ ] **Step 2: Thêm filter state và UI**

```tsx
// Thêm state
const [channelFilter, setChannelFilter] = useState<string>("all");
const [storeFilter, setStoreFilter] = useState<string>("all");

// Thêm filter UI vào phần header
<div className="mt-4 flex gap-4">
  <select
    className="form-control w-40"
    value={channelFilter}
    onChange={(e) => setChannelFilter(e.target.value)}
  >
    <option value="all">Tất cả kênh</option>
    <option value="online">Online</option>
    <option value="pos">POS</option>
  </select>
  
  <select
    className="form-control w-48"
    value={storeFilter}
    onChange={(e) => setStoreFilter(e.target.value)}
  >
    <option value="all">Tất cả cửa hàng</option>
    {stores.map((s) => (
      <option key={s.store_id} value={s.store_id}>{s.name}</option>
    ))}
  </select>
</div>

// Thêm column header cho channel
<th>Kênh</th>
<th>Cửa hàng</th>

// Thêm cell cho channel
<td>{order.channel === "pos" ? "POS" : "Online"}</td>
<td>{order.store_name || "-"}</td>
```

- [ ] **Step 3: Verify build**

```bash
cd apps/storefront && npx tsc --noEmit
```

- [ ] **Step 4: Commit**

```bash
git add apps/storefront/src/app/admin/orders/page.tsx
git commit -m "feat(admin): add channel and store filters to orders page"
```

---

## Task 9: Cập nhật Admin Nav

**Files:**
- Modify: `apps/storefront/src/components/AdminNav.tsx`

**Interfaces:**
- Consumes: None
- Produces: Nav item cho POS

**Lý do:** Thêm navigation item để staff dễ dàng truy cập POS.

- [ ] **Step 1: Thêm POS nav item**

```tsx
// Thêm vào navItems array
{ href: "/admin/pos", label: "POS", icon: "cart" },
```

- [ ] **Step 2: Commit**

```bash
git add apps/storefront/src/components/AdminNav.tsx
git commit -m "feat(admin): add POS navigation item"
```

---

## Task 10: Seed Data - Tạo store inventory cho test

**Files:**
- Create: `database/seeds/0011_pos_test_inventory.sql`

**Interfaces:**
- Consumes: stores, product_variants tables
- Produces: Test inventory data

**Lý do:** Cần có dữ liệu test để kiểm tra POS hoạt động đúng. Mỗi cửa hàng cần có tồn kho cho tất cả sản phẩm.

- [ ] **Step 1: Tạo seed script**

```sql
-- database/seeds/0011_pos_test_inventory.sql
-- Tồn kho test cho POS

-- Store HCM (store_id = 1)
INSERT INTO store_inventory (store_id, variant_id, on_hand, opening_on_hand, version)
SELECT 1, variant_id, 10, 10, 1
FROM product_variants
WHERE is_active = 1
ON DUPLICATE KEY UPDATE on_hand = VALUES(on_hand);

-- Store HN (store_id = 2)
INSERT INTO store_inventory (store_id, variant_id, on_hand, opening_on_hand, version)
SELECT 2, variant_id, 8, 8, 1
FROM product_variants
WHERE is_active = 1
ON DUPLICATE KEY UPDATE on_hand = VALUES(on_hand);

-- Store DN (store_id = 3)
INSERT INTO store_inventory (store_id, variant_id, on_hand, opening_on_hand, version)
SELECT 3, variant_id, 5, 5, 1
FROM product_variants
WHERE is_active = 1
ON DUPLICATE KEY UPDATE on_hand = VALUES(on_hand);
```

- [ ] **Step 2: Chạy seed**

```bash
docker exec -i tlcn-mysql-1 mysql -u ecommerce_app -ppassword ecommerce < database/seeds/0011_pos_test_inventory.sql
```

- [ ] **Step 3: Verify**

```bash
docker exec tlcn-mysql-1 mysql -u ecommerce_app -ppassword ecommerce -Bse "SELECT store_id, COUNT(*) as variants, SUM(on_hand) as total_stock FROM store_inventory GROUP BY store_id;"
```

- [ ] **Step 4: Commit**

```bash
git add database/seeds/0011_pos_test_inventory.sql
git commit -m "seed(pos): add test store inventory for POS"
```

---

## Task 11: Tests cho POS API

**Files:**
- Create: `services/ecommerce-api/tests/test_pos_api.py`

**Interfaces:**
- Consumes: POS endpoints (Task 5)
- Produces: API tests

**Lý do:** Tests đảm bảo POS API hoạt động đúng, phân quyền đúng, validation đúng.

- [ ] **Step 1: Viết tests**

```python
# services/ecommerce-api/tests/test_pos_api.py
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


def test_search_products_requires_staff(client, mock_staff):
    response = client.get("/api/v1/pos/products?store_id=1&search=APN")
    assert response.status_code == 401


def test_search_products_success(client, mock_staff, mock_db):
    with patch("app.modules.pos.router.search_products") as mock_search:
        mock_search.return_value = [
            {
                "variant_id": 1,
                "product_name": "Áo Polo Nam",
                "sku": "APN001",
                "size_code": "L",
                "color_code": "DEN",
                "price_vnd": 300000,
                "store_stock": 5,
                "global_stock": 20,
            }
        ]
        response = client.get(
            "/api/v1/pos/products?store_id=1&search=APN",
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code == 200
        assert len(response.json()) == 1


def test_create_transaction_success(client, mock_staff, mock_db):
    with patch("app.modules.pos.router.create_pos_transaction") as mock_create:
        mock_create.return_value = {
            "order_number": "POS-001",
            "status": "completed",
            "channel": "pos",
            "store_id": 1,
            "payment_method": "cash",
            "items": [],
            "subtotal_vnd": 300000,
            "total_vnd": 300000,
            "created_at": "2026-09-15T10:00:00",
        }
        response = client.post(
            "/api/v1/pos/transactions",
            json={
                "store_id": 1,
                "items": [{"variant_id": 1, "quantity": 1}],
                "payment_method": "cash",
            },
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code == 200
        assert response.json()["channel"] == "pos"
```

- [ ] **Step 2: Chạy test**

```bash
cd services/ecommerce-api && python -m pytest tests/test_pos_api.py -v
```
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add services/ecommerce-api/tests/test_pos_api.py
git commit -m "test(pos): add POS API tests"
```

---

## Task 12: Final Integration Test

**Files:**
- Create: `services/ecommerce-api/tests/test_pos_integration.py`

**Interfaces:**
- Consumes: All POS components
- Produces: End-to-end test

**Lý do:** Integration test đảm bảo tất cả POS components hoạt động cùng nhau đúng cách.

- [ ] **Step 1: Viết integration test**

```python
# services/ecommerce-api/tests/test_pos_integration.py
import pytest
from unittest.mock import MagicMock, patch


def test_pos_full_flow():
    """Test complete POS transaction flow."""
    mock_db = MagicMock()
    
    # Mock store
    mock_store = MagicMock(store_id=1, is_active=True)
    
    # Mock variant with product
    mock_variant = MagicMock(
        variant_id=10,
        sku="APN001",
        size_code="L",
        color_code="DEN",
        price_vnd=300000,
        product=MagicMock(name="Áo Polo Nam", public_id="uuid-123"),
    )
    
    # Mock store inventory
    mock_store_inv = MagicMock(on_hand=10, version=1)
    
    # Mock global inventory
    mock_global_inv = MagicMock(on_hand=50, version=1)
    
    # Setup mock responses
    def mock_execute(stmt):
        result = MagicMock()
        if hasattr(stmt, 'where'):
            # Return appropriate mock based on query
            result.scalar_one_or_none.return_value = mock_variant
        return result
    
    mock_db.execute.side_effect = mock_execute
    
    from app.modules.pos.service import create_pos_transaction
    from app.modules.pos.schemas import POSTransactionRequest, POSTItemRequest
    
    request = POSTransactionRequest(
        store_id=1,
        items=[POSTItemRequest(variant_id=10, quantity=2)],
        payment_method="cash",
        amount_received_vnd=1000000,
    )
    
    with patch("app.modules.pos.service.new_order_number", return_value="POS-001"):
        result = create_pos_transaction(mock_db, request, staff_id=1)
    
    assert result["order_number"] == "POS-001"
    assert result["channel"] == "pos"
    assert result["total_vnd"] == 600000
```

- [ ] **Step 2: Chạy test**

```bash
cd services/ecommerce-api && python -m pytest tests/test_pos_integration.py -v
```

- [ ] **Step 3: Commit**

```bash
git add services/ecommerce-api/tests/test_pos_integration.py
git commit -m "test(pos): add POS integration test"
```

---

## Summary

| Task | Mô tả | Lý do | Est. Time |
|------|-------|-------|-----------|
| 1 | DB Migration | Schema thay đổi cho POS | 15 min |
| 2 | POS Schemas | Request/response validation | 10 min |
| 3 | POS Service - Search | Tìm SP theo SKU/tên | 20 min |
| 4 | POS Service - Create Order | Tạo đơn + trừ tồn kho kép | 30 min |
| 5 | POS Router | API endpoints | 15 min |
| 6 | Store Allocation Logic | Auto-gán cửa hàng cho online order | 30 min |
| 7 | POS Frontend Page | UI bán hàng tại quầy | 45 min |
| 8 | Admin Orders Filter | Lọc đơn theo kênh/cửa hàng | 20 min |
| 9 | Admin Nav Update | Điều hướng POS | 5 min |
| 10 | Seed Data | Dữ liệu test | 10 min |
| 11 | POS API Tests | Test API | 20 min |
| 12 | Integration Test | Test end-to-end | 15 min |
| **Total** | | | **~3.5 hours** |

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-15-pos-multi-store.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
