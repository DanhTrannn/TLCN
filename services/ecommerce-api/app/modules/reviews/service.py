from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import (
    REVIEW_ALREADY_EXISTS,
    REVIEW_NOT_ALLOWED,
    AppError,
    not_found,
)
from app.core.ids import uuid7
from app.db.uow import run_in_transaction
from app.models.catalog import Product, ProductVariant
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.review import ProductReview
from app.modules.reviews.schemas import (
    AdminReviewResponse,
    CreateReviewRequest,
    CustomerReviewResponse,
    ModerateReviewRequest,
    ReviewListResponse,
    ReviewResponse,
)


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def list_approved_reviews(db: Session, slug: str) -> ReviewListResponse:
    product = db.execute(
        select(Product).where(Product.slug == slug, Product.is_active.is_(True))
    ).scalar_one_or_none()
    if product is None:
        raise not_found("Không tìm thấy sản phẩm.")
    rows = db.execute(
        select(ProductReview, Customer.display_name)
        .join(Customer, Customer.customer_id == ProductReview.customer_id)
        .where(
            ProductReview.product_id == product.product_id,
            ProductReview.status == "approved",
        )
        .order_by(ProductReview.created_at.desc(), ProductReview.review_id.desc())
        .limit(100)
    ).all()
    ratings = [review.rating for review, _ in rows]
    return ReviewListResponse(
        items=[
            ReviewResponse(
                public_id=str(review.public_id),
                rating=review.rating,
                content=review.content,
                customer_name=customer_name,
                created_at=review.created_at,
            )
            for review, customer_name in rows
        ],
        total=len(rows),
        average_rating=(round(sum(ratings) / len(ratings), 2) if ratings else None),
    )


def create_review(
    customer_id: int,
    order_number: str,
    order_item_public_id: str,
    payload: CreateReviewRequest,
) -> CustomerReviewResponse:
    try:
        parsed_item_id = UUID(order_item_public_id)
    except ValueError as error:
        raise not_found("Không tìm thấy sản phẩm trong đơn hàng.") from error

    def _work(db: Session) -> CustomerReviewResponse:
        order = db.execute(
            select(Order)
            .where(Order.order_number == order_number)
            .with_for_update()
        ).scalar_one_or_none()
        if order is None or order.customer_id != customer_id:
            raise not_found("Không tìm thấy đơn hàng.")
        if order.status != "completed":
            raise AppError(
                REVIEW_NOT_ALLOWED,
                "Chỉ có thể đánh giá sản phẩm trong đơn đã hoàn tất.",
                status_code=409,
            )
        row = db.execute(
            select(OrderItem, ProductVariant.product_id)
            .join(ProductVariant, ProductVariant.variant_id == OrderItem.variant_id)
            .where(
                OrderItem.order_id == order.order_id,
                OrderItem.public_id == parsed_item_id,
            )
            .with_for_update()
        ).first()
        if row is None:
            raise not_found("Không tìm thấy sản phẩm trong đơn hàng.")
        order_item, product_id = row
        existing = db.execute(
            select(ProductReview).where(
                ProductReview.order_item_id == order_item.order_item_id
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise AppError(
                REVIEW_ALREADY_EXISTS,
                "Sản phẩm trong đơn này đã được đánh giá.",
                status_code=409,
            )
        review = ProductReview(
            public_id=uuid7(),
            order_item_id=order_item.order_item_id,
            customer_id=customer_id,
            product_id=product_id,
            rating=payload.rating,
            content=payload.content or None,
            status="approved",
        )
        db.add(review)
        db.flush()
        db.refresh(review)
        return CustomerReviewResponse(
            public_id=str(review.public_id),
            rating=review.rating,
            content=review.content,
            status=review.status,
            moderation_reason=review.moderation_reason,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )

    return run_in_transaction(_work)


def list_admin_reviews(
    db: Session, status: str | None
) -> list[AdminReviewResponse]:
    stmt = (
        select(
            ProductReview,
            Order.order_number,
            OrderItem.product_name_snapshot,
            Customer.display_name,
        )
        .join(OrderItem, OrderItem.order_item_id == ProductReview.order_item_id)
        .join(Order, Order.order_id == OrderItem.order_id)
        .join(Customer, Customer.customer_id == ProductReview.customer_id)
    )
    if status:
        stmt = stmt.where(ProductReview.status == status)
    rows = db.execute(
        stmt.order_by(ProductReview.created_at.desc(), ProductReview.review_id.desc()).limit(300)
    ).all()
    return [
        AdminReviewResponse(
            public_id=str(review.public_id),
            order_number=order_number,
            product_name=product_name,
            customer_name=customer_name,
            rating=review.rating,
            content=review.content,
            status=review.status,
            moderation_reason=review.moderation_reason,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )
        for review, order_number, product_name, customer_name in rows
    ]


def moderate_review(
    admin_customer_id: int,
    public_id: str,
    payload: ModerateReviewRequest,
) -> CustomerReviewResponse:
    try:
        parsed_id = UUID(public_id)
    except ValueError as error:
        raise not_found("Không tìm thấy đánh giá.") from error

    def _work(db: Session) -> CustomerReviewResponse:
        review = db.execute(
            select(ProductReview)
            .where(ProductReview.public_id == parsed_id)
            .with_for_update()
        ).scalar_one_or_none()
        if review is None:
            raise not_found("Không tìm thấy đánh giá.")
        if review.status == payload.status:
            return CustomerReviewResponse(
                public_id=str(review.public_id),
                rating=review.rating,
                content=review.content,
                status=review.status,
                moderation_reason=review.moderation_reason,
                created_at=review.created_at,
                updated_at=review.updated_at,
            )
        now = _utc_now()
        review.status = payload.status
        review.moderation_reason = (
            payload.reason if payload.status == "rejected" else None
        )
        review.moderated_by_customer_id = admin_customer_id
        review.moderated_at = now
        review.updated_at = now
        db.flush()
        db.refresh(review)
        return CustomerReviewResponse(
            public_id=str(review.public_id),
            rating=review.rating,
            content=review.content,
            status=review.status,
            moderation_reason=review.moderation_reason,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )

    return run_in_transaction(_work)
