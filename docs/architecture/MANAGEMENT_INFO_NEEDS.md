# Phân tích Nhu cầu Thông tin theo Cấp bậc Quản lý

Mô tả chi tiết từng nhóm thông tin mà mỗi cấp bậc quản lý cần truy xuất từ hệ thống D&K E-Commerce. Dữ liệu nguồn đến từ 16 bảng OLTP + Access Logs.

---

## 1. Tổng Giám đốc (CEO) / Ban Lãnh đạo

### 1.1. Tổng quan Tài chính

| Thông tin | Chi tiết | Đơn vị | Nguồn dữ liệu |
|-----------|---------|--------|---------------|
| GMV (Gross Merchandise Value) | Tổng giá trị đơn hàng trước hoàn tiền, trong kỳ | VND | `orders.subtotal_vnd` WHERE `status IN ('paid','confirmed','completed')` |
| Doanh thu ròng (Net Revenue) | GMV - discount - refund | VND | `orders.total_vnd` JOIN `payments` WHERE `status='succeeded'` minus `refunds.amount_vnd` |
| Discount tổng | Tổng tiền giảm giá từ coupon trong kỳ | VND | SUM(`orders.discount_amount_vnd`) |
| Refund tổng | Tổng tiền hoàn lại trong kỳ | VND | SUM(`refunds.amount_vnd`) WHERE `status='succeeded'` |
| Tỷ lệ hoàn tiền | Refund / GMV × 100 | % | Tính từ refund total / GMV |
| Doanh thu theo tháng | GMV rollup theo tháng, so sánh cùng kỳ năm trước | VND/tháng | `fact_order` group by `date_key.month` |

### 1.2. KPIs Chiến lược

| Thông tin | Chi tiết | Công thức | Nguồn |
|-----------|---------|----------|-------|
| AOV (Average Order Value) | Giá trị trung bình mỗi đơn | SUM(total_vnd) / COUNT(orders) | `fact_order` |
| Conversion rate | Tỷ lệ visitor → order | COUNT(orders with status paid+) / COUNT(unique visitors) | `fact_order` + `fact_web_events` |
| Repeat purchase rate | Tỷ lệ khách mua lại | COUNT(customers with >1 order) / COUNT(total customers with order) | `fact_order` group by customer |
| Customer Lifetime Value (CLV) | Tổng chi tiêu trung bình mỗi khách | AVG(total_spend) trên `dim_customer` | `fact_order` group by customer |
| Items per order | Số sản phẩm trung bình mỗi đơn | AVG(item_count) | `fact_order_item` count per order |
| Sell-through rate | Tỷ lệ hàng đã bán / hàng tồn đầu kỳ | SUM(quantity_sold) / SUM(opening_on_hand) | `fact_order_item` + `inventory` |

### 1.3. Xu hướng tăng trưởng

| Thông tin | Chi tiết | Phân tích | Nguồn |
|-----------|---------|----------|-------|
| Revenue trend | Đường cong doanh thu theo tuần/tháng/quý | Line chart, so sánh period-over-period | `mart_sales_daily` rollup |
| Order volume trend | Số lượng đơn theo ngày/tuần | Line chart | `fact_order` group by date |
| Customer acquisition curve | Số khách mới theo tháng | Line chart | `dim_customer.created_date_key` |
| Growth rate | Tỷ lệ tăng trưởng so với kỳ trước | ((Current - Previous) / Previous) × 100 | Tính từ revenue trend |
| Seasonal pattern | Pattern mua sắm theo mùa/tháng | Heatmap month × revenue | `mart_sales_daily` |

### 1.4. Rủi ro & Cảnh báo

| Thông tin | Chi tiết | Threshold | Nguồn |
|-----------|---------|-----------|-------|
| Tỷ lệ hủy đơn | Đơn cancelled / total orders | > 10% cần cảnh báo | `fact_order` status |
| Tỷ lệ thanh toán thất bại | Payment failed / total payments | > 5% cần cảnh báo | `fact_payment` status |
| Tỷ lệ hoàn tiền | Refund amount / GMV | > 5% cần xem xét | `fact_refund` |
| Doanh thu sụt giảm | GMV kỳ này < kỳ trước | Giảm > 15% | Revenue trend comparison |
| Inventory risk | Số variant hết hàng tăng | > 20% variant out of stock | `inventory.on_hand = 0` |

### 1.5. Hiệu suất Danh mục

