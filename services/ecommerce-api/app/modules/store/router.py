from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.errors import forbidden
from app.db.deps import get_current_staff, get_db
from app.models.customer import Customer
from app.modules.orders.schemas import OrderDetailResponse
from app.modules.store.schemas import (
    StoreDashboardResponse,
    StoreInventoryItem,
    StoreOrderResponse,
    StoreStaffMember,
)
from app.modules.store.service import (
    get_store_dashboard,
    get_store_order_detail,
    list_store_inventory,
    list_store_orders,
    list_store_staff,
)

admin_store_router = APIRouter(prefix="/admin/store", tags=["admin-store"])


def _require_store_manager(actor: Customer) -> Customer:
    if actor.role != "store_manager":
        raise forbidden("Chỉ quản lý cửa hàng mới có quyền truy cập.")
    if actor.store_id is None:
        raise forbidden("Tài khoản không gắn với cửa hàng nào.")
    return actor


@admin_store_router.get("/dashboard", response_model=StoreDashboardResponse)
def store_dashboard(
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> StoreDashboardResponse:
    manager = _require_store_manager(actor)
    return get_store_dashboard(db, manager.store_id)


@admin_store_router.get("/orders", response_model=list[StoreOrderResponse])
def store_orders(
    status: str | None = Query(
        default=None,
        pattern=r"^(paid|payment_failed|confirmed|completed|cancelled)$",
    ),
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> list[StoreOrderResponse]:
    manager = _require_store_manager(actor)
    return list_store_orders(db, manager.store_id, status)


@admin_store_router.get("/orders/{order_number}", response_model=OrderDetailResponse)
def store_order_detail(
    order_number: str,
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> OrderDetailResponse:
    manager = _require_store_manager(actor)
    return get_store_order_detail(db, manager.store_id, order_number)


@admin_store_router.get("/inventory", response_model=list[StoreInventoryItem])
def store_inventory(
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> list[StoreInventoryItem]:
    manager = _require_store_manager(actor)
    return list_store_inventory(db, manager.store_id)


@admin_store_router.get("/staff", response_model=list[StoreStaffMember])
def store_staff(
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> list[StoreStaffMember]:
    manager = _require_store_manager(actor)
    return list_store_staff(db, manager.store_id)
