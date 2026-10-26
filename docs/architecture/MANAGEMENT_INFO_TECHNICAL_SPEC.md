# Phục vụ phân tích và dashboard

Tài liệu này mô tả lớp serving đã có trong đồ án DE. [Metrics Catalog](METRICS_CATALOG.md) là nơi định nghĩa công thức; [BUSINESS_DOMAIN](BUSINESS_DOMAIN.md) giữ các nhu cầu kinh doanh mở rộng cho tiểu luận.

## 1. Luồng phục vụ

BI Hub `/admin/analytics` gọi FastAPI. API xác thực vai trò và cửa hàng, đọc Trino/MySQL rồi trả JSON cho ECharts.

- Trino đọc Iceberg qua Polaris/MinIO.
- MySQL cung cấp trạng thái vận hành hiện tại.
- Frontend không gọi Trino, Spark, Polaris hoặc MySQL trực tiếp.
- Dữ liệu tổng hợp do generator tạo vẫn là dữ liệu tổng hợp, dù được xử lý qua pipeline hoàn chỉnh.

## 2. Vai trò và nguồn dữ liệu

| Vai trò hiển thị | Vai trò tài khoản | Nguồn chính / nội dung |
|---|---|---|
| Executive | `admin` | Gold fact_order và mart trả hàng; tổng doanh thu, cost/profit, đơn; bổ sung COD đang giao từ OLTP |
| Sales | `sales_manager` | Gold fact_order/fact_order_item/mart_sales_daily; doanh thu kênh, cửa hàng, sản phẩm |
| Marketing | `marketing_manager` | Gold fact_web_events trong 30 ngày; bổ sung coupon/review từ OLTP |
| Store | `store_manager` | MySQL theo cửa hàng; doanh thu hôm nay, số đơn, stockout |
| Inventory | `inventory_manager` | MySQL; lượng/giá trị tồn, inbound, depletion |
| Operations | `operations_manager` | MySQL; đơn chờ, shipment, COD lỗi, return |
| System | `system_admin` | Gold freshness và đối soát count/tiền với MySQL |

Admin có quyền truy cập các dashboard; các vai trò khác bị giới hạn bởi hàm `validate_role_access`. Store manager bị cố định theo cửa hàng được gán bằng `resolve_effective_store_id`. Đây là lọc ở ứng dụng/API, không phải row-level security tự động trong Trino.

## 3. API và trạng thái nguồn

| Endpoint | Mục đích |
|---|---|
| `GET /api/v1/admin/analytics/role-metrics` | Chỉ số theo vai trò và store hợp lệ |
| `GET /api/v1/admin/analytics/stores` | Danh sách cửa hàng theo quyền |
| `GET /api/v1/admin/analytics/sales-trend` | Biểu đồ theo ngày, quyền admin/sales_manager |
| `GET /api/v1/admin/analytics/overview` | Tổng quan OLTP, quyền admin |

Mỗi response analytics có `data_source`, `is_degraded`, `degraded_reason`. Trino lỗi có thể dẫn đến OLTP fallback; marketing không có event trong cửa sổ cũng có thể fallback. Các công thức fallback không phải lúc nào cũng đồng nhất với Gold, nên nguồn cần hiển thị trên UI.

Store/inventory/operations ưu tiên OLTP ngay cả khi Trino đang hoạt động. Marketing/store/inventory/operations có cơ chế tự tải lại 60 giây khi trang hoạt động; việc reload không khiến batch Gold tự chạy.

## 4. Phần không còn dùng số minh họa

Đã gỡ seed kịch bản, nút đăng nhập nhanh và SQL chèn sẵn Gold. Các mốc doanh thu chia theo giờ, mục tiêu 15 triệu/ngày, biên lợi nhuận nội suy, tỷ lệ chia COD cho nhà vận chuyển và chỉ số growth/viral không có căn cứ thời gian đã được bỏ khỏi response tính toán.

API giữ một số trường optional để tương thích giao diện. Không có số liệu thì trả null/danh sách rỗng; target là null và UI ẩn phần chỉ tiêu. Các chỉ số còn lại được tính từ dữ liệu nguồn theo cửa sổ và công thức trong Metrics Catalog.

## 5. Giới hạn diễn giải

- Funnel là lượt event, chưa phải conversion theo unique visitor/session.
- Fact_order revenue, sales mart revenue và OLTP fallback có quy tắc khác nhau.
- Số order trên mart theo danh mục có thể trùng khi cộng lên toàn hệ thống.
- Freshness UI 15/60 phút không phải SLA của batch chạy hằng ngày.
- Thuật ngữ SLA/COD ở một số field là tên API; đọc công thức thực tế trước khi viết kết luận kinh doanh.

Nguồn: [router](../../services/ecommerce-api/app/modules/analytics/router.py), [service](../../services/ecommerce-api/app/modules/analytics/service.py), [schemas](../../services/ecommerce-api/app/modules/analytics/schemas.py), [BI Hub](../../apps/storefront/src/app/admin/analytics/page.tsx).