| Thông tin | Chi tiết | Phân tích | Nguồn |
|-----------|---------|----------|-------|
| Top danh mục theo doanh thu | Category ranking | Bar chart top 10 | `fact_order_item` join `dim_product` → category |
| Danh mục giảm sút | Category có revenue giảm so với kỳ trước | So sánh month-over-month | `mart_sales_daily` |
| Product mix | Tỷ lệ doanh thu theo category | Pie chart | `fact_order_item` |
| New product performance | Sản phẩm mới (created < 30 ngày)贡献 bao nhiêu revenue | Filter dim_product.created_date | `fact_order_item` |

---

## 2. Quản lý Cửa hàng (Store Manager)

### 2.1. Doanh thu theo Ca/ngày

| Thông tin | Chi tiết | Tần suất | Nguồn |
|-----------|---------|---------|-------|
| Doanh thu hôm nay | Tổng `total_vnd` của đơn `paid/confirmed/completed` trong ngày | Realtime | `fact_order` WHERE date = today |
| Doanh thu hôm qua | So sánh với hôm qua | Daily | `fact_order` WHERE date = yesterday |
| Same day last week | Cùng ngày tuần trước | Weekly | `fact_order` WHERE date = same day last week |
| Doanh thu theo ca (sáng/trưa/chiều/tối) | Breakdown theo giờ trong ngày | Hourly | `fact_order.created_at` group by hour |
| Cumulative daily | Doanh thu tích lũy trong ngày (cập nhật realtime) | Running total | `fact_order` WHERE date = today, SUM running |

### 2.2. Quản lý Đơn hàng

| Thông tin | Chi tiết | Action | Nguồn |
|-----------|---------|--------|-------|
| Đơn chờ xác nhận | Đơn có status = `paid`, chờ admin confirm | Cần confirm ASAP | `fact_order` filter status |
| Đơn chờ giao | Đơn `confirmed`, chờ xử lý giao hàng | Theo dõi SLA | `fact_order` filter status |
| Đơn vừa hủy | Đơn `cancelled` trong ngày, có lý do | Xem lý do | `fact_order` + `order_status_history` |
| Đơn vừa hoàn tất | Đơn `completed` trong ngày | Celebration tracker | `fact_order` filter completed_at |
| Tuổi đơn (order age) | Số ngày từ created_at đến hiện tại | Đơn > 3 ngày cần xử lý | `fact_order`DATEDIFF |

### 2.3. Sản phẩm

| Thông tin | Chi tiết | Phân tích | Nguồn |
|-----------|---------|----------|-------|
| Top sản phẩm bán chạy (7 ngày) | Sản phẩm có quantity sold cao nhất | Ranking bar chart | `fact_order_item` last 7 days, group by product |
| Bottom sản phẩm (30 ngày) | Sản phẩm bán ít nhất | Cảnh báo tồn đọng | `fact_order_item` last 30 days |
| Sản phẩm vừa bán được | Đơn mới nhất chứa sản phẩm nào | Realtime feed | `fact_order_item` latest |
| Doanh thu theo size | Size nào bán chạy nhất | Breakdown by size_code | `fact_order_item` group by size |
| Doanh thu theo màu | Màu nào bán chạy nhất | Breakdown by color_code | `fact_order_item` group by color |

### 2.4. Tồn kho

| Thông tin | Chi tiết | Threshold | Nguồn |
|-----------|---------|-----------|-------|
| Sản phẩm sắp hết hàng | Variant có `on_hand` < 10 | Low stock alert | `inventory` + `dim_variant` |
| Sản phẩm hết hàng | Variant có `on_hand` = 0 | Out of stock | `inventory` |
| Tồn kho đầu kỳ vs hiện tại | So sánh `opening_on_hand` vs `on_hand` | Inventory drawdown | `inventory` |
| Tỷ lệ bán hết | Đã bán / opening_on_hand |越高越好 | `inventory` calculated |

### 2.5. Khách hàng

| Thông tin | Chi tiết | Phân tích | Nguồn |
|-----------|---------|----------|-------|
| Khách mới hôm nay | Customer có `created_at` = today | Acquisition tracker | `dim_customer` |
| Khách quay lại | Customer có > 1 order | Loyalty indicator | `fact_order` group by customer |
| Top customer theo chi tiêu | Customer có total spend cao nhất | VIP list | `fact_order` group by customer, order by total |

