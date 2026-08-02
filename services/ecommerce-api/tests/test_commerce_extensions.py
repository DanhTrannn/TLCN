from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.common.money import compute_amounts
from app.models.order import Order, OrderItem, OrderStatusHistory, Refund
from app.models.promotion import Coupon, CouponRedemption
from app.models.review import ProductReview
from app.modules.checkout.schemas import CheckoutRequest
from app.modules.coupons.schemas import CreateCouponRequest
from app.modules.coupons.service import (
    calculate_coupon_discount,
    list_available_coupons,
    normalize_coupon_code,
)
from app.modules.orders.schemas import CancelOrderRequest
from app.modules.reviews.schemas import ModerateReviewRequest


def test_money_breakdown_applies_discount_before_shipping() -> None:
    amounts = compute_amounts([300_000, 250_000], discount_amount_vnd=55_000)

    assert amounts.subtotal_vnd == 550_000
    assert amounts.discount_amount_vnd == 55_000
    assert amounts.shipping_fee_vnd == 0
    assert amounts.total_vnd == 495_000


def test_coupon_discount_is_integer_and_capped() -> None:
    assert calculate_coupon_discount("percentage", 10, 199_999) == 19_999
    assert calculate_coupon_discount("fixed_amount", 500_000, 199_999) == 199_999
    assert normalize_coupon_code(" welcome10 ") == "WELCOME10"




def test_available_coupons_exclude_customer_limit_and_sort_by_saving() -> None:
    now = datetime(2026, 8, 2, tzinfo=UTC)

    def coupon(
        coupon_id: int,
        code: str,
        discount_type: str,
        discount_value: int,
        *,
        per_customer_limit: int | None = None,
    ) -> Coupon:
        return Coupon(
            coupon_id=coupon_id,
            public_id=uuid4(),
            code_normalized=code,
            discount_type=discount_type,
            discount_value=discount_value,
            minimum_subtotal_vnd=100_000,
            starts_at=(now - timedelta(days=1)).replace(tzinfo=None),
            ends_at=(now + timedelta(days=1)).replace(tzinfo=None),
            is_active=True,
            total_usage_limit=100,
            per_customer_usage_limit=per_customer_limit,
            used_count=10,
        )

    candidates = [
        coupon(1, "GIAM10", "percentage", 10),
        coupon(2, "GIAM50K", "fixed_amount", 50_000),
        coupon(3, "DADUNG", "percentage", 20, per_customer_limit=1),
    ]

    class Result:
        def __init__(self, rows):
            self.rows = rows

        def all(self):
            return self.rows

        def scalars(self):
            return self

    class Session:
        def __init__(self):
            self.results = iter([Result([(3, 1)]), Result(candidates)])

        def execute(self, _statement):
            return next(self.results)

    response = list_available_coupons(
        Session(),
        customer_id=99,
        subtotal_vnd=600_000,
        now=now,
    )

    assert [item.code for item in response.items] == ["GIAM10", "GIAM50K"]
    assert [item.discount_amount_vnd for item in response.items] == [60_000, 50_000]
    assert response.items[0].remaining_uses == 90
    assert response.items[0].ends_at.tzinfo is UTC


def test_available_coupons_are_empty_for_empty_cart() -> None:
    class Session:
        def execute(self, _statement):
            raise AssertionError("Empty cart must not query coupons")

    response = list_available_coupons(Session(), customer_id=1, subtotal_vnd=0)
    assert response.items == []
    assert response.subtotal_vnd == 0


def test_checkout_normalizes_empty_coupon() -> None:
    payload = CheckoutRequest(
        receiver_name="Người nhận",
        receiver_phone="0900000000",
        shipping_address_text="TP. Hồ Chí Minh",
        coupon_code="",
    )

    assert payload.coupon_code is None


def test_coupon_schema_rejects_invalid_window_and_percentage() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValidationError):
        CreateCouponRequest(
            code="TOO-MUCH",
            discount_type="percentage",
            discount_value=101,
            starts_at=now,
            ends_at=now - timedelta(days=1),
        )


def test_cancel_and_review_moderation_require_meaningful_reason() -> None:
    with pytest.raises(ValidationError):
        CancelOrderRequest(reason="x")
    with pytest.raises(ValidationError):
        ModerateReviewRequest(status="rejected", reason=None)


def test_new_table_grains_have_database_unique_arbiters() -> None:
    order_item_indexes = {index.name for index in OrderItem.__table__.indexes}
    refund_indexes = {index.name for index in Refund.__table__.indexes}
    redemption_indexes = {index.name for index in CouponRedemption.__table__.indexes}
    review_indexes = {index.name for index in ProductReview.__table__.indexes}
    coupon_indexes = {index.name for index in Coupon.__table__.indexes}

    assert "uq_order_items_public_id" in order_item_indexes
    assert "uq_refunds_payment_id" in refund_indexes
    assert "uq_coupon_redemptions_order_id" in redemption_indexes
    assert "uq_product_reviews_order_item_id" in review_indexes
    assert "uq_coupons_code_normalized" in coupon_indexes


def test_order_state_constraints_include_confirmed_and_cancelled() -> None:
    order_checks = " ".join(
        str(constraint.sqltext)
        for constraint in Order.__table__.constraints
        if hasattr(constraint, "sqltext")
    )
    history_checks = " ".join(
        str(constraint.sqltext)
        for constraint in OrderStatusHistory.__table__.constraints
        if hasattr(constraint, "sqltext")
    )

    assert "confirmed" in order_checks
    assert "cancelled" in order_checks
    assert "from_status = 'confirmed'" in history_checks
    assert "to_status in ('confirmed','cancelled')" in history_checks
