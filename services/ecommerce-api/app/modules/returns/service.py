import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, VALIDATION_ERROR, INVALID_STATE_TRANSITION, not_found
from app.models.customer import CustomerCredential
from app.models.inventory import Inventory
from app.models.inventory_tx import InventoryTransaction
from app.models.order import Order, OrderItem, OrderStatusHistory, Payment, Refund
from app.models.returns import ReturnItem, ReturnRequest
from app.modules.returns.schemas import (
    AdminInspectAndResolvePayload,
    AdminReturnListResponse,
    CreateReturnRequestPayload,
    ReturnItemDetailResponse,
    ReturnRequestDetailResponse,
    ReturnRequestListResponse,
    ReturnRequestSummaryResponse,
)

RETURN_WINDOW_DAYS = 7
ACTIVE_RETURN_STATUSES = ("pending_review", "approved", "goods_received")


def _bank_metadata(image_urls_json: dict | list | None) -> tuple[dict | None, list[str]]:
    """Extract (bank_info, image_urls) from the JSON metadata stored on ReturnRequest."""
    if not isinstance(image_urls_json, dict):
        return None, list(image_urls_json or [])
    bank_info = {
        key: image_urls_json[key]
        for key in ("bank_name", "bank_account_number", "bank_account_holder")
        if key in image_urls_json
    }
    return (bank_info or None), list(image_urls_json.get("images") or [])


def _build_detail_response(
    db: Session, order_number: str, return_req: ReturnRequest
) -> ReturnRequestDetailResponse:
    items = db.execute(
        select(OrderItem).where(OrderItem.order_id == return_req.order_id)
    ).scalars().all()
    items_by_id = {item.order_item_id: item for item in items}
    bank_info, image_urls = _bank_metadata(return_req.image_urls)
    return_items = [
        ReturnItemDetailResponse(
            return_item_id=ri.return_item_id,
            order_item_id=ri.order_item_id,
            variant_id=ri.variant_id,
            product_name=items_by_id[ri.order_item_id].product_name_snapshot,
            variant_title=(
                f"{items_by_id[ri.order_item_id].size_code_snapshot} / "
                f"{items_by_id[ri.order_item_id].color_code_snapshot}"
            ),
            sku=items_by_id[ri.order_item_id].sku_snapshot,
            quantity=ri.quantity,
            refund_amount_vnd=ri.refund_amount_vnd,
            inspection_status=ri.inspection_status,
        )
        for ri in return_req.items
    ]
    order = db.execute(
        select(Order).where(Order.order_id == return_req.order_id)
    ).scalar_one_or_none()
    cred = db.execute(
        select(CustomerCredential.email_normalized).where(CustomerCredential.customer_id == return_req.customer_id)
    ).scalar_one_or_none()

    return ReturnRequestDetailResponse(
        return_id=return_req.return_id,
        return_code=return_req.return_code,
        order_id=return_req.order_id,
        order_number=order_number,
        customer_name=order.receiver_name if order else None,
        customer_phone=order.receiver_phone if order else None,
        customer_email=cred if cred else None,
        action_type=return_req.action_type,
        status=return_req.status,
        customer_reason=return_req.customer_reason,
        admin_note=return_req.admin_note,
        image_urls=image_urls,
        bank_info=bank_info,
        total_refund_amount_vnd=sum(ri.refund_amount_vnd for ri in return_req.items),
        created_at=return_req.created_at,
        reviewed_at=return_req.reviewed_at,
        resolved_at=return_req.resolved_at,
        items=return_items,
    )


def _compute_prorated_unit_price(unit_price_vnd: int, order: Order) -> int:
    if order.subtotal_vnd > 0 and order.discount_amount_vnd > 0:
        return round(unit_price_vnd * (1 - order.discount_amount_vnd / order.subtotal_vnd))
    return unit_price_vnd


def _generate_return_code(now: datetime, idempotency_key: str, order_number: str) -> str:
    digest = hashlib.sha256(f"{idempotency_key}:{order_number}".encode()).hexdigest()[:6].upper()
    return f"RT-{now.strftime('%Y%m%d')}-{digest}"


def _lock_order(db: Session, order_number: str, customer_id: int) -> Order:
    order = db.execute(
        select(Order).where(Order.order_number == order_number).with_for_update()
    ).scalar_one_or_none()
    if order is None or order.customer_id != customer_id:
        raise not_found("Không tìm thấy đơn hàng.")
    return order


