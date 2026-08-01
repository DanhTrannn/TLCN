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

## Phân phối dữ liệu theo thị trường VN (`distributions`)

Mỗi config có thể khai báo khối `distributions` để mô phỏng đặc điểm mua hàng thời trang online tại Việt Nam. Nếu không khai báo, generator dùng bộ mặc định (profile VN) trong `src/tlcn_generator/config.py`.

| Tham số | Ý nghĩa |
|---|---|
| `day_of_week` | 7 hệ số cho Thứ 2..Chủ nhật (cuối tuần cao hơn) |
| `hour_of_day` | 24 hệ số cho 0h..23h (peak tối 19h-22h) |
| `seasonality.tet` | Cửa sổ xấp xỉ Tết (mặc định 25/1–18/2), `peak` = hệ số nhân doanh số tại đỉnh |
| `seasonality.sales` | Sự kiện sale: ngày cố định (`month`+`day`) hoặc Black Friday (`weekday`+`week_index`); `boost` áp cho ngày sự kiện và `after_days` ngày sau |
| `categories` | Trọng số 8 danh mục (ao, dam, vay, quan, khoac, phu-kien, giay, tui-xach) |
| `price_bands` | Histogram giá sản phẩm (min/max/weight); giá làm tròn tới 1.000đ |
| `order_size` | Phần trăm đơn có 1/2/3/4 món (tổng = 100) |
| `quantity_per_item` | Phần trăm số lượng 1/2/3 mỗi món (tổng = 100) |
| `customers` | 3 nhóm khách: `loyal` (mua lại nhanh, tạo tín hiệu repurchase 30 ngày), `regular`, `one_off` (mua 1 lần); `share` cộng = 1 |

Lưu ý:
- `logical_identity` phụ thuộc vào `distributions` — thay đổi phân phối tạo ra dataset mới; không import trùng vào database đã chứa dataset cũ cùng `scenario_id` (hãy đổi `scenario_id`/`seed` hoặc reset DB).
- Sau khi sửa config phải build lại image: `docker compose --profile tools build generator`.