---

## 3. Quản lý Bán hàng (Sales Manager)

### 3.1. Phân tích Doanh thu theo Danh mục

| Thông tin | Chi tiết | Phân tích | Nguồn |
|-----------|---------|----------|-------|
| Revenue theo category | Doanh thu mỗi danh mục trong kỳ | Bar chart | `fact_order_item` join `dim_product` → category |
| Category growth | Tỷ lệ tăng trưởng mỗi danh mục | So sánh period | `mart_sales_daily` group by category |
| Cross-sell analysis | Danh mục nào hay mua kèm nhau | Market basket analysis | `fact_order_item` group by order, find co-occurrence |
| Category seasonality | Pattern theo mùa từng danh mục | Heatmap | `mart_sales_daily` monthly rollup |

### 3.2. Phân tích Sản phẩm

| Thông tin | Chi tiết | Phân tích | Nguồn |
|-----------|---------|----------|-------|
| SKU performance | Doanh thu/số lượng bán theo SKU | Table + ranking | `fact_order_item` group by sku |
| Product velocity | Tốc độ bán (units/day) trong 7/14/30 ngày | Trend | `fact_order_item` daily average |
| Stock-out impact | Sản phẩm hết hàng mất bao nhiêu doanh thu tiềm năng | Estimated lost revenue | `inventory.on_hand = 0` × `product_velocity` × `price` |
| New product uptake | Sản phẩm mới bán được bao nhiêu trong 30 ngày đầu | Lifecycle curve | `dim_product.created_date` + `fact_order_item` |
| Return rate by product | Tỷ lệ hoàn theo sản phẩm | % | `fact_refund` + `fact_order_item` |

### 3.3. Hiệu quả Khuyến mãi

| Thông tin | Chi tiết | Phân tích | Nguồn |
|-----------|---------|----------|-------|
| Coupon usage rate | Số lần dùng / total_usage_limit | % utilized | `dim_coupon.used_count` / `total_usage_limit` |
| Revenue attribution | Doanh thu từ đơn có coupon vs không | Compare groups | `fact_order` group by `coupon_id IS NOT NULL` |
| Discount impact | Tổng discount amount / total revenue | Cost of promotion | `fact_order.discount_amount_vnd` |
| Coupon ROI | (Revenue from coupon orders - discount amount) / discount amount | ROI metric | Calculated |
| Per-coupon performance | Top/bottom coupons theo usage và revenue | Ranking | `fact_coupon_redemption` join `fact_order` |
| Release rate | Tỷ lệ coupon bị release (đơn hủy) | Quality indicator | `fact_coupon_redemption.status = 'released'` |

### 3.4. Phân khúc Khách hàng

| Thông tin | Chi tiết | Phân tích | Nguồn |
|-----------|---------|----------|-------|
| RFM Segmentation | Recency (ngày cuối mua), Frequency (số đơn), Monetary (tổng chi tiêu) | 3×3 matrix = 9 segments | `fact_order` group by customer |
| New vs Returning | Khách mua lần đầu vs mua lại | % ratio | `fact_order` count per customer |
| Customer cohorts | Nhóm khách theo tháng đăng ký, retention rate | Cohort retention table | `dim_customer.created_date_key` + `fact_order` |
| VIP identification | Top 10% customer theo CLV | Pareto 80/20 | `fact_order` group by customer |
| Churn risk | Khách không mua > 90 ngày | At-risk list | `fact_order` MAX(created_at) per customer |

### 3.5. Dự báo Nhu cầu

| Thông tin | Chi tiết | Phương pháp | Nguồn |
|-----------|---------|------------|-------|
| Historical demand | Nhu cầu theo ngày/tuần cho từng sản phẩm | Time series | `fact_order_item` daily |
| Seasonal forecast | Dự báo nhu cầu mùa tiếp theo | Seasonal index | Historical 2 years |
| Trend projection | Xu hướng tăng/giảm | Linear regression | `mart_sales_daily` |
| New product demand | Ước tính nhu cầu sản phẩm mới | Analogous forecasting | Similar products historical |

---

## 4. Quản lý Kho / Warehouse Manager

### 4.1. Tồn kho Hiện tại

