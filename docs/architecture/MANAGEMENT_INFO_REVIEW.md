# Phân tích Chuyên sâu: MANAGEMENT_INFO_NEEDS.md

**Loại document:** Review & Design Specification
**Ngày tạo:** 2026-09-07
**Tác giả:** Senior Data Engineer / Analytics Engineer
**Nguồn tham chiếu:** MANAGEMENT_INFO_NEEDS.md, OLTP_TABLES.md, LAKEHOUSE_DESIGN_PLAN.md

---

## PHẦN 1: ISSUE LOG

| ID | Nhóm | Vấn đề | Rủi ro Kinh doanh | Rủi ro Kỹ thuật | Câu hỏi Business | Đề xuất Sửa | Ưu tiên |
|----|------|--------|-------------------|-----------------|------------------|-------------|---------|
| I-01 | Định nghĩa Metric | GMV định nghĩa chưa rõ ràng | Cùng 1 con số CEO/Store/Sales hiểu khác nhau → quyết định sai | Query mỗi nơi filter khác nhau → data không nhất quán | GMV có bao gồm cancelled không? Có gồm shipping fee không? subtotal_vnd trước hay sau discount? | Định nghĩa GMV rõ ràng trong Metric Catalog (xem Phần 2). Chọn 1 cách tính duy nhất, viết vào data dictionary | **Critical** |
| I-02 | Định nghĩa Metric | Net Revenue có nguy cơ double counting | Reported revenue sai → quyết định tài chính sai | Net Revenue = GMV - discount - refund NHƯNG source lại dùng total_vnd (đã trừ discount) - refund → discount bị trừ 2 lần | `total_vnd` đã bao gồm discount chưa? | Sửa công thức: Net Revenue = `orders.total_vnd` (đã trừ discount, chưa trừ refund) - `refunds.amount_vnd`. KHÔNG trừ discount lần 2 | **Critical** |
| I-03 | Định nghĩa Metric | Refund chưa rõ kỳ ghi nhận | Refund đơn Q1 ghi nhận vào Q2 → P&L bị lệch | Không biết group theo `refunds.created_at` hay `orders.created_at` | Refund ghi nhận theo ngày refund hay ngày order gốc? Có partial refund không? | Ghi nhận theo `refunds.created_at` (ngày phát sinh refund). Hiện tại OLTP chỉ hỗ trợ full refund (1:1 payment) | **High** |
| I-04 | Định nghĩa Metric | Conversion rate thiếu denominator chuẩn | So sánh channel sai → budget phân bổ sai | Visitor count không consistent giữa các report | Unique visitor tính theo gì (user_id/session/device/cookie)? Có lọc bot/internal không? | Định nghĩa: `COUNT(DISTINCT orders.customer_id) / COUNT(DISTINCT fact_web_events.actor_key WHERE actor_type='anonymous'+customer)` trong kỳ. Lọc bot theo user_agent | **High** |
| I-05 | Định nghĩa Metric | Repeat purchase rate thiếu time window | So sánh sai giữa các kỳ | Không thể reproducible | Tính trong bao nhiêu ngày? Có loại cancelled/refund không? | Định nghĩa: "Tỷ lệ khách có ≥2 đơn completed trong 12 tháng tính từ ngày xét." Chỉ tính đơn status = 'completed' | **High** |
| I-06 | Định nghĩa Metric | CLV chỉ là historical average, không phải CLV dự báo | kỳ vọng CLV = revenue潜力, thực tế chỉ là past spend | Không có margin, không có discount, không có projection | Business cần CLV historical hay CLV forecast? | Phân biệt: (1) Historical CLV = AVG(total_spend) trên completed orders. (2) Predictive CLV cần ML model + acquisition cost — external input | **Medium** |
| I-07 | Dữ liệu Nguồn | inventory.on_hand chỉ là snapshot hiện tại, không có lịch sử | Không tính được sell-through, dead stock, inventory turnover | Thiếu `opening_on_hand` lịch sử → mở_on_hand hiện tại có thể không phải đầu kỳ | `opening_on_hand` trong inventory là opening của khi nào? Ngày generate data? | Bổ sung `fact_inventory_snapshot_daily` (end-of-day snapshot). `opening_on_hand` hiện tại = snapshot khi generate, KHÔNG phải opening thực tế theo ngày | **Critical** |
| I-08 | Dữ liệu Nguồn | Inventory threshold on_hand < 10 hard-code không phù hợp | Variant bán 100 units/ngày cũng alert khi còn 10, variant bán 1 unit/ngày alert quá sớm | Không adaptive theo velocity | Cần reorder point động? | Tính reorder point = (velocity_7d × lead_time_days) + safety_stock. Lead time hiện tại không có trong OLTP → cần input từ business | **High** |
| I-09 | Dữ liệu Nguồn | Stock-out impact thổi phồng | Ước tính lost revenue quá cao → ưu tiên nhập hàng sai | Revenue Potential = velocity × price giả định 100% conversion → sai | Có data về conversion rate thực tế khi sản phẩm có hàng không? | Dùng: `velocity_7d × (1 - avg_stockout_rate) × price × attribution_factor`. `attribution_factor` cần business input (0.3-0.7 tùy ngành) | **Medium** |
| I-10 | Dữ liệu Nguồn | Dead stock nhận diện sai | Đánh dấu sản phẩm_alive là dead → ngưng nhập hàng sai | Sản phẩm có thể dead vì out of stock, không phải vì không demand | Cần phân biệt: (1) hết hàng, (2) ngừng bán, (3) không có traffic, (4) không convert | Phân loại: Dead Stock = variant `is_active=TRUE` AND `on_hand>0` AND không có `fact_order_item` trong 90 ngày VÀ có traffic (fact_web_events) | **Medium** |
| I-11 | Dữ liệu Nguồn | Không có purchase order / goods receipt | Không phân tích được hiệu suất supplier, lead time, damaged goods | Không có input cho inventory planning | Có hệ thống PO/GR không? Hay nhập kho bằng cách khác? | Nếu không có PO system → bỏ qua phần "Hiệu suất Nhập kho", tập trung vào sell-through và reorder recommendation | **Medium** |
| I-12 | Định nghĩa Metric | Outstanding payments logic sai | Finance hiểu nhầm → reconciliation sai | `payment.status = 'failed'` không phải outstanding | Payment nào được coi là outstanding? | Outstanding = order `paid` nhưng payment `status='failed'` HOẶC order `status='payment_failed'`. Thay vì dùng fact_payment, query từ `fact_order` WHERE status = 'payment_failed' | **High** |
| I-13 | Ghi nhận Kế toán | Revenue recognition chỉ dùng `completed` | Có thể không đúng chuẩn kế toán Việt Nam | Finance cần xác nhận nguyên tắc | Doanh thu ghi nhận theo ngày nào: giao hàng, xuất hóa đơn, hay thanh toán? | Design Giai đoạn 1: ghi nhận theo `completed_at`. Giai đoạn 2: bổ sung theo yêu cầu kế toán cụ thể | **Medium** |
| I-14 | Ghi nhận Kế toán | Deferred revenue chưa rõ | Có thể understate/overstate revenue | Không có rule rõ ràng | Đơn `paid/confirmed` có phải deferred revenue không? | Deferred Revenue = Đơn `status='paid'` CHƯA `confirmed` + Đơn `status='confirmed'` CHƯA `completed`. Đây là working definition, cần Finance confirm | **Medium** |
| I-15 | Ghi nhận Kế toán | Tax summary thiếu dữ liệu thuế | Không báo cáo được VAT chính xác | OLTP không có `tax_rate`, `tax_amount` | Giá sản phẩm đã gồm VAT chưa? Cần xuất hóa đơn không? | Giai đoạn 1: Bỏ qua tax. Giai đoạn 2: Bổ sung `tax_rate`, `tax_amount` vào OLTP nếu cần | **Low** |
| I-16 | Ghi nhận Kế toán | Daily P&L thiếu chi phí | P&L không thực tế, chỉ có revenue side | Không có COGS, shipping cost, marketing cost, payment fee | Cần import chi phí từ hệ thống khác? | Giai đoạn 1: P&L chỉ gồm revenue, discount, refund. Giai đoạn 2: Bổ sung cost feeds từ accounting system | **Low** |
| I-17 | Dữ liệu Marketing | Không có campaign dimension | Không track được hiệu quả từng campaign | Không có `dim_campaign`, không có UTM mapping, attribution window | Có hệ thống campaign tracking không? UTM parameters có được log không? | Giai đoạn 1: Phân tích coupon performance. Giai đoạn 2: Bổ sung campaign dimension nếu có data | **Medium** |
| I-18 | Dữ liệu Marketing | Wishlist thiếu lịch sử | Không phân tích được wishlist-to-purchase conversion theo thời gian | `wishlist_items` chỉ lưu `is_present` hiện tại, không có event history | `first_added_at`, `last_added_at` có đủ cho analysis không? | Đủ cho analysis cơ bản. `first_added_at` = lần đầu thêm, `last_added_at` = lần thêm lại sau khi xóa. Có thể tính time-to-purchase từ đó | **Low** |
| I-19 | Dữ liệu Marketing | Review moderation queue logic sai | Hiển thị nhầm review chờ duyệt | Document ghi `status = 'approved'` nhưng queue phải là review CHƯA duyệt | Review status hiện tại có bao nhiêu giá trị? | Review statuses: `approved` (auto, hiển thị), `rejected` (admin ẩn). moderation queue hiện tại RỖNG vì review auto-approved. Queue chỉ cần khi business muốn pre-moderation | **Low** |
| I-20 | Dữ liệu Marketing | Search analytics thiếu schema chuẩn | Không phân tích được search quality | Access log hiện có `ecommerce_action='search'` nhưng không có `result_count`, `query_text` | Search logs có capture `result_count` không? Có normalize query không? | Giai đoạn 1: Dùng `fact_web_events` filter search action. Giai đoạn 2: Bổ sung search enrichment (result_count, query normalization) | **Medium** |
| I-21 | Customer Data | Customer identity chưa được xử lý | Customer duplicate → CLV, retention sai | OLTP 1 customer = 1 account, nhưng có thể nhiều account cùng 1 người | Có guest checkout không? Có customer duplicate không? | Giai đoạn 1: Giả định 1 account = 1 customer (OLTP enforce). Guest checkout hiện tại chưa có trong OLTP | **Low** |
| I-22 | Customer Data | Customer 360 thiếu complaint data | Không đánh giá được satisfaction thực tế | Không có ticket, chat, call log trong OLTP | Có hệ thống CSKH riêng không? | Giai đoạn 1: Dùng order cancelled + refund + negative review làm proxy. Giai đoạn 2: Tích hợp ticketing system nếu có | **Low** |
| I-23 | Vận hành | SLA chưa được định nghĩa | Không measure được performance | `N giờ` trong SLA compliance chưa cụ thể | SLA cho từng giai đoạn là bao nhiêu giờ? | Cần business input. Ví dụ đề xuất: paid→confirmed ≤ 24h, confirmed→completed ≤ 72h, refund ≤ 5 ngày | **High** |
| I-24 | Vận hành | Realtime vs batch chưa rõ | Store Manager cần realtime nhưng DWH batch | Dashboard OLTP realtime hay đọc từ DWH? | Dashboard vận hành đọc trực tiếp OLTP hay từ DWH? | **Khuyến nghị:** Dashboard vận hành (Store Manager, CS) đọc trực tiếp OLTP/API. Dashboard analytics (CEO, Sales, Marketing) đọc từ DWH/SuperSet | **High** |
| I-25 | Triển khai | Threshold cảnh báo hard-code | Alert không phù hợp theo mùa/danh mục/kênh | Không configurable, phải sửa code khi đổi ngưỡng | Cần configurable alerts hay hard-code OK? | Giai đoạn 1: Hard-code hợp lý. Giai đoạn 2: Configurable theo category/season/channel | **Medium** |
| I-26 | Triển khai | Mapping DWH thiếu nhiều đối tượng | Nhiều yêu cầu không build được | Thiếu fact_inventory_snapshot, fact_search_event, dim_channel, dim_campaign... | Có cần build tất cả hay ưu tiên? | Theo ưu tiên Giai đoạn 1-4 (xem Phần 5). Không build tất cả cùng lúc | **Medium** |
| I-27 | Triển khai | Thiếu NFR (data freshness, quality, access control) | Dashboard data cũ, không ai chịu trách nhiệm | Không có SLA freshness, không có data quality rules, không có RBAC | Data freshness requirement là bao nhiêu? | Định nghĩa: DWH batch daily (T+1). Dashboard OLTP realtime. Data quality rules: not-null, range, referential integrity. RBAC: theo namespace | **High** |
| I-28 | Định nghĩa Metric | Sell-through rate thiếu inventory snapshot | Không tính được sell-through thực tế | `opening_on_hand` trong inventory hiện tại không phải daily snapshot | Opening stock tính từ khi nào? | Bổ sung `fact_inventory_snapshot_daily` với grain: 1 row/(date, variant). Partition by date | **Critical** |

