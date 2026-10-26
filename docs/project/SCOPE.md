# Phạm vi đồ án

## 1. Mục tiêu

Xây dựng Data Lakehouse cho thương mại điện tử: thu thập, lưu trữ, chuẩn hóa, đối soát và cung cấp dữ liệu phân tích. Website/POS tạo nguồn giao dịch và access log; phần DE là trọng tâm.

## 2. Nguồn dữ liệu

| Nguồn | Nội dung và biên giới |
|---|---|
| MySQL | 28 bảng ứng dụng; batch/CDC lấy 27 bảng, loại `customer_credentials` |
| Access log FastAPI | HTTP events theo JSON contract; không ghi password/token/cookie/raw IP |
| Generator | Dữ liệu giao dịch và log tổng hợp theo cấu hình |
| Website/API | Giao dịch và access log phát sinh khi sử dụng hệ thống |

Dữ liệu tổng hợp cần được ghi nhận là dữ liệu tổng hợp khi trình bày kết quả. Số dòng và tốc độ xử lý phải lấy từ lần chạy thực tế.

## 3. Phần đã có trong mã nguồn

- Batch MySQL → Landing → Bronze → Silver → Gold bằng Spark/Airflow.
- Incremental cursor `(cursor_field, pk)`, lookback và manifest.
- Chuẩn hóa, khử trùng, MERGE, pseudonymization và quarantine.
- Đối soát MySQL/Silver và kiểm tra Gold; lưu quality results.
- Binlog → Debezium → Kafka → Flink → Bronze CDC.
- Access log → Kafka → Flink → các tầng Iceberg; Spark rollup mart.
- Trino SQL và BI Hub; RBAC và phạm vi cửa hàng tại API.
- Bảo trì Iceberg, snapshot/file và retention quarantine.
- CLI sinh dữ liệu nguồn; CI kiểm tra cấu hình, lint, typecheck và build.

## 4. Đầu ra phân tích

Gold OLTP gồm 6 dimension, 5 fact, 4 mart. Nhóm log gồm 1 fact, 3 mart. Bronze CDC là log sự kiện riêng, không phải bảng trạng thái hiện tại.

Chi tiết grain ở [Lakehouse Design](LAKEHOUSE_DESIGN_PLAN.md). Công thức và khác biệt Gold/OLTP ở [Metrics Catalog](../architecture/METRICS_CATALOG.md).

## 5. Giới hạn

- CDC chưa tự cập nhật Silver/Gold OLTP theo sự kiện.
- Cursor batch chưa thay thế toàn bộ bài toán đồng bộ hard delete.
- Upload JSONL vào MinIO chưa có job tự động đọc file thô sang Gold.
- KPI mở rộng trong tài liệu A–D không mặc nhiên là tính năng đã triển khai.
- Chưa có bảng cấu hình mục tiêu doanh số; target/run-rate để không có dữ liệu thay vì dùng số minh họa.
- Chưa có benchmark end-to-end hoặc cam kết latency/throughput production.
- HTTPS và secret manager production chưa được đóng gói đầy đủ.
- Machine Learning/RAG/fine-tuning ngoài phạm vi hiện tại.

## 6. Bằng chứng trình bày

Dùng log DAG/Flink, snapshot Iceberg, Trino SQL và `system.data_quality_results` của lần chạy cụ thể. Ghi kèm dataset, thời điểm, số dòng từng tầng và môi trường thực thi.

[Kiến trúc hệ thống](../architecture/SYSTEM_ARCHITECTURE_VISUAL.md) là tham chiếu triển khai. A–D được giữ để phân tích nghiệp vụ và viết tiểu luận.
