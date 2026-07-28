from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError, VALIDATION_ERROR, not_found
from app.core.ids import uuid7
from app.db.uow import run_in_transaction
from app.models.catalog import Category, Product, ProductVariant
from app.models.customer import Customer, CustomerCredential
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem
from app.modules.orders.schemas import OrderDetailResponse
from app.modules.orders.service import get_order_detail
from app.modules.admin.schemas import (
    AdminCustomerResponse,
    AdminOrderResponse,
    AdminOverviewResponse,
    AdminProductResponse,
    AdminVariantResponse,
    CreateProductRequest,
    UpdateProductRequest,
    UpdateVariantRequest,
)


def _parse_public_id(value: str, label: str) -> UUID:
    try:
        return UUID(value)
    except (TypeError, ValueError) as error:
        raise not_found(f"Không tìm thấy {label}.") from error


def get_overview(db: Session) -> AdminOverviewResponse:
    active_products = db.scalar(select(func.count()).select_from(Product).where(Product.is_active.is_(True))) or 0
    active_variants = db.scalar(
        select(func.count()).select_from(ProductVariant).where(ProductVariant.is_active.is_(True))
    ) or 0
    low_stock_variants = db.scalar(
        select(func.count())
        .select_from(Inventory)
        .join(ProductVariant, ProductVariant.variant_id == Inventory.variant_id)
        .where(ProductVariant.is_active.is_(True), Inventory.on_hand <= 5)
    ) or 0
    customers = db.scalar(select(func.count()).select_from(Customer).where(Customer.role == "customer")) or 0
    paid_orders = db.scalar(
        select(func.count()).select_from(Order).where(Order.status.in_(("paid", "completed")))
    ) or 0
    revenue = db.scalar(
        select(func.coalesce(func.sum(Order.total_vnd), 0)).where(Order.status.in_(("paid", "completed")))
    ) or 0
    return AdminOverviewResponse(
        active_products=int(active_products),
        active_variants=int(active_variants),
        low_stock_variants=int(low_stock_variants),
        customers=int(customers),
        paid_orders=int(paid_orders),
        recognized_revenue_vnd=int(revenue),
    )


def list_products(db: Session) -> list[AdminProductResponse]:
    product_rows = db.execute(
        select(Product, Category.code)
        .join(Category, Category.category_id == Product.category_id)
        .order_by(Product.created_at.desc(), Product.product_id.desc())
    ).all()
    product_ids = [product.product_id for product, _ in product_rows]
    variants_by_product: dict[int, list[AdminVariantResponse]] = {product_id: [] for product_id in product_ids}
    if product_ids:
        variant_rows = db.execute(
            select(ProductVariant, func.coalesce(Inventory.on_hand, 0).label("on_hand"))
            .outerjoin(Inventory, Inventory.variant_id == ProductVariant.variant_id)
            .where(ProductVariant.product_id.in_(product_ids))
            .order_by(ProductVariant.product_id, ProductVariant.variant_id)
        ).all()
        for variant, on_hand in variant_rows:
            variants_by_product[variant.product_id].append(
                AdminVariantResponse(
                    public_id=str(variant.public_id),
                    sku=variant.sku,
                    size_code=variant.size_code,
                    color_code=variant.color_code,
                    price_vnd=variant.price_vnd,
                    is_active=variant.is_active,
                    on_hand=int(on_hand or 0),
                )
            )
    return [
        AdminProductResponse(
            public_id=str(product.public_id),
            category_code=category_code,
            slug=product.slug,
            name=product.name,
            description=product.description,
            image_url=product.image_url,
            is_active=product.is_active,
            variants=variants_by_product[product.product_id],
        )
        for product, category_code in product_rows
    ]


def create_product(payload: CreateProductRequest) -> AdminProductResponse:
    def _work(db: Session) -> None:
        category = db.execute(
            select(Category).where(Category.code == payload.category_code, Category.is_active.is_(True))
        ).scalar_one_or_none()
        if category is None:
            raise AppError(VALIDATION_ERROR, "Danh mục không hợp lệ.", status_code=422)
        product = Product(
            public_id=uuid7(),
            category_id=category.category_id,
            slug=payload.slug,
            name=payload.name,
            description=payload.description or None,
            image_url=str(payload.image_url) if payload.image_url else None,
            is_active=True,
        )
        db.add(product)
        db.flush()
        for item in payload.variants:
            variant = ProductVariant(
                public_id=uuid7(),
                product_id=product.product_id,
                sku=item.sku.upper(),
                size_code=item.size_code,
                color_code=item.color_code,
                price_vnd=item.price_vnd,
                is_active=True,
            )
            db.add(variant)
            db.flush()
            db.add(
                Inventory(
                    variant_id=variant.variant_id,
                    opening_on_hand=item.opening_on_hand,
                    on_hand=item.opening_on_hand,
                    version=0,
                )
            )
        db.flush()

    try:
        run_in_transaction(_work)
    except IntegrityError as error:
        raise AppError(
            VALIDATION_ERROR,
            "Slug, SKU hoặc tổ hợp size/màu đã tồn tại.",
            status_code=409,
        ) from error
    # Read through a fresh transaction so the response always reflects committed data.
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        product = db.execute(select(Product).where(Product.slug == payload.slug)).scalar_one()
        return next(item for item in list_products(db) if item.public_id == str(product.public_id))
    finally:
        db.close()