def create_customer_return_request(
    db: Session,
    customer_id: int,
    order_number: str,
    payload: CreateReturnRequestPayload,
    idempotency_key: str,
) -> ReturnRequestDetailResponse:
    now = datetime.now(UTC).replace(tzinfo=None)
    order = _lock_order(db, order_number, customer_id)

    if order.status not in ("delivered", "completed"):
        raise AppError(
            INVALID_STATE_TRANSITION,
            "Chỉ đơn hàng đã giao thành công hoặc đã hoàn tất mới được yêu cầu đổi trả.",
            status_code=409,
        )

    window_start = order.completed_at or order.updated_at
    if window_start is None or (now - window_start) > timedelta(days=RETURN_WINDOW_DAYS):
        raise AppError(
            VALIDATION_ERROR,
            f"Đã quá thời hạn {RETURN_WINDOW_DAYS} ngày để yêu cầu đổi trả cho đơn hàng này.",
            status_code=400,
        )

    existing = db.execute(
        select(ReturnRequest).where(ReturnRequest.order_id == order.order_id)
    ).scalars().all()
    for req in existing:
        metadata = req.image_urls if isinstance(req.image_urls, dict) else {}
        if metadata.get("idempotency_key") == idempotency_key:
            return _build_detail_response(db, order_number, req)
        if req.status in ACTIVE_RETURN_STATUSES:
            raise AppError(
                INVALID_STATE_TRANSITION,
                "Đơn hàng đang có một yêu cầu đổi trả đang xử lý.",
                status_code=409,
            )

    order_items = {
        item.order_item_id: item
        for item in db.execute(
            select(OrderItem).where(OrderItem.order_id == order.order_id)
        ).scalars().all()
    }
    validated: list[tuple[OrderItem, int, int]] = []
    for entry in payload.items:
        item = order_items.get(entry.order_item_id)
        if item is None:
            raise AppError(
                VALIDATION_ERROR,
                f"Sản phẩm {entry.order_item_id} không thuộc đơn hàng này.",
                status_code=400,
            )
        already_returned_qty = db.execute(
            select(func.coalesce(func.sum(ReturnItem.quantity), 0))
            .join(ReturnRequest, ReturnRequest.return_id == ReturnItem.return_id)
            .where(
                ReturnItem.order_item_id == item.order_item_id,
                ReturnRequest.status.not_in(("cancelled", "rejected")),
            )
        ).scalar_one()
        remaining_qty = item.quantity - already_returned_qty
        if entry.quantity > remaining_qty:
            raise AppError(
                VALIDATION_ERROR,
                f"Số lượng trả cho sản phẩm {item.sku_snapshot or item.order_item_id} vượt quá số lượng còn lại có thể đổi trả ({remaining_qty}).",
                status_code=400,
            )
        prorated_price = _compute_prorated_unit_price(item.unit_price_vnd, order)
        refund_amount = prorated_price * entry.quantity
        validated.append((item, entry.quantity, refund_amount))

    return_req = ReturnRequest(
        public_id=uuid4(),
        return_code=_generate_return_code(now, idempotency_key, order_number),
        order_id=order.order_id,
        customer_id=customer_id,
        action_type="refund",
        status="pending_review",
        customer_reason=payload.customer_reason,
        image_urls={
            "bank_name": payload.bank_name,
            "bank_account_number": payload.bank_account_number,
            "bank_account_holder": payload.bank_account_holder,
            "images": payload.image_urls,
            "idempotency_key": idempotency_key,
        },
    )
    db.add(return_req)
    db.flush()
    for item, quantity, refund_amount in validated:
        db.add(
            ReturnItem(
                public_id=uuid4(),
                return_id=return_req.return_id,
                order_item_id=item.order_item_id,
                variant_id=item.variant_id,
                quantity=quantity,
                refund_amount_vnd=refund_amount,
                inspection_status="pending",
            )
        )
    db.commit()
    db.refresh(return_req)
    return _build_detail_response(db, order_number, return_req)



def list_customer_returns(db: Session, customer_id: int) -> ReturnRequestListResponse:
    requests = db.execute(
        select(ReturnRequest)
        .where(ReturnRequest.customer_id == customer_id)
        .order_by(ReturnRequest.created_at.desc(), ReturnRequest.return_id.desc())
    ).scalars().all()
    order_numbers = dict(
        db.execute(
            select(Order.order_id, Order.order_number).where(
                Order.order_id.in_([req.order_id for req in requests])
            )
        ).all()
    ) if requests else {}
    summaries = []
    for req in requests:
        summaries.append(
            ReturnRequestSummaryResponse(
                return_id=req.return_id,
                return_code=req.return_code,
                order_number=order_numbers.get(req.order_id, ""),
                action_type=req.action_type,
                status=req.status,
                total_items_count=len(req.items),
                total_refund_amount_vnd=sum(ri.refund_amount_vnd for ri in req.items),
                created_at=req.created_at,
            )
        )
    return ReturnRequestListResponse(items=summaries, total=len(summaries))


