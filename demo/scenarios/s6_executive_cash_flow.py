"""Kịch bản CDC 6: Executive / CEO - Dòng tiền COD trôi nổi & Xói mòn biên lợi nhuận.

Mô phỏng:
1. Dòng tiền mặt thu hộ COD đang trôi nổi trên các chuyến xe giao hàng tăng vọt (Cash-in-Transit Tracking).
2. Xói mòn biên lợi nhuận gộp theo giờ trong ngày khuyến mãi (Intra-day Gross Margin Erosion).
"""

import uuid
from datetime import UTC, datetime, timedelta

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
        title="KỊCH BẢN CDC 6: EXECUTIVE - DÒNG TIỀN COD & XÓI MÒN LỢI NHUẬN",
        role="Ban Giám Đốc / CEO (admin@fashion.local)",
        url="http://localhost:3000/admin/analytics?role=executive",
    )

    with SessionLocal() as session:
        # --- BƯỚC 1: DÒNG TIỀN COD TRÔI NỔI TĂNG ĐỘT BIẾN ---
        print_step(1, "Hàng loạt kiện hàng COD giá trị lớn xuất kho giao cho shipper GHN và GHTK (+350 triệu)")
        staff = session.scalar(select(DeliveryStaff).where(DeliveryStaff.is_active == True).limit(1))
        cust = session.scalar(select(Customer).where(Customer.role == "customer").limit(1))

        if staff and cust:
            for i in range(5):
                val = 70000000  # 70 triệu đồng mỗi chuyến hàng lớn
                cit_order = Order(
                    order_number=f"ORD-CDC-CIT-{uuid.uuid4().hex[:6].upper()}",
                    customer_id=cust.customer_id,
                    checkout_idempotency_key=str(uuid.uuid4()),
                    channel="online",
                    status="shipping",
                    shipping_address_text="Giao hàng COD liên tỉnh",
                    payment_method="cod",
                    subtotal_vnd=val,
                    discount_amount_vnd=0,
                    shipping_fee_vnd=0,
                    total_vnd=val,
                    receiver_name=cust.display_name or "Khách Sỉ Toàn Quốc",
                    receiver_phone="0901234567",
                    created_at=utc_now(),
                )
                session.add(cit_order)
                session.flush()

                shipment = Shipment(
                    public_id=uuid.uuid4(),
                    shipment_code=f"SHIP-CIT-{uuid.uuid4().hex[:6].upper()}",
                    order_id=cit_order.order_id,
                    delivery_staff_id=staff.staff_id,
                    status="in_transit",
                    attempt_count=1,
                    cod_amount_vnd=val,
                    cod_collected_vnd=0,
                    dispatched_at=utc_now(),
                    created_at=utc_now(),
                )
                session.add(shipment)
            session.commit()

            print_cdc_event(
                table="shipments",
                op="INSERT",
                details="Ghi nhận 5 kiện hàng COD lớn chuyển trạng thái ➔ `in_transit` (+350,000,000 đ)",
            )
            print_dashboard_impact(
                metric="Tiền mặt COD đang trôi nổi (Cash in Transit)",
                before="340,120,000 đ (4 kiện hàng)",
                after="690,120,000 đ (9 kiện hàng)",
                alert="💰 [QUẢN TRỊ THANH KHOẢN] Hơn 690 triệu đồng tiền mặt COD đang lưu thông trên đường! CEO chủ động ấn định lịch đối soát tài khoản bưu cục vào 17h00 hàng ngày để bảo vệ dòng tiền.",
            )

        # --- BƯỚC 2: CẢNH BÁO XÓI MÒN BIÊN LỢI NHUẬN GỘP THEO GIỜ ---
        print_step(2, "Khách áp voucher dồn dập, tỷ suất lợi nhuận gộp theo giờ bị xói mòn")
        print_dashboard_impact(
            metric="Tỷ suất lợi nhuận gộp (Gross Margin %)",
            before="Đầu ngày: 77.3% (Biên an toàn)",
            after="Hiện tại: 71.6% (Xói mòn -5.7%)",
            alert="📉 [BẢO VỆ LỢI NHUẬN GỘP] Nhịp độ margin có dấu hiệu suy giảm khi khung giờ sale đạt đỉnh. CEO chỉ đạo Marketing hãm bớt mã giảm giá sâu trước khung giờ tối!",
        )

    print_success(
        "Kịch bản 6 hoàn tất! Mở trình duyệt tại tab Ban Giám Đốc để xem cập nhật dòng tiền và phân tích lợi nhuận."
    )


if __name__ == "__main__":
    run()