---

## PHẦN 2: METRIC CATALOG

### 2.1. Revenue Metrics

#### GMV (Gross Merchandise Value)

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Tổng giá trị hàng hóa đặt hàng thành công (đã thanh toán) trong kỳ, trước khi hoàn tiền |
| **Công thức** | `SUM(orders.subtotal_vnd)` WHERE `orders.status IN ('paid','confirmed','completed')` AND `orders.created_at` trong kỳ |
| **Nguồn dữ liệu** | `silver_orders` (OLTP) → `fact_order` (Gold) |
| **Bộ lọc trạng thái** | Include: `paid`, `confirmed`, `completed`. Exclude: `payment_failed`, `cancelled` |
| **Mốc thời gian** | Theo `orders.created_at` (ngày đặt hàng) |
| **Không bao gồm** | Phí vận chuyển, discount, refund |
| **Tần suất cập nhật** | Batch hàng ngày (T+1), realtime từ OLTP cho dashboard vận hành |
| **Chủ sở hữu đề xuất** | Finance |

#### Net Revenue

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Doanh thu thực tế = GMV sau discount, trừ refund |
| **Công thức** | `SUM(orders.total_vnd)` WHERE `status IN ('paid','confirmed','completed')` - `SUM(refunds.amount_vnd)` WHERE `status='succeeded'` trong kỳ |
| **Nguồn dữ liệu** | `fact_order` + `fact_refund` |
| **Lưu ý quan trọng** | `orders.total_vnd` ĐÃ bao gồm discount (total = subtotal - discount + shipping). KHÔNG trừ discount thêm lần nữa |
| **Bộ lọc trạng thái** | Orders: `paid/confirmed/completed`. Refunds: `succeeded` |
| **Tần suất** | Daily batch |
| **Chủ sở hữu** | Finance |

