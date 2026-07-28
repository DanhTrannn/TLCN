from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.pagination import decode_cursor, encode_cursor
from app.core.config import get_settings
from app.core.errors import (
    INVALID_STATE_TRANSITION,
    AppError,
    not_found,
)
from app.db.uow import run_in_transaction
from app.models.order import Order, OrderItem, OrderStatusHistory, Payment
from app.modules.orders.schemas import (
    OrderDetailResponse,
    OrderItemResponse,
    OrderListItem,
    OrderListResponse,
    PaymentResponse,
    StatusHistoryResponse,
)


def list_orders(db: Session, customer_id: int, cursor: str | None) -> OrderListResponse:
    page_size = get_settings().order_page_size
    item_count = (
        select(OrderItem.order_id, func.count().label("cnt"))
        .group_by(OrderItem.order_id)
        .subquery()
    )
    stmt = (
        select(Order, func.coalesce(item_count.c.cnt, 0).label("item_count"))
        .outerjoin(item_count, item_count.c.order_id == Order.order_id)
        .where(Order.customer_id == customer_id)
    )
    if cursor:
        cur_t, cur_i = decode_cursor(cursor)
        stmt = stmt.where(
            (Order.created_at < cur_t)
            | ((Order.created_at == cur_t) & (Order.order_id < cur_i))
        )
    stmt = stmt.order_by(Order.created_at.desc(), Order.order_id.desc()).limit(page_size + 1)

    rows = db.execute(stmt).all()
    has_more = len(rows) > page_size
    rows = rows[:page_size]

    items = [
        OrderListItem(
            order_number=order.order_number,
            status=order.status,
            total_vnd=order.total_vnd,
            item_count=int(cnt),
            created_at=order.created_at,
        )
        for order, cnt in rows
    ]
    next_cursor = None
    if has_more and rows:
        last = rows[-1][0]
        next_cursor = encode_cursor(last.created_at, last.order_id)
    return OrderListResponse(items=items, next_cursor=next_cursor)


def get_order_detail(db: Session, customer_id: int, order_number: str) -> OrderDetailResponse:
    order = db.execute(
        select(Order).where(Order.order_number == order_number)
    ).scalar_one_or_none()
    if order is None or order.customer_id != customer_id:
        raise not_found("Không tìm thấy đơn hàng.")

    item_rows = (
        db.execute(
            select(OrderItem).where(OrderItem.order_id == order.order_id).order_by(OrderItem.order_item_id)
        )
        .scalars()
        .all()
    )
    payment = db.execute(
        select(Payment).where(Payment.order_id == order.order_id)
    ).scalar_one_or_none()
    history_rows = (
        db.execute(
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == order.order_id)
            .order_by(OrderStatusHistory.transitioned_at, OrderStatusHistory.order_status_history_id)
        )
        .scalars()
        .all()
    )

    return OrderDetailResponse(
        order_number=order.order_number,
        status=order.status,
        currency_code=order.currency_code,
        subtotal_vnd=order.subtotal_vnd,
        shipping_fee_vnd=order.shipping_fee_vnd,
        total_vnd=order.total_vnd,
        receiver_name=order.receiver_name,
        receiver_phone=order.receiver_phone,
        shipping_address_text=order.shipping_address_text,
        created_at=order.created_at,
        paid_at=order.paid_at,
        completed_at=order.completed_at,
        items=[
            OrderItemResponse(
                product_name=i.product_name_snapshot,
                sku=i.sku_snapshot,
                size_code=i.size_code_snapshot,
                color_code=i.color_code_snapshot,
                unit_price_vnd=i.unit_price_vnd,
                quantity=i.quantity,
                line_total_vnd=i.line_total_vnd,
            )
            for i in item_rows
        ],
        payment=(
            PaymentResponse(
                payment_reference=payment.payment_reference,
                status=payment.status,
                amount_vnd=payment.amount_vnd,
                failure_code=payment.failure_code,
                attempted_at=payment.attempted_at,
            )
            if payment
            else None
        ),
        status_history=[
            StatusHistoryResponse(
                from_status=h.from_status,
                to_status=h.to_status,
                transition_source=h.transition_source,
                transitioned_at=h.transitioned_at,
            )
            for h in history_rows
        ],
    )


def complete_order(
    order_number: str,
    idempotency_key: str | None,
    transition_source: str = "internal_endpoint",
) -> dict:
    """TX-04: paid -> completed, idempotent, for trusted transition sources."""

    def _work(db: Session) -> dict:
        order = db.execute(
            select(Order).where(Order.order_number == order_number).with_for_update()
        ).scalar_one_or_none()
        if order is None:
            raise not_found("Không tìm thấy đơn hàng.")

        key = idempotency_key or f"complete:{order.order_id}"

        existing = db.execute(
            select(OrderStatusHistory).where(
                OrderStatusHistory.transition_idempotency_key == key
            )
        ).scalar_one_or_none()
        if existing is not None or order.status == "completed":
            return {"order_number": order.order_number, "status": order.status}

        if order.status != "paid":
            raise AppError(
                INVALID_STATE_TRANSITION,
                "Chỉ đơn đã thanh toán mới có thể hoàn tất.",
                status_code=409,
            )

        now = datetime.now(UTC)
        order.status = "completed"
        order.completed_at = now
        order.updated_at = now
        db.add(
            OrderStatusHistory(
                order_id=order.order_id,
                from_status="paid",
                to_status="completed",
                transition_source=transition_source,
                transition_idempotency_key=key,
                transitioned_at=now,
            )
        )
        db.flush()
        return {"order_number": order.order_number, "status": order.status}

    return run_in_transaction(_work)
