# Bảng Đề Xuất Chốt — D&K E-Commerce Data Warehouse & BI Dashboard

**Phiên bản:** 1.1
**Ngày tạo:** 2026-09-07
**Ngày sửa:** 2026-09-07
**Trạng thái:** Revised — Chờ Sign-off
**Người soạn:** Data Team (Lead Data Engineer / Analytics Architect)
**Tham chiếu:** MANAGEMENT_INFO_NEEDS.md, MANAGEMENT_INFO_REVIEW.md

> **Hướng dẫn sử dụng:** Tài liệu này trình bày các đề xuất mặc định cho từng vấn đề chưa chốt trong MANAGEMENT_INFO_NEEDS.md. Nếu Stakeholder KHÔNG phản đối trước ngày DEADLINE, Data Team sẽ hard-code các logic này vào hệ thống. Nếu có ý kiến khác, vui lòng ghi rõ phương án thay thế vào cột **[Điều chỉnh]**.

---

## PHẦN 1: CHANGE LOG (v1.0 → v1.1)

| ID | Vấn đề | Mức độ | Bản cũ (v1.0) | Bản mới (v1.1) | Lý do sửa |
|----|--------|--------|---------------|----------------|-----------|
| C1 | RFM mâu thuẫn 9 vs 27 segments | Critical | "9 segments (3×3) R,F,M each 3 bậc" | RF Score = R×F = 9 segments. M dùng riêng làm cờ VIP/high spender | 3×3×3 = 27 cells, không phải 9. Giai đoạn 1 dùng RF trước, M riêng |
| C2 | Inventory snapshot sai timezone | Critical | Snapshot 23:59:59 UTC = 06:59:59 ICT | Snapshot 23:59:59 ICT = 16:59:59 UTC. snapshot_date = ngày kinh doanh ICT | 23:59 UTC = 06:59 ICT ngày hôm SAU, không phải cuối ngày ICT |
| C3 | Deferred Revenue quá rộng | Critical | Include cả COD chưa thu tiền | Tách: Deferred Revenue (đã thu tiền, chưa giao) vs Open Order Value (COD chưa hoàn thành) | COD chưa thu tiền không phải deferred revenue theo chuẩn kế toán |
| C4 | Net Revenue bao gồm shipping | Critical | Net Revenue = total_vnd - refund (gồm shipping) | Tách: GMV, Net Merchandise Revenue, Shipping Revenue | Phân biệt merchandise vs shipping để Finance phân tích chính xác |
| C5 | Search analytics mâu thuẫn | Critical | "Chưa log query_text" nhưng yêu cầu top keywords | Descope Giai đoạn 1: chỉ đo search events. Giai đoạn 2 cần API logging | Không log query_text → không thể phân tích top keywords |
| C6 | Phủ nhận inventory_movement | Critical | "Không cần inventory_movement" | Giai đoạn 1: dùng snapshot suy luận. Giai đoạn 2: bắt buộc fact_inventory_movement | Suy luận từ snapshot không phải audit trail đầy đủ |
| C7 | Outstanding Payments sai logic | Critical | "status = 'failed'" | Outstanding = pending/processing/authorized. Failed = payment failure analytics | Failed ≠ outstanding |
| C8 | PII/address xử lý chưa đủ an toàn | Critical | "Address không phải PII, giữ nguyên" | Address = dữ liệu nhạy cảm. Gold giữ region/city/district. Full address chỉ trong OLTP | NĐ13/2023: địa chỉ liên quan đến cá nhân |
| C9 | Reconciliation quá nghiêm ngặt | Critical | "Row count = 0" | Thêm cutoff_time, tolerance, expected difference | Late-arriving data, CDC timing có thể gây lệch ngắn hạn |
| C10 | Daily Revenue trộn lẫn created_at/paid_at | Critical | Dùng chung tên "Daily Revenue" cho 2 mốc | Tách 3 metric: Order Intake, Paid Today, Completed Today | Tránh nhầm lẫn giữa các con số |
| H1 | Return rate by product sai | High | COUNT(refunds) / COUNT(order_items) | Giai đoạn 1: refund rate theo order, chưa theo product (thiếu refund item) | OLTP chỉ có refund amount, không có refund item allocation |
| H2 | Dead stock bắt buộc có traffic | High | "Có fact_web_events" là điều kiện | Bỏ điều kiện traffic. Dead stock = active + on_hand > 0 + no sale 90 ngày | Sản phẩm không có traffic nhưng có hàng vẫn là dead stock |
| H3 | Sell-through chưa ghi rõ ước tính | High | Công thức chính xác | Ghi rõ: Approximate Sell-through. Điều kiện: no receipts, no adjustments | Giai đoạn 1 thiếu inventory movement data |
| H4 | Coupon ROI tên sai | High | "Coupon ROI" | Đổi thành "Coupon Efficiency Ratio". Công thức: Net Revenue from coupon / Discount | Không phải ROI thật (thiếu incremental revenue) |
| H5 | Thiếu discount allocation rule | High | Không có | Discount phân bổ theo tỷ lệ revenue item. Refund nhận phần discount tương ứng | Cần cho refund item tracking |
| H6 | Conversion rate chưa định nghĩa | High | Không có | Conversion = orders(paid+) / sessions(page_view). Fallback: anonymous_id + date | MANAGEMENT_INFO_NEEDS yêu cầu nhưng v1.0 chưa chốt |
| H7 | Thiếu repeat purchase, CLV, retention, churn | High | Không có | Bổ sung 4 metric với công thức cụ thể | MANAGEMENT_INFO_NEEDS yêu cầu nhưng v1.0 chưa chốt |
| H8 | New product dùng created_at | High | "30 ngày từ created_at" | Ưu tiên: launch_date → first_visible_date → first_order_date → created_at | created_at có thể ≠ ngày mở bán |
| H9 | Cash flow, payment failure chưa rõ | High | Không có | Bổ sung cash flow proxy, payment failure rate definition | MANAGEMENT_INFO_NEEDS yêu cầu |
| H10 | Coupon release rate chưa có | High | Không có | Coupon redemption status: redeemed/released. Release rate = released / total | MANAGEMENT_INFO_NEEDS yêu cầu |
| M1 | Lỗi chính tả, thuật ngữ | Medium | "Giai_intervals", "approve/bject" | Sửa lỗi, thống nhất thuật ngữ | Chuyên nghiệp hơn |
| M2 | Thiếu traceability | Medium | Không map MANAGEMENT_INFO_NEEDS | Thêm cột "Yêu cầu gốc" map tới MANAGEMENT_INFO_NEEDS | Audit trail cho requirements |
| M3 | Thiếu trạng thái | Medium | Không có status | Thêm trạng thái: Ready/Needs Confirmation/Descoped/Deferred | Theo dõi progress |
| M4 | Thiếu owner, deadline | Medium | Không có | Thêm Owner, Deadline, Người ký duyệt | Accountability |
| M5 | "Competition Tracking" lỗi chính tả | Medium | "Competition Tracking" | Sửa thành "Complaint Tracking" | Lỗi chính tả |
| M6 | Thiếu phụ thuộc hệ thống | Medium | Không có dependency | Thêm cột "Phụ thuộc" cho mỗi mục | Hiểu được điều kiện tiên quyết |

