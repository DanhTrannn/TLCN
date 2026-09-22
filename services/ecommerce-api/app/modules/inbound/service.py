import hashlib
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.models.catalog import Product, ProductVariant
from app.models.customer import Customer
from app.models.inbound import InboundReceipt, InboundReceiptItem
from app.models.inventory import Inventory
from app.models.inventory_tx import InventoryTransaction
from app.modules.inbound.schemas import (
    CreateInboundReceiptPayload,
    InboundReceiptDetailResponse,
    InboundReceiptItemDetailResponse,
    InboundReceiptListResponse,
    InboundReceiptSummaryResponse,
)


def _extract_digest(idempotency_key: str | None) -> str:
    if idempotency_key and idempotency_key.strip():
        return hashlib.sha256(idempotency_key.strip().encode()).hexdigest()[:6].upper()
    return uuid4().hex[:6].upper()


def _generate_receipt_code(now: datetime, idempotency_key: str | None) -> tuple[str, str]:
    digest = _extract_digest(idempotency_key)
    return f"INB-{now.strftime('%Y%m%d')}-{digest}", digest


def create_inbound_receipt(
    db: Session,
    admin_customer_id: int,
    payload: CreateInboundReceiptPayload,
    idempotency_key: str,
) -> InboundReceiptDetailResponse:
    now = datetime.now(UTC).replace(tzinfo=None)
    receipt_code, digest = _generate_receipt_code(now, idempotency_key)

    # Idempotency check: search if any receipt exists with receipt_code like f"INB-%-{digest}"
    existing = db.execute(
        select(InboundReceipt)
        .where(InboundReceipt.receipt_code.like(f"INB-%-{digest}"))
        .order_by(InboundReceipt.receipt_id.desc())
    ).scalars().first()
    if existing is not None:
        return get_inbound_receipt_detail(db, existing.receipt_code)

    try:
        total_items_count = sum(item.quantity for item in payload.items)
        total_cost_vnd = sum(item.quantity * item.unit_cost_vnd for item in payload.items)

        receipt = InboundReceipt(
            public_id=uuid4(),
            receipt_code=receipt_code,
            batch_name=payload.batch_name,
            status="completed",
            total_items_count=total_items_count,
            total_cost_vnd=total_cost_vnd,
            notes=payload.notes,
            created_by_customer_id=admin_customer_id,
            created_at=now,
            updated_at=now,
        )
        db.add(receipt)
        db.flush()

        # Sort items by variant_id to guarantee consistent row lock acquisition order and prevent deadlocks
        sorted_items = sorted(payload.items, key=lambda x: x.variant_id)

        for item in sorted_items:
            variant = db.execute(
                select(ProductVariant)
                .where(ProductVariant.variant_id == item.variant_id)
                .with_for_update()
            ).scalar_one_or_none()
            if variant is None:
                raise not_found(f"Không tìm thấy biến thể với ID {item.variant_id}.")

            inv = db.execute(
                select(Inventory)
                .where(Inventory.variant_id == variant.variant_id)
                .with_for_update()
            ).scalar_one_or_none()
            if inv is None:
                inv = Inventory(
                    variant_id=variant.variant_id,
                    opening_on_hand=0,
                    on_hand=0,
                    version=0,
                    updated_at=now,
                )
                db.add(inv)
                db.flush()

            current_qty = inv.on_hand
            current_cost = int(variant.cost_price_vnd or 0)

            # Moving Weighted Average Costing formula
            # If Q_current == 0 (or <= 0), new cost = inbound unit cost
            if current_qty > 0:
                new_cost = round(
                    (current_qty * current_cost + item.quantity * item.unit_cost_vnd)
                    / (current_qty + item.quantity)
                )
            else:
                new_cost = item.unit_cost_vnd

            new_cost_int = int(new_cost)

            # Update variant cost price
            variant.cost_price_vnd = new_cost_int
            variant.updated_at = now

            # Update inventory on_hand and opening_on_hand
            inv.on_hand += item.quantity
            inv.opening_on_hand += item.quantity
            inv.version += 1
            inv.updated_at = now

            # Create inventory transaction record (sliced to 255 chars max for DB column constraint)
            inv_tx = InventoryTransaction(
                public_id=uuid4(),
                variant_id=variant.variant_id,
                location_type="central_warehouse",
                movement_type="inbound",
                quantity_delta=item.quantity,
                reference_code=receipt_code,
                notes=f"Nhập kho thành phẩm: {payload.batch_name}"[:255],
                created_at=now,
            )
            db.add(inv_tx)

            # Record receipt item
            receipt_item = InboundReceiptItem(
                public_id=uuid4(),
                receipt_id=receipt.receipt_id,
                variant_id=variant.variant_id,
                quantity=item.quantity,
                unit_cost_vnd=item.unit_cost_vnd,
                total_cost_vnd=item.quantity * item.unit_cost_vnd,
                previous_cost_price_vnd=current_cost,
                new_cost_price_vnd=new_cost_int,
                created_at=now,
            )
            db.add(receipt_item)

        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.execute(
            select(InboundReceipt)
            .where(InboundReceipt.receipt_code.like(f"INB-%-{digest}"))
            .order_by(InboundReceipt.receipt_id.desc())
        ).scalars().first()
        if existing is not None:
            return get_inbound_receipt_detail(db, existing.receipt_code)
        raise
    except Exception:
        db.rollback()
        raise

    return get_inbound_receipt_detail(db, receipt_code)


