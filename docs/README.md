# Mục lục tài liệu đồ án

Bộ tài liệu lấy phần Data Engineering làm trọng tâm. Kiến trúc, bảng dữ liệu và công thức được đối chiếu với mã nguồn; số dòng và hiệu năng thực tế cần lấy từ môi trường đang chạy.

## Tài liệu triển khai hiện tại

| Tài liệu | Nội dung |
|---|---|
| [SCOPE](project/SCOPE.md) | Mục tiêu, nguồn dữ liệu, phạm vi batch/CDC/log và giới hạn |
| [SYSTEM_ARCHITECTURE_VISUAL](architecture/SYSTEM_ARCHITECTURE_VISUAL.md) | Thành phần, ba luồng dữ liệu, serving, lịch chạy và triển khai |
| [LAKEHOUSE_DESIGN_PLAN](project/LAKEHOUSE_DESIGN_PLAN.md) | Namespace, lưu trữ, dimension/fact/mart và nhóm log |
| [METRICS_CATALOG](architecture/METRICS_CATALOG.md) | Công thức, grain, nguồn, cửa sổ thời gian và giới hạn chỉ số |
| [MANAGEMENT_INFO_TECHNICAL_SPEC](architecture/MANAGEMENT_INFO_TECHNICAL_SPEC.md) | Vai trò dashboard, nguồn SQL, RBAC và trạng thái dữ liệu |
| [OLTP_SCHEMA](architecture/OLTP_SCHEMA.md) | 28 bảng MySQL, quan hệ, ràng buộc và giao dịch |
| [ACCESS_LOG_DESIGN](architecture/ACCESS_LOG_DESIGN.md) | JSON contract, quyền riêng tư và xử lý log |
| [CDC_DASHBOARD_DATA_SPEC](architecture/CDC_DASHBOARD_DATA_SPEC.md) | Binlog, Debezium, Kafka, Bronze CDC và phục hồi |
| [PROJECT_STRUCTURE](architecture/PROJECT_STRUCTURE.md) | Thư mục và điểm vào của mã nguồn |
| [Runbook](runbook/README.md) | Cài đặt, khởi động, sinh dữ liệu và vận hành |
| [Diagrams](diagrams/README.md) | Draw.io, ERD DBML, Use Case, Activity và Sequence |
| [Access log schema](contracts/ecommerce-access-v1.schema.json) | JSON Schema cho hợp đồng dữ liệu |

## Tài liệu giữ để phân tích và viết tiểu luận

Các tài liệu A–D được giữ theo lựa chọn của tác giả. Chúng mô tả nghiệp vụ và thiết kế mở rộng; khi xác định tính năng/công thức đang triển khai, dùng nhóm tài liệu ở trên và mã nguồn.

| Mã | Tài liệu | Nội dung |
|---|---|---|
| A | [OOSAD_ANALYSIS](design-analysis/OOSAD_ANALYSIS.md) | Actors, Use Case, Activity, Sequence và phân tích Web/Lakehouse |
| B | [BUSINESS_DOMAIN](architecture/BUSINESS_DOMAIN.md) | Bảy vai trò quản lý, câu hỏi kinh doanh và KPI mong muốn |
| C | [BUSINESS_REQUIREMENTS](project/BUSINESS_REQUIREMENTS.md) | Mua hàng, POS, kho, giao vận, COD và đổi trả |
| D | [WEB_DESIGN_PLAN](project/WEB_DESIGN_PLAN.md) | Thiết kế website nguồn, API và giao dịch |

Bản `BUSINESS_DOMAIN.md` tại `design-analysis/` trùng nội dung đã được gộp về bản B.