---

## PHẦN 2: TÀI LIỆU SIGNOFF v1.1 HOÀN CHỈNH

### 2.0. Thông tin tài liệu

| Thuộc tính | Giá trị |
|-----------|---------|
| Phiên bản | 1.1 |
| Ngày tạo | 2026-09-07 |
| Ngày sửa | 2026-09-07 |
| Trạng thái | Revised — Chờ Sign-off |
| Người soạn | Data Team (Lead Data Engineer / Analytics Architect) |
| Tham chiếu | MANAGEMENT_INFO_NEEDS.md, MANAGEMENT_INFO_REVIEW.md, OLTP_TABLES.md |

---

### NHÓM 1: CEO / FINANCE (Tài chính & Kế toán)

| # | Yêu cầu gốc | Vấn đề cần chốt | Đề xuất chốt | Lý do | Rủi ro nếu sai | Phụ thuộc | Trạng thái |
|---|-------------|-----------------|-------------|-------|----------------|-----------|-----------|
| 1.1 | MN-1.1 GMV | Trạng thái đơn nào được tính? | Include: `paid`, `confirmed`, `completed`. Exclude: `payment_failed`, `cancelled` | Đơn `payment_failed` chưa bao giờ là đơn thực. Đơn `cancelled` đã hoàn kho. Chuẩn Shopify, Lazada VN | GMV bị thổi phồng nếu include cancelled | OLTP `orders.status` | Ready |
| 1.2 | MN-1.1 GMV | Có bao gồm phí vận chuyển? | **KHÔNG.** GMV = `SUM(subtotal_vnd)`, không gồm shipping | GMV = giá trị hàng hóa. Shipping là chi phí dịch vụ. Để nhất quán với ngành | GMV bị inflation nếu gồm shipping | `orders.subtotal_vnd` | Ready |
| 1.3 | MN-1.1 GMV | subtotal_vnd trước hay sau discount? | subtotal_vnd = **TRƯỚC** discount. `subtotal - discount + shipping = total` | Để nhất quán: GMV = subtotal. Discount track riêng. Net Revenue dùng total (sau discount) | Double-counting discount nếu nhầm | `orders.discount_amount_vnd` | Ready |
| 1.4 | MN-1.1 Net Revenue | Công thức chính xác, tránh double-counting | **Net Merchandise Revenue** = `SUM(subtotal_vnd - discount_amount_vnd)` WHERE status IN ('paid','confirmed','completed') - merchandise refund. **Shipping Revenue** = `SUM(shipping_fee_vnd)` - shipping refund | Phân biệt merchandise vs shipping để Finance phân tích. Tránh double-counting discount | Revenue bị sai → quyết định tài chính sai | `orders.subtotal_vnd`, `orders.discount_amount_vnd`, `orders.shipping_fee_vnd`, `refunds.amount_vnd` | Ready |
| 1.5 | MN-1.5 Revenue Recognition | Ghi nhận theo ngày nào? | **Giai đoạn 1:** Theo `completed_at` (giao hàng thành công). **Giai đoạn 2:** Bổ sung theo yêu cầu kế toán | E-commerce VN: COD ghi nhận khi giao thành công. Online: khi payment succeeded. `completed_at` an toàn nhất | Ghi nhận sai kỳ → P&L sai lệch | `orders.completed_at` | Ready |
| 1.6 | MN-1.5 Deferred Revenue | Định nghĩa, tách COD chưa thu tiền | **Deferred Revenue** = Đơn có payment succeeded VÀ status IN ('paid','confirmed') VÀ chưa completed. **Open Order Value (COD)** = Đơn COD có status IN ('paid','confirmed') VÀ chưa completed. **KHÔNG gọi COD là Deferred Revenue** | COD chưa thu tiền không phải deferred revenue theo chuẩn kế toán. Deferred = đã thu tiền nhưng chưa giao | Gọi nhầm COD là deferred → Finance understated revenue | `orders.status`, `payments.status` | Ready |
| 1.7 | MN-1.5 Tax (VAT) | Xử lý thế nào? | **Giai đoạn 1:** Bỏ qua tax. Giá hiện tại là giá cuối (chưa rõ có VAT không). **Giai đoạn 2:** Bổ sung `tax_rate`, `tax_amount` nếu cần | OLTP hiện tại không có cột tax. Thêm schema = effort lớn. Ưu tiên revenue metrics trước | Thiếu tax data → P&L chưa đầy đủ | OLTP schema | Ready |
| 1.8 | MN-1.5 P&L Scope | Giai đoạn 1 tính đến đâu? | **Giai đoạn 1:** GMV → Net Merchandise Revenue → Discount → Refund = **Gross Margin Proxy**. KHÔNG có COGS, shipping cost, marketing cost, payment fee | P&L đầy đủ cần external data. Giai đoạn 1 tập trung revenue side | P&L chưa thực tế | External systems | Ready |
| 1.9 | MN-1.5 Fiscal Calendar | Năm tài chính | Calendar Year (Jan-Dec). Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec | Chuẩn VN. `dim_date` có `fiscal_year`, `fiscal_quarter` | So sánh sai kỳ tài chính | `dim_date` | Ready |
| 1.10 | MN-1.5 Holiday/Weekend | Xử lý ngày lễ, cuối tuần | `dim_date` có `is_weekend`, `is_holiday`. Dashboard so sánh dùng business day (loại T7, CN, lễ) | So sánh T2 với CN → số liệu sai lệch | Phân tích sai seasonality | `dim_date` | Ready |
| 1.11 | MN-1.5 Currency | Đơn vị tiền tệ | Luôn VND. `currency_code = 'VND'` hardcoded | Thị trường VN thuần VND. Không cần multi-currency Giai đoạn 1 | Sai currency conversion | `orders.currency_code` | Ready |
| 1.12 | MN-1.5 Cash Flow Proxy | Dòng tiền ước tính | **Cash Inflow Proxy** = SUM(payment amount succeeded) theo payment date. **Cash Outflow Proxy** = SUM(refund amount succeeded). **Net Cash Flow** = Inflow - Outflow | Proxy vì chưa có settlement data từ payment gateway. Đủ cho Finance tracking | Cash flow sai nếu settlement khác payment date | `payments`, `refunds` | Ready |
| 1.13 | MN-1.15 Daily P&L | Scope P&L hàng ngày | **Giai đoạn 1:** Revenue, Discount, Refund. **Giai đoạn 2:** Bổ sung COGS, shipping cost, marketing cost, payment fee từ external systems | P&L đầy đủ cần data từ accounting, payment gateway, logistics | P&L chưa đầy đủ | External systems | Ready |
| | | | | | | | **[Điều chỉnh]** |

