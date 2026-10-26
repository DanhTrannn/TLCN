# Sơ đồ phục vụ đồ án D&K E-Commerce

Các sơ đồ nguồn trong thư mục này bám theo code hiện hành. Bộ màu dùng cùng palette với Storefront (`paper #f7f4ee`, `ink #152722`, `accent #a94728`, `moss #315b4f`).

| Mục trong tiểu luận | Sơ đồ nguồn | Bản xem / sử dụng |
|---|---|---|
| Kiến trúc Web và Lakehouse | [`system-architecture.drawio`](system-architecture.drawio) | Mở bằng [draw.io](https://app.diagrams.net/) để kéo sửa; một trang với năm cột thành phần và khoảng cách rộng giữa các khối. |
| 3.2 — Thiết kế dữ liệu OLTP | [`erd-oltp-28-tables.dbml`](erd-oltp-28-tables.dbml) | Mở bằng [dbdiagram](https://dbdiagram.io/) hoặc VS Code DBML; đủ 28 bảng và 51 khóa ngoại. |
| 3.3.1 — Use Case tổng quan | [`usecase-web-overview.puml`](usecase-web-overview.puml) | [`SVG`](usecase-web-overview.svg) |
| 3.3.2 — Use Case phân rã bán hàng | [`usecase-checkout-pos.puml`](usecase-checkout-pos.puml) | [`SVG`](usecase-checkout-pos.svg) |
| 3.3.3 — Activity checkout | [`activity-checkout.puml`](activity-checkout.puml) | [`SVG`](activity-checkout.svg) |
| 3.3.4 — Sequence checkout | [`sequence-checkout.puml`](sequence-checkout.puml) | [`SVG`](sequence-checkout.svg) |

## Cập nhật khi code đổi

ERD đầy đủ được sinh từ `services/ecommerce-api/app/models` qua [`export_oltp_dbml.py`](export_oltp_dbml.py). [`database/schema.sql`](../../database/schema.sql) là nguồn quyết định DDL vật lý; DBML dùng để đọc và thuyết minh.

DBML có 51 quan hệ theo ORM; DDL vật lý hiện có 50 khóa ngoại. Quan hệ `orders.staff_id → customers.customer_id` hiện chỉ được khai báo trong ORM. File SQL giữ cấu trúc database hiện hành, không tự bổ sung ràng buộc mới.

```bash
.venv/bin/python docs/diagrams/export_oltp_dbml.py
.venv/bin/python docs/diagrams/export_oltp_dbml.py --check
```

Để kiểm tra cú pháp DBML bằng CLI chính thức, cài `@dbml/cli` rồi chạy:

```bash
dbml2sql docs/diagrams/erd-oltp-28-tables.dbml --mysql -o /tmp/tlcn-erd-check.sql
```

Các file `.puml` là nguồn của bốn file SVG. PlantUML hỗ trợ kết xuất SVG bằng `-tsvg`:

```bash
plantuml -tsvg docs/diagrams/*.puml
```

Sơ đồ `.drawio` là file XML có thể chỉnh sửa từng ô và đường nối. Mở bằng draw.io để chỉnh sửa hoặc xuất PNG/SVG/PDF. Khi dùng Codex có plugin draw.io, có thể cập nhật file bằng `/drawio:drawio`.

## Giới hạn biểu diễn

- ERD DBML phản ánh SQLAlchemy metadata, bao gồm cột, PK, quan hệ, unique/index và nullability. DDL vật lý nằm trong `database/schema.sql`; các quy tắc nghiệp vụ và state machine được mô tả trong [`OLTP_SCHEMA.md`](../architecture/OLTP_SCHEMA.md).
- Use Case tổng quan chỉ thể hiện tương tác website; các đường dữ liệu nội bộ nằm ở sơ đồ kiến trúc.
- Checkout hiện tại xử lý VietQR và COD trong transaction MySQL. `payments.status` là `succeeded` hoặc `pending` tương ứng; sơ đồ không giả định có cổng thanh toán ngoài hay email xác nhận trong luồng này.
- Phần ML nằm ngoài phạm vi các sơ đồ triển khai hiện tại.
