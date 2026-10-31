# B — Nghiệp vụ phân tích theo vai trò

D&K kết hợp bán online và POS, dùng MySQL làm nguồn giao dịch và Lakehouse phục vụ lịch sử phân tích. Tài liệu ánh xạ câu hỏi quản trị với các góc nhìn BI đang có; công thức chi tiết được quản lý tại [Metrics Catalog](METRICS_CATALOG.md).

## 1. Phạm vi dữ liệu phục vụ quyết định

- Đơn, thanh toán, hoàn tiền và snapshot giá bán/giá vốn cung cấp dữ liệu bán hàng.
- Tồn kho tổng/cửa hàng, phiếu nhập và ledger cung cấp dữ liệu hàng hóa.
- Shipment, lần giao và trả hàng cung cấp dữ liệu vận hành sau bán.
- Access log cung cấp sự kiện HTTP/hành vi; chưa có mô hình session hoặc định danh unique visitor đầy đủ.
- Gold OLTP xây theo batch; store/inventory/operations đọc MySQL hiện tại. CDC lưu sự kiện ở Bronze, chưa là nguồn cập nhật trực tiếp cho toàn bộ dashboard.

Dữ liệu generator là tổng hợp. Mẫu phân phối hoặc quy mô cấu hình không phải số liệu kinh doanh thực tế hay kết quả đánh giá hiệu năng.

## 2. Góc nhìn và quyền truy cập

| Góc nhìn BI | Role tài khoản | Câu hỏi chính | Nguồn chính |
|---|---|---|---|
| Executive | `admin` | Quy mô đơn, doanh thu, giá vốn, lợi nhuận và rủi ro COD? | Gold order + mart returns; MySQL bổ sung |
| Sales | `sales_manager` | Kênh/cửa hàng/sản phẩm/danh mục nào đóng góp doanh thu? | Gold facts và sales mart |
| Marketing | `marketing_manager` | Lượng sự kiện chuyển đổi, sử dụng coupon và review xấu? | Gold web events 30 ngày + MySQL |
| Store | `store_manager` | Hôm nay bán bao nhiêu, SKU nào thiếu tại cửa hàng? | MySQL, cửa hàng được gán |
| Inventory | `inventory_manager` | Vốn tồn, lượng hàng và nguy cơ hết SKU? | MySQL |
| Operations | `operations_manager` | Đơn chờ, lần giao lỗi, COD và yêu cầu trả? | MySQL |
| System | `system_admin` | Gold mới tới đâu và chênh với nguồn ở chỉ số nào? | Trino Gold so với MySQL |

`admin` được chọn mọi góc nhìn; role khác chỉ được góc nhìn tương ứng. Phạm vi cửa hàng được xử lý ở API, không phải Trino RLS. Quyền xem KPI khác quyền ghi nghiệp vụ: API đơn/giao vận/trả hàng hiện vẫn yêu cầu `admin` dù UI mở menu cho `operations_manager`.

## 3. Executive và Sales

Executive trả GMV, net revenue, COGS, gross profit/margin, total orders, AOV, boom rate và return rate. COD đang giao được bổ sung từ MySQL. Lợi nhuận ở đây là doanh thu trừ giá vốn, chưa bao gồm toàn bộ chi phí vận hành.

Sales trả đóng góp cửa hàng/kênh, sản phẩm bán chạy và cơ cấu danh mục. Endpoint sales trend cung cấp chuỗi revenue/COGS/profit/orders theo ngày với lựa chọn 7/30/90 ngày trên UI. Bộ lọc này không đồng thời giới hạn mọi KPI tổng quan.

Các giới hạn cần giữ khi viết báo cáo:

- Order fact loại một số trạng thái khỏi net revenue; sales mart chỉ tính item revenue của đơn delivered/completed. Hai cách ghi nhận không thể thay thế cho nhau.
- Số đơn trong sales mart có thể lặp qua danh mục. Không cộng các nhóm đó thành distinct orders toàn hệ thống.
- Fallback MySQL có quy tắc tiền thanh toán/hoàn tiền khác Gold. So sánh hai nguồn phải xét công thức và thời điểm.
- Chưa có bảng target hoặc mô hình dự báo được phục vụ. Các trường margin-erosion/channel-growth/viral/run-rate chưa có nguồn tính phù hợp không được hiển thị như số đo đã có.

## 4. Marketing

Dashboard theo dõi các bước xem sản phẩm, giỏ, checkout và mua trong cửa sổ 30 ngày. Đây là số **sự kiện**, không phải số người duy nhất, cohort hay chuỗi hành trình đã nối theo session. Một người có thể tạo nhiều sự kiện; số bước không bắt buộc giảm dần.

Coupon signal sử dụng số redemption trong 15 phút, `used_count`, giới hạn sử dụng và tỷ lệ đã dùng. Giới hạn sử dụng là số lượt coupon, không mặc định là ngân sách tiền quảng cáo. Review signal đếm đánh giá rating ≤ 2 trong 45 phút theo sản phẩm.