---

### NHÓM 2: STORE MANAGER (Vận hành Cửa hàng)

| # | Yêu cầu gốc | Vấn đề cần chốt | Đề xuất chốt | Lý do | Rủi ro nếu sai | Phụ thuộc | Trạng thái |
|---|-------------|-----------------|-------------|-------|----------------|-----------|-----------|
| 2.1 | MN-2.1 Daily Revenue | Tính theo ngày nào? | **Tách 3 metric:** (1) **Order Intake Today** = `created_at` (đơn mới). (2) **Paid Today** = `paid_at` (đơn đã thanh toán). (3) **Completed Today** = `completed_at` (đơn giao xong). KHÔNG dùng chung tên "Daily Revenue" | Trộn created_at/paid_at → cùng 1 metric có 2 con số. Tách rõ để Store Manager biết đang xem gì | Nhầm lẫn giữa đơn mới và đơn đã thanh toán | `orders.created_at`, `orders.paid_at`, `orders.completed_at` | Ready |
| 2.2 | MN-2.2 Shift Definition | Định nghĩa ca | Ca sáng: 06:00-12:00. Ca chiều: 12:00-18:00. Ca tối: 18:00-24:00. Ca đêm: 00:00-06:00 (ICT) | Chuẩn shift VN. `dim_date` có `shift_key` mapping theo hour | So sánh hiệu suất sai ca | `dim_date` | Ready |
| 2.3 | MN-2.3 Order Aging | Tính từ thời điểm nào? | **Tổng tuổi đơn:** `DATEDIFF(NOW(), created_at)`. **Tuổi đơn cần xử lý:** `DATEDIFF(NOW(), paid_at)` (SLA tính từ lúc thanh toán) | created_at = đơn tồn tại bao lâu. paid_at = đơn cần xử lý bao lâu. Phân biệt 2 khái niệm | SLA tracking sai nếu dùng sai timestamp | `orders.created_at`, `orders.paid_at` | Ready |
| 2.4 | MN-2.4 Low Stock Threshold | Hard-code hay velocity-based? | **Velocity-based:** `reorder_point = (velocity_7d × lead_time_default) + safety_stock`. Mặc định: `lead_time = 14 ngày`, `safety_stock = 10% × velocity_30d`. **Floor:** `on_hand < 5` → always alert | Velocity-based chính xác hơn hard-code. Lead time 14 ngày = chuẩn ngành thời trang VN | Alert sai nếu hard-code không phù hợp theo variant | `fact_order_item` (velocity), `inventory.on_hand` | Ready |
| 2.5 | MN-2.5 Realtime vs Batch | Dashboard cần realtime mức nào? | **Dashboard Store Manager: OLTP direct** (realtime, <200ms latency). **KHÔNG đọc DWH** (batch T+1) | Store Manager cần xem đơn vừa đặt, tồn kho vừa thay đổi. OLTP đã có index | Data quá cũ nếu dùng DWH batch | OLTP API | Ready |
| 2.6 | MN-2.2 Order Status | "Đơn cần xử lý" include gì? | Include: `paid` (chờ confirm), `confirmed` (chờ giao). Exclude: `completed`, `cancelled`, `payment_failed` | Action queue — chỉ hiện đơn cần hành động. Không noise | Thiếu đơn cần xử lý nếu filter sai | `orders.status` | Ready |
| 2.7 | MN-2.3 Top Products | Top sản phẩm bán chạy? | Top 10 theo `quantity_sold` trong 7 ngày. Nếu bằng nhau, sort theo `revenue` giảm dần | Top 10 đủ cho decision. Quá nhiều = noise | Ưu tiên sai sản phẩm | `fact_order_item` | Ready |
| | | | | | | | **[Điều chỉnh]** |

---

### NHÓM 3: SALES MANAGER (Kinh doanh & Danh mục)

