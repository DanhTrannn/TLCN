from datetime import datetime
from uuid import uuid4

from app.models.order import Order, OrderItem
from app.models.review import ProductReview
from app.modules.reviews import service as review_service
from app.modules.reviews.schemas import CreateReviewRequest, ModerateReviewRequest


class _ScalarResult:
    def __init__(self, entity):
        self.entity = entity

    def scalar_one_or_none(self):
        return self.entity


class _RowResult:
    def __init__(self, row):
        self.row = row

    def first(self):
        return self.row


class _Session:
    def __init__(self, order: Order, order_item: OrderItem):
        self.results = iter(
            (
                _ScalarResult(order),
                _RowResult((order_item, 303)),
                _ScalarResult(None),
            )
        )
        self.added_review: ProductReview | None = None

    def execute(self, _statement):
        return next(self.results)

    def add(self, review: ProductReview) -> None:
        self.added_review = review

    def flush(self) -> None:
        return None

    def refresh(self, review: ProductReview) -> None:
        now = datetime(2026, 8, 12, 12, 0, 0)
        review.created_at = now
        review.updated_at = now


def test_create_review_is_published_immediately(monkeypatch) -> None:
    order = Order(
        order_id=101,
        order_number="DK-REVIEW-001",
        customer_id=202,
        status="completed",
    )
    order_item = OrderItem(
        order_item_id=404,
        public_id=uuid4(),
        order_id=order.order_id,
        variant_id=505,
    )
    session = _Session(order, order_item)
    monkeypatch.setattr(
        review_service,
        "run_in_transaction",
        lambda work: work(session),
    )

    response = review_service.create_review(
        customer_id=order.customer_id,
        order_number=order.order_number,
        order_item_public_id=str(order_item.public_id),
        payload=CreateReviewRequest(rating=5, content="Sản phẩm đẹp và đúng mô tả."),
    )

    assert response.status == "approved"
    assert session.added_review is not None
    assert session.added_review.status == "approved"
    assert session.added_review.moderated_by_customer_id is None
    assert session.added_review.moderated_at is None
    assert session.added_review.moderation_reason is None


def test_review_constraints_allow_auto_publish_without_moderator() -> None:
    checks = " ".join(
        str(constraint.sqltext)
        for constraint in ProductReview.__table__.constraints
        if hasattr(constraint, "sqltext")
    )

    assert "status in ('approved','rejected')" in checks
    assert "'pending'" not in checks
    assert "moderated_by_customer_id is null and moderated_at is null" in checks


class _ModerationSession:
    def __init__(self, review: ProductReview):
        self.review = review
        self.flush_count = 0

    def execute(self, _statement):
        return _ScalarResult(self.review)

    def flush(self) -> None:
        self.flush_count += 1

    def refresh(self, _review: ProductReview) -> None:
        return None


def test_admin_can_hide_and_restore_published_review(monkeypatch) -> None:
    review = ProductReview(
        public_id=uuid4(),
        order_item_id=1,
        customer_id=2,
        product_id=3,
        rating=2,
        content="Nội dung cần hậu kiểm",
        status="approved",
        created_at=datetime(2026, 8, 12, 10, 0, 0),
        updated_at=datetime(2026, 8, 12, 10, 0, 0),
    )
    session = _ModerationSession(review)
    monkeypatch.setattr(
        review_service,
        "run_in_transaction",
        lambda work: work(session),
    )

    hidden = review_service.moderate_review(
        99,
        str(review.public_id),
        ModerateReviewRequest(status="rejected", reason="Nội dung vi phạm"),
    )

    assert hidden.status == "rejected"
    assert review.moderation_reason == "Nội dung vi phạm"
    assert review.moderated_by_customer_id == 99
    assert review.moderated_at is not None

    restored = review_service.moderate_review(
        99,
        str(review.public_id),
        ModerateReviewRequest(status="approved"),
    )

    assert restored.status == "approved"
    assert review.moderation_reason is None
    assert review.moderated_by_customer_id == 99
    assert review.moderated_at is not None
    assert session.flush_count == 2

    review_service.moderate_review(
        101,
        str(review.public_id),
        ModerateReviewRequest(status="approved"),
    )
    assert session.flush_count == 2
    assert review.moderated_by_customer_id == 99
