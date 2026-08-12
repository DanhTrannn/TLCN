from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.errors import AppError, INVALID_STATE_TRANSITION
from app.models.catalog import Product
from app.models.promotion import Coupon
from app.modules.admin import service as admin_service
from app.modules.admin.schemas import UpdateProductRequest
from app.modules.coupons import service as coupon_service


class _ScalarResult:
    def __init__(self, entity):
        self.entity = entity

    def scalar_one_or_none(self):
        return self.entity


class _Session:
    def __init__(self, entity):
        self.entity = entity
        self.flush_count = 0

    def execute(self, _statement):
        return _ScalarResult(self.entity)

    def flush(self):
        self.flush_count += 1


def _run_with(session: _Session):
    return lambda work: work(session)


def test_product_archive_is_idempotent_and_preserves_first_audit(monkeypatch) -> None:
    product = Product(
        public_id=uuid4(),
        category_id=1,
        slug="archive-me",
        name="Archive me",
        is_active=True,
    )
    session = _Session(product)
    monkeypatch.setattr(admin_service, "run_in_transaction", _run_with(session))

    admin_service.archive_product(42, str(product.public_id), "Ngừng kinh doanh")
    first_archived_at = product.archived_at

    admin_service.archive_product(99, str(product.public_id), "Lý do khác")

    assert product.is_active is False
    assert first_archived_at is not None
    assert product.archived_at == first_archived_at
    assert product.archived_by_customer_id == 42
    assert product.archive_reason == "Ngừng kinh doanh"
    assert session.flush_count == 1


def test_archived_product_cannot_be_reactivated(monkeypatch) -> None:
    product = Product(
        public_id=uuid4(),
        category_id=1,
        slug="archived-product",
        name="Archived product",
        is_active=False,
        archived_at=datetime.now(UTC) - timedelta(days=1),
        archived_by_customer_id=42,
        archive_reason="Ngừng kinh doanh",
    )
    session = _Session(product)
    monkeypatch.setattr(admin_service, "run_in_transaction", _run_with(session))

    with pytest.raises(AppError) as raised:
        admin_service.update_product(
            str(product.public_id),
            UpdateProductRequest(is_active=True),
        )

    assert raised.value.code == INVALID_STATE_TRANSITION


def test_coupon_archive_is_idempotent_and_cannot_be_reactivated(monkeypatch) -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    coupon = Coupon(
        public_id=uuid4(),
        code_normalized="ARCHIVE10",
        discount_type="percentage",
        discount_value=10,
        minimum_subtotal_vnd=0,
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=1),
        is_active=True,
        used_count=0,
    )
    session = _Session(coupon)
    monkeypatch.setattr(coupon_service, "run_in_transaction", _run_with(session))

    coupon_service.archive_coupon(42, coupon.public_id, "Kết thúc chiến dịch")
    first_archived_at = coupon.archived_at
    coupon_service.archive_coupon(99, coupon.public_id, "Lý do khác")

    assert coupon.is_active is False
    assert coupon.archived_at == first_archived_at
    assert coupon.archived_by_customer_id == 42
    assert coupon.archive_reason == "Kết thúc chiến dịch"
    assert session.flush_count == 1

    with pytest.raises(AppError) as raised:
        coupon_service.set_coupon_active(coupon.public_id, True)

    assert raised.value.code == INVALID_STATE_TRANSITION