| # | Yêu cầu gốc | Vấn đề cần chốt | Đề xuất chốt | Lý do | Rủi ro nếu sai | Phụ thuộc | Trạng thái |
|---|-------------|-----------------|-------------|-------|----------------|-----------|-----------|
| 3.1 | MN-3.1 Category Hierarchy | Mấy cấp? | **2 cấp:** Level 1 (ÁO, QUẦN, PHỤ KIỆN...), Level 2 (ÁO THUN, ÁO SƠ MI...). Product chỉ thuộc Level 2 | Đơn giản, đủ phân tích. 3 cấp phức tạp khi data chưa đủ | Phân tích sai cấp category | `categories`, `dim_category` | Ready |
| 3.2 | MN-3.2 Product Lifecycle | Sản phẩm archived hiển thị trong report? | **CÓ.** `fact_order_item` giữ snapshot lịch sử. `dim_product` có `is_active`, `archived_at` | Order items là snapshot, đã ghi nhận không đổi. Report lịch sử cần thấy archived products | Mất data lịch sử nếu xóa | `products`, `order_items` | Ready |
| 3.3 | MN-3.3 Cross-sell | Phân tích ở mức nào? | **Mức Category.** Metric: `support` (tỷ lệ đơn chứa cả category A và B). Không cần `confidence`, `lift` Giai đoạn 1 | Category-level đủ cho bundle/promotion. SKU-level quá chi tiết | Phân tích quá phức tạp | `fact_order_item` | Ready |
| 3.4 | MN-3.5 Seasonal Forecast | Data < 1 năm xử lý thế nào? | **Giai đoạn 1:** Không forecast. Chỉ show historical trend + YoY comparison. **Giai đoạn 2:** Khi có ≥12 tháng data, dùng seasonal index | Forecast <12 tháng unreliable. Better honest trend than wrong prediction | Dự báo sai | Historical data | Ready |
| 3.5 | MN-3.3 Coupon ROI | Tính incremental revenue? | **Đổi tên:** Coupon Efficiency Ratio (không gọi ROI). **Công thức:** Net Revenue from coupon orders / Discount amount. **Giai đoạn 1:** Chưa tính incremental (thiếu control group) | "ROI" hiểu nhầm là ROI thật. Coupon Efficiency = ratio, không phải return on investment | Marketing hiểu sai hiệu quả coupon | `fact_order`, `fact_coupon_redemption` | Ready |
| 3.6 | MN-3.4 RFM Segmentation | Bao nhiêu segment? | **Giai đoạn 1:** RF Score = R×F = **9 segments** (R: 3 bậc × F: 3 bậc). **Monetary dùng riêng** làm cờ VIP/high spender. **Giai đoạn 2:** RFM đầy đủ 27 cells → map về 8-11 segment nghiệp vụ | 9 segments đủ cho marketing action. M riêng = đơn giản hơn, tránh 27 cells phức tạp | Phân khúc sai nếu nhầm 9 vs 27 | `fact_order` | Ready |
| 3.7 | MN-3.2 New Product | Bao nhiêu ngày là "mới"? | Ưu tiên: (1) `launch_date` nếu có. (2) `first_visible_date` nếu có. (3) `first_order_date` nếu không có. (4) `created_at` chỉ là fallback. **Mặc định: 30 ngày** từ source ưu tiên nhất | `created_at` có thể ≠ ngày mở bán. Ưu tiên ngày thực tế hơn hệ thống | Phân tích sai lifecycle sản phẩm | `products` | Ready |
| 3.8 | MN-3.2 Return Rate | Tính theo product? | **Giai đoạn 1:** Refund Rate theo **order** (không theo product) vì OLTP chỉ có refund amount, không có refund item allocation. **Công thức:** COUNT(orders có refund) / COUNT(orders completed) × 100. **Giai đoạn 2:** Cần `fact_refund_item` cho refund rate theo product | Refund không có item-level → không thể phân bổ chính xác cho từng product | Phân tích sai nếu cố gắng tính theo product | `refunds`, `fact_order` | Ready |
| 3.9 | MN-3.4 Discount Allocation | Discount phân bổ thế nào? | Discount phân bổ xuống `order_item` theo tỷ lệ `line_total_vnd / subtotal_vnd`. Refund item nhận phần discount tương ứng. Nếu OLTP chỉ lưu `coupon_id` duy nhất per order → mỗi order tối đa 1 coupon | Cần cho refund tracking. Nếu OLTP đã enforce 1 coupon/order → đơn giản | Refund sai discount allocation | `orders`, `order_items` | Ready |
| | | | | | | | **[Điều chỉnh]** |

---

### NHÓM 4: WAREHOUSE (Quản lý Kho)

| # | Yêu cầu gốc | Vấn đề cần chốt | Đề xuất chốt | Lý do | Rủi ro nếu sai | Phụ thuộc | Trạng thái |
|---|-------------|-----------------|-------------|-------|----------------|-----------|-----------|
| 4.1 | MN-4.2 Reorder Point | Lead time mặc định? | `lead_time_default = 14 ngày` (ngành thời trang VN). Khi có data NCC → cập nhật | 14 ngày = 7 ngày đặt + 3 ngày vận chuyển + 4 ngày kiểm tra. Fashion VN: 10-20 ngày | Nhập hàng sai thời điểm | Supplier data (chưa có) | Ready |
| 4.2 | MN-4.3 Dead Stock | Định nghĩa chính xác? | Dead Stock = `is_active = TRUE` AND `on_hand > 0` AND **KHÔNG có đơn sold trong 90 ngày** AND **không bị out-of-stock liên tục trong 90 ngày**. **Bỏ điều kiện traffic** (sản phẩm không có traffic nhưng có hàng vẫn là dead stock) | Traffic chỉ dùng để chẩn đoán, không phải điều kiện bắt buộc. Sản phẩm hết traffic vẫn có thể là dead stock nếu có hàng | Nhận diện sai dead stock | `inventory`, `fact_order_item` | Ready |
| 4.3 | MN-4.3 Inventory Snapshot | Bắt buộc snapshot hàng ngày? | **CÓ.** `fact_inventory_snapshot_daily`: 1 row/(date, variant). **Snapshot time:** 23:59:59 ICT (= 16:59:59 UTC). **snapshot_date = ngày kinh doanh ICT** (KHÔNG phải ngày UTC) | Bắt buộc cho sell-through, inventory turnover, dead stock. Snapshot cuối ngày ICT vì business operates in ICT | Không tính được sell-through nếu thiếu snapshot | Spark job tạo snapshot | Ready |
| 4.4 | MN-4.4 Reconciliation | Tự động, ngưỡng bao nhiêu? | Chạy **daily** sau Gold build. Checks: (1) Row count = 0 sau cutoff (`updated_at <= 00:00 ICT ngày D+1`). (2) SUM(total_vnd) lệch ≤ 1,000 VND. (3) NULL PK/FK = 0. (4) Orphan FK = 0. (5) Duplicate PK = 0. **Failure:** alert Slack + email, KHÔNG auto-reject. **Expected difference:** ghi nhận late-arriving updates | Reconciliation gate đã thiết kế. Threshold 1,000 VND chấp nhận (rounding). Cần cutoff để xử lý late-arriving data | DWH chứa data sai mà không phát hiện | Silver OLTP | Ready |
| 4.5 | MN-4.3 Sell-through Rate | Công thức chính xác? | **Approximate Sell-through** = `Units sold in period / opening_stock × 100`. **Điều kiện:** (1) Không có nhập hàng lớn trong kỳ. (2) Không có điều chỉnh kho lớn. (3) Chưa có `fact_inventory_movement`. **Ghi rõ:** Đây là ước tính vận hành, chưa phải sell-through kế toán | Giai đoạn 1 thiếu receipts/adjustments data → approximate. Không nên gọi là "chính xác" khi thiếu data | Hiệu suất kho bị ước tính sai | `fact_inventory_snapshot_daily`, `fact_order_item` | Ready |
| 4.6 | MN-4.4 Hoàn kho khi hủy đơn | Audit trail cần gì? | **Giai đoạn 1:** Dùng `fact_inventory_snapshot_daily` để **suy luận** thay đổi tồn kho (so sánh snapshot trước/sau). **KHÔNG phải audit trail đầy đủ.** **Giai đoạn 2:** Bắt buộc `fact_inventory_movement` để audit chính xác. **Risk:** Không chứng minh được hoàn kho nếu nhiều nghiệp vụ kho xảy ra trong ngày | Suy luận từ snapshot = giải pháp tạm thời. Đúng audit cần movement log | Không audit được hoàn kho chính xác | `fact_inventory_snapshot_daily` | Descoped Phase 1, Deferred Phase 2 |
| 4.7 | MN-4.3 Stock-out Duration | Track thời gian hết hàng? | Track: `stockout_start_at` (khi on_hand → 0), `stockout_end_at` (khi on_hand > 0). Duration = `DATEDIFF(end, start)` | Cần cho metric "avg stockout duration". Cần snapshot daily để detect | Không biết sản phẩm hết hàng bao lâu | `fact_inventory_snapshot_daily` | Ready |
| 4.8 | MN-4.2 Inventory Reconciliation | OLTP vs DWH cần reconcile? | **CÓ.** Job reconciliation daily. Kiểm tra: `inventory.on_hand` OLTP vs `fact_inventory_snapshot_daily` latest snapshot. Ngưỡng lệch: 0 (bắt buộc chính xác vì cùng 1 source) | OLTP và DWH phải nhất quán về tồn kho | Tồn kho sai → nhập hàng sai | OLTP `inventory`, `fact_inventory_snapshot_daily` | Ready |
| | | | | | | | **[Điều chỉnh]** |