def get_customer_return(
    db: Session, customer_id: int, return_code: str
) -> ReturnRequestDetailResponse:
    return_req = db.execute(
        select(ReturnRequest).where(ReturnRequest.return_code == return_code)
    ).scalar_one_or_none()
    if return_req is None or return_req.customer_id != customer_id:
        raise not_found("Không tìm thấy yêu cầu đổi trả.")
    order_number = db.execute(
        select(Order.order_number).where(Order.order_id == return_req.order_id)
    ).scalar_one()
    return _build_detail_response(db, order_number, return_req)


def cancel_customer_return_request(
    db: Session, customer_id: int, return_code: str
) -> ReturnRequestDetailResponse:
    return_req = db.execute(
        select(ReturnRequest).where(ReturnRequest.return_code == return_code).with_for_update()
    ).scalar_one_or_none()
    if return_req is None or return_req.customer_id != customer_id:
        raise not_found("Không tìm thấy yêu cầu đổi trả.")
    if return_req.status != "pending_review":
        raise AppError(
            INVALID_STATE_TRANSITION,
            "Chỉ yêu cầu ở trạng thái chờ duyệt mới có thể hủy.",
            status_code=409,
        )
    return_req.status = "cancelled"
    return_req.resolved_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    order_number = db.execute(
        select(Order.order_number).where(Order.order_id == return_req.order_id)
    ).scalar_one()
    return _build_detail_response(db, order_number, return_req)



def _get_admin_return(
    db: Session, return_code: str, for_update: bool = False
) -> tuple[ReturnRequest, str]:
    stmt = select(ReturnRequest).where(ReturnRequest.return_code == return_code)
    if for_update:
        stmt = stmt.with_for_update()
    return_req = db.execute(stmt).scalar_one_or_none()
    if return_req is None:
        raise not_found("Không tìm thấy yêu cầu đổi trả.")
    order_number = db.execute(
        select(Order.order_number).where(Order.order_id == return_req.order_id)
    ).scalar_one()
    return return_req, order_number


def list_admin_returns(
    db: Session,
    status: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> AdminReturnListResponse:
    query = (
        select(ReturnRequest, Order.order_number)
        .join(Order, Order.order_id == ReturnRequest.order_id)
    )
    if status:
        query = query.where(ReturnRequest.status == status)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                ReturnRequest.return_code.ilike(pattern),
                Order.order_number.ilike(pattern),
                Order.receiver_phone.ilike(pattern),
                Order.receiver_name.ilike(pattern),
            )
        )
    rows = db.execute(
        query.order_by(ReturnRequest.created_at.desc(), ReturnRequest.return_id.desc())
    ).all()
    items = [
        _build_detail_response(db, order_number, return_req)
        for return_req, order_number in rows[offset : offset + limit]
    ]
    return AdminReturnListResponse(items=items, total=len(rows))


def get_admin_return_detail(db: Session, return_code: str) -> ReturnRequestDetailResponse:
    return_req, order_number = _get_admin_return(db, return_code)
    return _build_detail_response(db, order_number, return_req)


def review_admin_return(
    db: Session, return_code: str, action: str, admin_note: str | None
) -> ReturnRequestDetailResponse:
    return_req, order_number = _get_admin_return(db, return_code, for_update=True)
    if return_req.status != "pending_review":
        raise AppError(
            INVALID_STATE_TRANSITION,
            "Chỉ yêu cầu ở trạng thái chờ duyệt mới có thể xét duyệt.",
            status_code=409,
        )
    return_req.status = action
    return_req.reviewed_at = datetime.now(UTC).replace(tzinfo=None)
    if admin_note:
        return_req.admin_note = admin_note
    db.commit()
    db.refresh(return_req)
    return _build_detail_response(db, order_number, return_req)


def receive_admin_return(db: Session, return_code: str) -> ReturnRequestDetailResponse:
    return_req, order_number = _get_admin_return(db, return_code, for_update=True)
    if return_req.status != "approved":
        raise AppError(
            INVALID_STATE_TRANSITION,
            "Chỉ yêu cầu đã duyệt mới có thể xác nhận nhận hàng.",
            status_code=409,
        )
    return_req.status = "goods_received"
    db.commit()
    db.refresh(return_req)
    return _build_detail_response(db, order_number, return_req)



