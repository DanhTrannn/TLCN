from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.common.money import compute_amounts
from app.core.errors import (
    auth_required,
    CART_NOT_ACTIVE,
    EMPTY_CART,
    IDEMPOTENCY_CONFLICT,
    OUT_OF_STOCK,
    VARIANT_NOT_SELLABLE,
    AppError,
)
from app.core.ids import new_order_number, new_payment_reference
from app.db.uow import run_in_transaction
from app.models.cart import Cart, CartItem
from app.models.catalog import Category, Product, ProductVariant
from app.models.inventory import Inventory
from app.models.customer import Customer
from app.models.order import Order, OrderItem, OrderStatusHistory, Payment
from app.modules.checkout.schemas import CheckoutRequest, CheckoutResultResponse


def _result_from_order(order: Order, payment: Payment) -> CheckoutResultResponse:
    return CheckoutResultResponse(
        order_number=order.order_number,
        status=order.status,
        payment_status=payment.status,
        failure_code=payment.failure_code,
        subtotal_vnd=order.subtotal_vnd,
        shipping_fee_vnd=order.shipping_fee_vnd,
        total_vnd=order.total_vnd,
    )


def checkout(customer_id: int, idempotency_key: str, payload: CheckoutRequest) -> CheckoutResultResponse:
    def _work(db: Session) -> CheckoutResultResponse:
        customer = db.execute(
            select(Customer).where(Customer.customer_id == customer_id).with_for_update()
        ).scalar_one_or_none()
        if customer is None or customer.status != "active":
            raise auth_required()

        # Idempotent replay: return the committed order for the same key.
        existing = db.execute(
            select(Order).where(Order.checkout_idempotency_key == idempotency_key)
        ).scalar_one_or_none()
        if existing is not None:
            if existing.customer_id != customer_id:
                raise AppError(
                    IDEMPOTENCY_CONFLICT,
                    "Idempotency key đã được dùng cho request khác.",
                    status_code=409,
                )
            payment = db.execute(
                select(Payment).where(Payment.order_id == existing.order_id)
            ).scalar_one()
            return _result_from_order(existing, payment)

        # Lock the customer's active cart.
        cart = db.execute(
            select(Cart)
            .where(Cart.customer_id == customer_id, Cart.status == "active")
            .with_for_update()
        ).scalar_one_or_none()
        if cart is None:
            raise AppError(CART_NOT_ACTIVE, "Không có giỏ hàng đang hoạt động.", status_code=409)

        # Lock present cart items in variant_id order.
        items = (
            db.execute(
                select(CartItem)
                .where(CartItem.cart_id == cart.cart_id, CartItem.is_present.is_(True))
                .order_by(CartItem.variant_id)
                .with_for_update()
            )
            .scalars()
            .all()
        )
        if not items:
            raise AppError(EMPTY_CART, "Giỏ hàng trống.", status_code=409)

        variant_ids = sorted({i.variant_id for i in items})

        # Load the catalog snapshot in key order and validate sellability.
        catalog_rows = db.execute(
            select(ProductVariant, Product, Category)
            .join(Product, Product.product_id == ProductVariant.product_id)
            .join(Category, Category.category_id == Product.category_id)
            .where(ProductVariant.variant_id.in_(variant_ids))
            .order_by(ProductVariant.variant_id)
            .with_for_update()
        ).all()
        catalog = {row[0].variant_id: row for row in catalog_rows}
        for vid in variant_ids:
            entry = catalog.get(vid)
            if entry is None:
                raise AppError(VARIANT_NOT_SELLABLE, "Sản phẩm không khả dụng.", status_code=409)
            variant, product, category = entry
            if not (variant.is_active and product.is_active and category.is_active):
                raise AppError(VARIANT_NOT_SELLABLE, "Sản phẩm không khả dụng.", status_code=409)

        # Lock inventory rows in key order and validate stock.
        inv_rows = (
            db.execute(
                select(Inventory)
                .where(Inventory.variant_id.in_(variant_ids))
                .order_by(Inventory.variant_id)
                .with_for_update()
            )
            .scalars()
            .all()
        )
        inventory = {r.variant_id: r for r in inv_rows}
        qty_by_variant = {i.variant_id: i.quantity for i in items}
        for vid in variant_ids:
            inv = inventory.get(vid)
            if inv is None or inv.on_hand < qty_by_variant[vid]:
                raise AppError(OUT_OF_STOCK, "Sản phẩm không đủ tồn kho.", status_code=409)

        # Compute line items and amounts from server-side data using integer VND.
        now = datetime.now(UTC)
        order_items: list[OrderItem] = []
        line_totals: list[int] = []
        for vid in variant_ids:
            variant, product, category = catalog[vid]
            qty = qty_by_variant[vid]
            line_total = variant.price_vnd * qty
            line_totals.append(line_total)
            order_items.append(
                OrderItem(
                    variant_id=vid,
                    product_public_id_snapshot=product.public_id,
                    category_code_snapshot=category.code,
                    category_name_snapshot=category.name,
                    product_name_snapshot=product.name,
                    sku_snapshot=variant.sku,
                    size_code_snapshot=variant.size_code,
                    color_code_snapshot=variant.color_code,
                    unit_price_vnd=variant.price_vnd,
                    quantity=qty,
                    line_total_vnd=line_total,
                    created_at=now,
                )
            )
        amounts = compute_amounts(line_totals)

        # Insert the paid order, items, successful payment, and initial history.
        order = Order(
            order_number=new_order_number(),
            cart_id=cart.cart_id,
            customer_id=customer_id,
            checkout_idempotency_key=idempotency_key,
            status="paid",
            currency_code="VND",
            subtotal_vnd=amounts.subtotal_vnd,
            shipping_fee_vnd=amounts.shipping_fee_vnd,
            total_vnd=amounts.total_vnd,
            receiver_name=payload.receiver_name.strip(),
            receiver_phone=payload.receiver_phone.strip(),
            shipping_address_text=payload.shipping_address_text.strip(),
            data_origin="manual",
            created_at=now,
            paid_at=now,
        )
        db.add(order)
        db.flush()

        for oi in order_items:
            oi.order_id = order.order_id
            db.add(oi)

        payment = Payment(
            payment_reference=new_payment_reference(),
            order_id=order.order_id,
            payment_idempotency_key=f"{idempotency_key}:pay",
            status="succeeded",
            currency_code="VND",
            amount_vnd=amounts.total_vnd,
            failure_code=None,
            attempted_at=now,
        )
        db.add(payment)

        db.add(
            OrderStatusHistory(
                order_id=order.order_id,
                from_status=None,
                to_status="paid",
                transition_source="checkout",
                transition_idempotency_key=f"{idempotency_key}:paid",
                transitioned_at=now,
            )
        )

        # Decrement inventory after all checkout validations pass.
        for vid in variant_ids:
            qty = qty_by_variant[vid]
            result = db.execute(
                update(Inventory)
                .where(Inventory.variant_id == vid, Inventory.on_hand >= qty)
                .values(
                    on_hand=Inventory.on_hand - qty,
                    version=Inventory.version + 1,
                    updated_at=now,
                )
            )
            if result.rowcount != 1:
                raise AppError(OUT_OF_STOCK, "Sản phẩm không đủ tồn kho.", status_code=409)

        # Close the cart only after all validations and writes succeed.
        cart.status = "checked_out"
        cart.checked_out_at = now
        cart.updated_at = now

        db.flush()
        return _result_from_order(order, payment)

    return run_in_transaction(_work)
