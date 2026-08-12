"""publish product reviews immediately

Revision ID: 0009_reviews_publish_immediately
Revises: 0008_archive_catalog_promotions
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_reviews_publish_immediately"
down_revision = "0008_archive_catalog_promotions"
branch_labels = None
depends_on = None


_PUBLISHED_OR_HIDDEN = "status in ('approved','rejected')"
_POST_PUBLICATION_MODERATION = (
    "(status = 'approved' and moderation_reason is null and "
    "((moderated_by_customer_id is null and moderated_at is null) or "
    "(moderated_by_customer_id is not null and moderated_at is not null))) "
    "or (status = 'rejected' and moderated_by_customer_id is not null "
    "and moderated_at is not null and moderation_reason is not null "
    "and char_length(trim(moderation_reason)) >= 3)"
)


def _drop_review_check_constraint(logical_name: str) -> None:
    """Drop either the legacy double-prefixed name or the normalized name."""
    existing_names = {
        constraint["name"]
        for constraint in sa.inspect(op.get_bind()).get_check_constraints("product_reviews")
    }
    candidates = (
        f"ck_product_reviews_{logical_name}",
        f"ck_product_reviews_ck_product_reviews_{logical_name}",
    )
    for constraint_name in candidates:
        if constraint_name in existing_names:
            op.drop_constraint(op.f(constraint_name), "product_reviews", type_="check")
            return


def upgrade() -> None:
    _drop_review_check_constraint("moderation_consistency")
    _drop_review_check_constraint("status")
    op.execute(
        sa.text(
            "UPDATE product_reviews SET status = 'approved', updated_at = CURRENT_TIMESTAMP(6) "
            "WHERE status = 'pending'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE product_reviews SET moderation_reason = NULL "
            "WHERE status = 'approved'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE product_reviews "
            "SET moderation_reason = 'Ẩn theo chính sách kiểm duyệt trước đây' "
            "WHERE status = 'rejected' "
            "AND (moderation_reason IS NULL OR CHAR_LENGTH(TRIM(moderation_reason)) < 3)"
        )
    )
    op.alter_column(
        "product_reviews",
        "status",
        existing_type=sa.String(length=16),
        existing_nullable=False,
        server_default=sa.text("'approved'"),
    )
    op.create_check_constraint(
        "status",
        "product_reviews",
        _PUBLISHED_OR_HIDDEN,
    )
    op.create_check_constraint(
        "moderation_consistency",
        "product_reviews",
        _POST_PUBLICATION_MODERATION,
    )


def downgrade() -> None:
    _drop_review_check_constraint("moderation_consistency")
    _drop_review_check_constraint("status")
    op.execute(
        sa.text(
            "UPDATE product_reviews SET status = 'pending', updated_at = CURRENT_TIMESTAMP(6) "
            "WHERE status = 'approved' AND moderated_by_customer_id IS NULL"
        )
    )
    op.alter_column(
        "product_reviews",
        "status",
        existing_type=sa.String(length=16),
        existing_nullable=False,
        server_default=sa.text("'pending'"),
    )
    op.create_check_constraint(
        "status",
        "product_reviews",
        "status in ('pending','approved','rejected')",
    )
    op.create_check_constraint(
        "moderation_consistency",
        "product_reviews",
        "(status = 'pending' and moderated_by_customer_id is null and moderated_at is null) "
        "or (status in ('approved','rejected') and moderated_by_customer_id is not null "
        "and moderated_at is not null)",
    )
