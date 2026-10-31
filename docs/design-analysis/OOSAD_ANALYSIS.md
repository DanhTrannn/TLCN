# A — Phân tích và thiết kế hệ thống

Tài liệu đối chiếu với router, service, model, giao diện và pipeline trong repository. Phạm vi gồm ứng dụng tạo dữ liệu giao dịch, ba luồng thu thập và lớp BI. Các sơ đồ chỉnh sửa được đặt tại [docs/diagram](../diagram/README.md); tài liệu này bổ sung điều kiện và giới hạn của từng luồng.

## 1. Tác nhân và ranh giới

| Tác nhân | Tương tác hiện có |
|---|---|
| Khách chưa đăng nhập | Xem danh mục, sản phẩm, đánh giá công khai và cửa hàng còn hàng |
| Người dùng đăng nhập | Giỏ hàng, wishlist, checkout, đơn của mình, xác nhận nhận hàng, đánh giá và yêu cầu trả hàng |
| `admin` | Quản trị nghiệp vụ và truy cập các góc nhìn BI |
| `store_manager` | Dashboard, đơn, tồn và nhân sự của cửa hàng được gán; POS |
| `sales_manager` | Dashboard bán hàng và sales trend |
| `marketing_manager` | Dashboard marketing, coupon và hậu kiểm đánh giá |
| `inventory_manager` | Sản phẩm/biến thể, nhập kho và dashboard kho |
| `operations_manager` | Dashboard vận hành; quyền API quản trị đơn/giao vận/trả hàng vẫn yêu cầu `admin` |
| `system_admin` | Dashboard chất lượng/đối soát; không đồng nghĩa toàn quyền quản trị ứng dụng |
| Người vận hành dữ liệu | Khởi động dịch vụ, nạp nguồn, chạy DAG, kiểm tra Kafka/Flink/Trino và kết quả chất lượng |

Nhân viên giao hàng là thực thể trong `delivery_staff`, chưa có cơ chế đăng nhập riêng. Các service account MinIO/Polaris là danh tính kỹ thuật, không phải role đăng nhập website. POS API cho phép staff theo cửa hàng được gán, riêng `admin`/`system_admin` được bỏ qua kiểm tra gán cửa hàng; giao diện `/store` vẫn giới hạn `store_manager`/`admin`.

Nguồn quyền: [dependencies](../../services/ecommerce-api/app/db/deps.py), [store router](../../services/ecommerce-api/app/modules/store/router.py), [POS router](../../services/ecommerce-api/app/modules/pos/router.py), [định tuyến UI](../../apps/storefront/src/lib/role-routes.ts).

## 2. Các ca sử dụng của ứng dụng nguồn

| Ca sử dụng | Điều kiện / kết quả chính | Module |
|---|---|---|
| Đăng ký, đăng nhập, đăng xuất | Tài khoản active; JWT cookie và CSRF cookie | `auth` |
| Khám phá catalog | Tìm kiếm, lọc, xem biến thể và giá; category chỉ có API đọc | `catalog` |
| Tra cứu địa điểm còn hàng | City → store → tồn biến thể; không giữ hàng | `location` |
| Quản lý giỏ và wishlist | Có đăng nhập; thao tác thêm/sửa/xóa theo định danh public | `cart`, `wishlist` |
| Báo giá và checkout | Kiểm tra lại hàng, giá, coupon; tạo order/payment, trừ kho tổng | `checkout` |
| Theo dõi, hủy, hoàn tất đơn | Đúng chủ đơn; hủy chỉ từ `paid`, hoàn tất từ `delivered` | `orders` |
| Đánh giá sau mua | Đơn `completed`, đúng order item; một review/item | `reviews` |
| Trả hàng và hoàn tiền | Đơn `delivered`/`completed`, kiểm tra cửa sổ 7 ngày và lượng còn được trả | `returns` |
| Bán tại quầy | Cửa hàng hợp lệ, đủ tồn; đơn hoàn tất và thanh toán thành công | `pos` |
| Quản lý sản phẩm | Tạo/sửa/archive sản phẩm, cập nhật biến thể | `admin` |
| Quản lý khách và rủi ro COD | Sửa role/trạng thái/store; mở lại quyền COD kèm lý do | `admin` |
| Quản lý coupon và review | Tạo/sửa/archive coupon; ẩn/khôi phục review | `coupons`, `reviews` |
| Nhập kho | Phiếu nhập, chi tiết, cập nhật tồn và giá vốn bình quân | `inbound` |
| Điều phối giao vận | Phân công delivery staff, dispatch, deliver, ghi lần giao thất bại | `orders`, `logistics` |
| Xử lý trả hàng | Duyệt/từ chối, nhận hàng, kiểm định và hoàn tiền | `returns` |
| Quản lý cửa hàng | Đọc dashboard, đơn/tồn/nhân sự theo phạm vi; confirm/cancel theo trạng thái cho phép | `store` |

