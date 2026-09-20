from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.core.errors import AppError, VALIDATION_ERROR
from app.db.deps import get_current_admin, get_current_customer, get_db, verify_csrf
from app.models.customer import Customer
from app.modules.returns.schemas import (
    AdminInspectAndResolvePayload,
    AdminReturnListResponse,
    AdminReviewReturnPayload,
    CreateReturnRequestPayload,
    ReturnRequestDetailResponse,
    ReturnRequestListResponse,
)
from app.modules.returns.service import (
    cancel_customer_return_request,
    create_customer_return_request,
    get_admin_return_detail,
    get_customer_return,
    inspect_and_resolve_admin_return,
    list_admin_returns,
    list_customer_returns,
    receive_admin_return,
    review_admin_return,
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


admin_router = APIRouter(prefix="/admin/returns", tags=["admin-returns"])


@admin_router.get("", response_model=AdminReturnListResponse)
def admin_list_returns(
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminReturnListResponse:
    return list_admin_returns(db, status=status, search=search, limit=limit, offset=offset)


@admin_router.get("/{return_code}", response_model=ReturnRequestDetailResponse)
def admin_return_detail(
    return_code: str,
    _: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ReturnRequestDetailResponse:
    return get_admin_return_detail(db, return_code)


@admin_router.post("/{return_code}/review", response_model=ReturnRequestDetailResponse)
def admin_review_return(
    return_code: str,
    payload: AdminReviewReturnPayload,
    _: Customer = Depends(get_current_admin),
    __: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> ReturnRequestDetailResponse:
    return review_admin_return(db, return_code, payload.action, payload.admin_note)


@admin_router.post("/{return_code}/receive", response_model=ReturnRequestDetailResponse)
def admin_receive_return(
    return_code: str,
    _: Customer = Depends(get_current_admin),
    __: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> ReturnRequestDetailResponse:
    return receive_admin_return(db, return_code)


@admin_router.post("/{return_code}/inspect-and-resolve", response_model=ReturnRequestDetailResponse)
def admin_inspect_and_resolve_return(
    return_code: str,
    payload: AdminInspectAndResolvePayload,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    _: Customer = Depends(get_current_admin),
    __: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> ReturnRequestDetailResponse:
    return inspect_and_resolve_admin_return(
        db,
        return_code=return_code,
        payload=payload,
        idempotency_key=_require_idempotency_key(idempotency_key),
    )