---

### NHÓM 5: MARKETING

| # | Yêu cầu gốc | Vấn đề cần chốt | Đề xuất chốt | Lý do | Rủi ro nếu sai | Phụ thuộc | Trạng thái |
|---|-------------|-----------------|-------------|-------|----------------|-----------|-----------|
| 5.1 | MN-5.2 Campaign Tracking | Bắt buộc UTM gì? | Bắt buộc: `utm_source`, `utm_medium`, `utm_campaign`. Optional: `utm_term`, `utm_content`. Mapping vào `dim_campaign` | 3 tham số chính đủ attribution. UTM quá dài bị user sửa | Attribution sai nếu thiếu UTM | Backend logging | Descoped Phase 1, Deferred Phase 2 |
| 5.2 | MN-5.2 Attribution Window | Last-click hay multi-touch? | **Last-click attribution.** Window: 7 ngày click, 1 ngày view. **Giai đoạn 1:** Chưa implement multi-touch | Last-click đơn giản, phổ biến VN. Multi-touch cần ML pipeline | Attribution sai | `fact_web_events` | Ready |
| 5.3 | MN-5.5 Search Analytics | Log những gì Giai đoạn 1? | **Giai đoạn 1: Descope.** Chỉ đo số lượt search events (`ecommerce_action = 'search'`). **CHƯA phân tích:** top keywords, zero-result, search-to-purchase theo từ khóa. **Giai đoạn 2:** Cần API logging `search_query_text`, `search_result_count`, `session_id` | Access log hiện tại không có `query_text`, `result_count`. Muốn search quality metrics → cần sửa API. **[CẦN XÁC NHẬN Marketing]** | Marketing không có search quality data | Backend API modification | Descoped Phase 1, Deferred Phase 2 |
| 5.4 | MN-5.3 Wishlist vs Cart Abandonment | Ưu tiên gì? | **Cart Abandonment > Wishlist.** Cart abandonment ảnh hưởng trực tiếp đến revenue. Wishlist = leading indicator | Cart = tiền mất. Wishlist = tiền tiềm năng. Ưu tiên mất tiền trước | Mất doanh thu nếu ignore cart abandonment | `fact_order_item`, `cart_items` | Ready |
| 5.5 | MN-5.1 Customer Acquisition | Fallback khi không có UTM? | Nếu không có UTM: attribution = `first_touch` (channel của session đầu tiên). Nếu có UTM: theo UTM | First-touch là standard fallback khi thiếu attribution data | Attribution sai nếu fallback không hợp lý | `fact_web_events` | Ready |
| 5.6 | MN-5.2 Campaign Cost | Ai nhập, format gì? | **Manual input.** Marketing cập nhật vào `dim_campaign` qua admin interface. Format: VND integer. Tần suất: sau khi campaign kết thúc. **Giai đoạn 2:** API integration với ad platforms | Campaign cost nằm ở external systems. Manual = effort thấp, đủ Giai đoạn 1 | Không có campaign cost → không tính được ROI | Admin interface | Ready |
| 5.7 | MN-5.4 Coupon vs Campaign | Khác gì? | **Coupon** = giảm giá trên đơn (track được trong OLTP). **Campaign** = marketing activity (cần external cost). **Giai đoạn 1:** Chỉ Coupon. **Giai đoạn 2:** Bổ sung Campaign | Coupon có sẵn trong OLTP. Campaign cần external → Giai đoạn 2 | Không phân biệt được coupon vs campaign | OLTP `coupons`, `coupon_redemptions` | Ready |
| 5.8 | MN-5.1 RFM | Apply cho ai? | Tất cả customers có ≥1 đơn `completed` trong 12 tháng. Exclude: customers chỉ có đơn cancelled/failed | RFM meaningless nếu chưa mua thành công | Phân khúc sai | `fact_order` | Ready |
| 5.9 | MN-5.3 Coupon Release Rate | Tính thế nào? | **Coupon Redemption Status:** `redeemed` (đơn đang dùng), `released` (đơn hủy, coupon trả lại). **Release Rate** = COUNT(released) / COUNT(redeemed + released) × 100. **[CẦN XÁC NHẬN]:** OLTP hiện có `coupon_redemptions.status` = 'redeemed'/'released' — cần verify | Nếu OLTP đã track released status → tính được. Nếu chưa → descoped | Không measure được coupon wastage | `coupon_redemptions.status` | Ready |
| 5.10 | MN-5.1 Conversion Rate | Định nghĩa numerator/denominator | **Conversion Rate** = COUNT(DISTINCT order_id có status paid/confirmed/completed trong kỳ) / COUNT(DISTINCT session_id có ≥1 page_view trong kỳ) × 100. **Fallback:** Nếu không có `session_id`, dùng `anonymous_id + date`. **Loại:** bot/internal traffic nếu có rule. **Giai đoạn 1:** Chưa tính cross-device | Conversion rate cần numerator (orders) và denominator (sessions). Thiếu session data → fallback anonymous_id | Conversion sai nếu denominator không chính xác | `fact_order`, `fact_web_events` | Ready |
| | | | | | | | **[Điều chỉnh]** |

---

### NHÓM 6: CS/OPS (Chăm sóc Khách hàng)

