from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.errors import AppError, OUT_OF_STOCK, RESOURCE_NOT_FOUND
from app.core.ids import new_order_number
from app.db.uow import run_in_transaction
from app.models.catalog import Product, ProductVariant
from app.models.inventory import Inventory
from app.models.multicity import Store, StoreInventory
from app.models.order import Order, OrderItem, OrderStatusHistory, Payment
from app.modules.pos.schemas import POSTransactionRequest


def search_products(db: Session, store_id: int, query: str) -> list[dict]:
    stmt = (
        select(
            ProductVariant.variant_id,
            Product.name.label("product_name"),
            ProductVariant.sku,
            ProductVariant.size_code,
            ProductVariant.color_code,
            ProductVariant.price_vnd,
            func.coalesce(StoreInventory.on_hand, 0).label("store_on_hand"),
            func.coalesce(Inventory.on_hand, 0).label("global_stock"),
        )
        .join(Product, Product.product_id == ProductVariant.product_id)
        .outerjoin(Inventory, Inventory.variant_id == ProductVariant.variant_id)
        .outerjoin(
            StoreInventory,
            (StoreInventory.variant_id == ProductVariant.variant_id)
            & (StoreInventory.store_id == store_id),
        )
        .where(ProductVariant.is_active == True)  # noqa: E712
        .where(Product.is_active == True)  # noqa: E712
        .where(
            (ProductVariant.sku.ilike(f"%{query}%"))
            | (Product.name.ilike(f"%{query}%"))
        )
        .limit(20)
    )
    rows = db.execute(stmt).all()
    return [dict(row._mapping) for row in rows]


def create_pos_transaction(
    db: Session, request: POSTransactionRequest, staff_id: int
) -> dict:
    with run_in_transaction(db):
        # Validate store exists and is active
        store = db.execute(
            select(Store).where(Store.store_id == request.store_id, Store.is_active == True)  # noqa: E712
        ).scalar_one_or_none()
        if not store:
            raise AppError(
                RESOURCE_NOT_FOUND,
                "Cửa hàng không tồn tại hoặc đã ngừng hoạt động",
                status_code=404,
            )

        now = datetime.now(timezone.utc)
        order_number = new_order_number()

        # Build order items and validate stock
        order_items = []
        subtotal = 0

        for item in request.items:
            # Check variant exists
            variant = db.execute(
                select(ProductVariant).where(
                    ProductVariant.variant_id == item.variant_id,
                    ProductVariant.is_active == True,  # noqa: E712
                )
            ).scalar_one_or_none()
            if not variant:
                raise AppError(
                    OUT_OF_STOCK,
                    f"Variant {item.variant_id} không tồn tại",
                    status_code=409,
                )

            # Check store inventory
            store_inv = db.execute(
                select(StoreInventory).where(
                    StoreInventory.store_id == request.store_id,
                    StoreInventory.variant_id == item.variant_id,
                ).with_for_update()
            ).scalar_one_or_none()

            if not store_inv or store_inv.on_hand < item.quantity:
                raise AppError(
                    OUT_OF_STOCK,
                    f"{variant.sku} không đủ hàng tại cửa hàng (còn {store_inv.on_hand if store_inv else 0})",
                    status_code=409,
                )

            line_total = variant.price_vnd * item.quantity
            subtotal += line_total

            order_items.append({
                "variant_id": variant.variant_id,
                "product_name": variant.product.name if hasattr(variant, "product") else "",
                "sku": variant.sku,
                "size_code": variant.size_code,
                "color_code": variant.color_code,
                "unit_price_vnd": variant.price_vnd,
                "quantity": item.quantity,
                "line_total_vnd": line_total,
                "product_public_id": str(variant.product.public_id) if hasattr(variant, "product") else "",
            })

            # Deduct store inventory
            store_inv.on_hand -= item.quantity
            store_inv.version += 1
            store_inv.updated_at = now

            # Deduct global inventory
            global_inv = db.execute(
                select(Inventory).where(
                    Inventory.variant_id == item.variant_id,
                ).with_for_update()
            ).scalar_one_or_none()
            if global_inv:
                global_inv.on_hand -= item.quantity
                global_inv.version += 1
                global_inv.updated_at = now

        total = subtotal  # POS: no shipping fee

        # Create order
        order = Order(
            order_number=order_number,
            customer_id=staff_id,
            store_id=request.store_id,
            channel="pos",
            staff_id=staff_id,
            status="completed",
            currency_code="VND",
            subtotal_vnd=subtotal,
            discount_amount_vnd=0,
            shipping_fee_vnd=0,
            total_vnd=total,
            receiver_name="POS Customer",
            receiver_phone="",
            shipping_address_text=store.address or "",
            data_origin="manual",
            paid_at=now,
            completed_at=now,
        )
        db.add(order)
        db.flush()

        # Create order items
        for item_data in order_items:
            order_item = OrderItem(
                order_id=order.order_id,
                variant_id=item_data["variant_id"],
                product_public_id_snapshot=item_data["product_public_id"],
                product_name_snapshot=item_data["product_name"],
                sku_snapshot=item_data["sku"],
                size_code_snapshot=item_data["size_code"],
                color_code_snapshot=item_data["color_code"],
                unit_price_vnd=item_data["unit_price_vnd"],
                quantity=item_data["quantity"],
                line_total_vnd=item_data["line_total_vnd"],
            )
            db.add(order_item)

        # Create payment
        payment = Payment(
            order_id=order.order_id,
            status="succeeded",
            amount_vnd=total,
        )
        db.add(payment)

        # Create status history
        history = OrderStatusHistory(
            order_id=order.order_id,
            from_status=None,
            to_status="completed",
            transition_source="pos",
        )
        db.add(history)

        db.flush()

        return {
            "order_number": order.order_number,
            "status": order.status,
            "channel": order.channel,
            "store_id": order.store_id,
            "payment_method": request.payment_method,
            "items": order_items,
            "subtotal_vnd": subtotal,
            "total_vnd": total,
            "created_at": now.isoformat(),
        }
