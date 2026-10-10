"""Kịch bản CDC 1: Marketing Manager - Flash Sale Voucher Burn Rate & Negative Review Spike.

Mô phỏng:
1. Tốc độ đốt ngân sách Voucher Flash Sale vượt ngưỡng 90% (Voucher Burn Rate Alarm).
2. Bùng phát đánh giá tiêu cực 1-2 sao cho sản phẩm đang chạy quảng cáo (Negative Review Spike).
"""

import uuid
from datetime import UTC, datetime, timedelta

from app.db.session import SessionLocal
from app.models.catalog import Product, ProductVariant
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.promotion import Coupon, CouponRedemption
from app.models.review import ProductReview
from demo.scenarios.base import (
    print_banner,
    print_cdc_event,
    print_dashboard_impact,
    print_step,
    print_success,
    utc_now,
)
from sqlalchemy import desc, select


def run() -> None:
    print_banner(
        title="KỊCH BẢN CDC 1: MARKETING - FLASH SALE & REVIEW SPIKE",
        role="Marketing Manager (marketing@fashion.local)",
        url="http://localhost:3000/admin/analytics?role=marketing",
    )

    with SessionLocal() as session:
        # --- BƯỚC 1: KÍCH HOẠT VOUCHER FLASH SALE CHÁY NGÂN SÁCH ---
        print_step(1, "Khách hàng ồ ạt áp mã SALE50K trong Flash Sale (Voucher Burn Rate)")
        coupon = session.scalar(
            select(Coupon).where(Coupon.code_normalized == "SALE50K")
        )
        if not coupon:
            coupon = session.scalar(select(Coupon).where(Coupon.is_active == True))

        if coupon:
            old_used = coupon.used_count
            limit = coupon.total_usage_limit or 1000
            new_used = min(limit, max(old_used + 95, int(limit * 0.96)))
            coupon.used_count = new_used

            # Thêm các redemption mới (chỉ thêm cho order chưa có redemption)
            subq = select(CouponRedemption.order_id)
            available_orders = session.scalars(
                select(Order).where(~Order.order_id.in_(subq)).limit(5)
            ).all()

            for order in available_orders:
                redemption = CouponRedemption(
                    coupon_id=coupon.coupon_id,
                    order_id=order.order_id,
                    customer_id=order.customer_id,
                    status="redeemed",
                    redeemed_at=utc_now(),
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
                session.add(redemption)

            session.commit()

            print_cdc_event(
                table="coupons",
                op="UPDATE",
                details=f"Mã `{coupon.code_normalized}`: used_count={new_used}/{limit} (Đạt {round(new_used / limit * 100, 1)}% ngân sách)",
            )
            print_cdc_event(
                table="coupon_redemptions",
                op="INSERT",
                details=f"Ghi nhận thêm {len(available_orders)} lượt áp mã giảm giá trong 5 phút qua",
            )
            print_dashboard_impact(
                metric="Tốc độ tiêu hao ngân sách Voucher",
                before=f"{round(old_used / limit * 100, 1)}%",
                after=f"{round(new_used / limit * 100, 1)}%",
                alert="🚨 [BẬT CẢNH BÁO ĐỎ] Đã dùng >80% ngân sách Flash Sale! Đề xuất đóng mã hoặc bổ sung hạn mức khẩn cấp.",
            )

        # --- BƯỚC 2: BÙNG PHÁT ĐÁNH GIÁ TIÊU CỰC 1 SAO ---
        print_step(2, "Khách hàng đồng loạt gửi đánh giá 1 sao phản ánh lỗi may (Negative Review Spike)")
        product = session.scalar(
            select(Product).where(Product.product_id == 9)
        )
        if not product:
            product = session.scalar(select(Product).where(Product.is_active == True).limit(1))
        cust = session.scalar(select(Customer).where(Customer.role == "customer").limit(1))

        # Tìm các order_item chưa có review
        subq_rev = select(ProductReview.order_item_id)
        unreviewed_items = session.scalars(
            select(OrderItem).where(~OrderItem.order_item_id.in_(subq_rev)).limit(3)
        ).all()

        if product and cust and unreviewed_items:
            complaints = [
                "[DEMO CDC] Vải mỏng hơn mô tả rất nhiều, đường may bị tuột chỉ ngay nách áo!",
                "[DEMO CDC] Màu thực tế bị xỉn, form áo bị lệch vạt, đề nghị shop hoàn tiền gấp.",
                "[DEMO CDC] Giao sai mẫu và chất liệu thô cứng, mặc rất ngứa không hài lòng chút nào.",
            ]
            for idx, order_item in enumerate(unreviewed_items):
                text_content = complaints[idx % len(complaints)]
                review = ProductReview(
                    public_id=uuid.uuid4(),
                    order_item_id=order_item.order_item_id,
                    customer_id=cust.customer_id,
                    product_id=product.product_id,
                    rating=1,
                    content=text_content,
                    status="approved",
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
                session.add(review)
            session.commit()

            print_cdc_event(
                table="product_reviews",
                op="INSERT",
                details=f"Ghi nhận thêm {len(unreviewed_items)} đánh giá 1 sao cho sản phẩm `{product.name}` (ID: {product.product_id})",
            )
            print_dashboard_impact(
                metric="Tín hiệu CDC: Điểm nóng Review tiêu cực",
                before="Bình thường",
                after=f"Bùng phát review xấu cho `{product.name}`",
                alert="🚨 [BẬT CẢNH BÁO ĐỎ] Đề xuất tạm dừng chiến dịch Quảng cáo (Ads) cho sản phẩm này để kiểm tra chất lượng lô hàng!",
            )

    print_success(
        "Kịch bản 1 hoàn tất! Mở trình duyệt tại tab Marketing để xem cảnh báo CDC xuất hiện trực tiếp."
    )


if __name__ == "__main__":
    run()