#### Confirmed Revenue

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Doanh thu từ đơn đã hoàn tất giao hàng |
| **Công thức** | `SUM(orders.total_vnd)` WHERE `status = 'completed'` trong kỳ (tính theo `completed_at`) |
| **Nguồn** | `fact_order` |
| **Tần suất** | Daily batch |
| **Chủ sở hữu** | Finance |

#### Discount Amount

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Tổng tiền giảm giá từ coupon trong kỳ |
| **Công thức** | `SUM(orders.discount_amount_vnd)` WHERE `status IN ('paid','confirmed','completed')` |
| **Nguồn** | `fact_order` |
| **Tần suất** | Daily batch |
| **Chủ sở hữu** | Finance + Marketing |

#### Refund Amount

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Tổng tiền hoàn lại trong kỳ từ các refund thành công |
| **Công thức** | `SUM(refunds.amount_vnd)` WHERE `status = 'succeeded'` AND `created_at` trong kỳ |
| **Nguồn** | `fact_refund` |
| **Mốc thời gian** | Theo `refunds.created_at` (ngày phát sinh refund) |
| **Lưu ý** | Hiện tại OLTP chỉ hỗ trợ full refund (1:1 với payment). Refund amount = payment amount |
| **Tần suất** | Daily batch |
| **Chủ sở hữu** | Finance |

