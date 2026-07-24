# Database

Thư mục này giữ migration, seed và init asset của MySQL ecommerce.

- `migrations/`: Alembic environment và version scripts cho 12 bảng OLTP.
- `seeds/`: master data có version, không chứa dữ liệu giao dịch giả.
- `init/`: bootstrap asset chỉ chạy khi database volume được tạo mới.

Mọi invariant liên bảng vẫn phải được bảo vệ trong application transaction và reconciliation; migration không thay thế transaction catalogue trong `schema.md`.

DE reader được bootstrap ở trạng thái không có quyền đọc. Sau khi migration tạo đủ bảng, post-migration grant phải cấp `SELECT` theo allowlist từng source table và tuyệt đối không cấp trên `customer_credentials`.
