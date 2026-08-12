from sqlalchemy import CheckConstraint

from app.models.catalog import Product
from app.models.promotion import Coupon


def _check_names(model: type[Product] | type[Coupon]) -> set[str]:
    return {
        constraint.name
        for constraint in model.__table__.constraints
        if isinstance(constraint, CheckConstraint) and constraint.name is not None
    }


def test_product_archive_metadata_is_guarded_by_database_constraints() -> None:
    assert {"archived_at", "archived_by_customer_id", "archive_reason"}.issubset(
        Product.__table__.columns.keys()
    )
    assert {
        "ck_products_archive_metadata_consistency",
        "ck_products_archived_not_active",
    }.issubset(_check_names(Product))
    assert Product.__table__.c.archived_by_customer_id.foreign_keys


def test_coupon_archive_metadata_is_guarded_by_database_constraints() -> None:
    assert {"archived_at", "archived_by_customer_id", "archive_reason"}.issubset(
        Coupon.__table__.columns.keys()
    )
    assert {
        "ck_coupons_archive_metadata_consistency",
        "ck_coupons_archived_not_active",
    }.issubset(_check_names(Coupon))
    assert Coupon.__table__.c.archived_by_customer_id.foreign_keys
