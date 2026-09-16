from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.core.errors import forbidden, not_found
from app.db.deps import get_current_staff, get_db, verify_csrf
from app.models.customer import Customer
from app.models.multicity import Store
from sqlalchemy import select
from app.modules.orders.schemas import CancelOrderRequest, OrderDetailResponse, OrderTransitionResponse
from app.modules.orders.service import cancel_order, confirm_order
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


def _resolve_store_id(db: Session, actor: Customer, store_id: int | None) -> int:
    if actor.role == "store_manager":
        if actor.store_id is None:
            raise forbidden("Tài khoản không gắn với cửa hàng nào.")
        return actor.store_id
    if actor.role == "admin":
        if store_id is not None:
            return store_id
        first_store = db.execute(
            select(Store).where(Store.is_active == True).order_by(Store.store_id).limit(1)
        ).scalar_one_or_none()
        if first_store is None:
            raise not_found("Không có cửa hàng nào.")
        return first_store.store_id
    raise forbidden("Chỉ quản lý cửa hàng hoặc quản trị viên mới có quyền truy cập.")


@admin_store_router.get("/dashboard", response_model=StoreDashboardResponse)
def store_dashboard(
    store_id: int | None = Query(default=None, gt=0),
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> StoreDashboardResponse:
    resolved_store_id = _resolve_store_id(db, actor, store_id)
    return get_store_dashboard(db, resolved_store_id)


@admin_store_router.get("/orders", response_model=list[StoreOrderResponse])
def store_orders(
    status: str | None = Query(
        default=None,
        pattern=r"^(paid|payment_failed|confirmed|completed|cancelled)$",
    ),
    store_id: int | None = Query(default=None, gt=0),
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> list[StoreOrderResponse]:
    resolved_store_id = _resolve_store_id(db, actor, store_id)
    return list_store_orders(db, resolved_store_id, status)


@admin_store_router.get("/orders/{order_number}", response_model=OrderDetailResponse)
def store_order_detail(
    order_number: str,
    store_id: int | None = Query(default=None, gt=0),
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> OrderDetailResponse:
    resolved_store_id = _resolve_store_id(db, actor, store_id)
    return get_store_order_detail(db, resolved_store_id, order_number)


@admin_store_router.post("/orders/{order_number}/confirm", response_model=OrderTransitionResponse)
def store_confirm_order(
    order_number: str,
    store_id: int | None = Query(default=None, gt=0),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> OrderTransitionResponse:
    resolved_store_id = _resolve_store_id(db, actor, store_id)
    get_store_order_detail(db, resolved_store_id, order_number)
    if not idempotency_key:
        raise forbidden("Yêu cầu idempotency key.")
    return confirm_order(order_number, idempotency_key, transition_source="admin")


@admin_store_router.post("/orders/{order_number}/cancel", response_model=OrderTransitionResponse)
def store_cancel_order(
    order_number: str,
    payload: CancelOrderRequest,
    store_id: int | None = Query(default=None, gt=0),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> OrderTransitionResponse:
    resolved_store_id = _resolve_store_id(db, actor, store_id)
    get_store_order_detail(db, resolved_store_id, order_number)
    if not idempotency_key:
        raise forbidden("Yêu cầu idempotency key.")
    return cancel_order(
        order_number,
        actor_customer_id=actor.customer_id,
        owner_customer_id=None,
        reason=payload.reason,
        idempotency_key=idempotency_key,
        transition_source="admin",
    )


@admin_store_router.get("/inventory", response_model=list[StoreInventoryItem])
def store_inventory(
    store_id: int | None = Query(default=None, gt=0),
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> list[StoreInventoryItem]:
    resolved_store_id = _resolve_store_id(db, actor, store_id)
    return list_store_inventory(db, resolved_store_id)


@admin_store_router.get("/staff", response_model=list[StoreStaffMember])
def store_staff(
    store_id: int | None = Query(default=None, gt=0),
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> list[StoreStaffMember]:
    resolved_store_id = _resolve_store_id(db, actor, store_id)
    return list_store_staff(db, resolved_store_id)
