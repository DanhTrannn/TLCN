# Database

Thư mục này giữ migration, seed và init asset của MySQL ecommerce.

- `migrations/`: Alembic environment và version scripts cho 17 bảng OLTP.
- `seeds/`: master data có version, không chứa dữ liệu giao dịch giả.
- `init/`: bootstrap asset chỉ chạy khi database volume được tạo mới.

Mọi invariant liên bảng vẫn phải được bảo vệ trong application transaction và reconciliation; migration không thay thế transaction catalogue trong `../docs/architecture/oltp-schema.md`.

DE reader được bootstrap ở trạng thái không có quyền đọc. Sau khi migration tạo đủ bảng, chạy `./scripts/grant_de_reader.sh` để cấp `SELECT` theo allowlist 16 source table. Script kiểm tra fail-closed và tuyệt đối không cấp quyền trên `customer_credentials`.
