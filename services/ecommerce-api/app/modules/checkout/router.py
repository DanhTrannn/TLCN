from fastapi import APIRouter, Depends, Header

from app.core.errors import VALIDATION_ERROR, AppError
from app.db.deps import get_current_customer, verify_csrf
from app.models.customer import Customer
from app.modules.checkout.schemas import CheckoutRequest, CheckoutResultResponse
from app.modules.checkout.service import checkout

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.post("", response_model=CheckoutResultResponse)
def create_checkout(
    payload: CheckoutRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    customer: Customer = Depends(get_current_customer),
    _: None = Depends(verify_csrf),
) -> CheckoutResultResponse:
    if not idempotency_key or not idempotency_key.strip():
        raise AppError(VALIDATION_ERROR, "Thiếu Idempotency-Key.", status_code=400)
    return checkout(customer.customer_id, idempotency_key.strip(), payload)
