from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.pagination import decode_cursor, encode_cursor
from app.core.config import get_settings
from app.core.errors import (
    IDEMPOTENCY_CONFLICT,
    INTERNAL_ERROR,
    INVALID_STATE_TRANSITION,
    AppError,
    not_found,
)
from app.core.ids import uuid7
from app.db.uow import run_in_transaction
from app.models.catalog import Product, ProductVariant
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem, OrderStatusHistory, Payment, Refund
from app.models.promotion import Coupon, CouponRedemption
from app.models.review import ProductReview
from app.modules.orders.schemas import (
    OrderDetailResponse,
    OrderItemResponse,
    OrderItemReviewResponse,
    OrderListItem,
    OrderListPreviewItem,
    OrderListResponse,
    OrderTransitionResponse,
    PaymentResponse,
    RefundResponse,
    StatusHistoryResponse,
)


_ORDER_PREVIEW_LIMIT = 3


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


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
        cursor_time, cursor_id = decode_cursor(cursor)
        stmt = stmt.where(
            (Order.created_at < cursor_time)
            | ((Order.created_at == cursor_time) & (Order.order_id < cursor_id))
        )
    stmt = stmt.order_by(Order.created_at.desc(), Order.order_id.desc()).limit(page_size + 1)

    rows = db.execute(stmt).all()
    has_more = len(rows) > page_size
    rows = rows[:page_size]

    previews_by_order_id: dict[int, list[OrderListPreviewItem]] = {
        order.order_id: [] for order, _ in rows
    }
    if previews_by_order_id:
        ranked_items = (
            select(
                OrderItem.order_id.label("order_id"),
                OrderItem.order_item_id.label("order_item_id"),
                OrderItem.product_name_snapshot.label("product_name"),
                Product.image_url.label("image_url"),
                OrderItem.sku_snapshot.label("sku"),
                OrderItem.size_code_snapshot.label("size_code"),
                OrderItem.color_code_snapshot.label("color_code"),
                OrderItem.quantity.label("quantity"),
                OrderItem.line_total_vnd.label("line_total_vnd"),
                func.row_number()
                .over(
                    partition_by=OrderItem.order_id,
                    order_by=OrderItem.order_item_id,
                )
                .label("preview_rank"),
            )
            .join(ProductVariant, ProductVariant.variant_id == OrderItem.variant_id)
            .join(Product, Product.product_id == ProductVariant.product_id)
            .where(OrderItem.order_id.in_(previews_by_order_id))
            .subquery()
        )
        preview_rows = db.execute(
            select(ranked_items)
            .where(ranked_items.c.preview_rank <= _ORDER_PREVIEW_LIMIT)
            .order_by(ranked_items.c.order_id, ranked_items.c.order_item_id)
        ).all()
        for preview in preview_rows:
            previews_by_order_id[preview.order_id].append(
                OrderListPreviewItem(
                    product_name=preview.product_name,
                    image_url=preview.image_url,
                    sku=preview.sku,
                    size_code=preview.size_code,
                    color_code=preview.color_code,
                    quantity=preview.quantity,
                    line_total_vnd=preview.line_total_vnd,
                )
            )

    items = [
        OrderListItem(
            order_number=order.order_number,
            status=order.status,
            total_vnd=order.total_vnd,
            item_count=int(count),
            created_at=order.created_at,
            preview_items=previews_by_order_id[order.order_id],
        )
        for order, count in rows
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

    item_rows = db.execute(
        select(OrderItem, Product.image_url)
        .join(ProductVariant, ProductVariant.variant_id == OrderItem.variant_id)
        .join(Product, Product.product_id == ProductVariant.product_id)
        .where(OrderItem.order_id == order.order_id)
        .order_by(OrderItem.order_item_id)
    ).all()
    item_ids = [item.order_item_id for item, _ in item_rows]
    reviews = {}
    if item_ids:
        review_rows = db.execute(
            select(ProductReview).where(ProductReview.order_item_id.in_(item_ids))
        ).scalars().all()
        reviews = {review.order_item_id: review for review in review_rows}
    payment = db.execute(
        select(Payment).where(Payment.order_id == order.order_id)
    ).scalar_one_or_none()
    refund = (
        db.execute(select(Refund).where(Refund.payment_id == payment.payment_id)).scalar_one_or_none()
        if payment
        else None
    )
    history_rows = (
        db.execute(
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == order.order_id)
            .order_by(
                OrderStatusHistory.transitioned_at,
                OrderStatusHistory.order_status_history_id,
            )
        )
        .scalars()
        .all()
    )

    response_items: list[OrderItemResponse] = []
    for item, image_url in item_rows:
        review = reviews.get(item.order_item_id)
        response_items.append(
            OrderItemResponse(
                public_id=str(item.public_id),
                product_public_id=str(item.product_public_id_snapshot),
                image_url=image_url,
                product_name=item.product_name_snapshot,
                sku=item.sku_snapshot,
                size_code=item.size_code_snapshot,
                color_code=item.color_code_snapshot,
                unit_price_vnd=item.unit_price_vnd,
                quantity=item.quantity,
                line_total_vnd=item.line_total_vnd,
                review=(
                    OrderItemReviewResponse(
                        public_id=str(review.public_id),
                        rating=review.rating,
                        content=review.content,
                        status=review.status,
                        moderation_reason=review.moderation_reason,
                    )
                    if review
                    else None
                ),
            )
        )

    return OrderDetailResponse(
        order_number=order.order_number,
        status=order.status,
        currency_code=order.currency_code,
        subtotal_vnd=order.subtotal_vnd,
        coupon_code=order.coupon_code_snapshot,
        discount_amount_vnd=order.discount_amount_vnd,
        shipping_fee_vnd=order.shipping_fee_vnd,
        total_vnd=order.total_vnd,
        receiver_name=order.receiver_name,
        receiver_phone=order.receiver_phone,
        shipping_address_text=order.shipping_address_text,
        created_at=order.created_at,
        paid_at=order.paid_at,
        confirmed_at=order.confirmed_at,
        completed_at=order.completed_at,
        cancelled_at=order.cancelled_at,
        items=response_items,
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
        refund=(
            RefundResponse(
                public_id=str(refund.public_id),
                status=refund.status,
                amount_vnd=refund.amount_vnd,
                reason=refund.reason,
                created_at=refund.created_at,
                completed_at=refund.completed_at,
            )
            if refund
            else None
        ),
        status_history=[
            StatusHistoryResponse(
                from_status=history.from_status,
                to_status=history.to_status,
                transition_source=history.transition_source,
                reason=history.reason,
                transitioned_at=history.transitioned_at,
            )
            for history in history_rows
        ],
    )


