from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import auth_required, not_found
from app.db.uow import run_in_transaction
from app.models.catalog import Category, Product, ProductVariant
from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.wishlist import WishlistItem
from app.modules.wishlist.schemas import WishlistItemResponse, WishlistResponse


def _parse_product_public_id(value: str) -> UUID:
    try:
        return UUID(value)
    except (ValueError, AttributeError) as error:
        raise not_found("Không tìm thấy sản phẩm.") from error


def _lock_active_customer(db: Session, customer_id: int) -> None:
    customer = db.execute(
        select(Customer).where(Customer.customer_id == customer_id).with_for_update()
    ).scalar_one_or_none()
    if customer is None or customer.status != "active":
        raise auth_required()


def get_wishlist(db: Session, customer_id: int) -> WishlistResponse:
    variant_stats = (
        select(
            ProductVariant.product_id.label("product_id"),
            func.min(ProductVariant.price_vnd).label("min_price_vnd"),
            func.max(func.coalesce(Inventory.on_hand, 0)).label("max_on_hand"),
        )
        .outerjoin(Inventory, Inventory.variant_id == ProductVariant.variant_id)
        .where(ProductVariant.is_active.is_(True))
        .group_by(ProductVariant.product_id)
        .subquery()
    )
    rows = db.execute(
        select(
            WishlistItem,
            Product.public_id,
            Product.slug,
            Product.name,
            Product.image_url,
            Product.is_active.label("product_active"),
            Category.code.label("category_code"),
            Category.is_active.label("category_active"),
            variant_stats.c.min_price_vnd,
            variant_stats.c.max_on_hand,
        )
        .join(Product, Product.product_id == WishlistItem.product_id)
        .join(Category, Category.category_id == Product.category_id)
        .outerjoin(variant_stats, variant_stats.c.product_id == Product.product_id)
        .where(
            WishlistItem.customer_id == customer_id,
            WishlistItem.is_present.is_(True),
        )
        .order_by(WishlistItem.last_added_at.desc(), WishlistItem.wishlist_item_id.desc())
    ).all()

    return WishlistResponse(
        items=[
            WishlistItemResponse(
                product_public_id=str(row.public_id),
                slug=row.slug,
                name=row.name,
                image_url=row.image_url,
                category_code=row.category_code,
                min_price_vnd=(
                    int(row.min_price_vnd) if row.min_price_vnd is not None else None
                ),
                in_stock=int(row.max_on_hand or 0) > 0,
                is_available=(
                    bool(row.product_active)
                    and bool(row.category_active)
                    and row.min_price_vnd is not None
                ),
                first_added_at=row.WishlistItem.first_added_at,
                last_added_at=row.WishlistItem.last_added_at,
            )
            for row in rows
        ]
    )


def set_product_presence(customer_id: int, product_public_id: str, present: bool) -> None:
    parsed_id = _parse_product_public_id(product_public_id)

    def _work(db: Session) -> None:
        _lock_active_customer(db, customer_id)
        product = db.execute(
            select(Product, Category.is_active.label("category_active"))
            .join(Category, Category.category_id == Product.category_id)
            .where(Product.public_id == parsed_id)
        ).first()
        if product is None:
            raise not_found("Không tìm thấy sản phẩm.")
        product_row, category_active = product
        if present and (not product_row.is_active or not category_active):
            raise not_found("Sản phẩm hiện không khả dụng.")

        item = db.execute(
            select(WishlistItem)
            .where(
                WishlistItem.customer_id == customer_id,
                WishlistItem.product_id == product_row.product_id,
            )
            .with_for_update()
        ).scalar_one_or_none()
        now = datetime.now(UTC)

        if item is None:
            if not present:
                return
            db.add(
                WishlistItem(
                    customer_id=customer_id,
                    product_id=product_row.product_id,
                    is_present=True,
                    first_added_at=now,
                    last_added_at=now,
                    updated_at=now,
                )
            )
        elif present and not item.is_present:
            item.is_present = True
            item.last_added_at = now
            item.removed_at = None
            item.updated_at = now
        elif not present and item.is_present:
            item.is_present = False
            item.removed_at = now
            item.updated_at = now
        db.flush()

    run_in_transaction(_work)