#### Refund Rate

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Tỷ lệ hoàn tiền trên tổng doanh thu |
| **Công thức** | `Refund Amount / Net Revenue × 100` |
| **Threshold** | > 5% cần xem xét |
| **Tần suất** | Daily |
| **Chủ sở hữu** | Finance |

---

### 2.2. Order Metrics

#### AOV (Average Order Value)

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Giá trị trung bình mỗi đơn hàng đã thanh toán |
| **Công thức** | `SUM(orders.total_vnd) / COUNT(DISTINCT orders.order_id)` WHERE `status IN ('paid','confirmed','completed')` |
| **Nguồn** | `fact_order` |
| **Bộ lọc** | Chỉ tính đơn có payment succeeded |
| **Tần suất** | Daily |
| **Chủ sở hữu** | Sales |

#### Cancellation Rate

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Tỷ lệ đơn hàng bị hủy trên tổng đơn |
| **Công thức** | `COUNT(orders WHERE status='cancelled') / COUNT(orders WHERE status != 'payment_failed') × 100` |
| **Lưu ý** | Exclude `payment_failed` vì đây không phải đơn thực sự |
| **Threshold** | > 10% cần cảnh báo |
| **Tần suất** | Daily |
| **Chủ sở hữu** | Operations |

#### Payment Failure Rate

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Tỷ lệ thanh toán thất bại trên tổng nỗ lực thanh toán |
| **Công thức** | `COUNT(payments WHERE status='failed') / COUNT(payments) × 100` |
| **Nguồn** | `fact_payment` |
| **Threshold** | > 5% cần cảnh báo |
| **Tần suất** | Daily |
| **Chủ sở hữu** | Finance + Tech |

#### Order Cycle Time

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Thời gian trung bình từ đặt hàng đến hoàn tất |
| **Công thức** | `AVG(DATEDIFF(orders.completed_at, orders.created_at))` WHERE `status = 'completed'` |
| **Đơn vị** | Ngày |
| **Tần suất** | Daily |
| **Chủ sở hữu** | Operations |

---

### 2.3. Customer Metrics

#### Conversion Rate

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Tỷ lệ khách truy cập chuyển thành đơn hàng |
| **Công thức** | `COUNT(DISTINCT fact_order.customer_key WHERE order created in period) / COUNT(DISTINCT fact_web_events.actor_key WHERE event in period AND actor_type IN ('anonymous','customer')) × 100` |
| **Lưu ý** | Cross-device chưa hỗ trợ. Chỉ tính session-based uniques |
| **Tần suất** | Daily |
| **Chủ sở hữu** | Marketing |

#### Repeat Purchase Rate

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Tỷ lệ khách quay lại mua trong 12 tháng |
| **Công thức** | `COUNT(DISTINCT customer_id WHERE order_count ≥ 2 AND status='completed' trong 12 tháng) / COUNT(DISTINCT customer_id WHERE order_count ≥ 1 AND status='completed' trong 12 tháng) × 100` |
| **Bộ lọc** | Chỉ tính đơn `status = 'completed'` |
| **Time window** | 12 tháng rolling |
| **Tần suất** | Monthly |
| **Chủ sở hữu** | Marketing + Sales |

#### Customer Lifetime Value (CLV) — Historical

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Tổng chi tiêu trung bình mỗi khách trong toàn bộ lịch sử |
| **Công thức** | `SUM(orders.total_vnd WHERE status='completed') / COUNT(DISTINCT customer_id)` |
| **Lưu ý** | Đây là CLV lịch sử, KHÔNG phải CLV dự báo. Chưa trừ margin, chưa tính acquisition cost |
| **Tần suất** | Monthly |
| **Chủ sở hữu** | Marketing + Finance |

#### Retention Rate

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Tỷ lệ khách từ cohort month M vẫn mua hàng trong month M+N |
| **Công thức** | `COUNT(DISTINCT customer_id WHERE first_order_month = M AND has_order_in_month M+N) / COUNT(DISTINCT customer_id WHERE first_order_month = M) × 100` |
| **Nguồn** | `dim_customer` + `fact_order` |
| **Time windows** | 30/60/90/180/365 ngày |
| **Tần suất** | Monthly |
| **Chủ sở hữu** | Marketing |

#### Churn Risk

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Khách có đơn completed cuối cùng > 90 ngày trước |
| **Công thức** | ` customer_id WHERE MAX(completed_at) < CURRENT_DATE - INTERVAL 90 DAY` |
| **Lưu ý** | Đây là heuristic, không phải ML prediction |
| **Tần suất** | Weekly |
| **Chủ sở hữu** | Marketing |

---

### 2.4. Inventory Metrics

#### Sell-through Rate

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Tỷ lệ hàng đã bán so với tồn đầu kỳ |
| **Công thức** | `(opening_stock - closing_stock) / opening_stock × 100` trong kỳ |
| **Nguồn** | `fact_inventory_snapshot_daily` (CẦN BUILD) |
| **Lưu ý** | Opening stock hiện tại trong OLTP chỉ là snapshot khi generate, KHÔNG phải daily. Cần `fact_inventory_snapshot_daily` |
| **Tần suất** | Daily |
| **Chủ sở hữu** | Warehouse |

