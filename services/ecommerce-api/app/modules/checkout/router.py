from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.errors import VALIDATION_ERROR, AppError
from app.db.deps import get_current_customer, get_db, verify_csrf
from app.models.customer import Customer
from app.modules.checkout.schemas import CheckoutRequest, CheckoutResultResponse
from app.modules.checkout.service import checkout, quote_checkout
from app.modules.coupons.schemas import CheckoutQuoteRequest, CheckoutQuoteResponse

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.post("/quote", response_model=CheckoutQuoteResponse)
def quote(
    payload: CheckoutQuoteRequest,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> CheckoutQuoteResponse:
    return quote_checkout(db, customer.customer_id, payload)


@router.post("", response_model=CheckoutResultResponse)
def create_checkout(
    payload: CheckoutRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    customer: Customer = Depends(get_current_customer),
    _: None = Depends(verify_csrf),
) -> CheckoutResultResponse:
    if not idempotency_key or not idempotency_key.strip() or len(idempotency_key.strip()) > 59:
        raise AppError(VALIDATION_ERROR, "Idempotency-Key phải có từ 1 đến 59 ký tự.", status_code=400)
    return checkout(customer.customer_id, idempotency_key.strip(), payload)
