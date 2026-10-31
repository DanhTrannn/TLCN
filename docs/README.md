# Mục lục tài liệu đồ án

Bộ tài liệu lấy phần Data Engineering làm trọng tâm, được đối chiếu tĩnh với mã nguồn ngày **31/10/2026**. Schema/quyền/công thức lấy từ code; số dòng, trạng thái dịch vụ và hiệu năng cần lấy từ môi trường đang chạy.

## Tài liệu triển khai hiện tại

| Tài liệu | Nội dung |
|---|---|
| [SCOPE](project/SCOPE.md) | Mục tiêu, nguồn dữ liệu, phạm vi batch/CDC/log và giới hạn |
| [SYSTEM_ARCHITECTURE_VISUAL](architecture/SYSTEM_ARCHITECTURE_VISUAL.md) | Thành phần, ba luồng dữ liệu, vai trò/API dashboard, RBAC, lịch chạy và triển khai |
| [LAKEHOUSE_DESIGN_PLAN](project/LAKEHOUSE_DESIGN_PLAN.md) | Namespace, lưu trữ, dimension/fact/mart và nhóm log |
| [METRICS_CATALOG](architecture/METRICS_CATALOG.md) | Công thức, grain, nguồn, cửa sổ thời gian và giới hạn chỉ số |
| [OLTP_SCHEMA](architecture/OLTP_SCHEMA.md) | 28 bảng MySQL, quan hệ, ràng buộc và giao dịch |
| [schema.sql](../database/schema.sql) | File DDL vật lý duy nhất để khởi tạo MySQL trống |
| [ACCESS_LOG_DESIGN](architecture/ACCESS_LOG_DESIGN.md) | JSON contract, quyền riêng tư và xử lý log |
| [CDC_DASHBOARD_DATA_SPEC](architecture/CDC_DASHBOARD_DATA_SPEC.md) | Binlog, Debezium, Kafka, Bronze CDC và phục hồi |
| [PROJECT_STRUCTURE](architecture/PROJECT_STRUCTURE.md) | Thư mục và điểm vào của mã nguồn |
| [SETUP](runbook/SETUP.md) | Cài đặt, thứ tự khởi động, vận hành batch/streaming, quyền truy cập và xử lý lỗi |
| [Phát triển và CI](../README.md#development-commands) | Lệnh kiểm tra cục bộ và các job GitHub Actions |
| [Sơ đồ Chương 3](diagram/README.md) | Bộ sơ đồ theo dàn ý: Use Case, Activity, Sequence, kiến trúc, ERD MySQL, Lakehouse và wireframe; có trang HTML xem nhanh |
| [Access log schema](contracts/ecommerce-access-v1.schema.json) | JSON Schema cho hợp đồng dữ liệu |

## Tài liệu giữ để phân tích và viết tiểu luận

Các tài liệu A–D mô tả phân tích, nghiệp vụ và thiết kế theo code hiện tại. Các phần chưa triển khai và khác biệt UI/API được ghi rõ; định nghĩa công thức chi tiết dùng Metrics Catalog để tránh lặp lại.

| Mã | Tài liệu | Nội dung |
|---|---|---|
| A | [OOSAD_ANALYSIS](design-analysis/OOSAD_ANALYSIS.md) | Actors, Use Case, Activity, Sequence và phân tích Web/Lakehouse |
| B | [BUSINESS_DOMAIN](architecture/BUSINESS_DOMAIN.md) | Bảy góc nhìn BI, câu hỏi kinh doanh, nguồn và giới hạn diễn giải KPI |
| C | [BUSINESS_REQUIREMENTS](project/BUSINESS_REQUIREMENTS.md) | Mua hàng, POS, kho, giao vận, COD và đổi trả |
| D | [WEB_DESIGN_PLAN](project/WEB_DESIGN_PLAN.md) | Thiết kế website nguồn, API và giao dịch |

## Quy tắc cập nhật

Khi đổi schema, đối chiếu SQL, ORM, cấu hình extract và ERD. Khi đổi dashboard, cập nhật công thức/nguồn, quyền API và tài liệu giao diện. Lệnh chạy lấy từ script, Makefile hoặc Compose; không dùng lịch chạy/checkpoint làm bằng chứng SLA. Bộ sơ đồ nằm tại `docs/diagram/`; các bản cũ trong `docs/diagrams/` đã được loại bỏ.
