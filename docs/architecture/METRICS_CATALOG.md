# Danh mục chỉ số đang triển khai

Tài liệu mô tả công thức trong pipeline và API hiện tại. Đây là định nghĩa tính toán, không phải kết quả benchmark hay cam kết SLA. Dữ liệu tổng hợp cần được ghi rõ khi dùng để minh họa kết quả đồ án.

Nguồn chính: [Gold OLTP](../../pipelines/src/lakehouse/oltp/gold.py), [Gold logs](../../pipelines/src/lakehouse/logs/gold.py), [analytics service](../../services/ecommerce-api/app/modules/analytics/service.py).

Vai trò dashboard, API và phạm vi truy cập được mô tả trong [kiến trúc serving](SYSTEM_ARCHITECTURE_VISUAL.md#5-serving-và-phân-quyền).

## 1. Quy ước đọc số liệu

- Tiền là số nguyên VND. Lợi nhuận trong Gold là doanh thu trừ giá vốn, chưa trừ đầy đủ chi phí vận hành, thuế và quảng cáo.
- Phải kiểm tra grain trước khi SUM hoặc JOIN. `fact_order` có một dòng/đơn; `fact_order_item` có một dòng/chi tiết đơn.
- Đếm đơn toàn hệ thống bằng `COUNT(DISTINCT order_id)` trên fact. Một đơn có nhiều nhóm sản phẩm sẽ xuất hiện ở nhiều dòng `mart_sales_daily`.
- `data_source` cho biết `lakehouse`, `oltp` hoặc `oltp_fallback`. `is_degraded` và `degraded_reason` cho biết nguồn thay thế hoặc dữ liệu chưa đầy đủ.
- Ngày hôm nay ở chỉ số cửa hàng dùng Asia/Ho_Chi_Minh. Log Flink chuyển timestamp sang giờ Việt Nam trước SQL cast và tạo event_date theo ngày đó; Spark session dùng UTC. Kiểm tra timestamp lưu và múi giờ engine khi đối chiếu ngày/giờ, không mặc định tất cả bucket là UTC.

## 2. Doanh thu, giá vốn và lợi nhuận

| Chỉ số | Công thức hiện tại | Nguồn / grain |
|---|---|---|
| GMV executive | `SUM(gross_revenue_vnd)`; mỗi giá trị gốc là `orders.total_vnd` | `fact_order`, một dòng/đơn, không lọc bỏ trạng thái trong truy vấn executive |
| Giá vốn mỗi đơn | `SUM(quantity × cost_price_vnd)`; dùng cột snapshot nếu schema có cột này (null thành 0), chỉ fallback cột variant khi schema thiếu snapshot | `fact_order` / `fact_order_item` |
| Net revenue mỗi đơn | 0 nếu `failed_delivery`, `returned`, `cancelled`, `payment_failed`; các trạng thái khác lấy `total_vnd` | `fact_order.net_revenue_vnd` |
| Net profit mỗi đơn | 0 cho bốn trạng thái trên; còn lại `total_vnd - total_cost_vnd` | `fact_order.net_profit_vnd` |
| Gross profit executive | `SUM(net_profit_vnd)` | `fact_order`; tên API không có nghĩa là lợi nhuận kế toán sau mọi chi phí |
| COGS executive | `SUM(net_revenue_vnd - net_profit_vnd)` | `fact_order` |
| Gross margin | `gross_profit / net_revenue × 100`, trả 0 nếu mẫu số không dương | API executive |
| Total orders | `COUNT(DISTINCT order_id)` | `fact_order` |
| AOV executive | `net_revenue / total_orders`, trả 0 nếu mẫu số hoặc doanh thu không dương | API executive; mẫu số gồm mọi đơn |
| Doanh thu sales mart | Tổng `item_total_vnd` của đơn `delivered`/`completed` | `mart_sales_daily`, ngày × kênh × cửa hàng × danh mục |
| COGS/profit sales mart | Tổng item cost/profit của đơn `delivered`/`completed` | `mart_sales_daily` |
| Tỷ lệ giao thất bại executive | `SUM(is_boom) / total_orders × 100` | `fact_order`, `is_boom` khi đơn `failed_delivery` |
| Return rate executive | `SUM(total_return_requests)` ở mart trả hàng / số đơn × 100 | Mart có grain theo chi tiết trả hàng; chưa phải tỷ lệ số đơn được trả distinct |

**Hai cách ghi nhận doanh thu đang khác nhau:** `fact_order.net_revenue_vnd` loại bốn trạng thái không ghi nhận, nên có thể còn tính đơn chưa giao. Sales mart chỉ cộng item revenue của đơn delivered/completed. GMV order total còn có thể chứa phí ship, trong khi tổng item không tương đương order total. Không mô tả tất cả các trường này bằng cùng một tên “doanh thu đã giao”.

OLTP fallback executive dùng tiền thanh toán thành công trừ hoàn tiền thành công, COGS của đơn delivered/completed và GMV bỏ đơn cancelled. Vì thế fallback không phải bản sao công thức Gold; UI cần hiển thị nguồn. Biểu đồ sales trend cộng mart theo ngày, nên `orders_count` có thể trùng đơn khi cộng qua danh mục.

Gold order hiện suy ra net revenue từ trạng thái và order total, không trực tiếp trừ mọi refund trả lẻ. Khi mới trả một phần và order chưa returned, net revenue có thể chưa phản ánh khoản hoàn một phần. Không dùng công thức này như số liệu kế toán đã đối soát hoàn tiền đầy đủ.

## 3. Chỉ số vận hành từ MySQL

| Chỉ số | Công thức / phạm vi |
|---|---|
| Doanh thu/số đơn cửa hàng hôm nay | Tổng `Order.total_vnd` / đếm đơn của store từ 00:00 giờ Việt Nam, trạng thái paid/shipping/delivered/completed |
| Tồn kho thấp cửa hàng | Số dòng `store_inventory` có `on_hand <= 5` tại store được phép |
| Giá trị tồn kho | Tổng `on_hand × variant.cost_price_vnd` ở kho trung tâm và cửa hàng |
| Số lượng tồn | Tổng on_hand theo từng nhóm kho/cửa hàng |
| Số SKU hết hàng | Số variant distinct xuất hiện với on_hand=0 ở kho hoặc cửa hàng; không phải số cặp SKU–địa điểm |
| Tốc độ xuất hàng | Số lượng bán trong 60 phút / 60; thời gian dự kiến hết hàng lấy tồn hiện tại chia tốc độ |
| Đơn chờ xử lý | Query paid/confirmed/processing; processing không nằm trong CHECK trạng thái orders hiện tại, nên dữ liệu đúng DDL chỉ đóng góp paid/confirmed |
| Đơn chờ quá 2 giờ | Đếm paid/confirmed với created_at trước ngưỡng 2 giờ |
| Thời gian chờ trung bình | Trung bình số giờ từ created_at tới hiện tại của đơn paid/confirmed/processing |
| Giao vận có vấn đề | Trường API `shipping_sla_violations_count` hiện đếm shipment attempt_count > 1 hoặc status failed; chưa phải so sánh deadline SLA |
| Tỷ lệ COD lỗi theo vùng | Shipment COD failed / tổng shipment COD trong nhóm địa chỉ; nhóm vùng dựa trên từ khóa địa chỉ |
| Tiền COD đang giao | Tổng order total của COD có shipment dispatched/in_transit; chưa phải số dư tiền thực tế shipper đang giữ |
| Coupon burn rate | Số redemption trong 15 phút / 15; phần trăm sử dụng = used_count / total_usage_limit, không tự đặt limit khi coupon không có cap |
| Đánh giá xấu gần đây | Đếm rating <= 2 trong 45 phút, nhóm theo product |

Mục tiêu 15 triệu/ngày, các mốc doanh thu chia sẵn theo giờ, biên lợi nhuận nội suy, tỷ lệ chia tiền cho nhà vận chuyển và nhãn “viral” áp cứng đã được bỏ. `target_achievement_percent`, run-rate, margin-erosion và channel-growth không có dữ liệu khi chưa có cách tính từ nguồn phù hợp; UI ẩn các biểu đồ tương ứng.

Một số trường API vẫn optional để tương thích giao diện. Khi thiếu dữ liệu, API trả `null` hoặc danh sách rỗng; target là `null` và UI ẩn phần chỉ tiêu. Các trường SLA/COD cần được diễn giải theo công thức trong tài liệu này, không chỉ theo tên trường.

## 4. Access log và hành vi web

| Chỉ số | Công thức / grain |
|---|---|
| Total requests | Số dòng sự kiện; mart theo event_date × giờ của event_ts trong Spark × route × method; xem quy tắc múi giờ ở mục 1 |
| Duration | `event_duration_ns / 1_000_000`, đơn vị ms |
| Error rate | `(4xx + 5xx) / total_requests × 100` |
| Avg / p50 / p95 / p99 | AVG duration và `percentile_approx` theo nhóm route/giờ |
| Slow request | duration_ms >= 1000 |
| Product demand | Đếm action product_detail/cart_add/cart_remove/wishlist_add/checkout_quote theo ngày × product |
| Funnel views | Action product_detail/catalog_search hoặc route sản phẩm |
| Funnel cart / checkout | Action hoặc route cart / checkout tương ứng |
| Funnel purchase | Action order_complete/order_confirm_internal hoặc checkout_submit thành công |
| Conversion marketing | Purchase events / view events × 100, cửa sổ 30 ngày |

Funnel hiện đếm **sự kiện**, không phải unique visitor hoặc chuỗi session đã gắn kết. Nhiều request của cùng người có thể được tính nhiều lần; tỷ lệ không được hiểu là xác suất một người mua hàng. `total_visitors` là tên API cho lượt sự kiện đầu phễu. Cột `success_2xx_count` ở mart hiện cộng `is_success`, mà logic bao gồm cả phản hồi <400.

Khi không có log trong kỳ hoặc nguồn lỗi, marketing có thể dùng OLTP fallback: số đơn, cart item và khách hàng được tạo trong 30 ngày. Đây là proxy nghiệp vụ, không thay thế phép đo truy cập web; response đánh dấu degraded.

## 5. Chỉ số kỹ thuật DE

| Chỉ số | Cách lấy / giới hạn |
|---|---|
| Row count từng tầng | COUNT theo table/run_id hoặc snapshot cụ thể; phân biệt Bronze history và Silver current state |
| Source–Silver variance | `abs(source-target)/abs(source) × 100`; source=0/target!=0 được tính 100%; ngưỡng gate mặc định 0,05% |
| Gold parity | Count/tiền, PK, FK, lineage và PII token được kiểm tra bởi quality gate |
| Gold freshness | Thời gian hiện tại trừ `MAX(_gold_ingested_at)` của fact_order; không phải tuổi của từng bản ghi nguồn |
| CDC event count | Đếm theo table_name, operation, event_date; số event khác số bản ghi hiện hữu ở nguồn |
| CDC traceability | event_id, before/after, binlog và Kafka offset; kiểm tra replay/truy vết từ Bronze |
| Processing duration / throughput | Lấy từ log thời gian và khối lượng lần chạy; repo không ấn định con số benchmark |

Trang system đánh dấu degraded khi variance >5% hoặc freshness >15 phút; unhealthy khi variance >20%, freshness >60 phút hoặc chưa xác định được freshness. Đây là ngưỡng giao diện, khác ngưỡng đối soát pipeline 0,05%. Lịch batch hằng ngày khiến Gold có thể cũ hơn ngưỡng UI giữa hai lần chạy.

Đối soát dashboard dùng hai metric: `total_orders` so COUNT đơn MySQL với COUNT DISTINCT order_id Gold; `gross_revenue_vnd` so SUM orders.total_vnd với SUM fact_order.gross_revenue_vnd, đều gồm mọi trạng thái. Chênh lệch = abs(OLTP−Gold)/OLTP × 100, làm tròn hai chữ số; OLTP=0 thì 0% nếu Gold=0, ngược lại 100%.

UI vẽ từng metric riêng để số đơn không dùng chung thang với doanh thu. Số đơn có đơn vị đơn; tiền có trục VND, nhãn rút gọn và tooltip giá trị đầy đủ; badge dùng variance_percent từ API. Trong fallback, API còn trả các giá trị placeholder Gold=0/variance=100%, nhưng UI ẩn cột so sánh và hiển thị thiếu nguồn. Không đọc các placeholder như chênh lệch đã đo.

## 6. Cách trình bày kết quả

Ghi rõ dataset, dữ liệu tổng hợp hay phát sinh thật, thời gian chạy, tầng/bảng, bộ lọc, grain, công thức, đơn vị và nguồn response. Các tài liệu A–D mô tả nghiệp vụ và giới hạn, không cung cấp bộ số liệu đo để thay thế truy vấn thực tế.