| # | Yêu cầu gốc | Vấn đề cần chốt | Đề xuất chốt | Lý do | Rủi ro nếu sai | Phụ thuộc | Trạng thái |
|---|-------------|-----------------|-------------|-------|----------------|-----------|-----------|
| 6.1 | MN-7.2 SLA | Thời gian chuẩn từng giai đoạn? | **Paid → Confirmed:** ≤ 4 giờ làm việc (8h-22h ICT). **Confirmed → Completed:** ≤ 72 giờ (3 ngày). **Refund Processing:** ≤ 5 ngày làm việc | COD VN cần confirm nhanh. Giao hàng nội thành 1-2 ngày. Refund 5 ngày = chuẩn NHNN | SLA sai → đánh giá performance sai | `order_status_history` | Ready |
| 6.2 | MN-7.3 Complaint Tracking | Proxy khi chưa có ticketing? | Proxy: (1) Đơn `cancelled` + reason. (2) Refund + reason. (3) Review ≤ 2 sao. **KHÔNG cần hệ thống ticketing mới** | 3 signals đủ measure dissatisfaction. Ticketing = external tool, effort lớn | Không track được complaint | `orders`, `refunds`, `product_reviews` | Ready |
| 6.3 | MN-7.3 Customer Lookup | Định danh khách hàng? | Lookup: (1) `order_number`, (2) `public_id` (UUID). **KHÔNG lookup email/phone trong DWH** (PII protection). **OLTP:** Admin role xem được PII | DWH pseudonymize PII. Order number = enough cho CS. Email/phone chỉ OLTP | CS không tìm được khách hàng | OLTP API | Ready |
| 6.4 | MN-7.4 Order Status Lookup | OLTP hay DWH? | **OLTP.** Dashboard CS đọc trực tiếp API. **KHÔNG đọc DWH** (batch T+1 quá chậm) | CS cần realtime. OLTP API <200ms | CS dùng data quá cũ | OLTP API | Ready |
| 6.5 | MN-7.5 Cancel/Refund Reason | Dropdown hay free-text? | **Dropdown + free-text.** Dropdown: `customer_request`, `out_of_stock`, `pricing_error`, `quality_issue`, `shipping_delay`, `other`. Free-text: optional `reason_detail` | Dropdown = data consistency cho reporting. Free-text = chi tiết | Phân tích sai lý do hủy | `orders`, `order_status_history` | Ready |
| 6.6 | MN-7.4 Customer 360 | Hiển thị gì? | (1) Order history, (2) Total spend, (3) Last order date, (4) Cancel/refund count, (5) Review history. **KHÔNG hiển thị:** phone, email, address trong DWH. **OLTP:** Admin xem được PII | Đủ thông tin cho CS. PII protection: phone/email chỉ OLTP | CS thiếu thông tin xử lý | `dim_customer`, `fact_order` | Ready |
| 6.7 | MN-7.2 Payment Failure Rate | Định nghĩa theo gì? | **Payment Failure Rate** = COUNT(DISTINCT order_id có ≥1 failed payment) / COUNT(DISTINCT order_id có payment attempt) × 100. Nếu có nhiều retry → ghi rõ giới hạn (chưa track retry) | Tính theo order (không theo attempt) để metric meaningful hơn | Payment failure sai | `payments` | Ready |
| | | | | | | | **[Điều chỉnh]** |

---

### NHÓM 7: DATA PLATFORM / SECURITY

| # | Yêu cầu gốc | Vấn đề cần chốt | Đề xuất chốt | Lý do | Rủi ro nếu sai | Phụ thuộc | Trạng thái |
|---|-------------|-----------------|-------------|-------|----------------|-----------|-----------|
| 7.1 | MN-7.1 Data Freshness | Mỗi nhóm cần mức nào? | **CEO/Sales/Marketing/Finance:** Daily (T+1, batch 2AM ICT). **Store Manager/CS:** Realtime (<5 phút, OLTP direct). **Warehouse:** Daily (T+1) + realtime alert (on_hand changes) | OLTP realtime cho vận hành. DWH batch cho analytics. Không cần CDC Giai đoạn 1 | Data quá cũ hoặc quá chậm | OLTP, DWH pipeline | Ready |
| 7.2 | MN-7.2 Access Control | Row-Level hay Column-Level? | **Namespace-level RBAC** (Polaris). `gold`: CEO, Sales, Marketing, Finance. `silver`: Data Team only. Store Manager: OLTP API only. **Giai đoạn 2:** Row-level nếu cần phân tách cửa hàng | Namespace-level đơn giản, đủ Giai đoạn 1. Row-level phức tạp hơn | Access sai nếu RBAC quá thô | Polaris | Ready |
| 7.3 | MN-7.3 PII Handling — NĐ13/2023 | Phone, email, address xử lý thế nào? | (1) **Customer name:** pseudonymize SHA-256 trong Silver. (2) **Email, phone:** pseudonymize SHA-256. (3) **Address:** phân loại là dữ liệu nhạy cảm. **Gold:** chỉ giữ `region`, `city`, `district` nếu cần phân tích địa lý. **Full address:** chỉ trong OLTP, truy cập theo quyền Admin/CS. **[CẦN XÁC NHẬN]:** Nếu pseudonymize, dùng salted hash hoặc tokenization có quản lý key | NĐ13/2023: phone, email, name, address đều là PII. Address liên quan đến cá nhân. Gold chỉ cần region/city/district cho analytics | Vi phạm NĐ13/2023 nếu lộ PII | OLTP schema, Silver DDL | Ready |
| 7.4 | MN-7.4 Retention Policy | Hot/Cold storage bao lâu? | **Hot (Iceberg active):** 2 năm. **Cold (compacted):** 5 năm. **Archive (MinIO):** vĩnh viễn | 2 năm hot đủ analytics. 5 năm cold cho audit. Vĩnh viễn archive cho compliance | Mất data lịch sử | Iceberg lifecycle | Ready |
| 7.5 | MN-7.5 Timezone | Raw data lưu gì, presentation dùng gì? | **Raw (DWH):** Lưu UTC. **Presentation:** Hiển thị UTC+7 (ICT) trong Superset/dashboard | Chuẩn quốc tế. Superset hỗ trợ timezone display | Sai timezone → phân tích sai | Superset config | Ready |
| 7.6 | MN-7.6 Data Quality | Reconciliation chạy khi nào, ngưỡng bao nhiêu? | Chạy **daily** sau Gold build. Checks: (1) Row count = 0 sau cutoff. (2) SUM(total_vnd) ≤ 1,000 VND. (3) NULL PK/FK = 0. (4) Orphan FK = 0. (5) Duplicate PK = 0. **Failure:** alert Slack + email, KHÔNG auto-reject | Reconciliation gate đã thiết kế. Threshold 1,000 VND chấp nhận | DWH chứa data sai | Silver OLTP | Ready |
| 7.7 | MN-7.7 PII — Ai được xem? | Dashboard hiển thị gì? | **Superset:** Không hiển thị name, email, phone, full address. Chỉ `public_id` + region/city. **OLTP Admin:** Admin role xem được PII (xử lý đơn) | DWH analytics không cần PII. OLTP operational cần PII cho CS | Phân tích sai nếu dùng pseudonymized data | Superset config | Ready |
| 7.8 | MN-7.6 Data Quality Alerts | Alert kênh nào? | (1) Slack `#data-quality-alerts`. (2) Email data-team. (3) Superset dashboard "Data Quality Monitor" | 3 channels đảm bảo team nhận được alerts | Alert bị miss | Alert system | Ready |
| | | | | | | | **[Điều chỉnh]** |