#### Stockout Rate

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Tỷ lệ variant hết hàng trên tổng variant active |
| **Công thức** | `COUNT(variants WHERE on_hand = 0 AND is_active = TRUE) / COUNT(variants WHERE is_active = TRUE) × 100` |
| **Threshold** | > 20% cần cảnh báo |
| **Tần suất** | Daily |
| **Chủ sở hữu** | Warehouse |

---

### 2.5. Promotion Metrics

#### Coupon Usage Rate

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Tỷ lệ coupon đã dùng so với giới hạn |
| **Công thức** | `coupons.used_count / coupons.total_usage_limit × 100` (NULL nếu unlimited) |
| **Nguồn** | `dim_coupon` |
| **Tần suất** | Daily |
| **Chủ sở hữu** | Marketing |

#### Coupon ROI

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Hiệu quả đầu tư coupon |
| **Công thức** | `(Revenue_from_coupon_orders - Discount_amount) / Discount_amount × 100` |
| **Nguồn** | `fact_order` group by coupon_id |
| **Lưu ý** | Chưa tính incremental revenue (so sánh với baseline) |
| **Tần suất** | Weekly |
| **Chủ sở hữu** | Marketing |

---

### 2.6. Operational Metrics

#### SLA Compliance

| Thuộc tính | Giá trị |
|-----------|---------|
| **Định nghĩa nghiệp vụ** | Tỷ lệ đơn xử lý đúng thời gian cam kết |
| **Công thức** | `COUNT(orders WHERE each_stage_within_SLA) / COUNT(orders) × 100` |
| **SLA đề xuất** | paid→confirmed ≤ 24h, confirmed→completed ≤ 72h, refund requested→completed ≤ 5 ngày |
| **Nguồn** | `fact_order` + `fact_order_status_transition` |
| **Tần suất** | Daily |
| **Chủ sở hữu** | Operations |

---

## PHẦN 3: DATA MODEL ĐỀ XUẤT

### 3.1. Dimension Tables

| Dimension | Grain | PK | Columns chính | Nguồn OLTP | Partition |
|-----------|-------|----|--------------|------------|-----------|
| `dim_date` | 1 row/ngày | `date_key` (INT YYYYMMDD) | date, year, month, week_of_year, day_of_month, day_of_week, is_weekend, is_holiday, quarter, fiscal_year | Generated (no source) | None (small) |
| `dim_customer` | 1 row/customer | `customer_key` (BIGINT) | customer_key, public_id, display_name, role, status, acquisition_date_key, created_at, updated_at | `customers` | None |
| `dim_product` | 1 row/product | `product_key` (BIGINT) | product_key, public_id, slug, name, category_key, is_active, archived_at, created_date_key | `products` + `categories` | None |
| `dim_category` | 1 row/category (hierarchy) | `category_key` (BIGINT) | category_key, code, name, parent_category_key (self-ref), level, is_active | `categories` | None |
| `dim_variant` | 1 row/variant | `variant_key` (BIGINT) | variant_key, public_id, sku, size_code, color_code, price_vnd, is_active, product_key | `product_variants` | None |
| `dim_coupon` | 1 row/coupon | `coupon_key` (BIGINT) | coupon_key, code, discount_type, discount_value, min_subtotal_vnd, starts_at, ends_at, is_active, total_usage_limit, per_customer_limit | `coupons` | None |
| `dim_order_status` | 1 row/status | `status_key` (INT) | status_key, status_code, status_name, status_category | Static lookup | None |

### 3.2. Fact Tables

#### `fact_order`

| Thuộc tính | Giá trị |
|-----------|---------|
| **Grain** | 1 row / 1 order |
| **PK** | `order_key` (BIGINT) |
| **FKs** | `order_date_key`, `customer_key`, `coupon_key` (nullable), `status_key` |
| **Measures** | `subtotal_vnd`, `discount_amount_vnd`, `shipping_fee_vnd`, `total_vnd`, `item_count` |
| **Timestamps** | `created_at`, `paid_at`, `confirmed_at`, `completed_at`, `cancelled_at` |
| **Status** | `order_status` (current) |
| **Partition** | `order_date_key` (by month) |
| **Nguồn** | `silver_orders` |
| **Write mode** | MERGE (mutable) |

#### `fact_order_item`

| Thuộc tính | Giá trị |
|-----------|---------|
| **Grain** | 1 row / 1 order line item |
| **PK** | `order_item_key` (BIGINT) |
| **FKs** | `order_key`, `variant_key`, `product_key`, `order_date_key` |
| **Measures** | `unit_price_vnd`, `quantity`, `line_total_vnd` |
| **Sảnp phẩm snapshot** | `sku_snapshot`, `size_code_snapshot`, `color_code_snapshot`, `product_name_snapshot`, `category_code_snapshot` |
| **Partition** | `order_date_key` (by month) |
| **Nguồn** | `silver_order_items` |
| **Write mode** | Append-only |

#### `fact_payment`

| Thuộc tính | Giá trị |
|-----------|---------|
| **Grain** | 1 row / 1 payment attempt |
| **PK** | `payment_key` (BIGINT) |
| **FKs** | `order_key`, `payment_date_key` |
| **Measures** | `amount_vnd` |
| **Status** | `payment_status` (succeeded/failed) |
| **Timestamps** | `attempted_at`, `created_at` |
| **Partition** | `payment_date_key` (by month) |
| **Nguồn** | `silver_payments` |
| **Write mode** | Append-only |