def update_product(public_id: str, payload: UpdateProductRequest) -> None:
    parsed_id = _parse_public_id(public_id, "sản phẩm")

    def _work(db: Session) -> None:
        product = db.execute(
            select(Product).where(Product.public_id == parsed_id).with_for_update()
        ).scalar_one_or_none()
        if product is None:
            raise not_found("Không tìm thấy sản phẩm.")
        fields = payload.model_fields_set
        if "category_code" in fields:
            category = db.execute(
                select(Category).where(Category.code == payload.category_code, Category.is_active.is_(True))
            ).scalar_one_or_none()
            if category is None:
                raise AppError(VALIDATION_ERROR, "Danh mục không hợp lệ.", status_code=422)
            product.category_id = category.category_id
        if "name" in fields:
            product.name = payload.name
        if "description" in fields:
            product.description = payload.description or None
        if "image_url" in fields:
            product.image_url = str(payload.image_url) if payload.image_url else None
        if "is_active" in fields:
            product.is_active = payload.is_active
        product.updated_at = datetime.now(UTC)
        db.flush()

    run_in_transaction(_work)


def update_variant(public_id: str, payload: UpdateVariantRequest) -> None:
    parsed_id = _parse_public_id(public_id, "biến thể")

    def _work(db: Session) -> None:
        variant = db.execute(
            select(ProductVariant).where(ProductVariant.public_id == parsed_id).with_for_update()
        ).scalar_one_or_none()
        if variant is None:
            raise not_found("Không tìm thấy biến thể.")
        if payload.price_vnd is not None:
            variant.price_vnd = payload.price_vnd
        if payload.is_active is not None:
            variant.is_active = payload.is_active
        variant.updated_at = datetime.now(UTC)
        db.flush()

    run_in_transaction(_work)


def list_orders(db: Session, status: str | None) -> list[AdminOrderResponse]:
    item_count = (
        select(OrderItem.order_id, func.sum(OrderItem.quantity).label("item_count"))
        .group_by(OrderItem.order_id)
        .subquery()
    )
    stmt = (
        select(
            Order,
            Customer.display_name,
            CustomerCredential.email_normalized,
            func.coalesce(item_count.c.item_count, 0),
        )
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(CustomerCredential, CustomerCredential.customer_id == Customer.customer_id)
        .outerjoin(item_count, item_count.c.order_id == Order.order_id)
    )
    if status:
        stmt = stmt.where(Order.status == status)
    rows = db.execute(stmt.order_by(Order.created_at.desc(), Order.order_id.desc()).limit(200)).all()
    return [
        AdminOrderResponse(
            order_number=order.order_number,
            customer_name=customer_name,
            customer_email=email,
            status=order.status,
            total_vnd=order.total_vnd,
            item_count=int(item_count_value),
            created_at=order.created_at,
        )
        for order, customer_name, email, item_count_value in rows
    ]



def get_admin_order_detail(db: Session, order_number: str) -> OrderDetailResponse:
    order = db.execute(
        select(Order).where(Order.order_number == order_number)
    ).scalar_one_or_none()
    if order is None:
        raise not_found("Không tìm thấy đơn hàng.")
    return get_order_detail(db, order.customer_id, order_number)


def list_customers(db: Session) -> list[AdminCustomerResponse]:
    rows = db.execute(
        select(Customer, CustomerCredential.email_normalized)
        .join(CustomerCredential, CustomerCredential.customer_id == Customer.customer_id)
        .order_by(Customer.created_at.desc(), Customer.customer_id.desc())
        .limit(200)
    ).all()
    return [
        AdminCustomerResponse(
            public_id=str(customer.public_id),
            display_name=customer.display_name,
            email=email,
            status=customer.status,
            role=customer.role,
            created_at=customer.created_at,
        )
        for customer, email in rows
    ]


def update_customer_status(admin_customer_id: int, public_id: str, status: str) -> None:
    parsed_id = _parse_public_id(public_id, "khách hàng")

    def _work(db: Session) -> None:
        customer = db.execute(
            select(Customer).where(Customer.public_id == parsed_id).with_for_update()
        ).scalar_one_or_none()
        if customer is None:
            raise not_found("Không tìm thấy khách hàng.")
        if customer.customer_id == admin_customer_id and status != "active":
            raise AppError(VALIDATION_ERROR, "Không thể vô hiệu hóa chính tài khoản đang dùng.", status_code=409)
        if customer.role == "admin" and status != "active":
            raise AppError(VALIDATION_ERROR, "Không thể vô hiệu hóa tài khoản quản trị.", status_code=409)
        customer.status = status
        customer.updated_at = datetime.now(UTC)
        db.flush()

    run_in_transaction(_work)
