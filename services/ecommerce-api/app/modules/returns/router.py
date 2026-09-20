from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.errors import AppError, VALIDATION_ERROR
from app.db.deps import get_current_customer, get_db, verify_csrf
from app.models.customer import Customer
from app.modules.returns.schemas import (
    CreateReturnRequestPayload,
    ReturnRequestDetailResponse,
    ReturnRequestListResponse,
)
from app.modules.returns.service import (
    cancel_customer_return_request,
    create_customer_return_request,
    get_customer_return,
    list_customer_returns,
)


def _require_idempotency_key(value: str | None) -> str:
    key = value.strip() if value else ""
    if not key or len(key) > 64:
        raise AppError(
            VALIDATION_ERROR,
            "Idempotency-Key phải có từ 1 đến 64 ký tự.",
            status_code=400,
        )
    return key


router = APIRouter(tags=["returns"])


@router.post("/orders/{order_number}/returns", response_model=ReturnRequestDetailResponse)
def create_return_request(
    order_number: str,
    payload: CreateReturnRequestPayload,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    customer: Customer = Depends(get_current_customer),
    _: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> ReturnRequestDetailResponse:
    return create_customer_return_request(
        db,
        customer_id=customer.customer_id,
        order_number=order_number,
        payload=payload,
        idempotency_key=_require_idempotency_key(idempotency_key),
    )


@router.get("/returns", response_model=ReturnRequestListResponse)
def list_returns(
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> ReturnRequestListResponse:
    return list_customer_returns(db, customer.customer_id)


@router.get("/returns/{return_code}", response_model=ReturnRequestDetailResponse)
def get_return_detail(
    return_code: str,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> ReturnRequestDetailResponse:
    return get_customer_return(db, customer.customer_id, return_code)


@router.post("/returns/{return_code}/cancel", response_model=ReturnRequestDetailResponse)
def cancel_return_request(
    return_code: str,
    customer: Customer = Depends(get_current_customer),
    _: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> ReturnRequestDetailResponse:
    return cancel_customer_return_request(db, customer.customer_id, return_code)