#### `fact_refund`

| Thuộc tính | Giá trị |
|-----------|---------|
| **Grain** | 1 row / 1 refund |
| **PK** | `refund_key` (BIGINT) |
| **FKs** | `order_key`, `payment_key`, `refund_date_key` |
| **Measures** | `amount_vnd` |
| **Status** | `refund_status` (succeeded/failed) |
| **Fields** | `reason` |
| **Partition** | `refund_date_key` (by month) |
| **Nguồn** | `silver_refunds` |
| **Write mode** | Append-only |

#### `fact_order_status_transition`

| Thuộc tính | Giá trị |
|-----------|---------|
| **Grain** | 1 row / 1 status transition |
| **PK** | `transition_key` (BIGINT) |
| **FKs** | `order_key`, `transition_date_key` |
| **Fields** | `from_status`, `to_status`, `transition_source`, `reason`, `transitioned_at` |
| **Partition** | `transition_date_key` (by month) |
| **Nguồn** | `silver_order_status_history` |
| **Write mode** | Append-only |

#### `fact_coupon_redemption`

| Thuộc tính | Giá trị |
|-----------|---------|
| **Grain** | 1 row / 1 coupon redemption |
| **PK** | `redemption_key` (BIGINT) |
| **FKs** | `coupon_key`, `order_key`, `customer_key`, `redemption_date_key` |
| **Status** | `redemption_status` (redeemed/released) |
| **Timestamps** | `redeemed_at`, `released_at` |
| **Partition** | `redemption_date_key` (by month) |
| **Nguồn** | `silver_coupon_redemptions` |
| **Write mode** | MERGE (mutable) |

#### `fact_product_review`

| Thuộc tính | Giá trị |
|-----------|---------|
| **Grain** | 1 row / 1 review |
| **PK** | `review_key` (BIGINT) |
| **FKs** | `product_key`, `customer_key`, `review_date_key` |
| **Measures** | `rating` |
| **Fields** | `content`, `status` (approved/rejected), `moderation_reason` |
| **Partition** | `review_date_key` (by month) |
| **Nguồn** | `silver_product_reviews` |
| **Write mode** | MERGE (mutable) |

#### `fact_inventory_snapshot_daily` *(CẦN BUILD — chưa có trong OLTP)*

| Thuộc tính | Giá trị |
|-----------|---------|
| **Grain** | 1 row / (date, variant) |
| **PK** | `snapshot_key` (BIGINT) |
| **FKs** | `variant_key`, `product_key`, `snapshot_date_key` |
| **Measures** | `on_hand`, `opening_on_hand` (snapshot at midnight) |
| **Partition** | `snapshot_date_key` (by month) |
| **Nguồn** | Spark job tạo snapshot hàng ngày từ `silver_inventory` + `silver_order_items` |
| **Write mode** | Append (mỗi ngày 1 snapshot) |

#### `fact_web_event` *(đã có — Logs Gold)*

| Thuộc tính | Giá trị |
|-----------|---------|
| **Grain** | 1 row / 1 HTTP request |
| **Nguồn** | `fact_web_events` (đã build) |
| **Columns** | event_id, event_ts, actor_key, actor_type, http_method, http_route, http_status, ecommerce_action, product_key, variant_key, duration_ms |

### 3.3. Mart Tables

| Mart | Grain | Mục đích | Nguồn |
|------|-------|---------|-------|
| `mart_sales_daily` | 1 row/(date, product, category) | Doanh thu hàng ngày theo sản phẩm/danh mục | `fact_order_item` + `fact_order` |
| `mart_inventory_daily` | 1 row/(date, variant) | Snapshot tồn kho hàng ngày | `fact_inventory_snapshot_daily` |
| `mart_customer_rfm` | 1 row/customer | RFM segmentation | `fact_order` |
| `mart_coupon_performance` | 1 row/coupon | Hiệu quả coupon | `fact_coupon_redemption` + `fact_order` |
| `mart_order_sla` | 1 row/order | SLA compliance | `fact_order` + `fact_order_status_transition` |
| `mart_web_funnel_daily` | 1 row/date | Funnel visitor→cart→checkout→order | `fact_web_events` + `fact_order` |
| `mart_hourly_route_metrics` | 1 row/(date, hour, route) | API performance | `fact_web_events` (đã build) |
| `mart_daily_product_demand` | 1 row/(date, product) | Product engagement | `fact_web_events` (đã build) |

---

## PHẦN 4: CÂU HỎI CẦN LÀM RÕ VỚI BUSINESS

### CEO / Finance

1. **GMV definition:** GMV có bao gồm phí vận chuyển không? Có bao gồm đơn `payment_failed` không?
2. **Revenue recognition:** Doanh thu ghi nhận theo ngày nào — giao hàng (`completed_at`), xuất hóa đơn, hay thanh toán (`paid_at`)?
3. **Deferred revenue:** Đơn `paid` chưa `confirmed` có coi là deferred revenue không?
4. **Tax:** Giá sản phẩm đã bao gồm VAT chưa? Có cần xuất hóa đơn VAT không?
5. **P&L scope:** Dashboard P&L cần đến mức nào — chỉ revenue side hay cần cả cost (COGS, shipping, marketing, payment fee)?
6. **Fiscal calendar:** Năm tài chính có khác calendar year không? Q1 = Jan-Mar hay khác?

