"""Kịch bản CDC 5: Sales Manager - Sản phẩm Viral bán chạy bất ngờ & Lệch pha kênh bán hàng.

Mô phỏng:
1. Mẫu sản phẩm bỗng nhiên bán chạy gấp nhiều lần (Viral Best-Seller Velocity Surge).
2. Lệch pha tốc độ tăng trưởng giữa Kênh Online và Chuỗi Cửa Hàng (Channel Pace Divergence).
"""

import uuid

from app.db.session import SessionLocal
from app.models.catalog import Category, Product, ProductVariant
from app.models.customer import Customer
from app.models.order import Order, OrderItem
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
        title="KỊCH BẢN CDC 5: SALES - SẢN PHẨM VIRAL & ĐIỀU PHỐI KÊNH",
        role="Sales Manager (sales@fashion.local)",
        url="http://localhost:3000/admin/analytics?role=sales",
    )

    with SessionLocal() as session:
        # --- BƯỚC 1: SẢN PHẨM NỔ SỐ BÁN CHẠY ĐỘT BIẾN ---
        print_step(1, "Một dòng sản phẩm bùng nổ đơn đặt hàng sau khi xuất hiện trên video TikTok viral")
        target_row = session.execute(
            select(Product, ProductVariant, Category)
            .join(ProductVariant, ProductVariant.product_id == Product.product_id)
            .join(Category, Category.category_id == Product.category_id)
            .where(Product.is_active == True)
            .limit(1)
        ).first()

        cust = session.scalar(select(Customer).where(Customer.role == "customer").limit(1))

        if target_row and cust:
            product, variant, category = target_row

            # Tạo đơn hàng mua ồ ạt 250 sản phẩm
            viral_order = Order(
                order_number=f"ORD-CDC-VIRAL-{uuid.uuid4().hex[:6].upper()}",
                customer_id=cust.customer_id,
                checkout_idempotency_key=str(uuid.uuid4()),
                channel="online",
                status="completed",
                shipping_address_text="Kênh Online Toàn Quốc",
                payment_method="vietqr",
                subtotal_vnd=variant.price_vnd * 250,
                discount_amount_vnd=0,
                shipping_fee_vnd=0,
                total_vnd=variant.price_vnd * 250,
                receiver_name=cust.display_name or "Khách Mua Online",
                receiver_phone="0901234567",
                created_at=utc_now(),
            )
            session.add(viral_order)
            session.flush()

            item = OrderItem(
                public_id=uuid.uuid4(),
                order_id=viral_order.order_id,
                variant_id=variant.variant_id,
                product_public_id_snapshot=product.public_id,
                category_code_snapshot=category.code if hasattr(category, "code") else "thoi-trang",
                category_name_snapshot=category.name,
                product_name_snapshot=product.name,
                sku_snapshot=variant.sku,
                size_code_snapshot=variant.size_code,
                color_code_snapshot=variant.color_code,
                unit_price_vnd=variant.price_vnd,
                cost_price_vnd=variant.cost_price_vnd,
                quantity=250,
                line_total_vnd=variant.price_vnd * 250,
                created_at=utc_now(),
            )
            session.add(item)
            session.commit()

            print_cdc_event(
                table="orders",
                op="INSERT",
                details=f"Đơn hàng `{viral_order.order_number}` (Channel Online, status='completed')",
            )
            print_cdc_event(
                table="order_items",
                op="INSERT",
                details=f"250 chiếc `{product.name}` (Line total: {variant.price_vnd * 250:,} đ)",
            )
            print_dashboard_impact(
                metric=f"Vận tốc tăng trưởng `{product.name}`",
                before="Bình thường (Vị trí Top 5-10)",
                after="Top 1 Bán chạy nhất | Tăng tốc x4.8 lần",
                alert="🔥 [PHÁT HIỆN SẢN PHẨM VIRAL] Dashboard gắn ngay huy hiệu 'Viral Item'! Giám đốc kinh doanh chỉ đạo đẩy banner chính trang chủ và tạo combo khuyến mại kèm phụ kiện!",
            )

        # --- BƯỚC 2: CẢNH BÁO LỆCH PHA KÊNH BÁN HÀNG ---
        print_step(2, "Doanh số Kênh Online áp đảo chuỗi Cửa hàng")
        print_dashboard_impact(
            metric="Cơ cấu đóng góp kênh (Channel Pacing)",
            before="Online 98% vs Cửa hàng 2%",
            after="Online 99.2% vs Cửa hàng 0.8%",
            alert="⚠️ [LỆCH PHA TĂNG TRƯỞNG] Doanh số Online bùng nổ mạnh. Đề xuất điều động nhân sự hỗ trợ tư vấn Online Chat/Live để tối đa hóa tỷ lệ chốt đơn!",
        )

    print_success(
        "Kịch bản 5 hoàn tất! Mở trình duyệt tại tab Kinh doanh (Sales Manager) để xem huy hiệu Viral Item xuất hiện."
    )


if __name__ == "__main__":
    run()
