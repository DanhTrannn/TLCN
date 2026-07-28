from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_current_customer, get_db, verify_csrf
from app.models.customer import Customer
from app.modules.cart.schemas import CartResponse, SetItemRequest
from app.modules.cart.service import get_cart, remove_item, set_item

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartResponse)
def read_cart(
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> CartResponse:
    return get_cart(db, customer.customer_id)


@router.put("/items/{variant_public_id}", response_model=CartResponse)
def put_item(
    variant_public_id: str,
    payload: SetItemRequest,
    customer: Customer = Depends(get_current_customer),
    _: None = Depends(verify_csrf),
) -> CartResponse:
    return set_item(customer.customer_id, variant_public_id, payload.quantity)


@router.delete("/items/{variant_public_id}", response_model=CartResponse)
def delete_item(
    variant_public_id: str,
    customer: Customer = Depends(get_current_customer),
    _: None = Depends(verify_csrf),
) -> CartResponse:
    return remove_item(customer.customer_id, variant_public_id)
