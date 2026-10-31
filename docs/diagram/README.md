# Sơ đồ Chương 3 — Phân tích và thiết kế hệ thống

Bộ sơ đồ phục vụ dàn ý Chương 3, được dựng theo mã nguồn ngày **28/10/2026**. Nguồn chỉnh sửa và bản xem nằm tại `docs/diagram/`; bộ sơ đồ cũ đã được loại bỏ. Tài liệu kiến trúc/nghiệp vụ được đối chiếu lại ngày 31/10/2026; các giới hạn mới ghi nhận bên dưới không đồng nghĩa đã thay đổi nội dung bản vẽ.

## Mở và sử dụng

1. Mở [index.html](index.html) bằng trình duyệt để duyệt toàn bộ hình. Chọn nhóm ở mục lục, mở trang cần xem; nút **Vừa màn hình / cỡ gốc** chuyển giữa xem tổng quan và đọc chi tiết. Bản xem hoạt động offline, không tải font hoặc thư viện ngoài.
2. Mở file `.drawio` bằng extension Draw.io Integration trong VS Code, hoặc vào [diagrams.net](https://app.diagrams.net/), chọn **Open Existing Diagram → Device** và chọn file. Những file nhiều trang có tab ở dưới canvas.
3. Dùng SVG tương ứng để đưa vào báo cáo (vector, phóng to không vỡ). Khi chỉnh file draw.io, xuất lại SVG từ **File → Export as → SVG** để đồng bộ bản xem; `index.html` là bản tổng hợp tại thời điểm tạo, không tự đọc thay đổi file.

Mỗi file `.drawio` là XML native, chỉnh sửa được từng khối và cạnh. Bản HTML/SVG được dựng từ cùng mô hình hình học; đường đi của connector có thể được draw.io tự định tuyến lại khi mở. SVG hiện tại không nhúng XML draw.io; dùng file `.drawio` làm nguồn chỉnh sửa. Máy tạo chưa có draw.io Desktop nên không coi bản SVG là kết quả CLI export.

## Đối chiếu với dàn ý

| Mục Chương 3 | Sơ đồ chỉnh sửa | Số trang | SVG theo thứ tự trang |
|---|---|---:|---|
| 3.1.1–3.1.4 | [Bối cảnh, tác nhân và phạm vi](01-system-context.drawio) | 1 | [1](context.svg) |
| 3.1.2–3.1.3; 3.2.1 | [Use Case theo tác nhân và phân hệ](02-use-cases.drawio) | 3 | [1](uc-storefront.svg) · [2](uc-admin.svg) · [3](uc-data-bi.svg) |
| 3.2.2; 3.4.4 | [Activity đặt hàng online](03-activity-checkout.drawio) | 2 | [1](activity-checkout-validate.svg) · [2](activity-checkout-commit.svg) |
| 3.2.2 | [Activity bán hàng tại quầy](04-activity-pos.drawio) | 1 | [1](activity-pos.svg) |
| 3.2.2; 3.4.4 | [Activity tiếp nhận và giải quyết trả hàng](05-activity-returns.drawio) | 1 | [1](activity-returns.svg) |
| 3.2.3; 3.4.4 | [Sequence đặt hàng online](06-sequence-checkout.drawio) | 1 | [1](seq-checkout.svg) |
| 3.2.3; 3.6.3 | [Sequence tải Dashboard theo vai trò](07-sequence-dashboard.drawio) | 1 | [1](seq-dashboard.svg) |
| 3.3.1 | [Kiến trúc tổng thể một trang](08-system-architecture.drawio) | 1 | [1](architecture-system.svg) |
| 3.3.2; 3.4.4 | [Thiết kế kiến trúc Web](09-web-architecture.drawio) | 1 | [1](architecture-web.svg) |
| 3.3.3 | [Kiến trúc Lakehouse và BI](10-lakehouse-architecture.drawio) | 1 | [1](architecture-lakehouse.svg) |
| 3.3.4; 3.5.1–3.5.2 | [Ba luồng thu thập và tương tác dữ liệu](11-data-ingestion.drawio) | 3 | [1](flow-batch.svg) · [2](flow-cdc.svg) · [3](flow-access-log.svg) |
| 3.4.1–3.4.2 | [Mô hình quan niệm các thực thể](12-erd-conceptual.drawio) | 2 | [1](erd-conceptual-sales.svg) · [2](erd-conceptual-stock.svg) |
| 3.4.2–3.4.4 | [ERD vật lý MySQL — 28 bảng, 50 FK](13-erd-mysql-physical.drawio) | 7 | [1](erd-physical-identity.svg) · [2](erd-physical-catalog.svg) · [3](erd-physical-orders.svg) · [4](erd-physical-payment.svg) · [5](erd-physical-inventory.svg) · [6](erd-physical-logistics.svg) · [7](erd-physical-returns.svg) |
| 3.4.4 | [Ràng buộc và tính nhất quán giao dịch](14-transaction-consistency.drawio) | 1 | [1](transaction-consistency.svg) |
| 3.5.1; 3.5.3 | [Thiết kế Landing – Bronze – Silver – Gold](15-medallion-layers.drawio) | 1 | [1](medallion.svg) |
| 3.5.4 | [Dimension, Fact và Data Mart](16-gold-data-model.drawio) | 4 | [1](gold-sales.svg) · [2](gold-operations.svg) · [3](gold-marts.svg) · [4](gold-log-marts.svg) |
| 3.5.5; 3.1.4 | [Thiết kế chất lượng và bảo mật dữ liệu](17-quality-and-security.drawio) | 3 | [1](quality-gates.svg) · [2](security-app.svg) · [3](security-engines.svg) |
| 3.6.1 | [Thiết kế giao diện Storefront](18-storefront-wireframes.drawio) | 3 | [1](ui-products.svg) · [2](ui-product-detail.svg) · [3](ui-checkout.svg) |
| 3.6.2 | [Thiết kế giao diện quản trị](19-admin-wireframes.drawio) | 2 | [1](ui-admin-orders.svg) · [2](ui-admin-inbound.svg) |
| 3.6.3 | [Thiết kế Dashboard BI theo vai trò](20-dashboard-design.drawio) | 2 | [1](ui-dashboard-sales.svg) · [2](ui-dashboard-operations.svg) |

## Phạm vi và quy ước

- **3.1:** sơ đồ bối cảnh xác định tác nhân, nguồn và đầu ra. Yêu cầu chức năng được cụ thể hóa ở Use Case; yêu cầu phi chức năng là ràng buộc thiết kế, không phải kết quả đo hiệu năng/SLA.
- **3.2:** Use Case cho người mua, quản trị/cửa hàng và người vận hành dữ liệu. Activity gồm checkout, POS và trả/hoàn tiền; Sequence minh họa checkout và truy vấn dashboard. Đây là các luồng tiêu biểu, không thay thế toàn bộ đặc tả API.
- Use Case bám theo quyền API hiện hành: quản lý giao vận và xử lý trả hàng yêu cầu `admin`; `operations_manager` có dashboard vận hành nhưng không vì thấy menu UI mà tự có quyền gọi các API ghi này. Chức năng coupon/review thuộc `marketing_manager` hoặc `admin`.
- **3.3:** sơ đồ tổng thể nằm trên một trang; các hình Web, Lakehouse và ba luồng thu thập giải thích chi tiết thành phần và tương tác. Chiều cạnh truy vấn mô tả bên gọi → nguồn đọc, không phải một pipeline ghi dữ liệu mới.
- **3.4:** ERD quan niệm chọn các quan hệ nghiệp vụ chính. ERD vật lý chia **7 trang**, có đủ **28 bảng sở hữu và 50 khóa ngoại thực tế**; Bảng tham chiếu có thể lặp giữa các trang phân hệ. Mỗi FK chỉ được khai báo ở trang sở hữu bảng con; đường nối gắn tới dòng cột FK/PK tương ứng, nhãn CASCADE/SET NULL thể hiện ON DELETE; các FK không có nhãn dùng RESTRICT. Các bảng chỉ trình bày cột chính; NOT NULL/NULL được ghi trực tiếp cạnh kiểu dữ liệu. PK/FK và SQL type được trích từ [schema.sql](../../database/schema.sql), không tạo thêm schema mới. CHECK/UNIQUE/index và toàn bộ cột xem trong DDL.
- Quan hệ `orders.staff_id → customers.customer_id` hiện chỉ có trong ORM, **không được vẽ thành FK vật lý**. Bộ DBML cũ có 51 quan hệ theo ORM nên không dùng số đó làm số FK MySQL.
- **3.5:** nguồn batch/CDC là 27 bảng MySQL, loại `customer_credentials`; nguồn access log là middleware FastAPI. Batch commit cursor sau Bronze, trước Silver/Gold. CDC kết thúc tại append-only `bronze.oltp_cdc_events`, chưa tự cập nhật Silver/Gold. Job log Flink dùng StatementSet với nhiều sink; Spark xây mart log. Upload JSONL lịch sử vào Landing chưa tự đưa file đó vào luồng Kafka.
- Dimension/fact/mart dùng tên trong DDL Gold; quan hệ `*_key` là liên kết logic, không phải FK được Iceberg cưỡng chế. Mô hình Gold thể hiện khóa chính; mart thể hiện các trường tạo nên grain. Snapshot inventory không mặc định chứng minh đã có lịch sử đủ mọi ngày.
- Quyền dashboard được kiểm tra/lọc tại FastAPI, không phải Trino RLS tự động. Polaris/MinIO dùng identity workload riêng; writer Polaris hiện có quyền quản lý nội dung ở mức catalog. MySQL batch vẫn dùng user ứng dụng trong Compose. Stack local HTTP; không vẽ HTTPS hoặc secret manager production thành chức năng đã triển khai.
- **3.6:** wireframe mô tả bố cục theo mã giao diện, không phải ảnh chụp runtime, không chứa giá trị KPI giả. Bộ chọn thời gian của dashboard chỉ đổi trend; tìm/sort/CSV áp dụng trong từng bảng. Menu/nút theo quyền vẫn phải được kiểm tra ở API.
- Toàn bộ sơ đồ dùng nền trắng, nét đen và nhãn ngắn. Phần giải thích nằm trong báo cáo/tài liệu, không đặt trên hình. Bảng dữ liệu chỉ giữ cột và khóa cần thiết; DDL gốc chứa đầy đủ định nghĩa.
- Nét đứt thể hiện phản hồi, lifeline hoặc luồng điều khiển theo loại sơ đồ; PK/FK và cardinality được giữ để đọc mô hình dữ liệu.

## Góc nhìn BI theo vai trò

| Tài khoản | Góc nhìn | Nguồn / phạm vi chính |
|---|---|---|
| `admin` | Executive, được chuyển các góc nhìn | Gold doanh thu/cost/profit/đơn; OLTP bổ sung theo KPI |
| `sales_manager` | Sales | Gold bán hàng; sales-trend theo ngày |
| `marketing_manager` | Marketing | Gold sự kiện 30 ngày + coupon/review OLTP; có thể fallback |
| `store_manager` | Store | MySQL, bị giới hạn theo cửa hàng được gán |
| `inventory_manager` | Inventory | MySQL tồn kho/nhập hàng hiện tại |
| `operations_manager` | Operations | MySQL đơn/giao vận/COD/trả hàng |
| `system_admin` | System | Độ mới Gold và đối soát với MySQL; thiếu nguồn phải được đánh dấu |

Response KPI có `data_source`, `is_degraded`, `degraded_reason`. Thời điểm UI nhận response khác thời điểm Gold được cập nhật. Marketing đếm sự kiện không mặc định là số người duy nhất; các nhóm giao vận có thể chồng lặp. Công thức và giới hạn đọc ở [METRICS_CATALOG.md](../architecture/METRICS_CATALOG.md).

## Nguồn đối chiếu chính

- [Phạm vi](../project/SCOPE.md), [kiến trúc hiện tại](../architecture/SYSTEM_ARCHITECTURE_VISUAL.md), [Lakehouse](../project/LAKEHOUSE_DESIGN_PLAN.md), [OLTP](../architecture/OLTP_SCHEMA.md).
- [MySQL DDL](../../database/schema.sql), [backend](../../services/ecommerce-api/app/modules), [frontend](../../apps/storefront/src/app).
- [DAG batch](../../airflow/dags/lakehouse_oltp_pipeline.py), [cấu hình extract](../../pipelines/config/default.yml), [Gold DDL](../../pipelines/src/lakehouse/oltp/gold_ddl.py), [Gold transforms](../../pipelines/src/lakehouse/oltp/gold/), [log marts](../../pipelines/src/lakehouse/logs/gold.py).
- [Polaris RBAC](../../infrastructure/polaris/rbac.yml), [Compose](../../docker-compose.yml), [CDC](../architecture/CDC_DASHBOARD_DATA_SPEC.md).

Các sơ đồ là tài liệu thiết kế được đối chiếu tĩnh với mã nguồn; không phải bằng chứng chạy thành công pipeline, kiểm thử tải hoặc hiệu năng production. Phần ML không nằm trong bộ sơ đồ này.

## Giới hạn cần đọc cùng sơ đồ

- Các hình nghiệp vụ chọn luồng chính. Mốc trả hàng hiện dùng `completed_at` hoặc `updated_at`, không cố định riêng `shipment.delivered_at`. Order chỉ returned khi trả đủ lượng đạt kiểm định.
- Có các route chỉnh/cấp tồn chi nhánh mới flush mà chưa commit; xem [kiến trúc](../architecture/SYSTEM_ARCHITECTURE_VISUAL.md). Hình vẽ không chứng minh thao tác đã lưu thành công.
- Code log mới đã chuẩn hóa UTC như Spark; hình vẽ cũ chưa phản ánh refactor module và dữ liệu cũ chưa được migrate.
- Dashboard system đã tách biểu đồ số đơn và tiền theo từng trục độc lập. Wireframe là bố cục minh họa, không thay thế giao diện runtime hiện tại.