### Store Manager

7. **Daily revenue:** "Doanh thu hôm nay" tính theo `created_at` hay `paid_at`?
8. **Shift definition:** Ca làm việc chia thế nào — sáng (6-12h), chiều (12-18h), tối (18-24h)? Hay theo shift thực tế?
9. **Order aging:** "Đơn > 3 ngày cần xử lý" — 3 ngày kể từ `created_at` hay `paid_at`?
10. **Low stock threshold:** Ngưỡng "sắp hết hàng" cho từng danh mục là bao nhiêu? Hay dùng chung 1 ngưỡng?

### Sales Manager

11. **Category hierarchy:** Category có mấy cấp? Level 1 = Level 2 = Level 3?
12. **Product lifecycle:** Sản phẩm `archived` có hiển thị trong report doanh thu không?
13. **Cross-sell analysis:** Cần phân tích cross-sell ở mức category hay product?
14. **Seasonal forecast:** Có data 2 năm trở lên chưa? Nếu chưa, forecast có ý nghĩa không?

### Warehouse

15. **Reorder point:** Có supplier lead time data không? Nếu không, dùng default bao nhiêu ngày?
16. **Dead stock definition:** "Không bán trong 90 ngày" — 90 ngày kể từ khi nào? Last sale hay created_at?
17. **Inventory snapshot:** Có cần snapshot tồn kho hàng ngày không? Hay chỉ cần知道 hiện tại?
18. **Reconciliation:** Có cần reconciliation giữa OLTP inventory và DWH không?

### Marketing

19. **Campaign tracking:** Có hệ thống campaign tracking (UTM, promo codes) không? Hay chỉ có coupon codes?
20. **Attribution window:** Nếu có campaign, attribution window là bao nhiêu ngày (last-click, first-click, linear)?
21. **Search analytics:** Search logs có capture `result_count` không? Có normalize query không?
22. **Wishlist analysis:** Wishlist analysis có quan trọng không? Ưu tiên thấp hay cao?

### CS/Ops

23. **SLA definition:** Từng giai đoạn xử lý đơn có SLA cụ thể không? (paid→confirmed, confirmed→completed, refund processing)
24. **Complaint tracking:** Có hệ thống ticketing/CSKH không? Nếu không, dùng proxy gì?
25. **Customer lookup:** CS cần lookup theo order_number, email, hay phone number?

### Data Platform / Security

26. **Data freshness:** Dashboard vận hành cần realtime (<5 phút) hay batch (15 phút, 1 giờ)?
27. **Access control:** Ai được xem dashboard nào? CEO xem tất cả, Store Manager chỉ xem cửa hàng mình?
28. **PII handling:** Trong DWH, customer name có cần pseudonymize không? Hay chỉ email/phone?
29. **Retention policy:** Dữ liệu DWH lưu trữ bao lâu? 2 năm, 5 năm, hay vĩnh viễn?
30. **Timezone:** Dashboard hiển thị theo timezone Việt Nam (UTC+7) hay UTC?

---

## PHẦN 5: ĐỀ XUẤT TRIỂN KHAI THEO GIAI ĐOẠN

### Giai đoạn 1: Nền tảng Dữ liệu Bắt buộc (Tuần 1-4)

**Mục tiêu:** Xây dựng star schema cơ bản, phục vụ CEO và Finance — nhóm có nhu cầu cấp bách nhất và data ít phụ thuộc external.

| Đối tượng | Chi tiết |
|-----------|---------|
| **Dimensions** | `dim_date`, `dim_customer`, `dim_product`, `dim_category`, `dim_variant`, `dim_coupon`, `dim_order_status` |
| **Facts** | `fact_order`, `fact_order_item`, `fact_payment`, `fact_refund`, `fact_order_status_transition`, `fact_coupon_redemption` |
| **Marts** | `mart_sales_daily`, `mart_customer_rfm` |
| **Dashboard** | CEO Overview: GMV, Net Revenue, Refund Rate, Order Count, AOV. Finance: Confirmed Revenue, Refund by reason, Cash flow |
| **KPIs** | GMV, Net Revenue, Confirmed Revenue, Discount Amount, Refund Amount, Refund Rate, AOV, Cancellation Rate, Payment Failure Rate, Repeat Purchase Rate (12M) |
| **Điều kiện** | Silver OLTP đã done (16/16). Gold star schema chưa có. Pipeline logs Gold done. Trino + Superset ready |
| **Rủi ro** | `fact_inventory_snapshot_daily` chưa có → sell-through rate, dead stock, inventory metrics BỊ LẠC | Chấp nhận: inventory metrics bị thiếu ở Giai đoạn 1 |

**Output cụ thể:**
- Spark jobs: `build_oltp_gold_dimensions.py`, `build_oltp_gold_facts.py`, `build_oltp_gold_marts.py`
- Airflow DAG: `ingest_oltp_gold.py` (daily schedule)
- Superset dashboards: CEO Overview, Finance Daily Report
- Tests: reconciliation checks (row count, revenue total)

---

### Giai đoạn 2: Dashboard Vận hành (Tuần 5-8)

