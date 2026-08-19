# Database

Thư mục này giữ migration, seed và init asset của MySQL ecommerce.

- `migrations/`: Alembic environment và version scripts cho 17 bảng OLTP.
- `seeds/`: master data có version, không chứa dữ liệu giao dịch giả.

Mọi invariant liên bảng vẫn phải được bảo vệ trong application transaction và reconciliation; migration không thay thế transaction catalogue trong `../docs/architecture/oltp-schema.md`.

Pipeline ingestion trích xuất 16 bảng nghiệp vụ từ MySQL (`customer_credentials` chứa password hash bị loại trừ hoàn toàn khỏi allowlist ingestion để đảm bảo an toàn).
