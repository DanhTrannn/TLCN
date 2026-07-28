from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.deps import get_current_customer, get_db, verify_csrf
from app.models.customer import Customer
from app.modules.wishlist.schemas import WishlistResponse
from app.modules.wishlist.service import get_wishlist, set_product_presence

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


@router.get("", response_model=WishlistResponse)
def read_wishlist(
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> WishlistResponse:
    return get_wishlist(db, customer.customer_id)


@router.put("/products/{product_public_id}", status_code=204)
def add_product(
    product_public_id: str,
    customer: Customer = Depends(get_current_customer),
    _: None = Depends(verify_csrf),
) -> Response:
    set_product_presence(customer.customer_id, product_public_id, True)
    return Response(status_code=204)


@router.delete("/products/{product_public_id}", status_code=204)
def remove_product(
    product_public_id: str,
    customer: Customer = Depends(get_current_customer),
    _: None = Depends(verify_csrf),
) -> Response:
    set_product_presence(customer.customer_id, product_public_id, False)
    return Response(status_code=204)
