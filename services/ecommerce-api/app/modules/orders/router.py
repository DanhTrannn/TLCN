from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.db.deps import get_current_customer, get_db, require_internal_secret
from app.models.customer import Customer
from app.modules.orders.schemas import (
    OrderDetailResponse,
    OrderListResponse,
)
from app.modules.orders.service import complete_order, get_order_detail, list_orders

router = APIRouter(prefix="/orders", tags=["orders"])
internal_router = APIRouter(prefix="/orders", tags=["internal-orders"])


@router.get("", response_model=OrderListResponse)
def get_orders(
    cursor: str | None = Query(default=None),
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> OrderListResponse:
    return list_orders(db, customer.customer_id, cursor)


@router.get("/{order_number}", response_model=OrderDetailResponse)
def get_order(
    order_number: str,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> OrderDetailResponse:
    return get_order_detail(db, customer.customer_id, order_number)


@internal_router.post("/{order_number}/complete")
def complete(
    order_number: str,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    _: None = Depends(require_internal_secret),
) -> dict:
    return complete_order(order_number, idempotency_key)
