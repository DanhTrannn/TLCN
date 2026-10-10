"""Script Reset: Khôi phục toàn bộ dữ liệu demo về trạng thái ban đầu sạch sẽ."""

from app.db.session import SessionLocal
from app.models.inventory import Inventory
from app.models.logistics import Shipment
from app.models.multicity import StoreInventory
from app.models.order import Order, OrderItem
from app.models.promotion import Coupon, CouponRedemption
from app.models.review import ProductReview
from demo.scenarios.base import (
    C_BOLD,
    C_GREEN,
    C_RESET,
    C_YELLOW,
    print_step,
    print_success,
)
from sqlalchemy import delete, select, update


def run() -> None:
    print(f"\n{C_BOLD}{C_YELLOW}🔄 ĐANG KHÔI PHỤC DỮ LIỆU DEMO VỀ TRẠNG THÁI GỐC...{C_RESET}\n")

    with SessionLocal() as session:
        # 1. Xóa các review giả lập TRƯỚC để tránh lỗi Foreign Key
        print_step(1, "Dọn dẹp các đánh giá tiêu cực giả lập...")
        del_reviews = session.execute(
            delete(ProductReview).where(
                (ProductReview.content.like("[DEMO CDC]%"))
                | (ProductReview.content.like("%Vải mỏng%"))
                | (ProductReview.content.like("%Màu thực tế%"))
                | (ProductReview.content.like("%Giao sai mẫu%"))
            )
        ).rowcount
        print(f"  {C_GREEN}✔ Đã xóa {del_reviews} đánh giá tiêu cực giả lập.{C_RESET}")

        # 2. Xóa các đơn hàng demo và các bảng phụ thuộc
        print_step(2, "Dọn dẹp các đơn hàng giả lập demo và shipments liên quan...")
        demo_order_ids = session.scalars(
            select(Order.order_id).where(
                (Order.order_number.like("ORD-CDC-%"))
                | (Order.order_number.like("ORD-DEMO-BT-%"))
                | (Order.order_number.like("ORD-BOTTLENECK-%"))
                | (Order.order_number.like("POS-RUSH-%"))
                | (Order.order_number.like("ORD-VIRAL-%"))
                | (Order.order_number.like("ORD-CIT-%"))
            )
        ).all()

        if demo_order_ids:
            session.execute(delete(Shipment).where(Shipment.order_id.in_(demo_order_ids)))
            session.execute(delete(OrderItem).where(OrderItem.order_id.in_(demo_order_ids)))
            session.execute(delete(CouponRedemption).where(CouponRedemption.order_id.in_(demo_order_ids)))
            session.execute(delete(Order).where(Order.order_id.in_(demo_order_ids)))
            print(f"  {C_GREEN}✔ Đã xóa {len(demo_order_ids)} đơn hàng giả lập và liên kết liên quan.{C_RESET}")
        else:
            print(f"  {C_GREEN}✔ Không có đơn hàng demo nào tồn đọng.{C_RESET}")

        # 3. Khôi phục voucher usage
        print_step(3, "Khôi phục ngân sách Voucher SALE50K...")
        coupon = session.scalar(select(Coupon).where(Coupon.code_normalized == "SALE50K"))
        if coupon:
            coupon.used_count = 150
            print(f"  {C_GREEN}✔ Đã đặt lại used_count mã SALE50K về 150/1000 (15.0% - Trạng thái an toàn).{C_RESET}")

        # 4. Khôi phục tồn kho kho tổng và cửa hàng
        print_step(4, "Khôi phục số lượng tồn kho an toàn cho Kho tổng và Cửa hàng...")
        session.execute(
            update(Inventory)
            .where(Inventory.on_hand <= 10)
            .values(on_hand=Inventory.opening_on_hand)
        )
        session.execute(
            update(StoreInventory)
            .where(StoreInventory.on_hand == 0)
            .values(on_hand=StoreInventory.opening_on_hand)
        )
        print(f"  {C_GREEN}✔ Đã hoàn nguyên tồn kho về opening_on_hand an toàn.{C_RESET}")

        session.commit()

    print_success("ĐÃ KHÔI PHỤC TOÀN BỘ DỮ LIỆU SẠCH SẼ! Hệ thống sẵn sàng cho lần trình diễn tiếp theo.")


if __name__ == "__main__":
    run()