Danh sách API và phương thức nằm trong [API README](../../services/ecommerce-api/README.md). Tên module là thư mục thực tế tại [app/modules](../../services/ecommerce-api/app/modules).

## 3. Luồng nghiệp vụ tiêu biểu

### Checkout online

1. API xác thực, kiểm tra CSRF và `Idempotency-Key`.
2. Service mở transaction, khóa customer và kiểm tra trạng thái/quyền COD; sau đó tìm kết quả theo khóa idempotency.
3. Với yêu cầu mới, kiểm tra giỏ, catalog, coupon và tồn; chụp giá bán/giá vốn vào order item.
4. Tạo order, payment, lịch sử trạng thái, redemption và ledger; trừ kho tổng, đóng giỏ rồi commit.
5. Nếu có lỗi, rollback; Unit of Work có cơ chế retry lỗi tranh chấp khóa theo cấu hình.

VietQR hiện mô phỏng thành công trong transaction; không có xác nhận từ cổng ngân hàng. Replay cùng khóa chỉ trả kết quả cũ khi qua được các kiểm tra tài khoản trước đó và khớp chủ đơn. Không suy rộng idempotency checkout cho mọi API ghi hoặc POS.

### POS và nhập kho

POS kiểm tra cửa hàng/catalog, khóa tồn cửa hàng, tạo order `completed`, payment `succeeded`, cost snapshot và ledger `outbound_pos` trong transaction. Khóa idempotency của POS do service sinh theo đơn mới, chưa bảo vệ retry của client như checkout.

Nhập kho khóa dữ liệu liên quan, tạo receipt/items, cộng tồn kho tổng và cập nhật giá vốn bình quân gia quyền di động. Giá vốn của đơn cũ giữ theo snapshot; thay đổi giá hiện tại không tính lại các dòng đã bán.

### Giao hàng và trả hàng

Đơn `paid` hoặc `confirmed` có thể dispatch sang `shipping`; `confirmed` không phải bước bắt buộc riêng cho mọi đơn VietQR. Sau `delivered`, khách xác nhận sang `completed`, khi đó COD pending được đánh dấu thành công. Giao thất bại được ghi từng lần; tới lần thứ ba service hoàn kho và chuyển `failed_delivery`. Điểm rủi ro khách được cập nhật theo phân loại nguyên nhân của lần thất bại kết thúc.

Trả hàng đi qua `pending_review → approved → goods_received → completed`; có nhánh `rejected` hoặc khách hủy khi còn chờ duyệt. Chỉ item kiểm định đạt mới nhập lại kho và được hoàn tiền. Tổng hoàn tiền được cộng dồn trong một refund/payment; đơn chỉ thành `returned` khi toàn bộ lượng mua đã được trả đạt kiểm định. Chi tiết cửa sổ 7 ngày xem [yêu cầu nghiệp vụ](../project/BUSINESS_REQUIREMENTS.md).

## 4. Các ca sử dụng dữ liệu và BI

