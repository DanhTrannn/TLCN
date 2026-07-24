# TLCN Batch Data Lakehouse

Monorepo cho đề tài:

> Xây dựng Data Lakehouse xử lý theo lô cho dữ liệu giao dịch, hành vi và dự đoán khả năng khách hàng mua lại trên website thương mại điện tử tối giản.

## Trạng thái

Repository hiện là **base scaffold** cho toàn bộ TLCN:

- storefront Next.js;
- Ecommerce API FastAPI và Alembic shell;
- Event Collector ghi closed JSONL;
- reproducible generator shell;
- package pipeline Bronze–Silver–Gold;
- Airflow core DAG và repurchase ML DAG;
- Spark/Delta/MinIO infrastructure;
- MySQL analytics và Superset;
- quality rules, test layout và documentation layout.

Các router nghiệp vụ, 12 model/migration OLTP và transformation thực tế chưa được triển khai. Pipeline/ML stage runner hiện chỉ tạo scaffold audit record để kiểm tra wiring, không tạo dữ liệu phân tích giả.

## Bắt đầu

Yêu cầu:

- Docker Engine và Docker Compose v2;
- Make;
- tối thiểu khoảng 8 GB RAM nếu chạy đồng thời cả ba profile.

```bash
cp .env.example .env
make core-up
```

Chạy toàn bộ platform:

```bash
make platform-up
```

Các địa chỉ local mặc định:

| Thành phần | URL |
|---|---|
| Storefront | `http://localhost:3000` |
| Ecommerce API docs | `http://localhost:8000/docs` |
| Event Collector docs | `http://localhost:8001/docs` |
| Airflow | `http://localhost:8080` |
| MinIO console | `http://localhost:9001` |
| Spark master UI | `http://localhost:8082` |
| Superset | `http://localhost:8088` |

Phải thay toàn bộ credential `change-me-*` trước khi dùng ngoài máy cá nhân.

## Lệnh chính

```bash
make help
make core-up
make batch-up
make bi-up
make generator-small
make validate
make down
```

`make reset` xóa cả persistent volumes và chỉ nên dùng khi muốn dựng lại môi trường sạch.

## Tài liệu nguồn

- `remake.md`: phạm vi TLCN và acceptance hiện hành.
- `schema.md`: logical schema OLTP và transaction catalogue.
- `web-plan.md`: implementation plan của source website.
- `PROJECT_STRUCTURE.md`: kiến trúc monorepo và dependency boundary.
- `OLTP.md`: nguyên tắc thiết kế OLTP tham khảo.

