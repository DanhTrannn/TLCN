"""Kịch bản CDC 2: Inventory Manager - Tốc độ rút kho khẩn cấp & Cảnh báo Cháy hàng.

Mô phỏng:
1. Tồn kho một biến thể bán chạy bị rút cực nhanh, thời gian tồn còn dưới 5 phút (Depletion Velocity - Critical Alert).
2. Tồn kho chạm mốc 0, kích hoạt cơ chế chống bán vượt tồn (Overselling Prevention).
"""

from app.db.session import SessionLocal
from app.models.catalog import Product, ProductVariant
from app.models.inventory import Inventory
from demo.scenarios.base import (
    print_banner,
    print_cdc_event,
    print_dashboard_impact,
    print_step,
    print_success,
)
from sqlalchemy import desc, func, select


def run() -> None:
    print_banner(
        title="KỊCH BẢN CDC 2: INVENTORY - TỐC ĐỘ RÚT KHO & CHÁY HÀNG",
        role="Inventory Manager (inventory@fashion.local)",
        url="http://localhost:3000/admin/analytics?role=inventory",
    )

    with SessionLocal() as session:
        # --- BƯỚC 1: RÚT TỒN KHO MẪU ÁO HOT VỀ MỨC NGUY HIỂM ---
        print_step(1, "Khách đặt dồn dập, tốc độ rút kho biến thể bán chạy nhất tụt xuống mức khẩn cấp")
        target_inv = session.execute(
            select(Inventory, ProductVariant, Product)
            .join(ProductVariant, ProductVariant.variant_id == Inventory.variant_id)
            .join(Product, Product.product_id == ProductVariant.product_id)
            .where(ProductVariant.variant_id == 20)
        ).first()

        if not target_inv:
            target_inv = session.execute(
                select(Inventory, ProductVariant, Product)
                .join(ProductVariant, ProductVariant.variant_id == Inventory.variant_id)
                .join(Product, Product.product_id == ProductVariant.product_id)
                .where(Inventory.on_hand > 50)
                .limit(1)
            ).first()

        if target_inv:
            inv, variant, product = target_inv
            old_stock = inv.on_hand
            # Rút tồn kho xuống chỉ còn 8 chiếc
            inv.on_hand = 8
            session.commit()

            print_cdc_event(
                table="inventory",
                op="UPDATE",
                details=f"Biến thể `{variant.sku}`: on_hand giảm từ {old_stock} ➔ {inv.on_hand} chiếc",
            )
            print_dashboard_impact(
                metric=f"Vận tốc rút hàng `{variant.sku}`",
                before=f"Tồn kho {old_stock} (Dự kiến: ~56 phút)",
                after=f"Tồn kho {inv.on_hand} (Dự kiến cháy hàng trong 2 phút)",
                alert="🚨 [CẢNH BÁO ĐỎ - CRITICAL] Tốc độ rút hàng đạt ~3.5 sản phẩm/phút! Dự kiến cạn kho trong 2 phút! Yêu cầu phát lệnh khẩn cấp cho xưởng Inbound hoặc điều chuyển hàng gấp!",
            )

        # --- BƯỚC 2: CHÁY HÀNG CỤC BỘ (ON_HAND = 0) VÀ KÍCH HOẠT SOLD OUT ---
        print_step(2, "Một mã hàng bán hết sạch chiếc cuối cùng (on_hand = 0)")
        zero_target = session.execute(
            select(Inventory, ProductVariant, Product)
            .join(ProductVariant, ProductVariant.variant_id == Inventory.variant_id)
            .join(Product, Product.product_id == ProductVariant.product_id)
            .where(ProductVariant.variant_id == 22)
        ).first()

        if not zero_target:
            zero_target = session.execute(
                select(Inventory, ProductVariant, Product)
                .join(ProductVariant, ProductVariant.variant_id == Inventory.variant_id)
                .join(Product, Product.product_id == ProductVariant.product_id)
                .where(Inventory.on_hand > 0, Inventory.variant_id != (variant.variant_id if target_inv else 0))
                .limit(1)
            ).first()

        if zero_target:
            z_inv, z_var, z_prod = zero_target
            prev_on_hand = z_inv.on_hand
            z_inv.on_hand = 0
            session.commit()

            print_cdc_event(
                table="inventory",
                op="UPDATE",
                details=f"Biến thể `{z_var.sku}`: on_hand {prev_on_hand} ➔ 0 (CHÁY HÀNG TOÀN DIỆN)",
            )
            print_dashboard_impact(
                metric=f"Trạng thái tồn kho `{z_var.sku}`",
                before=f"Còn {prev_on_hand} chiếc",
                after="0 chiếc (SOLD OUT)",
                alert="🛡 [KÍCH HOẠT CHỐNG BÁN VƯỢT TỒN] Hệ thống tự động khóa nút 'Thêm vào giỏ', ngăn chặn tình trạng khách đặt hàng ảo không có hàng giao!",
            )

    print_success(
        "Kịch bản 2 hoàn tất! Mở trình duyệt tại tab Kho vận (Inventory) để xem radar tồn kho cập nhật ngay tức thì."
    )


if __name__ == "__main__":
    run()