| Ca sử dụng | Luồng và đầu ra hiện có |
|---|---|
| Nạp lịch sử tổng hợp | Generator xuất SQL/JSONL; script import MySQL hoặc upload raw log |
| Batch tăng dần | 27 bảng → Landing/manifest → Bronze → commit cursor → Silver → reconciliation → Gold → quality gate |
| Thu CDC | MySQL binlog → Debezium → Kafka → Flink → `bronze.oltp_cdc_events` |
| Thu access log | Middleware → Kafka → Flink StatementSet với bốn Iceberg sink |
| Tổng hợp log | Spark tạo ba mart log từ `gold.fact_web_events` |
| Kiểm tra chất lượng | Ghi bằng chứng vào `system.data_quality_results`; gate lỗi làm task thất bại |
| Bảo trì | DAG riêng cho compaction, snapshot expiration, orphan cleanup; retention quarantine |
| Xem BI | UI → FastAPI xác thực/phạm vi → Trino hoặc MySQL → response nguồn/degraded → ECharts |

CDC chưa tự áp dụng vào typed Silver/Gold. Upload JSONL vào MinIO chưa tự đưa dữ liệu vào Flink Kafka source. Gate sau Gold không rollback nguyên tử mọi bảng đã ghi trước đó.

## 5. Phân chia thành phần và dữ liệu

| Thành phần thực tế | Trách nhiệm |
|---|---|
| Next.js pages/components, `src/lib/api*` | Trình bày và gọi API; không kết nối DB trực tiếp |
| FastAPI routers, Pydantic schemas | Endpoint, đầu vào/đầu ra, dependencies xác thực/phân quyền |
| Domain services, `app/db/uow.py` | Nghiệp vụ, transaction và retry |
| SQLAlchemy models | Ánh xạ thực thể OLTP; DDL vật lý là `database/schema.sql` |
| Pipeline jobs và `lakehouse` library | Session, extract, schema/transform, cursor, DQ và maintenance |
| Airflow DAGs | Thứ tự thực thi và lịch chạy; không thay thế Spark/Flink |
| Polaris / MinIO / Trino | Catalog/quyền, lưu file và truy vấn SQL |

[OLTP Schema](../architecture/OLTP_SCHEMA.md) mô tả 28 bảng và khác biệt FK SQL/ORM. [Lakehouse Design](../project/LAKEHOUSE_DESIGN_PLAN.md) mô tả grain dimension/fact/mart. Các quan hệ phân tích không phải FK được Iceberg cưỡng chế.

## 6. Ràng buộc và phần chưa triển khai

- Phân quyền dashboard/store nằm ở FastAPI. UI có menu orders/logistics/returns cho `operations_manager`, nhưng API tương ứng còn yêu cầu `admin`.
- JWT HttpOnly và cơ chế double-submit CSRF đã có; hai route confirm/cancel cửa hàng chưa gắn `verify_csrf`. Không tuyên bố mọi thao tác ghi đều có kiểm tra này.
- Route điều chỉnh/cấp tồn chi nhánh có logic cập nhật nhưng chưa commit; dependency chỉ đóng session. Chức năng này chưa được xem là luồng ghi đã hoàn thiện.
- Category CRUD, profile tự chỉnh sửa, đăng nhập shipper, thanh toán ngân hàng thực và đổi size/màu chưa có luồng API/UI đầy đủ.
- ML training/scoring, dự báo, CLV và recommendation chưa triển khai. Không dùng sơ đồ mô hình ML như thành phần đang chạy.
- Stack là Compose cục bộ dùng HTTP; chưa có cấu hình production hoàn chỉnh cho TLS, secret manager, rate limiting hoặc HA.
- Không có số liệu benchmark/SLA đã xác minh trong tài liệu này.

## 7. Sơ đồ và tài liệu liên quan

[Bộ sơ đồ Chương 3](../diagram/README.md) có Use Case, Activity checkout/POS/returns, Sequence checkout/dashboard, kiến trúc, ERD và wireframe. Wireframe là thiết kế theo mã nguồn, không phải ảnh chụp runtime. Sơ đồ thể hiện cấu trúc chính; điều kiện chi tiết và các giới hạn triển khai đọc trong tài liệu này cùng [kiến trúc](../architecture/SYSTEM_ARCHITECTURE_VISUAL.md), [chỉ số](../architecture/METRICS_CATALOG.md) và [runbook](../runbook/SETUP.md).