Nếu Gold không có event trong kỳ hoặc Trino lỗi, service có thể dùng đơn/cart item/customer MySQL làm proxy và đánh dấu degraded. Proxy này không chứng minh lượng truy cập website. Chưa có tích hợp nền tảng quảng cáo, attribution doanh thu campaign, ROAS/CAC hoặc gán nhãn cảm xúc bằng NLP.

## 5. Cửa hàng và tồn kho

Store view trả doanh thu/số đơn hôm nay, tồn thấp và SKU hết tại cửa hàng được phép. Ranh giới ngày dùng `Asia/Ho_Chi_Minh`; tập trạng thái tính doanh thu được nêu trong Metrics Catalog. Không có chỉ tiêu doanh thu được lưu nên target achievement và run-rate không được dựng từ số mẫu.

Inventory view trả giá trị tồn theo giá vốn hiện tại, tổng lượng kho/cửa hàng, số phiếu nhập, SKU hết hàng và tín hiệu tốc độ bán trong 60 phút. Dự kiến thời gian hết hàng là phép chia tồn hiện tại cho tốc độ gần đây; chưa phải mô hình dự báo nhu cầu đã huấn luyện. Số SKU hết là distinct variant có tồn bằng 0 ở ít nhất một địa điểm, khác số cặp variant–địa điểm hết hàng.

Gold inventory snapshot và mart hỗ trợ truy vấn phân tích, nhưng API vận hành hiện đọc MySQL. Tên bảng daily snapshot không chứng minh có đầy đủ snapshot của tất cả ngày trong lịch sử.

## 6. Vận hành đơn và giao hàng

Operations view tổng hợp đơn chờ xử lý, đơn chờ quá hai giờ, thời gian chờ trung bình, giao vận có vấn đề, đơn failed_delivery, yêu cầu trả và COD failed theo vùng.

`shipping_sla_violations_count` hiện dựa trên shipment có nhiều lần giao hoặc trạng thái failed; chưa đối chiếu một deadline SLA cụ thể. Nhóm vùng dựa trên từ khóa địa chỉ. Tiền COD đang giao dựa trên tổng giá trị đơn có shipment đang vận chuyển, chưa phải sổ quyết toán tiền mặt thực tế của shipper. Các nhóm đơn/shipment có thể chồng lặp nên không diễn giải như những phần loại trừ nhau của một biểu đồ cơ cấu.

Shipper được lưu ở `delivery_staff`; thao tác cập nhật do API quản trị thực hiện. Chưa có ứng dụng/đăng nhập shipper hoặc tích hợp hãng giao vận bên ngoài.

## 7. Chất lượng và đối soát

System view hiển thị tuổi Gold, trạng thái suy ra từ freshness/variance và các cặp giá trị MySQL–Gold. UI vẽ riêng từng chỉ số: total orders dùng đơn vị đơn; tiền dùng VND và trục riêng. Tooltip tiền hiển thị giá trị đầy đủ; badge chênh lệch dùng `variance_percent` từ API. Khi fallback hoặc không có cặp so sánh, UI không trình bày các giá trị placeholder Gold/variance như số liệu đối soát đã đo.

Ngưỡng 15/60 phút và 5/20% phục vụ trạng thái UI, khác ngưỡng reconciliation pipeline 0,05%. Dashboard này không thay thế kiểm tra trạng thái từng task Airflow, từng job Flink hoặc audit quality gate. Gold có lịch batch hằng ngày; nhấn refresh chỉ tải lại API.

## 8. Cách đọc nguồn và kết quả

Response có `data_source`, `is_degraded`, `degraded_reason`. Thời điểm trình duyệt nhận response khác thời điểm pipeline cập nhật Gold. Marketing/store/inventory/operations tự refresh 60 giây khi trang hoạt động; các góc nhìn khác dùng thao tác tải lại.

Khi trình bày kết quả, ghi rõ dataset, kỳ dữ liệu, grain, công thức, bộ lọc, đơn vị và nguồn. Các câu hỏi mở rộng như dự báo, CLV, retention cohort, recommendation và đánh giá hiệu quả quảng cáo cần dữ liệu/mô hình bổ sung; chưa phải chức năng hiện có.

## Nguồn đối chiếu

- [Analytics service](../../services/ecommerce-api/app/modules/analytics/service.py), [response schemas](../../services/ecommerce-api/app/modules/analytics/schemas.py), [router](../../services/ecommerce-api/app/modules/analytics/router.py).
- [Dashboard components](../../apps/storefront/src/components/analytics), [BI page](../../apps/storefront/src/app/admin/analytics/page.tsx).
- [Gold OLTP](../../pipelines/src/lakehouse/oltp/gold.py), [Gold logs](../../pipelines/src/lakehouse/logs/gold.py).
- [Kiến trúc](SYSTEM_ARCHITECTURE_VISUAL.md), [nghiệp vụ nguồn](../project/BUSINESS_REQUIREMENTS.md).
