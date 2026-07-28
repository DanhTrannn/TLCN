from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.money import compute_amounts
from app.core.config import get_settings
from app.core.errors import (
    auth_required,
    CART_NOT_ACTIVE,
    VARIANT_NOT_SELLABLE,
    AppError,
    not_found,
)
from app.core.ids import uuid7
from app.db.uow import run_in_transaction
from app.models.cart import Cart, CartItem
from app.models.catalog import Category, Product, ProductVariant
from app.models.inventory import Inventory
from app.models.customer import Customer
from app.modules.cart.schemas import CartItemResponse, CartResponse


def _empty_cart() -> CartResponse:
    return CartResponse(public_id=None, items=[], subtotal_vnd=0, shipping_fee_vnd=0, total_vnd=0)

def _lock_active_customer(db: Session, customer_id: int) -> None:
    customer = db.execute(
        select(Customer).where(Customer.customer_id == customer_id).with_for_update()
    ).scalar_one_or_none()
    if customer is None or customer.status != "active":
        raise auth_required()



def _load_cart_response(db: Session, cart: Cart) -> CartResponse:
    rows = db.execute(
        select(
            ProductVariant.public_id,
            Product.name,
            Product.slug,
            Product.image_url,
            ProductVariant.sku,
            ProductVariant.size_code,
            ProductVariant.color_code,
            ProductVariant.price_vnd,
            CartItem.quantity,
            ProductVariant.is_active.label("variant_active"),
            Product.is_active.label("product_active"),
            Category.is_active.label("category_active"),
            func.coalesce(Inventory.on_hand, 0).label("on_hand"),
        )
        .join(ProductVariant, ProductVariant.variant_id == CartItem.variant_id)
        .join(Product, Product.product_id == ProductVariant.product_id)
        .join(Category, Category.category_id == Product.category_id)
        .outerjoin(Inventory, Inventory.variant_id == ProductVariant.variant_id)
        .where(CartItem.cart_id == cart.cart_id, CartItem.is_present.is_(True))
        .order_by(CartItem.cart_item_id)
    ).all()

    items: list[CartItemResponse] = []
    line_totals: list[int] = []
    for r in rows:
        line_total = r.price_vnd * r.quantity
        line_totals.append(line_total)
        items.append(
            CartItemResponse(
                variant_public_id=str(r.public_id),
                product_name=r.name,
                slug=r.slug,
                sku=r.sku,
                size_code=r.size_code,
                color_code=r.color_code,
                image_url=r.image_url,
                unit_price_vnd=r.price_vnd,
                quantity=r.quantity,
                line_total_vnd=line_total,
                in_stock=(
                    bool(r.variant_active)
                    and bool(r.product_active)
                    and bool(r.category_active)
                    and int(r.on_hand or 0) >= r.quantity
                ),
            )
        )

    amounts = compute_amounts(line_totals)
    return CartResponse(
        public_id=str(cart.public_id),
        items=items,
        subtotal_vnd=amounts.subtotal_vnd,
        shipping_fee_vnd=amounts.shipping_fee_vnd,
        total_vnd=amounts.total_vnd,
    )


def get_cart(db: Session, customer_id: int) -> CartResponse:
    cart = db.execute(
        select(Cart).where(Cart.customer_id == customer_id, Cart.status == "active")
    ).scalar_one_or_none()
    if cart is None:
        return _empty_cart()
    return _load_cart_response(db, cart)


def _get_or_create_active_cart(db: Session, customer_id: int) -> Cart:
    cart = db.execute(
        select(Cart)
        .where(Cart.customer_id == customer_id, Cart.status == "active")
        .with_for_update()
    ).scalar_one_or_none()
    if cart is not None:
        return cart
    try:
        with db.begin_nested():
            cart = Cart(public_id=uuid7(), customer_id=customer_id, status="active")
            db.add(cart)
            db.flush()
        return cart
    except IntegrityError:
        cart = db.execute(
            select(Cart)
            .where(Cart.customer_id == customer_id, Cart.status == "active")
            .with_for_update()
        ).scalar_one()
        return cart


def _resolve_sellable_variant(db: Session, variant_public_id: UUID) -> ProductVariant:
    row = db.execute(
        select(ProductVariant)
        .join(Product, Product.product_id == ProductVariant.product_id)
        .join(Category, Category.category_id == Product.category_id)
        .where(
            ProductVariant.public_id == variant_public_id,
            ProductVariant.is_active.is_(True),
            Product.is_active.is_(True),
            Category.is_active.is_(True),
        )
    ).scalar_one_or_none()
    if row is None:
        raise AppError(VARIANT_NOT_SELLABLE, "Sản phẩm không khả dụng.", status_code=409)
    return row


def _parse_public_id(value: str) -> UUID:
    try:
        return UUID(value)
    except (ValueError, AttributeError) as error:
        raise not_found("Không tìm thấy biến thể sản phẩm.") from error


def set_item(customer_id: int, variant_public_id: str, quantity: int) -> CartResponse:
    settings = get_settings()
    if quantity > settings.cart_item_max_quantity:
        quantity = settings.cart_item_max_quantity
    vpid = _parse_public_id(variant_public_id)

    def _work(db: Session) -> CartResponse:
        _lock_active_customer(db, customer_id)
        cart = _get_or_create_active_cart(db, customer_id)
        variant = _resolve_sellable_variant(db, vpid)
        item = db.execute(
            select(CartItem)
            .where(CartItem.cart_id == cart.cart_id, CartItem.variant_id == variant.variant_id)
            .with_for_update()
        ).scalar_one_or_none()
        now = datetime.now(UTC)
        if item is None:
            db.add(
                CartItem(
                    cart_id=cart.cart_id,
                    variant_id=variant.variant_id,
                    quantity=quantity,
                    is_present=True,
                )
            )
        else:
            item.quantity = quantity
            item.is_present = True
            item.removed_at = None
        cart.updated_at = now
        db.flush()
        db.refresh(cart)
        return _load_cart_response(db, cart)

    return run_in_transaction(_work)


def remove_item(customer_id: int, variant_public_id: str) -> CartResponse:
    vpid = _parse_public_id(variant_public_id)

    def _work(db: Session) -> CartResponse:
        _lock_active_customer(db, customer_id)
        cart = db.execute(
            select(Cart)
            .where(Cart.customer_id == customer_id, Cart.status == "active")
            .with_for_update()
        ).scalar_one_or_none()
        if cart is None:
            raise AppError(CART_NOT_ACTIVE, "Không có giỏ hàng đang hoạt động.", status_code=409)
        variant = db.execute(
            select(ProductVariant).where(ProductVariant.public_id == vpid)
        ).scalar_one_or_none()
        if variant is None:
            raise not_found("Không tìm thấy biến thể sản phẩm.")
        item = db.execute(
            select(CartItem)
            .where(CartItem.cart_id == cart.cart_id, CartItem.variant_id == variant.variant_id)
            .with_for_update()
        ).scalar_one_or_none()
        now = datetime.now(UTC)
        if item is not None and item.is_present:
            item.is_present = False
            item.removed_at = now
            cart.updated_at = now
        db.flush()
        db.refresh(cart)
        return _load_cart_response(db, cart)

    return run_in_transaction(_work)
