"""Kịch bản CDC 4: Store Manager - Cháy hàng tại sào quầy & Giờ cao điểm bán lẻ POS.

Mô phỏng:
1. Cháy hàng cục bộ tại quầy POS (Store Stockout Alert) giúp nhân viên chủ động gợi ý khách đặt ship về nhà.
2. Giờ cao điểm tối (Rush Hour): Doanh số bán hàng tại quầy tăng vọt, kéo chỉ tiêu Run-Rate từ Chậm tiến độ (Behind) sang Đạt tiến độ (On Track).
"""

import uuid

from app.db.session import SessionLocal
from app.models.catalog import Product, ProductVariant
from app.models.customer import Customer
from app.models.multicity import Store, StoreInventory
from app.models.order import Order
from demo.scenarios.base import (
    print_banner,
    print_cdc_event,
    print_dashboard_impact,
    print_step,
    print_success,
    utc_now,
)
from sqlalchemy import select


def run() -> None:
    print_banner(
        title="KỊCH BẢN CDC 4: STORE MANAGER - CHÁY HÀNG TẠI QUẦY & GIỜ CAO ĐIỂM POS",
        role="Store Manager (store_mgr@fashion.local)",
        url="http://localhost:3000/admin/analytics?role=store",
    )

    with SessionLocal() as session:
        # --- BƯỚC 1: CHÁY HÀNG CỤC BỘ TẠI QUẦY POS ---
        print_step(1, "Khách mua chiếc áo/quần cuối cùng tại quầy trưng bày Cửa hàng Chi nhánh 1")
        store = session.scalar(select(Store).where(Store.is_active == True).limit(1))
        if store:
            target_inv = session.execute(
                select(StoreInventory, ProductVariant, Product)
                .join(ProductVariant, ProductVariant.variant_id == StoreInventory.variant_id)
                .join(Product, Product.product_id == ProductVariant.product_id)
                .where(StoreInventory.store_id == store.store_id, StoreInventory.on_hand > 0)
                .limit(1)
            ).first()

            if target_inv:
                s_inv, variant, product = target_inv
                old_qty = s_inv.on_hand
                s_inv.on_hand = 0
                session.commit()

                print_cdc_event(
                    table="store_inventory",
                    op="UPDATE",
                    details=f"Store `{store.name}` (ID: {store.store_id}) | SKU `{variant.sku}`: on_hand {old_qty} ➔ 0 chiếc",
                )
                print_dashboard_impact(
                    metric=f"Tồn kho tại sào `{variant.sku}`",
                    before=f"{old_qty} chiếc tại quầy",
                    after="0 chiếc (HẾT HÀNG TẠI QUẦY)",
                    alert="🛎 [HÀNH ĐỘNG TỨC THÌ] Màn hình POS hiển thị ngay nhãn 'Hết hàng tại sào'! Nhân viên chủ động tư vấn: 'Mẫu này tại quầy vừa hết, em hỗ trợ tạo đơn ship hỏa tốc từ kho tổng về nhà miễn phí'.",
                )

        # --- BƯỚC 2: GIỜ CAO ĐIỂM BÙNG NỔ DOANH SỐ POS ---
        print_step(2, "Khách đông nghẹt ca tối, máy tính tiền POS quét đơn liên tục (+7.5 triệu đồng)")
        cust = session.scalar(select(Customer).where(Customer.role == "customer").limit(1))

        if store and cust:
            for i in range(6):
                pos_order = Order(
                    order_number=f"ORD-CDC-POS-{uuid.uuid4().hex[:6].upper()}",
                    customer_id=cust.customer_id,
                    checkout_idempotency_key=str(uuid.uuid4()),
                    store_id=store.store_id,
                    channel="pos",
                    status="completed",
                    shipping_address_text=f"Mua tại quầy {store.name}",
                    payment_method="vietqr",
                    subtotal_vnd=1250000,
                    discount_amount_vnd=0,
                    shipping_fee_vnd=0,
                    total_vnd=1250000,
                    receiver_name=cust.display_name or "Khách POS",
                    receiver_phone="0909123456",
                    created_at=utc_now(),
                )
                session.add(pos_order)
            session.commit()

            print_cdc_event(
                table="orders",
                op="INSERT",
                details=f"Ghi nhận thêm 6 đơn hoàn tất tại quầy POS Chi nhánh `{store.name}` (+7,500,000 đ)",
            )
            print_dashboard_impact(
                metric="Tiến độ doanh số trong ngày (Hourly Run-Rate)",
                before="1,370,000 đ (9.1% - Chậm tiến độ / Behind)",
                after="8,870,000 đ (59.1% - Đạt tiến độ / On Track)",
                alert="📈 [NHỊP ĐỘ BÁN HÀNG BẬT XANH] Doanh số ca tối kéo tiến độ nhảy vọt! Kịch bản up-sell phụ kiện tại quầy đã phát huy tác dụng tích cực.",
            )

    print_success(
        "Kịch bản 4 hoàn tất! Mở trình duyệt tại tab Cửa hàng (Store Manager) để thấy nhịp độ doanh số chuyển sang On Track."
    )


if __name__ == "__main__":
    run()