def get_inbound_receipt_detail(db: Session, receipt_code: str) -> InboundReceiptDetailResponse:
    row = db.execute(
        select(InboundReceipt, Customer.display_name)
        .outerjoin(Customer, Customer.customer_id == InboundReceipt.created_by_customer_id)
        .where(InboundReceipt.receipt_code == receipt_code)
    ).one_or_none()
    if row is None:
        raise not_found("Không tìm thấy phiếu nhập kho.")
    receipt, created_by_name = row

    item_rows = db.execute(
        select(
            InboundReceiptItem,
            ProductVariant.sku,
            ProductVariant.size_code,
            ProductVariant.color_code,
            Product.name.label("product_name"),
        )
        .join(ProductVariant, ProductVariant.variant_id == InboundReceiptItem.variant_id)
        .join(Product, Product.product_id == ProductVariant.product_id)
        .where(InboundReceiptItem.receipt_id == receipt.receipt_id)
        .order_by(InboundReceiptItem.item_id.asc())
    ).all()

    items = [
        InboundReceiptItemDetailResponse(
            item_id=item.item_id,
            variant_id=item.variant_id,
            product_name=product_name,
            sku=sku,
            size_code=size_code,
            color_code=color_code,
            quantity=item.quantity,
            unit_cost_vnd=item.unit_cost_vnd,
            total_cost_vnd=item.total_cost_vnd,
            previous_cost_price_vnd=item.previous_cost_price_vnd,
            new_cost_price_vnd=item.new_cost_price_vnd,
        )
        for item, sku, size_code, color_code, product_name in item_rows
    ]

    return InboundReceiptDetailResponse(
        receipt_id=receipt.receipt_id,
        receipt_code=receipt.receipt_code,
        batch_name=receipt.batch_name,
        status=receipt.status,
        total_items_count=receipt.total_items_count,
        total_cost_vnd=receipt.total_cost_vnd,
        notes=receipt.notes,
        created_by_name=created_by_name,
        created_at=receipt.created_at,
        items=items,
    )


def list_inbound_receipts(
    db: Session,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> InboundReceiptListResponse:
    stmt = (
        select(InboundReceipt, Customer.display_name)
        .outerjoin(Customer, Customer.customer_id == InboundReceipt.created_by_customer_id)
    )
    agg_stmt = select(
        func.count(),
        func.coalesce(func.sum(InboundReceipt.total_items_count), 0),
        func.coalesce(func.sum(InboundReceipt.total_cost_vnd), 0),
    ).select_from(InboundReceipt)

    if search and search.strip():
        kw = f"%{search.strip()}%"
        filter_clause = or_(
            InboundReceipt.receipt_code.ilike(kw),
            InboundReceipt.batch_name.ilike(kw),
        )
        stmt = stmt.where(filter_clause)
        agg_stmt = agg_stmt.where(filter_clause)

    agg_res = db.execute(agg_stmt).first()
    total = int(agg_res[0]) if agg_res else 0
    total_items_count = int(agg_res[1]) if agg_res else 0
    total_cost_vnd = int(agg_res[2]) if agg_res else 0

    rows = db.execute(
        stmt.order_by(InboundReceipt.created_at.desc(), InboundReceipt.receipt_id.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    items = [
        InboundReceiptSummaryResponse(
            receipt_id=r.receipt_id,
            receipt_code=r.receipt_code,
            batch_name=r.batch_name,
            status=r.status,
            total_items_count=r.total_items_count,
            total_cost_vnd=r.total_cost_vnd,
            created_by_name=c_name,
            created_at=r.created_at,
        )
        for r, c_name in rows
    ]

    return InboundReceiptListResponse(
        items=items,
        total=total,
        total_items_count=total_items_count,
        total_cost_vnd=total_cost_vnd,
    )
