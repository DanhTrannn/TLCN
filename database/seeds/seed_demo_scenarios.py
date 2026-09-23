"""Comprehensive Seed & Demo Scenarios Script (Gói 4 - Task 4).

Populates realistic time-series data across 7 business domains:
1. Multi-City, Stores & Inventory
2. Catalogue & Opening Inventory
3. Demo Staff Accounts (7 roles) & Customers
4. Inbound Batches & Moving Weighted Average Costing
5. Orders (25+ orders over past 14 days: Delivered Online, POS Store, Boom/Failed Delivery, Customer Returns & Refunds)
6. Marketing & Engagement (Coupons, Redemptions, Reviews)
7. Logistics & Shipments
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.ids import uuid7
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.catalog import Category, Product, ProductVariant
from app.models.customer import Customer, CustomerCredential
from app.models.inbound import InboundReceipt, InboundReceiptItem
from app.models.inventory import Inventory
from app.models.inventory_tx import InventoryTransaction
from app.models.logistics import DeliveryStaff, Shipment
from app.models.multicity import City, Store, StoreInventory
from app.models.order import Order, OrderItem, Payment, Refund
from app.models.promotion import Coupon, CouponRedemption
from app.models.returns import ReturnItem, ReturnRequest
from app.models.review import ProductReview

_NS = uuid.uuid5(uuid.NAMESPACE_URL, "fashion:demo-seed")


def _pid(kind: str, key: str) -> uuid.UUID:
    return uuid.uuid5(_NS, f"{kind}:{key}")


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


# --- 1. Multi-City & Stores ---
CITIES_DATA = [
    {"code": "HCM", "name": "Hồ Chí Minh"},
    {"code": "HN", "name": "Hà Nội"},
    {"code": "DN", "name": "Đà Nẵng"},
]

STORES_DATA = [
    {"city_code": "HCM", "code": "HCM-CENTRE", "name": "Chi nhánh Sài Gòn Centre", "address": "123 Lê Lợi, Bến Nghé, Quận 1", "phone": "028-3822-1111"},
    {"city_code": "HN", "code": "HN-HOANKIEM", "name": "Chi nhánh Hoàn Kiếm", "address": "45 Tràng Tiền, Hoàn Kiếm", "phone": "024-3933-2222"},
]


def _seed_cities_and_stores(session: Session) -> tuple[dict[str, City], dict[str, Store]]:
    cities: dict[str, City] = {}
    for c in CITIES_DATA:
        city = session.execute(select(City).where(City.code == c["code"])).scalar_one_or_none()
        if city is None:
            city = City(code=c["code"], name=c["name"], is_active=True)
            session.add(city)
            session.flush()
        cities[c["code"]] = city

    stores: dict[str, Store] = {}
    for s in STORES_DATA:
        store = session.execute(select(Store).where(Store.code == s["code"])).scalar_one_or_none()
        if store is None:
            city = cities[s["city_code"]]
            store = Store(
                city_id=city.city_id,
                code=s["code"],
                name=s["name"],
                address=s["address"],
                phone=s["phone"],
                is_active=True,
            )
            session.add(store)
            session.flush()
        stores[s["code"]] = store

    return cities, stores


# --- 2. Catalog & Opening Inventory ---
CATEGORIES_DATA = [
    {"code": "ao", "name": "Áo Nam & Nữ"},
    {"code": "quan", "name": "Quần Nam & Nữ"},
    {"code": "phu-kien", "name": "Phụ kiện Thời trang"},
]

PRODUCTS_DATA = [
    ("ao-polo-basic", "ao", "Áo Polo Basic Cotton", "Áo polo cotton thoáng mát, lịch sự.", 299000, [("M", "black"), ("L", "navy"), ("XL", "white")]),
    ("ao-so-mi-oxford", "ao", "Áo Sơ Mi Oxford", "Áo sơ mi oxford dệt dày dặn, form chuẩn.", 389000, [("M", "white"), ("L", "blue")]),
    ("quan-jean-regular", "quan", "Quần Jean Regular Fit", "Quần jean ống suông dáng ôm vừa.", 450000, [("30", "blue"), ("32", "black")]),
    ("quan-kaki-slim", "quan", "Quần Kaki Slim Fit", "Quần kaki co giãn thoáng khí phong cách trẻ.", 350000, [("30", "beige"), ("32", "gray")]),
    ("that-lung-da-bo", "phu-kien", "Thắt Lưng Da Bò Thật", "Thắt lưng da cao cấp khóa kim loại không rỉ.", 250000, [("F", "black"), ("F", "brown")]),
]


def _seed_catalog(session: Session) -> list[ProductVariant]:
    cat_map: dict[str, Category] = {}
    for c in CATEGORIES_DATA:
        cat = session.execute(select(Category).where(Category.code == c["code"])).scalar_one_or_none()
        if cat is None:
            cat = Category(
                public_id=_pid("category", c["code"]),
                code=c["code"],
                name=c["name"],
                is_active=True,
            )
            session.add(cat)
            session.flush()
        cat_map[c["code"]] = cat

    variants: list[ProductVariant] = []
    for slug, cat_code, name, desc, base_price, combos in PRODUCTS_DATA:
        prod = session.execute(select(Product).where(Product.slug == slug)).scalar_one_or_none()
        if prod is None:
            prod = Product(
                public_id=_pid("product", slug),
                category_id=cat_map[cat_code].category_id,
                slug=slug,
                name=name,
                description=desc,
                image_url="https://sixdo.vn/modules/uniform/assets/image/aotruoc.webp",
                is_active=True,
            )
            session.add(prod)
            session.flush()

        for idx, (size, color) in enumerate(combos):
            sku = f"{slug}-{size}-{color}".upper()
            var = session.execute(select(ProductVariant).where(ProductVariant.sku == sku)).scalar_one_or_none()
            if var is None:
                var = ProductVariant(
                    public_id=str(_pid("variant", sku)),
                    product_id=prod.product_id,
                    sku=sku,
                    size_code=size,
                    color_code=color,
                    price_vnd=base_price + idx * 10000,
                    cost_price_vnd=0,
                    is_active=True,
                )
                session.add(var)
                session.flush()

            # Ensure warehouse inventory
            inv = session.execute(select(Inventory).where(Inventory.variant_id == var.variant_id)).scalar_one_or_none()
            if inv is None:
                inv = Inventory(
                    variant_id=var.variant_id,
                    opening_on_hand=50,
                    on_hand=50,
                    version=1,
                )
                session.add(inv)
                session.flush()

            variants.append(var)

    return variants


# --- 3. Accounts & Staff Roles ---
STAFF_ROLES_DATA = [
    ("admin", "Trần Quản Trị (CEO)", "admin@fashion.local"),
    ("sales_manager", "Lê Trưởng Kinh Doanh", "sales@fashion.local"),
    ("marketing_manager", "Nguyễn Trưởng Marketing", "marketing@fashion.local"),
    ("store_manager", "Phạm Quản Lý Cửa Hàng", "store_mgr@fashion.local"),
    ("inventory_manager", "Hoàng Trưởng Kho", "inventory@fashion.local"),
    ("operations_manager", "Vũ Trưởng Vận Hành", "operations@fashion.local"),
    ("system_admin", "Đỗ Quản Trị Hệ Thống", "sysadmin@fashion.local"),
]

CUSTOMERS_DATA = [
    ("Nguyễn Thị Mai", "cust_mai@fashion.local"),
    ("Trần Văn Bình", "cust_binh@fashion.local"),
    ("Lê Hoàng Nam", "cust_nam@fashion.local"),
    ("Phạm Minh Thảo", "cust_thao@fashion.local"),
    ("Vũ Đức Anh", "cust_anh@fashion.local"),
]


def _seed_accounts(
    session: Session, primary_store: Store
) -> tuple[dict[str, Customer], list[Customer], DeliveryStaff]:
    staff_map: dict[str, Customer] = {}
    default_pw = hash_password("Password123!")

    for role, display_name, email in STAFF_ROLES_DATA:
        cred = session.execute(
            select(CustomerCredential).where(CustomerCredential.email_normalized == email)
        ).scalar_one_or_none()
        if cred is not None:
            cust = session.get(Customer, cred.customer_id)
            staff_map[role] = cust
            continue

        store_id = primary_store.store_id if role == "store_manager" else None
        cust = Customer(
            public_id=str(_pid("account", email)),
            role=role,
            display_name=display_name,
            status="active",
            store_id=store_id,
            data_origin="manual",
        )
        session.add(cust)
        session.flush()

        session.add(
            CustomerCredential(
                customer_id=cust.customer_id,
                email_normalized=email,
                password_hash=default_pw,
                is_enabled=True,
            )
        )
        staff_map[role] = cust

    customers: list[Customer] = []
    for display_name, email in CUSTOMERS_DATA:
        cred = session.execute(
            select(CustomerCredential).where(CustomerCredential.email_normalized == email)
        ).scalar_one_or_none()
        if cred is not None:
            cust = session.get(Customer, cred.customer_id)
            customers.append(cust)
            continue

        cust = Customer(
            public_id=str(_pid("customer", email)),
            role="customer",
            display_name=display_name,
            status="active",
            data_origin="manual",
        )
        session.add(cust)
        session.flush()

        session.add(
            CustomerCredential(
                customer_id=cust.customer_id,
                email_normalized=email,
                password_hash=default_pw,
                is_enabled=True,
            )
        )
        customers.append(cust)

    # Seed delivery staff
    delivery_staff = session.execute(
        select(DeliveryStaff).where(DeliveryStaff.phone == "0981112233")
    ).scalar_one_or_none()
    if delivery_staff is None:
        delivery_staff = DeliveryStaff(
            public_id=_pid("delivery_staff", "0981112233"),
            full_name="Nguyễn Văn Giao Hàng",
            phone="0981112233",
            vehicle_plate="59-A1 888.88",
            is_active=True,
        )
        session.add(delivery_staff)
        session.flush()

    return staff_map, customers, delivery_staff


# --- 4. Inbound Batches & Moving Weighted Average Costing ---
def _seed_inbounds(
    session: Session, admin_id: int, variants: list[ProductVariant], now: datetime
) -> list[InboundReceipt]:
    batches_data = [
        ("INB-DEMO-001", "DEMO-BATCH-01", "Lô Áo Polo & Sơ Mi Cotton", now - timedelta(days=14), [
            (variants[0], 100, 110000),
            (variants[1], 80, 115000),
            (variants[2], 60, 120000),
            (variants[3], 70, 160000),
        ]),
        ("INB-DEMO-002", "DEMO-BATCH-02", "Lô Quần Jean & Kaki Denim", now - timedelta(days=10), [
            (variants[4], 90, 165000),
            (variants[5], 80, 180000),
            (variants[6], 75, 185000),
            (variants[0], 50, 125000),  # updates moving average for variants[0]
        ]),
        ("INB-DEMO-003", "DEMO-BATCH-03", "Lô Phụ Kiện Thắt Lưng & Bổ Sung", now - timedelta(days=6), [
            (variants[7], 100, 140000),
            (variants[8], 90, 145000),
            (variants[9], 80, 95000),
            (variants[1], 40, 122000),  # updates moving average for variants[1]
        ]),
    ]

    receipts: list[InboundReceipt] = []
    for receipt_code, batch_name, batch_desc, batch_time, items in batches_data:
        existing = session.execute(
            select(InboundReceipt).where(InboundReceipt.receipt_code == receipt_code)
        ).scalar_one_or_none()
        if existing is not None:
            receipts.append(existing)
            continue

        tot_items = sum(qty for _, qty, _ in items)
        tot_cost = sum(qty * cost for _, qty, cost in items)

        receipt = InboundReceipt(
            public_id=_pid("inbound", receipt_code),
            receipt_code=receipt_code,
            batch_name=f"{batch_name} - {batch_desc}",
            status="completed",
            total_items_count=tot_items,
            total_cost_vnd=tot_cost,
            notes=f"Nhập kho thành phẩm theo kế hoạch sản xuất: {batch_desc}",
            created_by_customer_id=admin_id,
            created_at=batch_time,
            updated_at=batch_time,
        )
        session.add(receipt)
        session.flush()

        for var, qty, unit_cost in items:
            inv = session.execute(
                select(Inventory).where(Inventory.variant_id == var.variant_id)
            ).scalar_one()

            cur_qty = inv.on_hand
            cur_cost = int(var.cost_price_vnd or 0)

            if cur_qty > 0 and cur_cost > 0:
                new_cost = round((cur_qty * cur_cost + qty * unit_cost) / (cur_qty + qty))
            else:
                new_cost = unit_cost

            new_cost_int = int(new_cost)
            var.cost_price_vnd = new_cost_int

            inv.on_hand += qty
            inv.opening_on_hand += qty
            inv.version += 1
            inv.updated_at = batch_time

            # Log inventory transaction
            inv_tx = InventoryTransaction(
                public_id=_pid("inv_tx", f"{receipt_code}-{var.sku}"),
                variant_id=var.variant_id,
                location_type="central_warehouse",
                movement_type="inbound",
                quantity_delta=qty,
                reference_code=receipt_code,
                notes=f"Nhập kho lô hàng {batch_name}"[:255],
                created_at=batch_time,
            )
            session.add(inv_tx)

            # Record receipt item
            receipt_item = InboundReceiptItem(
                public_id=_pid("inbound_item", f"{receipt_code}-{var.sku}"),
                receipt_id=receipt.receipt_id,
                variant_id=var.variant_id,
                quantity=qty,
                unit_cost_vnd=unit_cost,
                total_cost_vnd=qty * unit_cost,
                previous_cost_price_vnd=cur_cost,
                new_cost_price_vnd=new_cost_int,
                created_at=batch_time,
            )
            session.add(receipt_item)

        session.flush()
        receipts.append(receipt)

    return receipts


# --- 5. Store Inventory for POS ---
def _seed_store_inventory(session: Session, store: Store, variants: list[ProductVariant]):
    max_id = session.scalar(select(func.coalesce(func.max(StoreInventory.store_inventory_id), 0))) or 0
    for var in variants:
        st_inv = session.execute(
            select(StoreInventory).where(
                StoreInventory.store_id == store.store_id,
                StoreInventory.variant_id == var.variant_id,
            )
        ).scalar_one_or_none()
        if st_inv is None:
            max_id += 1
            st_inv = StoreInventory(
                store_inventory_id=max_id,
                store_id=store.store_id,
                variant_id=var.variant_id,
                opening_on_hand=80,
                on_hand=80,
                version=1,
            )
            session.add(st_inv)
    session.flush()


# --- 6. Marketing (Coupons) ---
def _seed_coupons(session: Session) -> Coupon:
    coupon = session.execute(
        select(Coupon).where(Coupon.code_normalized == "SUMMER20")
    ).scalar_one_or_none()
    if coupon is None:
        coupon = Coupon(
            public_id=_pid("coupon", "SUMMER20"),
            code_normalized="SUMMER20",
            discount_type="percentage",
            discount_value=10,
            minimum_subtotal_vnd=100000,
            starts_at=datetime(2025, 1, 1),
            ends_at=datetime(2030, 1, 1),
            is_active=True,
            total_usage_limit=1000,
            per_customer_usage_limit=2,
            used_count=0,
        )
        session.add(coupon)
        session.flush()
    return coupon


# --- 7. Orders across 7 Domains ---
def _seed_orders_and_related(
    session: Session,
    customers: list[Customer],
    staff_map: dict[str, Customer],
    delivery_staff: DeliveryStaff,
    variants: list[ProductVariant],
    store: Store,
    coupon: Coupon,
    now: datetime,
) -> tuple[int, int, int, int, int, int]:
    """Populates 27 orders:
    - 16 delivered online orders
    - 6 completed POS store orders
    - 3 failed delivery (boom) orders
    - 2 customer return requests (1 completed with refund, 1 approved)
    Returns counts: (orders, payments, shipments, returns, refunds, reviews)
    """
    store_mgr = staff_map["store_manager"]
    num_variants = len(variants)

    # Pre-fetch products to populate OrderItem snapshot fields
    prod_map = {v.variant_id: session.get(Product, v.product_id) for v in variants}

    order_counter = 0

    def _create_base_order(
        idx: int,
        channel: str,
        status: str,
        cust: Customer,
        days_ago: float,
        is_cod: bool = False,
        use_coupon: bool = False,
        assigned_store_id: int | None = None,
        staff_id: int | None = None,
    ) -> tuple[Order, list[OrderItem], Payment]:
        nonlocal order_counter
        order_counter += 1
        order_num = f"ORD-DEMO-{order_counter:03d}"
        key = f"demo-order-{order_num}"

        order_time = now - timedelta(days=days_ago, hours=(idx * 2) % 24)

        # 1-2 items
        selected_var_1 = variants[(idx * 2) % num_variants]
        selected_var_2 = variants[(idx * 2 + 1) % num_variants]
        chosen_vars = [selected_var_1]
        if idx % 2 == 1:
            chosen_vars.append(selected_var_2)

        items_to_create = []
        subtotal = 0
        for v in chosen_vars:
            qty = 1 + (idx % 2)
            unit_price = v.price_vnd
            line_tot = unit_price * qty
            subtotal += line_tot
            items_to_create.append((v, qty, unit_price, line_tot))

        discount = 0
        coupon_id = None
        coupon_code = None
        coupon_type = None
        coupon_val = None
        if use_coupon:
            coupon_id = coupon.coupon_id
            coupon_code = coupon.code_normalized
            coupon_type = coupon.discount_type
            coupon_val = coupon.discount_value
            discount = int(subtotal * coupon_val // 100)

        shipping_fee = 0 if channel == "pos" else 30000
        total_vnd = subtotal - discount + shipping_fee

        order = Order(
            order_number=order_num,
            customer_id=cust.customer_id,
            checkout_idempotency_key=key,
            coupon_id=coupon_id,
            status=status,
            payment_method="cod" if is_cod else "vietqr",
            currency_code="VND",
            subtotal_vnd=subtotal,
            coupon_code_snapshot=coupon_code,
            coupon_type_snapshot=coupon_type,
            coupon_value_snapshot=coupon_val,
            discount_amount_vnd=discount,
            shipping_fee_vnd=shipping_fee,
            total_vnd=total_vnd,
            receiver_name=cust.display_name,
            receiver_phone="0901122334",
            shipping_address_text="Số 88 đường Hai Bà Trưng, Phường Bến Nghé, Quận 1, TP Hồ Chí Minh",
            data_origin="manual",
            created_at=order_time,
            updated_at=order_time,
            paid_at=order_time if status in ("paid", "shipping", "delivered", "completed", "returned") else None,
            confirmed_at=order_time if status in ("confirmed", "shipping", "delivered", "completed", "returned") else None,
            completed_at=order_time if status == "completed" else None,
            store_id=assigned_store_id,
            channel=channel,
            staff_id=staff_id,
        )
        session.add(order)
        session.flush()

        order_items = []
        for v, qty, unit_p, line_t in items_to_create:
            p = prod_map[v.variant_id]
            cost_p = int(v.cost_price_vnd or 0)
            if cost_p == 0:
                cost_p = int(unit_p * 0.5)

            item = OrderItem(
                public_id=_pid("order_item", f"{order_num}-{v.sku}"),
                order_id=order.order_id,
                variant_id=v.variant_id,
                product_public_id_snapshot=p.public_id,
                category_code_snapshot="thoi-trang",
                category_name_snapshot="Thời Trang",
                product_name_snapshot=p.name,
                sku_snapshot=v.sku,
                size_code_snapshot=v.size_code,
                color_code_snapshot=v.color_code,
                unit_price_vnd=unit_p,
                cost_price_vnd=cost_p,
                quantity=qty,
                line_total_vnd=line_t,
                created_at=order_time,
            )
            session.add(item)
            order_items.append(item)

        # Payment
        pay_status = "failed" if status == "failed_delivery" and is_cod else "succeeded"
        fail_code = "DELIVERY_FAILED" if pay_status == "failed" else None
        payment = Payment(
            order_id=order.order_id,
            payment_reference=f"PAY-{order_num}",
            payment_idempotency_key=f"pay-idemp-{order_num}",
            status=pay_status,
            currency_code="VND",
            amount_vnd=total_vnd,
            failure_code=fail_code,
            attempted_at=order_time,
            created_at=order_time,
        )
        session.add(payment)

        # Coupon redemption if used
        if use_coupon:
            redemption = CouponRedemption(
                coupon_id=coupon.coupon_id,
                order_id=order.order_id,
                customer_id=cust.customer_id,
                status="redeemed",
                redeemed_at=order_time,
                created_at=order_time,
                updated_at=order_time,
            )
            session.add(redemption)
            coupon.used_count += 1

        session.flush()
        return order, order_items, payment

    # Check if orders already seeded
    existing_orders_count = session.scalar(
        select(func.count()).select_from(Order).where(Order.order_number.like("ORD-DEMO-%"))
    ) or 0
    if existing_orders_count >= 25:
        # Already seeded
        return 0, 0, 0, 0, 0, 0

    all_delivered_items: list[OrderItem] = []

    # 1. 16 Delivered Online Orders (Past 14 days)
    for i in range(16):
        cust = customers[i % len(customers)]
        days_ago = 13.0 - (i * 0.8)
        use_cp = (i == 0)  # Use coupon on order 1
        order, items, _ = _create_base_order(
            idx=i,
            channel="online",
            status="delivered",
            cust=cust,
            days_ago=days_ago,
            is_cod=(i % 3 == 0),
            use_coupon=use_cp,
        )

        # Warehouse Inventory deduction & tx
        for item in items:
            inv = session.execute(select(Inventory).where(Inventory.variant_id == item.variant_id)).scalar_one()
            inv.on_hand = max(0, inv.on_hand - item.quantity)
            inv.version += 1
            inv_tx = InventoryTransaction(
                public_id=_pid("inv_tx_out", f"{order.order_number}-{item.variant_id}"),
                variant_id=item.variant_id,
                location_type="central_warehouse",
                movement_type="outbound_order",
                quantity_delta=-item.quantity,
                reference_code=order.order_number,
                notes=f"Xuất kho đơn hàng online {order.order_number}",
                created_at=order.created_at,
            )
            session.add(inv_tx)

        # Shipment
        shipment = Shipment(
            public_id=_pid("shipment", order.order_number),
            shipment_code=f"SHP-{order.order_number}",
            order_id=order.order_id,
            delivery_staff_id=delivery_staff.staff_id,
            status="delivered",
            attempt_count=1,
            cod_amount_vnd=order.total_vnd if order.payment_method == "cod" else 0,
            cod_collected_vnd=order.total_vnd if order.payment_method == "cod" else 0,
            dispatched_at=order.created_at + timedelta(hours=2),
            delivered_at=order.created_at + timedelta(days=1),
            notes="Giao hàng thành công đúng hẹn.",
            created_at=order.created_at,
            updated_at=order.created_at + timedelta(days=1),
        )
        session.add(shipment)
        all_delivered_items.extend(items)

    # 2. 6 Completed POS Store Orders
    for i in range(6):
        cust = customers[(i + 2) % len(customers)]
        days_ago = 12.0 - (i * 1.8)
        order, items, _ = _create_base_order(
            idx=16 + i,
            channel="pos",
            status="completed",
            cust=cust,
            days_ago=days_ago,
            is_cod=False,
            assigned_store_id=store.store_id,
            staff_id=store_mgr.customer_id,
        )

        for item in items:
            st_inv = session.execute(
                select(StoreInventory).where(
                    StoreInventory.store_id == store.store_id,
                    StoreInventory.variant_id == item.variant_id,
                )
            ).scalar_one()
            st_inv.on_hand = max(0, st_inv.on_hand - item.quantity)
            st_inv.version += 1

            inv_tx = InventoryTransaction(
                public_id=_pid("inv_tx_pos", f"{order.order_number}-{item.variant_id}"),
                variant_id=item.variant_id,
                location_type="store",
                store_id=store.store_id,
                movement_type="outbound_pos",
                quantity_delta=-item.quantity,
                reference_code=order.order_number,
                notes=f"Bán hàng trực tiếp tại quầy POS {order.order_number}",
                created_at=order.created_at,
            )
            session.add(inv_tx)

    # 3. 3 Failed Delivery (Boom) Orders
    for i in range(3):
        cust = customers[i]
        days_ago = 8.0 - (i * 2.0)
        order, items, _ = _create_base_order(
            idx=22 + i,
            channel="online",
            status="failed_delivery",
            cust=cust,
            days_ago=days_ago,
            is_cod=True,
        )

        shipment = Shipment(
            public_id=_pid("shipment", order.order_number),
            shipment_code=f"SHP-{order.order_number}",
            order_id=order.order_id,
            delivery_staff_id=delivery_staff.staff_id,
            status="failed",
            attempt_count=3,
            cod_amount_vnd=order.total_vnd,
            cod_collected_vnd=0,
            dispatched_at=order.created_at + timedelta(hours=2),
            failed_at=order.created_at + timedelta(days=2),
            failure_reason="Khách không nghe máy sau 3 cuộc gọi, từ chối nhận hàng.",
            notes="Đơn hàng giao thất bại (boom hàng).",
            created_at=order.created_at,
            updated_at=order.created_at + timedelta(days=2),
        )
        session.add(shipment)

    # 4. 2 Customer Return Requests (1 completed with refund, 1 approved)
    # Return 1: on an online delivered order -> status="returned", with Refund(status="succeeded")
    ret_order_1, ret_items_1, pay_1 = _create_base_order(
        idx=25,
        channel="online",
        status="returned",
        cust=customers[0],
        days_ago=7.0,
    )
    shipment_ret1 = Shipment(
        public_id=_pid("shipment", ret_order_1.order_number),
        shipment_code=f"SHP-{ret_order_1.order_number}",
        order_id=ret_order_1.order_id,
        delivery_staff_id=delivery_staff.staff_id,
        status="delivered",
        attempt_count=1,
        dispatched_at=ret_order_1.created_at + timedelta(hours=2),
        delivered_at=ret_order_1.created_at + timedelta(days=1),
        notes="Giao hàng thành công trước khi đổi trả.",
        created_at=ret_order_1.created_at,
        updated_at=ret_order_1.created_at + timedelta(days=1),
    )
    session.add(shipment_ret1)

    return_req_1 = ReturnRequest(
        public_id=_pid("return_req", ret_order_1.order_number),
        return_code=f"RET-{ret_order_1.order_number}",
        order_id=ret_order_1.order_id,
        customer_id=ret_order_1.customer_id,
        action_type="refund",
        status="completed",
        customer_reason="Sản phẩm mặc không vừa kích thước, yêu cầu hoàn tiền.",
        admin_note="Kiểm tra hàng nguyên tem mác, chấp thuận hoàn tiền đầy đủ.",
        reviewed_at=ret_order_1.created_at + timedelta(days=2),
        resolved_at=ret_order_1.created_at + timedelta(days=3),
        created_at=ret_order_1.created_at + timedelta(days=1),
        updated_at=ret_order_1.created_at + timedelta(days=3),
    )
    session.add(return_req_1)
    session.flush()

    ret_item_1 = ReturnItem(
        public_id=_pid("return_item", f"ret-{ret_order_1.order_number}-1"),
        return_id=return_req_1.return_id,
        order_item_id=ret_items_1[0].order_item_id,
        variant_id=ret_items_1[0].variant_id,
        quantity=ret_items_1[0].quantity,
        refund_amount_vnd=ret_order_1.subtotal_vnd,
        inspection_status="passed",
        created_at=return_req_1.created_at,
        updated_at=return_req_1.resolved_at or return_req_1.created_at,
    )
    session.add(ret_item_1)

    refund_1 = Refund(
        public_id=_pid("refund", ret_order_1.order_number),
        payment_id=pay_1.payment_id,
        refund_idempotency_key=f"refund-idemp-{ret_order_1.order_number}",
        status="succeeded",
        currency_code="VND",
        amount_vnd=ret_order_1.subtotal_vnd,
        reason="Khách hàng hoàn trả sản phẩm nguyên vẹn, passed inspection.",
        requested_by_customer_id=ret_order_1.customer_id,
        created_at=return_req_1.created_at + timedelta(days=1),
        completed_at=return_req_1.resolved_at,
        updated_at=return_req_1.resolved_at,
    )
    session.add(refund_1)

    # Return 2: approved/pending return request on delivered order
    ret_order_2, ret_items_2, _ = _create_base_order(
        idx=26,
        channel="online",
        status="delivered",
        cust=customers[1],
        days_ago=4.0,
    )
    shipment_ret2 = Shipment(
        public_id=_pid("shipment", ret_order_2.order_number),
        shipment_code=f"SHP-{ret_order_2.order_number}",
        order_id=ret_order_2.order_id,
        delivery_staff_id=delivery_staff.staff_id,
        status="delivered",
        attempt_count=1,
        dispatched_at=ret_order_2.created_at + timedelta(hours=2),
        delivered_at=ret_order_2.created_at + timedelta(days=1),
        notes="Giao hàng thành công trước khi phát sinh khiếu nại.",
        created_at=ret_order_2.created_at,
        updated_at=ret_order_2.created_at + timedelta(days=1),
    )
    session.add(shipment_ret2)

    return_req_2 = ReturnRequest(
        public_id=_pid("return_req", ret_order_2.order_number),
        return_code=f"RET-{ret_order_2.order_number}",
        order_id=ret_order_2.order_id,
        customer_id=ret_order_2.customer_id,
        action_type="refund",
        status="approved",
        customer_reason="Sản phẩm có vết sờn chỉ nhỏ ở vạt áo.",
        admin_note="Chấp thuận tiếp nhận hàng để kiểm tra thực tế.",
        reviewed_at=ret_order_2.created_at + timedelta(days=1),
        resolved_at=None,
        created_at=ret_order_2.created_at + timedelta(hours=12),
        updated_at=ret_order_2.created_at + timedelta(days=1),
    )
    session.add(return_req_2)
    session.flush()

    ret_item_2 = ReturnItem(
        public_id=_pid("return_item", f"ret-{ret_order_2.order_number}-1"),
        return_id=return_req_2.return_id,
        order_item_id=ret_items_2[0].order_item_id,
        variant_id=ret_items_2[0].variant_id,
        quantity=ret_items_2[0].quantity,
        refund_amount_vnd=ret_order_2.subtotal_vnd,
        inspection_status="pending",
        created_at=return_req_2.created_at,
        updated_at=return_req_2.created_at,
    )
    session.add(ret_item_2)

    # 5. Seed Reviews on Delivered Items
    review_templates = [
        (5, "Chất lượng vải rất tốt, mặc ôm dáng và thoáng mát! Giao hàng cực nhanh."),
        (4, "Áo đẹp, đường chỉ may kỹ càng, màu sắc nhã nhặn đúng mô tả."),
        (5, "Rất ưng ý với sản phẩm này, sẽ tiếp tục ủng hộ shop trong các đơn hàng tới!"),
    ]
    for r_idx, (rating, text_content) in enumerate(review_templates):
        target_item = all_delivered_items[r_idx]
        existing_rev = session.execute(
            select(ProductReview).where(ProductReview.order_item_id == target_item.order_item_id)
        ).scalar_one_or_none()
        if existing_rev is None:
            p = prod_map[target_item.variant_id]
            rev = ProductReview(
                public_id=_pid("review", f"rev-{target_item.order_item_id}"),
                order_item_id=target_item.order_item_id,
                customer_id=customers[r_idx % len(customers)].customer_id,
                product_id=p.product_id,
                rating=rating,
                content=text_content,
                status="approved",
                moderation_reason=None,
                moderated_by_customer_id=None,
                moderated_at=None,
                created_at=target_item.created_at + timedelta(days=2),
                updated_at=target_item.created_at + timedelta(days=2),
            )
            session.add(rev)

    session.flush()
    return 27, 27, 21, 2, 1, 3


def seed_demo_data(session: Session | None = None) -> dict[str, int]:
    """Populates realistic demo data across 7 business domains idempotently."""
    def _seed(s: Session) -> dict[str, int]:
        now = _utc_now()

        # 1. Cities & Stores
        _, stores = _seed_cities_and_stores(s)
        primary_store = stores["HCM-CENTRE"]

        # 2. Catalogue & Inventory
        variants = _seed_catalog(s)

        # 3. Accounts (7 Staff Roles + Customers + DeliveryStaff)
        staff_map, customers, delivery_staff = _seed_accounts(s, primary_store)
        admin = staff_map["admin"]

        # 4. Inbound Batches & Costing
        _seed_inbounds(s, admin.customer_id, variants, now)

        # 5. Store Inventory
        _seed_store_inventory(s, primary_store, variants)

        # 6. Coupons
        coupon = _seed_coupons(s)

        # 7. Orders & Related Entities
        _seed_orders_and_related(
            session=s,
            customers=customers,
            staff_map=staff_map,
            delivery_staff=delivery_staff,
            variants=variants,
            store=primary_store,
            coupon=coupon,
            now=now,
        )

        s.commit()

        # Return actual counts
        return {
            "customers": s.scalar(select(func.count()).select_from(Customer)) or 0,
            "inbound_receipts": s.scalar(select(func.count()).select_from(InboundReceipt)) or 0,
            "orders": s.scalar(select(func.count()).select_from(Order)) or 0,
            "payments": s.scalar(select(func.count()).select_from(Payment)) or 0,
            "shipments": s.scalar(select(func.count()).select_from(Shipment)) or 0,
            "returns": s.scalar(select(func.count()).select_from(ReturnRequest)) or 0,
            "refunds": s.scalar(select(func.count()).select_from(Refund)) or 0,
            "reviews": s.scalar(select(func.count()).select_from(ProductReview)) or 0,
            "coupons": s.scalar(select(func.count()).select_from(Coupon)) or 0,
        }

    if session is None:
        with SessionLocal() as db:
            return _seed(db)
    else:
        return _seed(session)


if __name__ == "__main__":
    counts = seed_demo_data()
    print(f"Demo scenarios successfully seeded: {counts}")