| Thông tin | Chi tiết | Đơn vị | Nguồn |
|-----------|---------|--------|-------|
| Tổng tồn kho | Tổng `on_hand` tất cả variants | units | SUM(`inventory.on_hand`) |
| Tồn kho theo category | Breakdown theo danh mục | units/category | `inventory` join `dim_variant` → `dim_product` → category |
| Tồn kho theo size | Size nào có nhiều hàng nhất | units/size | `inventory` join `dim_variant` group by size_code |
| Tồn kho theo màu | Màu nào có nhiều hàng nhất | units/color | `inventory` join `dim_variant` group by color_code |

### 4.2. Sản phẩm Cần Bổ sung

| Thông tin | Chi tiết | Threshold | Nguồn |
|-----------|---------|-----------|-------|
| Variant sắp hết | `on_hand` < reorder point (ví dụ 10) | Configurable | `inventory` WHERE `on_hand < threshold` |
| Variant hết hàng | `on_hand` = 0 | Critical | `inventory` WHERE `on_hand = 0` |
| Trend bán của variant sắp hết | Tốc độ bán 7 ngày qua | units/day | `fact_order_item` last 7 days per variant |
| Estimated stockout date | Ngày dự kiến hết hàng | Days | `on_hand` / `velocity_7d` |

### 4.3. Hiệu suất Nhập kho

| Thông tin | Chi tiết | Phân tích | Nguồn |
|-----------|---------|----------|-------|
| Opening vs Current | So sánh `opening_on_hand` vs `on_hand` | Drawdown % | `inventory` |
| Sell-through rate | Đã bán / opening × 100 |越高越好 | `(opening_on_hand - on_hand) / opening_on_hand × 100` |
| Slow-moving inventory | Variant có sell-through < 20% trong 30 ngày | Overstock risk | `inventory` + `fact_order_item` 30 days |
| Dead stock | Variant không bán được trong 90 ngày | Investigation | `inventory` where not in `fact_order_item` last 90 days |

### 4.4. Hoàn kho khi Hủy đơn

| Thông tin | Chi tiết | Kiểm tra | Nguồn |
|-----------|---------|---------|-------|
| Đơn hủy đã hoàn kho | Kiểm tra `on_hand` đã tăng lại sau cancelled | Reconciliation | `orders.status = cancelled` + `inventory.on_hand` |
| Inventory discrepancy | Phát hiện sai lệch giữa expected vs actual | Audit | Calculated from order items vs inventory changes |
| Refund + restore log | Đơn nào đã hoàn kho + hoàn tiền | Audit trail | `order_status_history` + `refunds` + `inventory` |

---

## 5. Marketing Manager

### 5.1. Phân tích Khách hàng

| Thông tin | Chi tiết | Phân tích | Nguồn |
|-----------|---------|----------|-------|
| Customer acquisition | Số khách mới theo tháng | Growth curve | `dim_customer.created_date_key` |
| Retention rate | Tỷ lệ khách quay lại mua trong 30/60/90 ngày | Cohort analysis | `fact_order` |
| Customer lifetime | Thời gian từ đăng ký đến đơn cuối cùng | Avg lifetime | `dim_customer` + `fact_order` |
| Purchase frequency | Số đơn trung bình mỗi khách | F = COUNT(orders) / COUNT(customers) | `fact_order` |
| Average order value by segment | AOV theo RFM segment | Compare segments | `fact_order` + RFM |

### 5.2. Hiệu quả Campaign

| Thông tin | Chi tiết | So sánh | Nguồn |
|-----------|---------|--------|-------|
| Pre vs Post campaign | Doanh thu trước/sau campaign ±7 ngày | A/B comparison | `mart_sales_daily` |
| New customer from campaign | Khách mới trong period campaign | Attribution | `dim_customer.created_date` within campaign period |
| Campaign ROI | (Incremental revenue - campaign cost) / campaign cost | ROI | Requires manual campaign cost input |

### 5.3. Wishlist Analysis

| Thông tin | Chi tiết | Phân tích | Nguồn |
|-----------|---------|----------|-------|
| Most wishlisted products | Sản phẩm được lưu nhiều nhất | Popularity | `wishlist_items` group by product_id |
| Wishlist to purchase conversion | Tỷ lệ wishlist → order | Conversion | `wishlist_items` vs `fact_order_item` |
| Abandoned wishlist | Sản phẩm trong wishlist > 30 ngày chưa mua | Re-engagement | `wishlist_items.last_added_at` |
| Wishlist by category | Phân bổ wishlist theo danh mục | Interest map | `wishlist_items` join `dim_product` |

