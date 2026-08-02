from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.core.errors import VALIDATION_ERROR, AppError
from app.db.deps import get_current_customer, get_db, require_internal_secret, verify_csrf
from app.models.customer import Customer
from app.modules.orders.schemas import (
    CancelOrderRequest,
    OrderDetailResponse,
    OrderListResponse,
    OrderTransitionResponse,
)
from app.modules.orders.service import (
    cancel_order,
    complete_order,
    confirm_order,
    get_order_detail,
    list_orders,
)

router = APIRouter(prefix="/orders", tags=["orders"])
internal_router = APIRouter(prefix="/orders", tags=["internal-orders"])


def _require_idempotency_key(value: str | None) -> str:
    key = value.strip() if value else ""
    if not key or len(key) > 64:
        raise AppError(
            VALIDATION_ERROR,
            "Idempotency-Key phải có từ 1 đến 64 ký tự.",
            status_code=400,
        )
    return key


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


@router.post("/{order_number}/cancel", response_model=OrderTransitionResponse)
def cancel_customer_order(
    order_number: str,
    payload: CancelOrderRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    customer: Customer = Depends(get_current_customer),
    _: None = Depends(verify_csrf),
) -> OrderTransitionResponse:
    return cancel_order(
        order_number,
        actor_customer_id=customer.customer_id,
        owner_customer_id=customer.customer_id,
        reason=payload.reason,
        idempotency_key=_require_idempotency_key(idempotency_key),
        transition_source="customer",
    )


@router.post("/{order_number}/complete", response_model=OrderTransitionResponse)
def complete_customer_order(
    order_number: str,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    customer: Customer = Depends(get_current_customer),
    _: None = Depends(verify_csrf),
) -> OrderTransitionResponse:
    return complete_order(
        order_number,
        _require_idempotency_key(idempotency_key),
        transition_source="customer",
        owner_customer_id=customer.customer_id,
    )


@internal_router.post("/{order_number}/confirm", response_model=OrderTransitionResponse)
def confirm(
    order_number: str,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    _: None = Depends(require_internal_secret),
) -> OrderTransitionResponse:
    return confirm_order(
        order_number,
        _require_idempotency_key(idempotency_key),
        transition_source="internal_endpoint",
    )