def inspect_and_resolve_admin_return(
    db: Session,
    return_code: str,
    payload: AdminInspectAndResolvePayload,
    idempotency_key: str,
) -> ReturnRequestDetailResponse:
    now = datetime.now(UTC).replace(tzinfo=None)
    return_req, order_number = _get_admin_return(db, return_code, for_update=True)

    if return_req.status == "completed":
        # Idempotent replay: resolution already finalized for this request.
        return _build_detail_response(db, order_number, return_req)
    if return_req.status != "goods_received":
        raise AppError(
            INVALID_STATE_TRANSITION,
            "Chỉ yêu cầu đã nhận hàng về kho mới có thể kiểm định và hoàn tất.",
            status_code=409,
        )

    items_by_id = {ri.return_item_id: ri for ri in return_req.items}
    for entry in payload.items:
        item = items_by_id.get(entry.return_item_id)
        if item is None:
            raise AppError(
                VALIDATION_ERROR,
                f"Sản phẩm kiểm định {entry.return_item_id} không thuộc yêu cầu đổi trả này.",
                status_code=400,
            )
        item.inspection_status = entry.inspection_status

    # Restock passed items with pessimistic row locking.
    for entry in payload.items:
        if entry.inspection_status != "passed":
            continue
        item = items_by_id[entry.return_item_id]
        inv = db.execute(
            select(Inventory).where(Inventory.variant_id == item.variant_id).with_for_update()
        ).scalar_one_or_none()
        if inv is not None:
            inv.on_hand = inv.on_hand + item.quantity
            if inv.on_hand > inv.opening_on_hand:
                inv.opening_on_hand = inv.on_hand
        db.add(
            InventoryTransaction(
                public_id=uuid4(),
                variant_id=item.variant_id,
                location_type="central_warehouse",
                movement_type="return_customer",
                quantity_delta=item.quantity,
                reference_code=return_req.return_code,
                notes=f"Hàng hoàn từ {return_req.return_code}",
            )
        )

    refund_amount = sum(
        ri.refund_amount_vnd for ri in return_req.items if ri.inspection_status == "passed"
    )
    order = db.execute(
        select(Order).where(Order.order_id == return_req.order_id).with_for_update()
    ).scalar_one()
    payment = db.execute(
        select(Payment).where(Payment.order_id == order.order_id)
    ).scalar_one_or_none()

    if refund_amount > 0 and payment is not None:
        refund = db.execute(
            select(Refund).where(Refund.payment_id == payment.payment_id).with_for_update()
        ).scalar_one_or_none()
        new_key = f"ref:{idempotency_key[:58]}"
        if refund is None:
            reason = f"Hoàn tiền yêu cầu {return_req.return_code}"[:500]
            db.add(
                Refund(
                    public_id=uuid4(),
                    payment_id=payment.payment_id,
                    refund_idempotency_key=new_key,
                    status="succeeded",
                    amount_vnd=min(payment.amount_vnd, refund_amount),
                    reason=reason,
                    requested_by_customer_id=return_req.customer_id,
                    completed_at=now,
                )
            )
        else:
            # One refund per payment: accumulate subsequent partial returns.
            refund.amount_vnd = min(payment.amount_vnd, refund.amount_vnd + refund_amount)
            refund.refund_idempotency_key = new_key
            accumulated_reason = f"{refund.reason}; {return_req.return_code}".strip("; ")
            refund.reason = accumulated_reason[:500]
            refund.completed_at = now

    return_req.status = "completed"
    return_req.resolved_at = now
    if payload.admin_note:
        return_req.admin_note = payload.admin_note

    # Full-return detection: every ordered unit has been returned across
    # all completed return requests for this order.
    db.flush()  # ensure status/inspection mutations are visible to aggregate queries
    ordered_total = db.execute(
        select(func.coalesce(func.sum(OrderItem.quantity), 0)).where(
            OrderItem.order_id == order.order_id
        )
    ).scalar_one()
    returned_total = db.execute(
        select(func.coalesce(func.sum(ReturnItem.quantity), 0))
        .join(ReturnRequest, ReturnRequest.return_id == ReturnItem.return_id)
        .where(
            ReturnRequest.order_id == order.order_id,
            ReturnRequest.status == "completed",
            ReturnItem.inspection_status == "passed",
        )
    ).scalar_one()
    if ordered_total > 0 and returned_total >= ordered_total and order.status != "returned":
        from_status = order.status
        order.status = "returned"
        db.add(
            OrderStatusHistory(
                order_id=order.order_id,
                from_status=from_status,
                to_status="returned",
                transition_source="admin_return",
                transition_idempotency_key=f"ret:{idempotency_key[:58]}",
                transitioned_at=now,
            )
        )

    db.commit()
    db.refresh(return_req)
    return _build_detail_response(db, order_number, return_req)