### 5.4. Phân tích Review

| Thông tin | Chi tiết | Phân tích | Nguồn |
|-----------|---------|----------|-------|
| Average rating by product | Điểm trung bình mỗi sản phẩm | Quality metric | `product_reviews` group by product |
| Review volume | Số review theo tuần/tháng | Engagement | `product_reviews` count |
| Negative review alert | Review ≤ 2 sao | Quality alert | `product_reviews` WHERE rating <= 2 |
| Review to purchase ratio | Số review / số order của sản phẩm | Engagement | `product_reviews` / `fact_order_item` |
| Moderation queue | Review chờ duyệt | Ops | `product_reviews` WHERE status = 'approved' (auto) |

### 5.5. Search Analytics

| Thông tin | Chi tiết | Phân tích | Nguồn |
|-----------|---------|----------|-------|
| Top search keywords | Từ khóa tìm kiếm phổ biến nhất | Volume | `fact_web_events` WHERE ecommerce_action = 'search' |
| Zero-result queries | Tìm kiếm không có kết quả | UX issue | `fact_web_events` WHERE result_count = 0 |
| Search to purchase conversion | Tìm kiếm → mua hàng | Conversion | `fact_web_events` search → order funnel |

---

## 6. Kế toán / Tài chính (Finance)

### 6.1. Doanh thu Xác nhận

| Thông tin | Chi tiết | Điều kiện | Nguồn |
|-----------|---------|----------|-------|
| Confirmed revenue | Doanh thu chỉ từ đơn `completed` | exclude pending/cancelled | `fact_order` WHERE status = 'completed' |
| Recognized revenue by month | Doanh thu theo tháng (chính thức) | Accounting period | `fact_order` WHERE completed_at in month |
| Deferred revenue | Đơn `paid/confirmed` chưa `completed` | Not yet recognized | `fact_order` WHERE status IN ('paid','confirmed') |

### 6.2. Hoàn tiền & Chi phí

| Thông tin | Chi tiết | Phân tích | Nguồn |
|-----------|---------|----------|-------|
| Total refunds | Tổng refund thành công trong kỳ | Cost | `fact_refund` WHERE status = 'succeeded' |
| Refund by reason | Phân bổ refund theo lý do | Root cause | `fact_refund` group by reason |
| Refund rate | Refund / revenue × 100 | KPI | Calculated |
| Discount cost | Tổng discount từ coupon | Marketing cost | `fact_order.discount_amount_vnd` |

### 6.3. Dự toán Dòng tiền

| Thông tin | Chi tiết | Tính toán | Nguồn |
|-----------|---------|----------|-------|
| Cash inflow | Tổng payment thành công | Actual cash in | `fact_payment.amount_vnd` WHERE status = 'succeeded' |
| Cash outflow | Tổng refund hoàn tất | Actual cash out | `fact_refund.amount_vnd` WHERE status = 'succeeded' |
| Net cash flow | Inflow - Outflow | Net position | Calculated |
| Outstanding payments | Đơn `paid` nhưng payment chưa succeed | Pending | `fact_payment` WHERE status = 'failed' |

### 6.4. Báo cáo

| Thông tin | Chi tiết | Tần suất | Nguồn |
|-----------|---------|---------|-------|
| Daily P&L | Profit & Loss hàng ngày | Daily | Revenue - refunds - costs |
| Monthly financial report | Báo cáo tài chính tháng | Monthly | Aggregated from facts |
| Tax summary | Tổng VAT (nếu có) | Per period | `fact_order.subtotal_vnd` |
| Reconciliation check | Đối chiếu OLTP vs DWH totals | Daily | `fact_order` vs `orders` COUNT/SUM |

---

## 7. Chăm sóc Khách hàng / Operations (CS/Ops)

### 7.1. Trạng thái Đơn hàng

| Thông tin | Chi tiết | Nguồn |
|-----------|---------|-------|
| Order status lookup | Nhập order_number → xem status hiện tại | `fact_order` |
| Status timeline | Lịch sử transition trạng thái | `order_status_history` |
| Current status distribution | Phân bổ đơn theo status hiện tại | `fact_order` group by status |
| Aging orders | Đơn > N ngày chưa xử lý | `fact_order` DATEDIFF |

### 7.2. Thời gian Xử lý

