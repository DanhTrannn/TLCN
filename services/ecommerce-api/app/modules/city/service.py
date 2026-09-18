from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.models.catalog import Category, Product, ProductVariant
from app.models.customer import Customer, CustomerCredential
from app.models.multicity import City, Store, StoreInventory
from app.models.order import Order, OrderItem, Payment
from app.modules.city.schemas import (
    CityDashboardResponse,
    CityInventoryItem,
    CityOrderResponse,
    CityStoreResponse,
)


def get_city_dashboard(db: Session, city_id: int) -> CityDashboardResponse:
    city = db.execute(select(City).where(City.city_id == city_id)).scalar_one_or_none()
    if city is None:
        raise not_found("Không tìm thấy thành phố.")

    total_stores = db.scalar(
        select(func.count()).select_from(Store).where(Store.city_id == city_id)
    ) or 0
    active_stores = db.scalar(
        select(func.count()).select_from(Store).where(
            Store.city_id == city_id, Store.is_active.is_(True)
        )
    ) or 0

    store_ids = [
        sid for (sid,) in db.execute(
            select(Store.store_id).where(Store.city_id == city_id)
        ).all()
    ]

    total_orders = 0
    completed_orders = 0
    total_revenue_vnd = 0
    if store_ids:
        total_orders = db.scalar(
            select(func.count()).select_from(Order).where(Order.store_id.in_(store_ids))
        ) or 0
        completed_orders = db.scalar(
            select(func.count()).select_from(Order).where(
                Order.store_id.in_(store_ids), Order.status == "completed"
            )
        ) or 0
        total_revenue_vnd = db.scalar(
            select(func.coalesce(func.sum(Payment.amount_vnd), 0))
            .join(Order, Order.order_id == Payment.order_id)
            .where(Order.store_id.in_(store_ids), Payment.status == "succeeded")
        ) or 0

    total_staff = db.scalar(
        select(func.count()).select_from(Customer).where(
            Customer.city_id == city_id,
            Customer.role.in_(["store_manager"]),
            Customer.status == "active",
        )
    ) or 0

    low_stock_items = 0
    if store_ids:
        low_stock_items = db.scalar(
            select(func.count()).select_from(StoreInventory).where(
                StoreInventory.store_id.in_(store_ids),
                StoreInventory.on_hand <= 5,
            )
        ) or 0

    return CityDashboardResponse(
        city_name=city.name,
        total_stores=int(total_stores),
        active_stores=int(active_stores),
        total_orders=int(total_orders),
        completed_orders=int(completed_orders),
        total_revenue_vnd=int(total_revenue_vnd),
        total_staff=int(total_staff),
        low_stock_items=int(low_stock_items),
    )


def list_city_stores(db: Session, city_id: int) -> list[CityStoreResponse]:
    rows = db.execute(
        select(Store)
        .where(Store.city_id == city_id)
        .order_by(Store.name)
    ).all()
    return [
        CityStoreResponse(
            store_id=store.store_id,
            code=store.code,
            name=store.name,
            address=store.address,
            phone=store.phone,
            is_active=store.is_active,
            created_at=store.created_at,
        )
        for (store,) in rows
    ]


def list_city_orders(
    db: Session, city_id: int, status: str | None = None, store_id: int | None = None
) -> list[CityOrderResponse]:
    store_ids = [
        sid for (sid,) in db.execute(
            select(Store.store_id).where(Store.city_id == city_id)
        ).all()
    ]
    if not store_ids:
        return []

    item_count = (
        select(OrderItem.order_id, func.sum(OrderItem.quantity).label("item_count"))
        .group_by(OrderItem.order_id)
        .subquery()
    )
    stmt = (
        select(
            Order,
            Store.name.label("store_name"),
            Customer.display_name,
            func.coalesce(item_count.c.item_count, 0),
        )
        .join(Store, Store.store_id == Order.store_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .outerjoin(item_count, item_count.c.order_id == Order.order_id)
        .where(Order.store_id.in_(store_ids))
    )
    if status:
        stmt = stmt.where(Order.status == status)
    if store_id:
        stmt = stmt.where(Order.store_id == store_id)

    rows = db.execute(
        stmt.order_by(Order.created_at.desc(), Order.order_id.desc()).limit(200)
    ).all()
    return [
        CityOrderResponse(
            order_number=order.order_number,
            store_name=store_name,
            customer_name=customer_name,
            status=order.status,
            total_vnd=order.total_vnd,
            item_count=int(item_count_value),
            channel=order.channel,
            created_at=order.created_at,
        )
        for order, store_name, customer_name, item_count_value in rows
    ]


def list_city_inventory(db: Session, city_id: int) -> list[CityInventoryItem]:
    store_ids = [
        sid for (sid,) in db.execute(
            select(Store.store_id).where(Store.city_id == city_id)
        ).all()
    ]
    if not store_ids:
        return []

    stmt = (
        select(
            StoreInventory,
            Store.name.label("store_name"),
            ProductVariant.sku.label("variant_sku"),
            Product.name.label("product_name"),
            Category.name.label("category_name"),
            ProductVariant.size_code,
            ProductVariant.color_code,
            ProductVariant.price_vnd,
        )
        .join(Store, Store.store_id == StoreInventory.store_id)
        .join(ProductVariant, ProductVariant.variant_id == StoreInventory.variant_id)
        .join(Product, Product.product_id == ProductVariant.product_id)
        .join(Category, Category.category_id == Product.category_id)
        .where(StoreInventory.store_id.in_(store_ids))
    )
    rows = db.execute(stmt).all()
    return [
        CityInventoryItem(
            store_id=row.StoreInventory.store_id,
            store_name=row.store_name,
            variant_id=row.StoreInventory.variant_id,
            variant_sku=row.variant_sku,
            product_name=row.product_name,
            category_name=row.category_name,
            size_code=row.size_code,
            color_code=row.color_code,
            price_vnd=row.price_vnd,
            on_hand=row.StoreInventory.on_hand,
        )
        for row in rows
    ]
