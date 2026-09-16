from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.models.catalog import Product, ProductVariant
from app.models.customer import Customer, CustomerCredential
from app.models.multicity import Store, StoreInventory
from app.models.order import Order, OrderItem, Payment
from app.modules.orders.schemas import OrderDetailResponse
from app.modules.orders.service import get_order_detail
from app.modules.store.schemas import (
    StoreDashboardResponse,
    StoreInventoryItem,
    StoreOrderResponse,
    StoreStaffMember,
)


def get_store_dashboard(db: Session, store_id: int) -> StoreDashboardResponse:
    store = db.execute(
        select(Store).where(Store.store_id == store_id)
    ).scalar_one_or_none()
    if store is None:
        raise not_found("Không tìm thấy cửa hàng.")

    now = datetime.now(UTC).replace(tzinfo=None)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    today_revenue_vnd = int(
        db.scalar(
            select(func.coalesce(func.sum(Payment.amount_vnd), 0))
            .join(Order, Order.order_id == Payment.order_id)
            .where(
                Order.store_id == store_id,
                Order.created_at >= today_start,
                Payment.status == "succeeded",
            )
        )
        or 0
    )

    today_orders = int(
        db.scalar(
            select(func.count())
            .select_from(Order)
            .where(
                Order.store_id == store_id,
                Order.created_at >= today_start,
            )
        )
        or 0
    )

    total_orders = int(
        db.scalar(
            select(func.count())
            .select_from(Order)
            .where(Order.store_id == store_id)
        )
        or 0
    )

    completed_orders = int(
        db.scalar(
            select(func.count())
            .select_from(Order)
            .where(Order.store_id == store_id, Order.status == "completed")
        )
        or 0
    )

    total_revenue_vnd = int(
        db.scalar(
            select(func.coalesce(func.sum(Payment.amount_vnd), 0))
            .join(Order, Order.order_id == Payment.order_id)
            .where(
                Order.store_id == store_id,
                Payment.status == "succeeded",
            )
        )
        or 0
    )

    low_stock_items = int(
        db.scalar(
            select(func.count())
            .select_from(StoreInventory)
            .where(
                StoreInventory.store_id == store_id,
                StoreInventory.on_hand <= 5,
            )
        )
        or 0
    )

    active_staff = int(
        db.scalar(
            select(func.count())
            .select_from(Customer)
            .where(
                Customer.store_id == store_id,
                Customer.role == "store_manager",
                Customer.status == "active",
            )
        )
        or 0
    )

    return StoreDashboardResponse(
        store_name=store.name,
        today_orders=today_orders,
        today_revenue_vnd=today_revenue_vnd,
        total_orders=total_orders,
        completed_orders=completed_orders,
        total_revenue_vnd=total_revenue_vnd,
        low_stock_items=low_stock_items,
        active_staff=active_staff,
    )


def list_store_orders(
    db: Session, store_id: int, status: str | None
) -> list[StoreOrderResponse]:
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
        .where(Order.store_id == store_id)
    )
    if status:
        stmt = stmt.where(Order.status == status)
    rows = db.execute(
        stmt.order_by(Order.created_at.desc(), Order.order_id.desc()).limit(200)
    ).all()
    return [
        StoreOrderResponse(
            order_number=order.order_number,
            customer_name=customer_name,
            customer_email=email,
            channel=order.channel,
            status=order.status,
            total_vnd=order.total_vnd,
            item_count=int(item_count_value),
            created_at=order.created_at,
        )
        for order, customer_name, email, item_count_value in rows
    ]


def get_store_order_detail(
    db: Session, store_id: int, order_number: str
) -> OrderDetailResponse:
    order = db.execute(
        select(Order).where(
            Order.order_number == order_number,
            Order.store_id == store_id,
        )
    ).scalar_one_or_none()
    if order is None:
        raise not_found("Không tìm thấy đơn hàng.")
    return get_order_detail(db, order.customer_id, order_number)


def list_store_inventory(db: Session, store_id: int) -> list[StoreInventoryItem]:
    rows = db.execute(
        select(
            StoreInventory,
            Store.name.label("store_name"),
            ProductVariant.sku.label("variant_sku"),
            ProductVariant.size_code,
            ProductVariant.color_code,
            ProductVariant.price_vnd,
        )
        .join(Store, Store.store_id == StoreInventory.store_id)
        .join(ProductVariant, ProductVariant.variant_id == StoreInventory.variant_id)
        .where(StoreInventory.store_id == store_id)
        .order_by(StoreInventory.variant_id)
    ).all()
    return [
        StoreInventoryItem(
            store_id=row.StoreInventory.store_id,
            store_name=row.store_name,
            variant_id=row.StoreInventory.variant_id,
            variant_sku=row.variant_sku,
            size_code=row.size_code,
            color_code=row.color_code,
            price_vnd=row.price_vnd,
            on_hand=row.StoreInventory.on_hand,
            opening_on_hand=row.StoreInventory.opening_on_hand,
        )
        for row in rows
    ]


def list_store_staff(db: Session, store_id: int) -> list[StoreStaffMember]:
    rows = db.execute(
        select(Customer, CustomerCredential.email_normalized)
        .join(CustomerCredential, CustomerCredential.customer_id == Customer.customer_id)
        .where(
            Customer.store_id == store_id,
            Customer.role == "store_manager",
        )
        .order_by(Customer.customer_id)
    ).all()
    return [
        StoreStaffMember(
            public_id=str(customer.public_id),
            display_name=customer.display_name,
            email=email,
            role=customer.role,
            status=customer.status,
            created_at=customer.created_at,
        )
        for customer, email in rows
    ]