---

## PHẦN 3: DANH SÁCH DESCOPED PHASE 1

| # | Yêu cầu gốc | Lý do descope | Giải pháp thay thế | Giai đoạn dự kiến | Stakeholder cần chấp nhận |
|---|-------------|---------------|--------------------|--------------------|--------------------------|
| D-1 | MN-5.5 Search analytics (top keywords, zero-result) | Access log hiện tại không có `query_text`, `result_count`. Cần sửa backend API → effort lớn | Giai đoạn 1: chỉ đo search event count. Giai đoạn 2: API logging bổ sung | Phase 2 | Marketing |
| D-2 | MN-5.2 Campaign tracking (dim_campaign, UTM mapping) | Cần backend logging UTM + admin input campaign cost | Giai đoạn 1: chỉ coupon performance. Giai đoạn 2: campaign dimension | Phase 2 | Marketing |
| D-3 | MN-4.4 Inventory movement audit trail | OLTP hiện tại không có bảng inventory movement | Giai đoạn 1: suy luận từ snapshot. Giai đoạn 2: fact_inventory_movement | Phase 2 | Warehouse |
| D-4 | MN-3.5 Seasonal forecast | Data < 12 tháng → forecast unreliable | Giai đoạn 1: historical trend + YoY. Giai đoạn 2: seasonal index | Phase 2 | Sales |
| D-5 | MN-1.15 Full P&L (COGS, shipping cost, marketing cost) | Cần data từ external systems (accounting, payment gateway, logistics) | Giai đoạn 1: revenue side only. Giai đoạn 2: external data feeds | Phase 2 | Finance |
| D-6 | MN-1.5 Tax (VAT) | OLTP hiện tại không có cột tax. Thêm schema = effort lớn | Giai đoạn 1: bỏ qua tax. Giai đoạn 2: bổ sung tax nếu cần | Phase 2 | Finance |
| D-7 | MN-5.3 Wishlist-to-purchase conversion (detailed) | Cần event history chi tiết từ wishlist_items | Giai đoạn 1: basic wishlist analytics từ current data. Giai đoạn 2: event history | Phase 2 | Marketing |
| D-8 | MN-3.4 RFM 27 cells đầy đủ | Phức tạp, chưa cần cho marketing action Giai đoạn 1 | Giai đoạn 1: RF 9 segments + M separate. Giai đoạn 2: RFM 27 cells | Phase 2 | Marketing |
| D-9 | MN-1.5 Deferred Revenue cho COD | COD chưa thu tiền ≠ deferred revenue theo chuẩn kế toán | Giai đoạn 1: chỉ track Open Order Value cho COD. Giai đoạn 2: confirm với Finance | Phase 1 (needs confirmation) | Finance |

---

## PHẦN 4: DANH SÁCH CẦN XÁC NHẬN

| # | Câu hỏi | Nhóm | Vì sao cần xác nhận | Nếu không xác nhận thì rủi ro | Đề xuất mặc định |
|---|---------|------|---------------------|-------------------------------|-------------------|
| X-1 | GMV có bao gồm đơn `payment_failed` không? | CEO/Finance | Ảnh hưởng đến con số GMV reported | GMV bị inflation nếu include | Exclude `payment_failed` |
| X-2 | Net Merchandise Revenue có tách shipping không? | CEO/Finance | Ảnh hưởng đến phân tích revenue mix | Không phân biệt được merchandise vs shipping | Tách: GMV, Net Merchandise, Shipping |
| X-3 | Revenue recognition theo `completed_at` có đúng chuẩn kế toán VN không? | CEO/Finance | Ảnh hưởng đến P&L reporting | Ghi nhận sai kỳ tài chính | Giai đoạn 1: completed_at. Giai đoạn 2: confirm |
| X-4 | COD có cần track riêng không? | CEO/Finance | COD chiếm tỷ trọng lớn ở VN | Không phân biệt được COD vs online payment | Track theo payment method nếu OLTP có |
| X-5 | Address có cần pseudonymize không? | Data Platform | Ảnh hưởng NĐ13/2023 compliance | Vi phạm luật bảo vệ dữ liệu cá nhân | Gold giữ region/city/district. Full address OLTP only |
| X-6 | Search analytics có cần descope không? | Marketing | Ảnh hưởng đến search quality metrics | Marketing không có search data | Descope Giai đoạn 1. Phase 2 cần API logging |
| X-7 | SLA paid→confirmed ≤ 4 giờ có phù hợp không? | CS/Ops | Ảnh hưởng đến SLA tracking | SLA tracking sai nếu ngưỡng sai | ≤ 4 giờ làm việc (8h-22h ICT) |
| X-8 | Coupon redemption status OLTP hiện có những giá trị gì? | Marketing | Cần verify OLTP data để tính release rate | Không measure được coupon wastage | `redeemed`/`released` (verify OLTP) |
| X-9 | Có cần track COD separately không? | Warehouse | Ảnh hưởng đến reconciliation COD | COD reconciliation sai | Verify OLTP có payment method field |
| X-10 | New product date nên dùng nguồn nào? | Sales | Ảnh hưởng đến product lifecycle analysis | Phân tích sai lifecycle | Ưu tiên: launch_date → first_visible → first_order → created_at |

---

## PHẦN 5: AGENDA WORKSHOP 120 PHÚT

### Trước Workshop

| Hành động | Thời gian | Người thực hiện |
|-----------|-----------|----------------|
| Gửi tài liệu SIGNOFF v1.1 + MANAGEMENT_INFO_NEEDS cho stakeholders | Workshop - 3 ngày | Data Team |
| Stakeholders review, ghi ý kiến vào [Điều chỉnh] nếu có | Workshop - 3 đến -1 ngày | Tất cả stakeholders |
| Data Team chuẩn bị presentation slides | Workshop - 1 ngày | Data Team |

### Agenda Chi tiết

