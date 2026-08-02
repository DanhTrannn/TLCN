from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.db.deps import get_current_admin, get_current_customer, get_db, verify_csrf
from app.models.customer import Customer
from app.modules.coupons.schemas import (
    AvailableCouponListResponse,
    CouponResponse,
    CreateCouponRequest,
    UpdateCouponRequest,
)
from app.modules.cart.service import get_cart
from app.modules.coupons.service import (
    create_coupon,
    list_available_coupons,
    list_coupons,
    set_coupon_active,
)

router = APIRouter(prefix="/coupons", tags=["coupons"])
admin_router = APIRouter(prefix="/admin/coupons", tags=["admin-coupons"])


@router.get("/available", response_model=AvailableCouponListResponse)
def available_coupons(
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> AvailableCouponListResponse:
    cart = get_cart(db, customer.customer_id)
    return list_available_coupons(
        db,
        customer.customer_id,
        cart.subtotal_vnd,
    )


@admin_router.get("", response_model=list[CouponResponse])
def admin_coupons(
    _: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[CouponResponse]:
    return list_coupons(db)


@admin_router.post("", response_model=CouponResponse, status_code=201)
def add_coupon(
    payload: CreateCouponRequest,
    _: Customer = Depends(get_current_admin),
    __: None = Depends(verify_csrf),
) -> CouponResponse:
    return create_coupon(payload)


@admin_router.patch("/{public_id}", status_code=204)
def patch_coupon(
    public_id: str,
    payload: UpdateCouponRequest,
    _: Customer = Depends(get_current_admin),
    __: None = Depends(verify_csrf),
) -> Response:
    try:
        parsed_id = UUID(public_id)
    except ValueError as error:
        raise not_found("Không tìm thấy coupon.") from error
    set_coupon_active(parsed_id, payload.is_active)
    return Response(status_code=204)