**Mục tiêu:** Phục vụ Store Manager, CS/Ops — những người cần data realtime/near-realtime từ OLTP.

| Đối tượng | Chi tiết |
|-----------|---------|
| **Dimensions** | `dim_order_status` (mở rộng) |
| **Facts** | `fact_inventory_snapshot_daily` (BUILD mới) |
| **Marts** | `mart_inventory_daily`, `mart_order_sla` |
| **Dashboard** | Store Manager: Daily Revenue, Pending Orders, Low Stock, Top Products. CS: Order Status Lookup, Aging Orders, SLA Compliance |
| **KPIs** | Daily Revenue, Pending Order Count, Low Stock Variant Count, Top Selling Products, Order Cycle Time, SLA Compliance % |
| **Điều kiện** | Giai đoạn 1 done. OLTP API có endpoint cho Store Manager query trực tiếp |
| **Rủi ro** | Realtime requirement → cần quyết định: OLTP direct query vs DWH batch |

**Lưu ý quan trọng — Realtime vs Batch:**
- **Dashboard vận hành** (Store Manager, CS): Đọc trực tiếp từ OLTP/API, KHÔNG đọc từ DWH. Lý do: data cần realtime, OLTP đã có index, không cần Spark.
- **Dashboard analytics** (CEO, Sales, Marketing): Đọc từ DWH/SuperSet. Lý do: cần historical aggregation, complex joins, performance.

---

### Giai đoạn 3: Marketing / Customer Analytics (Tuần 9-12)

**Mục tiêu:** Phục vụ Sales Manager, Marketing — phân tích customer behavior, coupon effectiveness, review quality.

| Đối tượng | Chi tiết |
|-----------|---------|
| **Dimensions** | Mở rộng `dim_product` (thêm acquisition channel nếu có) |
| **Facts** | `fact_product_review` |
| **Marts** | `mart_coupon_performance`, `mart_web_funnel_daily` |
| **Dashboard** | Sales: Revenue by Category, Coupon ROI, RFM Segmentation, Cohort Analysis. Marketing: Coupon Performance, Wishlist Analysis, Review Quality, Search Analytics |
| **KPIs** | Category Revenue, Coupon Usage Rate, Coupon ROI, Retention Rate, Churn Risk, Avg Rating, Search-to-Purchase Conversion |
| **Điều kiện** | Giai đoạn 1+2 done. `fact_web_events` (logs) đã build |
| **Rủi ro** | Campaign analytics phụ thuộc external data (campaign cost, UTM) — có thể bị limited |

---

### Giai đoạn 4: Forecast / Nâng cao (Tuần 13-16)

**Mục tiêu:** Dự báo nhu cầu, inventory optimization, advanced analytics.

| Đối tượng | Chi tiết |
|-----------|---------|
| **Facts** | Mở rộng `fact_inventory_snapshot_daily` với velocity calculations |
| **Marts** | `mart_replenishment`, `mart_dead_stock`, `mart_stockout_impact` |
| **Dashboard** | Warehouse: Reorder Recommendations, Dead Stock Alert, Inventory Turnover. Sales: Demand Forecast, Seasonal Analysis |
| **KPIs** | Sell-through Rate, Stockout Rate, Dead Stock Value, Reorder Point, Demand Forecast Accuracy |
| **Điều kiện** | Giai đoạn 1-3 done. Đủ historical data (≥6 tháng) cho forecast |
| **Rủi ro** | Forecast accuracy phụ thuộc data quality + lượng historical data |

---

## PHỤ LỤC: MA TRẬN ƯU TIÊN

| Giai đoạn | Week | Blocks on | Deliverable chính | KPI chính |
|-----------|------|-----------|-------------------|-----------|
| **1** | 1-4 | Silver OLTP (done) | Star schema + CEO/Finance dashboard | GMV, Net Revenue, AOV, Refund Rate |
| **2** | 5-8 | Giai đoạn 1 | Inventory snapshot + Store Ops dashboard | Daily Revenue, Pending Orders, SLA |
| **3** | 9-12 | Giai đoạn 1 + Logs Gold (done) | Marketing/Customer analytics | Coupon ROI, Retention, RFM |
| **4** | 13-16 | Giai đoạn 1-3 + 6 tháng data | Forecast + advanced analytics | Demand Forecast, Dead Stock, Reorder |

---

## PHỤ LỤC: NGUYÊN TẮC DESIGN

1. **Single source of truth:** Mỗi metric có 1 định nghĩa duy nhất trong Metric Catalog. Không có 2 cách tính cùng 1 metric.
2. **Finance-first:** Ưu tiên metric phục vụ Finance/CEO trước. Sales/Marketing sau. Warehouse/CS riêng biệt.
3. **OLTP vs DWH separation:** Dashboard vận hành đọc OLTP. Dashboard analytics đọc DWH. Không trộn lẫn.
4. **Incremental build:** Mỗi giai đoạn độc lập, có thể deploy riêng. Không cần đợi tất cả xong mới dùng được.
5. **Reconciliation gate:** Gold chỉ publish khi reconciliation checks pass (row count, revenue total).
6. **Configurable thresholds:** Alert thresholds nên configurable theo category/season ở Giai đoạn 2+.
7. **PII protection:** Customer name pseudonymize trong DWH. Email/phone hash trước Silver.
8. **Timezone:** Tất cả timestamps trong DWH là UTC. Dashboard hiển thị UTC+7.