| Thời lượng | Phần | Người trình bày | Câu hỏi trọng tâm | Tiêu chí kết luận |
|-----------|------|-----------------|-------------------|-------------------|
| **5 phút** | **Mở đầu:** Giới thiệu mục tiêu workshop, quy trình sign-off | Lead Data Engineer | — | Stakeholders hiểu quy trình |
| **15 phút** | **Nhóm 1: CEO/Finance.** Trình bày: GMV, Net Revenue, Revenue Recognition, Deferred Revenue, P&L Scope | Lead Data Engineer | (1) GMV include cancelled? (2) Net Revenue tách shipping? (3) Revenue theo completed_at? (4) COD có phải deferred? | Finance đồng ý với metric definitions |
| **10 phút** | **Nhóm 2: Store Manager.** Trình bày: 3 revenue metrics, shift, low stock threshold, realtime vs batch | Data Engineer | (1) 3 revenue metrics có đủ? (2) Threshold velocity-based OK? (3) OLTP direct OK? | Store Manager đồng ý operational metrics |
| **10 phút** | **Nhóm 3: Sales Manager.** Trình bày: Category 2 cấp, RFM 9 segments, Coupon Efficiency, Return Rate | Data Engineer | (1) Category 2 cấp đủ? (2) RFM 9 segments OK? (3) Coupon Efficiency thay ROI? | Sales đồng ý analytical metrics |
| **10 phút** | **Nhóm 4: Warehouse.** Trình bày: Reorder point, dead stock, inventory snapshot, reconciliation | Data Engineer | (1) Lead time 14 ngày OK? (2) Dead stock 90 ngày OK? (3) Snapshot ICT OK? | Warehouse đồng ý inventory metrics |
| **10 phút** | **Nhóm 5: Marketing.** Trình bày: Search descope, Campaign descope, Coupon ROI → Efficiency, Attribution | Data Engineer | (1) Search descope OK? (2) Campaign Giai đoạn 2? (3) Last-click attribution OK? | Marketing chấp nhận descoping |
| **10 phút** | **Nhóm 6: CS/Ops.** Trình bày: SLA definition, Complaint proxy, Customer lookup | Data Engineer | (1) SLA 4h/72h/5 ngày OK? (2) Proxy complaint OK? (3) Order number lookup OK? | CS đồng ý SLA definitions |
| **10 phút** | **Nhóm 7: Data Platform.** Trình bày: Freshness, PII, Access control, Reconciliation | CTO/Tech Lead | (1) PII handling OK? (2) Namespace RBAC OK? (3) Reconciliation threshold OK? | Tech đồng ý security policies |
| **15 phút** | **Descoping & Needs Confirmation.** Trình bày danh sách D-1 đến D-9 và X-1 đến X-10 | Lead Data Engineer | (1) Descoping nào cần promote lên Phase 1? (2) Needs Confirmation nào cần trả lời ngay? | Stakeholders confirm descoping list |
| **10 phút** | **Q&A mở.** Stakeholders hỏi thêm nếu cần | Tất cả | — | Tất cả câu hỏi đã trả lời |
| **5 phút** | **Sign-off.** Ký duyệt tài liệu | Tất cả stakeholders | — | Tài liệu được ký duyệt |

### Tiêu chí Workshop thành công

| Tiêu chí | Đo lường |
|----------|----------|
| **Sign-off được** | ≥80% mục "Ready" được approve. ≤2 mục "Needs Confirmation" chưa trả lời. Không có mục bị reject |
| **Cần vòng 2** | >20% mục bị reject. >5 mục "Needs Confirmation" chưa trả lời. Có stakeholder vắng mặt quan trọng |
| **Bị hủy** | CEO/CTO vắng mặt. Không có quyết định về metric definitions |

### Xử lý sau Workshop

| Tình huống | Hành động | Thời gian |
|-----------|-----------|-----------|
| **Sign-off thành công** | Data Team update tài liệu theo [Điều chỉnh], commit git, bắt đầu Giai đoạn 1 | Workshop + 2 ngày |
| **Cần vòng 2** | Data Team tổng hợp ý kiến, chuẩn bị revised version, schedule workshop round 2 | Workshop + 3 ngày |
| **Có ý kiến phản đối** | Data Team cung cấp trade-off analysis cho từng điểm, trình CTO/CEO quyết định | Workshop + 5 ngày |

---

## PHẦN 6: TÓM TẮT QUYẾT ĐỊNH

| Nhóm | Ready | Needs Confirmation | Descoped | Deferred | Tổng |
|------|-------|-------------------|----------|----------|------|
| CEO/Finance | 13 | 4 (X-1,2,3,4) | 2 (D-5,D-6) | 1 (D-9) | 13 |
| Store Manager | 7 | 0 | 0 | 0 | 7 |
| Sales Manager | 9 | 0 | 2 (D-4,D-8) | 0 | 9 |
| Warehouse | 7 | 1 (X-9) | 1 (D-3) | 0 | 8 |
| Marketing | 7 | 2 (X-6,X-8) | 3 (D-1,D-2,D-7) | 0 | 7 |
| CS/Ops | 7 | 1 (X-7) | 0 | 0 | 7 |
| Data Platform | 8 | 1 (X-5) | 0 | 0 | 8 |
| **Tổng** | **58** | **9** | **8** | **1** | **59** |

---

## HƯỚNG DẪN SỬ DỤNG

### Cách tổ chức Workshop

1. **Pre-workshop:** Gửi tài liệu trước 3 ngày. Stakeholders review và ghi ý kiến.
2. **Workshop:** 120 phút, theo agenda trên. Lead Data Engineer chủ trì.
3. **Post-workshop:** Data Team update tài liệu trong 2 ngày. Commit git. Bắt đầu Giai đoạn 1.

### Ai cần tham gia

| Nhóm | Người | Bắt buộc? |
|------|-------|-----------|
| CEO/CFO | CEO hoặc CFO | **Bắt buộc** (sign-off metrics tài chính) |
| Store Manager | Head of Operations | Bắt buộc |
| Sales Manager | Head of Sales | Bắt buộc |
| Warehouse | Warehouse Manager | Bắt buộc |
| Marketing | Marketing Manager | Bắt buộc |
| CS/Ops | CS Team Lead | Bắt buộc |
| Data Platform | CTO / Tech Lead | **Bắt buộc** (sign-off security, PII) |
| Data Team | Lead Data Engineer | Bắt buộc (chủ trì) |

### Sau khi Sign-off

| Bước | Hành động | Thời gian |
|------|-----------|-----------|
| 1 | Data Team cập nhật tài liệu theo [Điều chỉnh] | Ngày 1-2 |
| 2 | Commit vào git (`docs/architecture/SIGNOFF_RECOMMENDATIONS.md`) | Ngày 2 |
| 3 | Bắt đầu Giai đoạn 1: Star schema (dimensions + facts + marts) | Tuần 1-4 |
| 4 | Build CEO/Finance dashboard trên Superset | Tuần 3-4 |
| 5 | UAT với stakeholders | Tuần 5 |
| 6 | Deploy production | Tuần 6 |
