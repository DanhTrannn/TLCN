# OLTP Data Generator

Generator tạo dataset deterministic từ YAML config. Dataset có thể được xuất thành file SQL để import trực tiếp vào MySQL đã chạy migration.

## Export SQL

```bash
docker compose --profile tools build generator
docker compose --profile tools run --rm generator export-sql \
  --config /app/configs/small.yml \
  --output /data/generator/small.sql
```

File xuất hiện trên host tại `data/generator/small.sql`.

Config `small.yml` tạo:

- 500 customer;
- 60 product;
- 240 variant;
- 3.000 order trong 12 tháng;
- wishlist, checked-out cart, active/abandoned cart;
- order item, succeeded/failed payment, status history;
- inventory đã đối soát với lượng bán thành công.

## Import MySQL

Sau khi profile `core` healthy và Alembic đã migrate:

```bash
./scripts/import_generated_sql.sh data/generator/small.sql
```

SQL không tắt FK/CHECK, chạy trong một transaction và fail-fast nếu vi phạm invariant. Cùng một file không được import hai lần; muốn thêm dataset khác, thay `scenario_id` hoặc `seed` để có logical identity mới rồi export lại.

CLI in tài khoản demo sau khi export. Với `small.yml` hiện tại:

```text
Email: demo.bce4c219@tlcn.local
Password: Demo@12345
```

Tài khoản này có nhiều đơn hàng trải đều trong lịch sử để kiểm tra Storefront.

## Chạy trực tiếp bằng uv

```bash
UV_PROJECT_ENVIRONMENT=.venv-generator uv run --locked \
  --package tlcn-data-generator -- \
  tlcn-generator export-sql \
  --config generator/configs/small.yml \
  --output data/generator/small.sql
```