def _transition_order(
    order_number: str,
    idempotency_key: str,
    from_status: str,
    to_status: str,
    transition_source: str,
    owner_customer_id: int | None = None,
) -> OrderTransitionResponse:
    def _work(db: Session) -> OrderTransitionResponse:
        order = db.execute(
            select(Order).where(Order.order_number == order_number).with_for_update()
        ).scalar_one_or_none()
        if order is None or (
            owner_customer_id is not None and order.customer_id != owner_customer_id
        ):
            raise not_found("Không tìm thấy đơn hàng.")
        existing = db.execute(
            select(OrderStatusHistory).where(
                OrderStatusHistory.transition_idempotency_key == idempotency_key
            )
        ).scalar_one_or_none()
        if existing is not None:
            if existing.order_id != order.order_id or existing.to_status != to_status:
                raise AppError(
                    IDEMPOTENCY_CONFLICT,
                    "Idempotency key đã được dùng cho request khác.",
                    status_code=409,
                )
            return OrderTransitionResponse(
                order_number=order.order_number,
                status=order.status,
            )
        if order.status == to_status:
            return OrderTransitionResponse(order_number=order.order_number, status=order.status)
        if order.status != from_status:
            raise AppError(
                INVALID_STATE_TRANSITION,
                f"Không thể chuyển đơn từ {order.status} sang {to_status}.",
                status_code=409,
            )

        now = _utc_now()
        order.status = to_status
        order.updated_at = now
        if to_status == "confirmed":
            order.confirmed_at = now
        elif to_status == "completed":
            order.completed_at = now
        db.add(
            OrderStatusHistory(
                order_id=order.order_id,
                from_status=from_status,
                to_status=to_status,
                transition_source=transition_source,
                transition_idempotency_key=idempotency_key,
                transitioned_at=now,
            )
        )
        db.flush()
        return OrderTransitionResponse(order_number=order.order_number, status=order.status)

    return run_in_transaction(_work)


def confirm_order(
    order_number: str,
    idempotency_key: str,
    transition_source: str = "admin",
) -> OrderTransitionResponse:
    return _transition_order(
        order_number,
        idempotency_key,
        "paid",
        "confirmed",
        transition_source,
    )


def complete_order(
    order_number: str,
    idempotency_key: str,
    transition_source: str,
    owner_customer_id: int,
) -> OrderTransitionResponse:
    return _transition_order(
        order_number,
        idempotency_key,
        "confirmed",
        "completed",
        transition_source,
        owner_customer_id,
    )


