"""Kịch bản CDC 3: Operations Manager - Điểm nóng Boom COD & Ùn tắc khâu đóng gói.

Mô phỏng:
1. Bùng phát shipper báo giao thất bại (Boom hàng COD) tại khu vực Bình Tân đạt tỷ lệ bất thường (>30%).
2. Ùn tắc đơn chờ xuất kho quá 2 giờ (Fulfillment Bottleneck Alarm).
"""

import uuid
from datetime import timedelta

from app.db.session import SessionLocal
from app.models.customer import Customer
from app.models.logistics import DeliveryStaff, Shipment
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
        title="KỊCH BẢN CDC 3: OPERATIONS - BOOM HÀNG COD & ÙN TẮC ĐÓNG GÓI",
        role="Operations Manager (operations@fashion.local)",
        url="http://localhost:3000/admin/analytics?role=operations",
    )

    with SessionLocal() as session:
        # --- BƯỚC 1: BÙNG PHÁT BOOM HÀNG TẠI BÌNH TÂN ---
        print_step(1, "Shipper đồng loạt cập nhật giao thất bại cho các đơn COD khu vực Bình Tân")
        staff = session.scalar(select(DeliveryStaff).where(DeliveryStaff.is_active == True).limit(1))
        cust = session.scalar(select(Customer).where(Customer.role == "customer").limit(1))

        if staff and cust:
            # Tạo 4 đơn hàng COD mới tại Quận Bình Tân và chuyển ngay sang thất bại
            for i in range(4):
                order_num = f"ORD-CDC-BT-{uuid.uuid4().hex[:6].upper()}"
                new_order = Order(
                    order_number=order_num,
                    customer_id=cust.customer_id,
                    checkout_idempotency_key=str(uuid.uuid4()),
                    channel="online",
                    status="failed_delivery",
                    shipping_address_text="Số 45/12 Đường Tên Lửa, Phường An Lạc A, Quận Bình Tân, TP.HCM",
                    payment_method="cod",
                    subtotal_vnd=450000,
                    discount_amount_vnd=0,
                    shipping_fee_vnd=30000,
                    total_vnd=480000,
                    receiver_name="Khách Demo Bình Tân",
                    receiver_phone="0901234567",
                    created_at=utc_now() - timedelta(hours=3),
                )
                session.add(new_order)
                session.flush()

                shipment = Shipment(
                    public_id=uuid.uuid4(),
                    shipment_code=f"SHIP-BT-{uuid.uuid4().hex[:6].upper()}",
                    order_id=new_order.order_id,
                    delivery_staff_id=staff.staff_id,
                    status="failed",
                    attempt_count=3,
                    cod_amount_vnd=480000,
                    cod_collected_vnd=0,
                    failure_reason="Khách khóa máy không liên lạc được, nghi vấn địa chỉ ảo",
                    failed_at=utc_now(),
                    created_at=utc_now() - timedelta(hours=3),
                )
                session.add(shipment)

            session.commit()

            print_cdc_event(
                table="shipments",
                op="UPDATE",
                details="Cập nhật 4 đơn COD tại `Quận Bình Tân` ➔ status='failed', reason='Khách khóa máy'",
            )
            print_cdc_event(
                table="orders",
                op="UPDATE",
                details="Chuyển trạng thái 4 đơn hàng tương ứng ➔ status='failed_delivery'",
            )
            print_dashboard_impact(
                metric="Tỷ lệ Boom COD khu vực Bình Tân",
                before="Bình thường (<10%)",
                after="100.0% (Tất cả đơn giao đều thất bại)",
                alert="🚨 [CẢNH BÁO ĐỎ - HIGH ALERT] Điểm nóng boom hàng bất thường tại Bình Tân! Đề xuất hoãn xuất chuyến tiếp theo và yêu cầu CSKH gọi xác nhận lại 100%!",
            )

        # --- BƯỚC 2: ÙN TẮC ĐƠN HÀNG CHỜ ĐÓNG GÓI XUẤT KHO ---
        print_step(2, "Hàng loạt đơn hàng thanh toán thành công nhưng bị nghẽn chưa kịp đóng gói > 2 giờ")
        if cust:
            for i in range(25):
                stale_order = Order(
                    order_number=f"ORD-CDC-BOTTLENECK-{uuid.uuid4().hex[:6].upper()}",
                    customer_id=cust.customer_id,
                    checkout_idempotency_key=str(uuid.uuid4()),
                    channel="online",
                    status="paid",  # Đã thanh toán nhưng chưa có shipment
                    shipping_address_text="Giao tận nhà",
                    payment_method="vietqr",
                    subtotal_vnd=300000,
                    discount_amount_vnd=0,
                    shipping_fee_vnd=25000,
                    total_vnd=325000,
                    receiver_name="Khách Demo Bưu Cục",
                    receiver_phone="0912345678",
                    created_at=utc_now() - timedelta(hours=3, minutes=15),  # Quá 2 giờ
                )
                session.add(stale_order)
            session.commit()

            print_cdc_event(
                table="orders",
                op="INSERT",
                details="Ghi nhận 25 đơn hàng `status='paid'` phát sinh từ hơn 3 giờ trước",
            )
            print_dashboard_impact(
                metric="Hàng đợi đóng gói (Fulfillment Queue)",
                before="Bình thường",
                after="25+ đơn chờ xử lý quá 2 giờ (Chờ TB: 2.5 giờ)",
                alert="🚨 [CẢNH BÁO ÙN TẮC - BOTTLENECK] Có hơn 20 đơn trễ hạn đóng gói! Nguy cơ trễ giờ xe bưu cục gom hàng (Cut-off 17:00). Cần điều động nhân sự hỗ trợ gấp!",
            )

    print_success(
        "Kịch bản 3 hoàn tất! Mở trình duyệt tại tab Vận hành để quan sát tín hiệu CDC bùng phát ngay tức khắc."
    )


if __name__ == "__main__":
    run()
