from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.deps import get_current_admin, get_current_customer, get_db, verify_csrf
from app.models.customer import Customer
from app.modules.reviews.schemas import (
    AdminReviewResponse,
    CreateReviewRequest,
    CustomerReviewResponse,
    ModerateReviewRequest,
    ReviewListResponse,
)
from app.modules.reviews.service import (
    create_review,
    list_admin_reviews,
    list_approved_reviews,
    moderate_review,
)

router = APIRouter(tags=["reviews"])
admin_router = APIRouter(prefix="/admin/reviews", tags=["admin-reviews"])


@router.get("/products/{slug}/reviews", response_model=ReviewListResponse)
def product_reviews(
    slug: str,
    db: Session = Depends(get_db),
) -> ReviewListResponse:
    return list_approved_reviews(db, slug)


@router.post(
    "/orders/{order_number}/items/{order_item_public_id}/review",
    response_model=CustomerReviewResponse,
    status_code=201,
)
def add_review(
    order_number: str,
    order_item_public_id: str,
    payload: CreateReviewRequest,
    customer: Customer = Depends(get_current_customer),
    _: None = Depends(verify_csrf),
) -> CustomerReviewResponse:
    return create_review(
        customer.customer_id,
        order_number,
        order_item_public_id,
        payload,
    )


@admin_router.get("", response_model=list[AdminReviewResponse])
def admin_reviews(
    status: str | None = Query(default=None, pattern=r"^(pending|approved|rejected)$"),
    _: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[AdminReviewResponse]:
    return list_admin_reviews(db, status)


@admin_router.patch("/{public_id}", response_model=CustomerReviewResponse)
def patch_review(
    public_id: str,
    payload: ModerateReviewRequest,
    admin: Customer = Depends(get_current_admin),
    _: None = Depends(verify_csrf),
) -> CustomerReviewResponse:
    return moderate_review(admin.customer_id, public_id, payload)