def cancel_order(
    order_number: str,
    actor_customer_id: int,
    owner_customer_id: int | None,
    reason: str,
    idempotency_key: str,
    transition_source: str,
) -> OrderTransitionResponse:
    def _work(db: Session) -> OrderTransitionResponse:
        order = db.execute(
            select(Order).where(Order.order_number == order_number).with_for_update()
        ).scalar_one_or_none()
        if order is None or (
            owner_customer_id is not None and order.customer_id != owner_customer_id
        ):
            raise not_found("Không tìm thấy đơn hàng.")

        existing_transition = db.execute(
            select(OrderStatusHistory).where(
                OrderStatusHistory.transition_idempotency_key == idempotency_key
            )
        ).scalar_one_or_none()
        if existing_transition is not None:
            if (
                existing_transition.order_id != order.order_id
                or existing_transition.to_status != "cancelled"
            ):
                raise AppError(
                    IDEMPOTENCY_CONFLICT,
                    "Idempotency key đã được dùng cho request khác.",
                    status_code=409,
                )
            payment = db.execute(
                select(Payment).where(Payment.order_id == order.order_id)
            ).scalar_one()
            refund = db.execute(
                select(Refund).where(Refund.payment_id == payment.payment_id)
            ).scalar_one()
            return OrderTransitionResponse(
                order_number=order.order_number,
                status=order.status,
                refunded_amount_vnd=refund.amount_vnd,
            )
        if order.status == "cancelled":
            payment = db.execute(
                select(Payment).where(Payment.order_id == order.order_id)
            ).scalar_one()
            refund = db.execute(
                select(Refund).where(Refund.payment_id == payment.payment_id)
            ).scalar_one()
            return OrderTransitionResponse(
                order_number=order.order_number,
                status=order.status,
                refunded_amount_vnd=refund.amount_vnd,
            )
        if order.status != "paid":
            raise AppError(
                INVALID_STATE_TRANSITION,
                "Chỉ đơn đã thanh toán và chưa được admin xác nhận mới có thể hủy.",
                status_code=409,
            )

        payment = db.execute(
            select(Payment)
            .where(Payment.order_id == order.order_id)
            .with_for_update()
        ).scalar_one_or_none()
        if payment is None or payment.status != "succeeded":
            raise AppError(
                INVALID_STATE_TRANSITION,
                "Đơn hàng không có thanh toán thành công để hoàn tiền.",
                status_code=409,
            )
        existing_refund = db.execute(
            select(Refund).where(Refund.payment_id == payment.payment_id).with_for_update()
        ).scalar_one_or_none()
        if existing_refund is not None:
            raise AppError(
                INTERNAL_ERROR,
                "Đơn có refund nhưng trạng thái chưa được hủy.",
                status_code=500,
            )

        redemption = db.execute(
            select(CouponRedemption)
            .where(CouponRedemption.order_id == order.order_id)
            .with_for_update()
        ).scalar_one_or_none()
        coupon = None
        if redemption is not None:
            coupon = db.execute(
                select(Coupon)
                .where(Coupon.coupon_id == redemption.coupon_id)
                .with_for_update()
            ).scalar_one()

        item_rows = db.execute(
            select(OrderItem)
            .where(OrderItem.order_id == order.order_id)
            .order_by(OrderItem.variant_id)
        ).scalars().all()
        variant_ids = [item.variant_id for item in item_rows]
        inventory_rows = (
            db.execute(
                select(Inventory)
                .where(Inventory.variant_id.in_(variant_ids))
                .order_by(Inventory.variant_id)
                .with_for_update()
            )
            .scalars()
            .all()
        )
        inventory = {row.variant_id: row for row in inventory_rows}
        if len(inventory) != len(variant_ids):
            raise AppError(INTERNAL_ERROR, "Thiếu dữ liệu tồn kho của đơn hàng.", status_code=500)

        now = _utc_now()
        for item in item_rows:
            inventory_row = inventory[item.variant_id]
            restored_on_hand = inventory_row.on_hand + item.quantity
            if restored_on_hand > inventory_row.opening_on_hand:
                raise AppError(
                    INTERNAL_ERROR,
                    "Hoàn tồn kho vượt số lượng mở đầu.",
                    status_code=500,
                )
            inventory_row.on_hand = restored_on_hand
            inventory_row.version += 1
            inventory_row.updated_at = now

        if redemption is not None and coupon is not None and redemption.status == "redeemed":
            if coupon.used_count <= 0:
                raise AppError(INTERNAL_ERROR, "Bộ đếm coupon không hợp lệ.", status_code=500)
            redemption.status = "released"
            redemption.released_at = now
            redemption.updated_at = now
            coupon.used_count -= 1
            coupon.updated_at = now

        db.add(
            Refund(
                public_id=uuid7(),
                payment_id=payment.payment_id,
                refund_idempotency_key=idempotency_key,
                status="succeeded",
                currency_code="VND",
                amount_vnd=payment.amount_vnd,
                reason=reason,
                requested_by_customer_id=actor_customer_id,
                created_at=now,
                completed_at=now,
            )
        )
        order.status = "cancelled"
        order.cancelled_at = now
        order.updated_at = now
        db.add(
            OrderStatusHistory(
                order_id=order.order_id,
                from_status="paid",
                to_status="cancelled",
                transition_source=transition_source,
                reason=reason,
                transition_idempotency_key=idempotency_key,
                transitioned_at=now,
            )
        )
        db.flush()
        return OrderTransitionResponse(
            order_number=order.order_number,
            status=order.status,
            refunded_amount_vnd=payment.amount_vnd,
        )

    return run_in_transaction(_work)
