from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.pagination import decode_cursor, encode_cursor
from app.core.config import get_settings
from app.core.errors import (
    IDEMPOTENCY_CONFLICT,
    INTERNAL_ERROR,
    INVALID_STATE_TRANSITION,
    VALIDATION_ERROR,
    AppError,
    not_found,
)
from app.core.ids import uuid7
from app.db.uow import run_in_transaction
from app.models.catalog import Product, ProductVariant
from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.logistics import DeliveryStaff, Shipment
from app.models.multicity import StoreInventory
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
from app.modules.logistics.schemas import ShipmentResponse
from app.models.returns import ReturnItem, ReturnRequest
from app.modules.orders.schemas import OrderActiveReturnResponse


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
    active_return = (
        db.execute(
            select(ReturnRequest)
            .where(
                ReturnRequest.order_id == order.order_id,
                ReturnRequest.status.in_(("pending_review", "approved", "goods_received")),
            )
            .order_by(ReturnRequest.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
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
                order_item_id=item.order_item_id,
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
        shipment=(
            ShipmentResponse(
                shipment_id=shipment_row[0].shipment_id,
                shipment_code=shipment_row[0].shipment_code,
                order_id=shipment_row[0].order_id,
                order_number=order.order_number,
                delivery_staff_id=shipment_row[0].delivery_staff_id,
                delivery_staff_name=shipment_row[1].full_name if shipment_row[1] else None,
                delivery_staff_phone=shipment_row[1].phone if shipment_row[1] else None,
                vehicle_plate=shipment_row[1].vehicle_plate if shipment_row[1] else None,
                status=shipment_row[0].status,
                attempt_count=shipment_row[0].attempt_count,
                dispatched_at=shipment_row[0].dispatched_at,
                delivered_at=shipment_row[0].delivered_at,
                failed_at=shipment_row[0].failed_at,
                cod_amount_vnd=shipment_row[0].cod_amount_vnd,
                cod_collected_vnd=shipment_row[0].cod_collected_vnd,
                failure_reason=shipment_row[0].failure_reason,
                notes=shipment_row[0].notes,
                created_at=shipment_row[0].created_at,
            )
            if (
                shipment_row := db.execute(
                    select(Shipment, DeliveryStaff)
                    .outerjoin(DeliveryStaff, DeliveryStaff.staff_id == Shipment.delivery_staff_id)
                    .where(Shipment.order_id == order.order_id)
                    .order_by(Shipment.shipment_id.desc())
                ).first()
            )
            else None
        ),
        active_return=(
            OrderActiveReturnResponse(
                return_code=active_return.return_code,
                action_type=active_return.action_type,
                status=active_return.status,
                total_refund_amount_vnd=sum(ri.refund_amount_vnd for ri in active_return.items),
                created_at=active_return.created_at,
            )
            if active_return
            else None
        ),
    )


def _transition_order(
    order_number: str,
    idempotency_key: str,
    from_status: str | tuple[str, ...],
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
        allowed_from = (from_status,) if isinstance(from_status, str) else from_status
        if order.status not in allowed_from:
            raise AppError(
                INVALID_STATE_TRANSITION,
                f"Không thể chuyển đơn từ {order.status} sang {to_status}.",
                status_code=409,
            )

        now = _utc_now()
        previous_status = order.status
        order.status = to_status
        order.updated_at = now
        if to_status == "confirmed":
            order.confirmed_at = now
        elif to_status == "completed":
            order.completed_at = now
        db.add(
            OrderStatusHistory(
                order_id=order.order_id,
                from_status=previous_status,
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
        ("delivered", "confirmed"),
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

        if order.store_id is not None:
            store_inv_rows = (
                db.execute(
                    select(StoreInventory)
                    .where(
                        StoreInventory.store_id == order.store_id,
                        StoreInventory.variant_id.in_(variant_ids),
                    )
                    .order_by(StoreInventory.variant_id)
                    .with_for_update()
                )
                .scalars()
                .all()
            )
            store_inv_map = {row.variant_id: row for row in store_inv_rows}
            for item in item_rows:
                si = store_inv_map.get(item.variant_id)
                if si is not None:
                    si.on_hand = si.on_hand + item.quantity

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


def _make_transition_key(order_number: str, action: str, idempotency_key: str | None) -> str:
    if idempotency_key and idempotency_key.strip():
        return f"{idempotency_key.strip()[:50]}:{action[:13]}"
    return f"{action[:10]}:{order_number[:20]}:{uuid7().hex[:30]}"[:64]


def dispatch_order(
    db: Session,
    order_number: str,
    staff_id: int,
    notes: str | None = None,
    idempotency_key: str | None = None,
) -> OrderTransitionResponse:
    order = db.execute(
        select(Order).where(Order.order_number == order_number).with_for_update()
    ).scalar_one_or_none()
    if order is None:
        raise not_found("Không tìm thấy đơn hàng.")

    transition_key = _make_transition_key(order_number, "disp", idempotency_key)
    if idempotency_key:
        existing_history = db.execute(
            select(OrderStatusHistory).where(
                OrderStatusHistory.transition_idempotency_key == transition_key
            )
        ).scalar_one_or_none()
        if existing_history is not None:
            if existing_history.order_id != order.order_id or existing_history.to_status != "shipping":
                raise AppError(
                    IDEMPOTENCY_CONFLICT,
                    "Idempotency key đã được dùng cho request khác.",
                    status_code=409,
                )
            return OrderTransitionResponse(order_number=order.order_number, status=order.status)

    if order.status == "shipping":
        raise AppError(
            INVALID_STATE_TRANSITION,
            "Đơn hàng đang trong trạng thái giao hàng.",
            status_code=409,
        )
    if order.status not in ("paid", "confirmed"):
        raise AppError(
            INVALID_STATE_TRANSITION,
            f"Không thể xuất kho đơn hàng ở trạng thái {order.status}.",
            status_code=409,
        )

    staff = db.execute(
        select(DeliveryStaff).where(DeliveryStaff.staff_id == staff_id)
    ).scalar_one_or_none()
    if staff is None or not staff.is_active:
        raise AppError(
            VALIDATION_ERROR,
            "Nhân viên giao hàng không tồn tại hoặc đã ngừng hoạt động.",
            status_code=400,
        )

    now = _utc_now()
    cod_amount = order.total_vnd if order.payment_method == "cod" else 0
    shipment = Shipment(
        public_id=uuid7(),
        shipment_code=f"SHP-{order.order_number}",
        order_id=order.order_id,
        delivery_staff_id=staff_id,
        status="in_transit",
        attempt_count=1,
        cod_amount_vnd=cod_amount,
        cod_collected_vnd=0,
        dispatched_at=now,
        notes=notes,
        created_at=now,
        updated_at=now,
    )
    db.add(shipment)

    from_status = order.status
    order.status = "shipping"
    order.updated_at = now

    db.add(
        OrderStatusHistory(
            order_id=order.order_id,
            from_status=from_status,
            to_status="shipping",
            transition_source="admin_dispatch",
            transition_idempotency_key=transition_key,
            transitioned_at=now,
        )
    )
    db.flush()
    return OrderTransitionResponse(order_number=order.order_number, status=order.status)


def deliver_order(
    db: Session,
    order_number: str,
    idempotency_key: str | None = None,
) -> OrderTransitionResponse:
    order = db.execute(
        select(Order).where(Order.order_number == order_number).with_for_update()
    ).scalar_one_or_none()
    if order is None:
        raise not_found("Không tìm thấy đơn hàng.")

    transition_key = _make_transition_key(order_number, "deliv", idempotency_key)
    if idempotency_key:
        existing_history = db.execute(
            select(OrderStatusHistory).where(
                OrderStatusHistory.transition_idempotency_key == transition_key
            )
        ).scalar_one_or_none()
        if existing_history is not None:
            if existing_history.order_id != order.order_id or existing_history.to_status != "delivered":
                raise AppError(
                    IDEMPOTENCY_CONFLICT,
                    "Idempotency key đã được dùng cho request khác.",
                    status_code=409,
                )
            return OrderTransitionResponse(order_number=order.order_number, status=order.status)

    if order.status == "delivered":
        return OrderTransitionResponse(order_number=order.order_number, status=order.status)
    if order.status != "shipping":
        raise AppError(
            INVALID_STATE_TRANSITION,
            f"Không thể giao đơn hàng ở trạng thái {order.status}.",
            status_code=409,
        )

    now = _utc_now()
    shipment = (
        db.execute(
            select(Shipment)
            .where(Shipment.order_id == order.order_id)
            .order_by(Shipment.shipment_id.desc())
            .with_for_update()
        )
        .scalars()
        .first()
    )
    if shipment:
        shipment.status = "delivered"
        shipment.delivered_at = now
        shipment.updated_at = now
        if order.payment_method == "cod":
            shipment.cod_collected_vnd = shipment.cod_amount_vnd

    if order.payment_method == "cod":
        order.paid_at = now
        payment = db.execute(
            select(Payment).where(Payment.order_id == order.order_id).with_for_update()
        ).scalar_one_or_none()
        if payment:
            payment.status = "succeeded"

    order.status = "delivered"
    order.updated_at = now

    db.add(
        OrderStatusHistory(
            order_id=order.order_id,
            from_status="shipping",
            to_status="delivered",
            transition_source="admin_deliver",
            transition_idempotency_key=transition_key,
            transitioned_at=now,
        )
    )
    db.flush()
    return OrderTransitionResponse(order_number=order.order_number, status=order.status)


def fail_delivery_order(
    db: Session,
    order_number: str,
    reason: str,
    idempotency_key: str | None = None,
) -> OrderTransitionResponse:
    cleaned_reason = reason.strip() if reason else ""
    if not cleaned_reason:
        raise AppError(VALIDATION_ERROR, "Lý do thất bại không được để trống.", status_code=400)

    order = db.execute(
        select(Order).where(Order.order_number == order_number).with_for_update()
    ).scalar_one_or_none()
    if order is None:
        raise not_found("Không tìm thấy đơn hàng.")

    transition_key = _make_transition_key(order_number, "fail", idempotency_key)
    if idempotency_key:
        existing_history = db.execute(
            select(OrderStatusHistory).where(
                OrderStatusHistory.transition_idempotency_key == transition_key
            )
        ).scalar_one_or_none()
        if existing_history is not None:
            if existing_history.order_id != order.order_id or existing_history.to_status != "failed_delivery":
                raise AppError(
                    IDEMPOTENCY_CONFLICT,
                    "Idempotency key đã được dùng cho request khác.",
                    status_code=409,
                )
            return OrderTransitionResponse(order_number=order.order_number, status=order.status)

    if order.status == "failed_delivery":
        return OrderTransitionResponse(order_number=order.order_number, status=order.status)
    if order.status != "shipping":
        raise AppError(
            INVALID_STATE_TRANSITION,
            f"Không thể báo giao thất bại cho đơn hàng ở trạng thái {order.status}.",
            status_code=409,
        )

    now = _utc_now()
    shipment = (
        db.execute(
            select(Shipment)
            .where(Shipment.order_id == order.order_id)
            .order_by(Shipment.shipment_id.desc())
            .with_for_update()
        )
        .scalars()
        .first()
    )
    if shipment:
        shipment.status = "failed"
        shipment.failed_at = now
        shipment.failure_reason = cleaned_reason[:255]
        shipment.attempt_count += 1
        shipment.updated_at = now

    item_rows = db.execute(
        select(OrderItem).where(OrderItem.order_id == order.order_id).order_by(OrderItem.variant_id)
    ).scalars().all()
    variant_ids = [item.variant_id for item in item_rows]
    if variant_ids:
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
        inv_map = {row.variant_id: row for row in inventory_rows}
        for item in item_rows:
            inv = inv_map.get(item.variant_id)
            if inv:
                inv.on_hand += item.quantity
                inv.version += 1
                inv.updated_at = now

        if order.store_id is not None:
            store_inv_rows = (
                db.execute(
                    select(StoreInventory)
                    .where(
                        StoreInventory.store_id == order.store_id,
                        StoreInventory.variant_id.in_(variant_ids),
                    )
                    .order_by(StoreInventory.variant_id)
                    .with_for_update()
                )
                .scalars()
                .all()
            )
            si_map = {row.variant_id: row for row in store_inv_rows}
            for item in item_rows:
                si = si_map.get(item.variant_id)
                if si:
                    si.on_hand += item.quantity

    customer = db.execute(
        select(Customer).where(Customer.customer_id == order.customer_id).with_for_update()
    ).scalar_one()
    customer.boom_count += 1
    if customer.boom_count >= 3:
        customer.is_cod_blocked = True
    customer.updated_at = now

    order.status = "failed_delivery"
    order.updated_at = now

    db.add(
        OrderStatusHistory(
            order_id=order.order_id,
            from_status="shipping",
            to_status="failed_delivery",
            transition_source="admin_failed_delivery",
            reason=cleaned_reason,
            transition_idempotency_key=transition_key,
            transitioned_at=now,
        )
    )
    db.flush()
    return OrderTransitionResponse(order_number=order.order_number, status=order.status)


def complete_admin_order(
    db: Session,
    order_number: str,
    idempotency_key: str | None = None,
) -> OrderTransitionResponse:
    order = db.execute(
        select(Order).where(Order.order_number == order_number).with_for_update()
    ).scalar_one_or_none()
    if order is None:
        raise not_found("Không tìm thấy đơn hàng.")

    transition_key = _make_transition_key(order_number, "comp", idempotency_key)
    if idempotency_key:
        existing_history = db.execute(
            select(OrderStatusHistory).where(
                OrderStatusHistory.transition_idempotency_key == transition_key
            )
        ).scalar_one_or_none()
        if existing_history is not None:
            if existing_history.order_id != order.order_id or existing_history.to_status != "completed":
                raise AppError(
                    IDEMPOTENCY_CONFLICT,
                    "Idempotency key đã được dùng cho request khác.",
                    status_code=409,
                )
            return OrderTransitionResponse(order_number=order.order_number, status=order.status)

    if order.status == "completed":
        return OrderTransitionResponse(order_number=order.order_number, status=order.status)
    if order.status != "delivered":
        raise AppError(
            INVALID_STATE_TRANSITION,
            f"Không thể hoàn tất đơn hàng ở trạng thái {order.status}.",
            status_code=409,
        )

    now = _utc_now()
    order.status = "completed"
    order.completed_at = now
    order.updated_at = now

    db.add(
        OrderStatusHistory(
            order_id=order.order_id,
            from_status="delivered",
            to_status="completed",
            transition_source="admin_complete",
            transition_idempotency_key=transition_key,
            transitioned_at=now,
        )
    )
    db.flush()
    return OrderTransitionResponse(order_number=order.order_number, status=order.status)