| Thông tin | Chi tiết | Tính toán | Nguồn |
|-----------|---------|----------|-------|
| Avg processing time | Thời gian trung bình paid → confirmed | AVG(transition time) | `order_status_history` |
| Avg confirmation time | paid → confirmed | Per order | `order_status_history` WHERE to_status = 'confirmed' |
| Avg completion time | confirmed → completed | Per order | `order_status_history` WHERE to_status = 'completed' |
| Avg total cycle time | created → completed | Per order | `fact_order` DATEDIFF(created_at, completed_at) |
| SLA compliance | Tỷ lệ đơn xử lý trong N giờ | % | Calculated |

### 7.3. Lý do Hủy & Hoàn tiền

| Thông tin | Chi tiết | Phân tích | Nguồn |
|-----------|---------|----------|-------|
| Top cancellation reasons | Các lý do hủy phổ biến nhất | Bar chart | `order_status_history` WHERE to_status = 'cancelled' group by reason |
| Cancellation by product | Sản phẩm nào bị hủy nhiều | Product quality | `fact_order` cancelled + `fact_order_item` |
| Cancellation by time | Hủy thường xảy ra ở giai đoạn nào | Funnel analysis | `order_status_history` |
| Refund processing time | Thời gian xử lý hoàn tiền | AVG days | `refunds.created_at` → `refunds.completed_at` |

### 7.4. Customer 360 View

| Thông tin | Chi tiết | Nguồn |
|-----------|---------|-------|
| Customer profile | Tên, status, ngày đăng ký | `dim_customer` |
| Order history | Tất cả đơn của customer | `fact_order` WHERE customer_key |
| Total spend | Tổng chi tiêu lifetime | SUM(`fact_order.total_vnd`) |
| Last order date | Đơn cuối cùng | MAX(`fact_order.created_at`) |
| Review history | Các review đã viết | `product_reviews` WHERE customer_id |
| Active coupons | Coupon đang khả dụng | `dim_coupon` WHERE is_active |
| Complaint history | Đơn bị hủy, refund | `fact_order` cancelled + `fact_refund` |

---

## 8. Tổng hợp Ma trận Nhu cầu

| Cấp bậc | Doanh thu | Tồn kho | Đơn hàng | Khách hàng | KM | Thanh toán | Reviews | Search |
|---------|-----------|---------|----------|------------|-----|------------|---------|--------|
| CEO | ★★★ | ★ | ★★ | ★★ | ★★ | ★★ | ★ | ★ |
| Store Mgr | ★★ | ★★★ | ★★★ | ★ | ★ | ★ | ★ | ★ |
| Sales Mgr | ★★★ | ★★ | ★★ | ★★★ | ★★★ | ★ | ★★ | ★★ |
| Warehouse | ★ | ★★★ | ★★ | ★ | ★ | ★ | ★ | ★ |
| Marketing | ★★ | ★ | ★ | ★★★ | ★★★ | ★ | ★★★ | ★★★ |
| Finance | ★★★ | ★ | ★★ | ★ | ★★ | ★★★ | ★ | ★ |
| CS/Ops | ★ | ★ | ★★★ | ★★★ | ★ | ★★ | ★★ | ★ |

**Legend:** ★★★ = Cần thiết, ★★ = Hữu ích, ★ = Tham khảo

---

## 9. Mapping sang DWH Star Schema

| Nhóm thông tin | Dimension cần | Fact cần | Mart cần |
|---------------|---------------|----------|----------|
| Doanh thu (tất cả cấp) | `dim_date`, `dim_product`, `dim_category` | `fact_order`, `fact_order_item`, `fact_payment` | `mart_sales_daily` |
| Tồn kho | `dim_variant`, `dim_product` | (snapshot từ `inventory`) | `mart_inventory_daily` |
| Đơn hàng | `dim_date`, `dim_customer`, `dim_order_status` | `fact_order`, `fact_order_item`, `order_status_history` | — |
| Khách hàng | `dim_customer`, `dim_date` | `fact_order` (RFM calculation) | `mart_customer_rfm` |
| Khuyến mãi | `dim_coupon`, `dim_date` | `fact_coupon_redemption` | `mart_coupon_performance` |
| Thanh toán | `dim_date` | `fact_payment`, `fact_refund` | — |
| Reviews | `dim_product`, `dim_customer` | `fact_product_review` | — |
| Search/Behavior | `dim_product`, `dim_date` | `fact_web_events` (logs) | `mart_daily_product_demand` |
