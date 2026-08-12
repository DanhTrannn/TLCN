# OLTP Data Generator

Generator tạo dataset deterministic từ YAML config. Dataset có thể được xuất thành file SQL để import trực tiếp vào MySQL đã chạy migration.

Generator cũng xuất structured access log cùng contract với API thật. Log được chia theo
cửa sổ UTC 15 phút, nén `jsonl.gz` và có manifest SHA-256 cạnh từng file.

## Export SQL

```bash
docker compose --profile tools build generator
docker compose --profile tools run --rm generator export-sql \
  --config /app/configs/small.yml \
  --output /data/generator/small.sql
```

File xuất hiện trên host tại `data/generator/small.sql`.

## Export access logs

```bash
docker compose --profile tools run --rm generator export-logs \
  --config /app/configs/small.yml \
  --output-directory /data/generator/access-logs \
  --expected-requests 60000
```

Output xuất hiện tại `data/generator/access-logs/landing/logs/`. Cùng config và
`expected-requests` tạo cùng logical identity và byte-identical gzip/manifest. Tổng số
event thực tế dao động deterministic quanh kỳ vọng vì arrivals được sinh riêng cho từng
cửa sổ bằng mô hình Poisson (xấp xỉ chuẩn khi kỳ vọng cửa sổ lớn).

Access log dùng đúng route/action của API, cùng UUIDv5 actor/product/variant với file SQL,
UTC event time và `data_origin=synthetic`. Phân phối giữ peak buổi tối, cuối tuần, Tết,
ngày đôi 1/1..12/12 và Black Friday theo giờ `Asia/Ho_Chi_Minh`; campaign tăng cả traffic,
checkout mix, latency và error rate. Các hệ số là giả định phục vụ test/BI, không phải số
liệu thực tế của một sàn hay thị trường Việt Nam.

Khi profile `batch` và MinIO đang chạy, upload các file đã đóng vào Landing:

```bash
./scripts/upload_generated_logs.sh data/generator/access-logs
```

Contract và giới hạn phân tích nằm tại
[`docs/architecture/access-logs.md`](../docs/architecture/access-logs.md).

Config `small.yml` tạo:

- 500 customer;
- 60 product có tên, mô tả và mã mẫu thời trang thực tế theo từng category;
- 3 product archive ở current snapshot (5% làm tròn xuống), vẫn giữ variant và lịch sử;
- 240 variant;
- 3.000 order trong 12 tháng;
- wishlist, checked-out cart, active/abandoned cart;
- order item, payment, lifecycle `paid/confirmed/completed/cancelled` và status history;
- coupon/redemption, full refund của đơn hủy và review sau mua;
- coupon campaign/0h đã hết hạn được archive, nhưng redemption cũ vẫn được giữ;
- inventory đã đối soát với đơn không bị hủy.

## Import MySQL

Sau khi profile `core` healthy và Alembic đã migrate:

```bash
./scripts/import_generated_sql.sh data/generator/small.sql
```

SQL không tắt FK/CHECK, chạy trong một transaction và fail-fast nếu vi phạm invariant. Cùng một file không được import hai lần; muốn thêm dataset khác, thay `scenario_id` hoặc `seed` để có logical identity mới rồi export lại.

Kiểm tra current archive state và số quan hệ lịch sử còn được bảo toàn trong DBeaver:

```sql
SELECT 'products' AS entity, COUNT(*) AS archived_count
FROM products WHERE archived_at IS NOT NULL
UNION ALL
SELECT 'coupons', COUNT(*)
FROM coupons WHERE archived_at IS NOT NULL;

SELECT COUNT(DISTINCT p.product_id) AS archived_products_with_order_history
FROM products p
JOIN product_variants v ON v.product_id = p.product_id
JOIN order_items oi ON oi.variant_id = v.variant_id
WHERE p.archived_at IS NOT NULL;

SELECT COUNT(DISTINCT c.coupon_id) AS archived_coupons_with_redemption_history
FROM coupons c
JOIN coupon_redemptions cr ON cr.coupon_id = c.coupon_id
WHERE c.archived_at IS NOT NULL;
```

Archive count là current business state từ MySQL. Không dùng số access log `DELETE`
2xx để thay cho các truy vấn này vì request lặp idempotent vẫn tạo thêm access log.

CLI in tài khoản demo sau mỗi lần export. Email chứa tám ký tự đầu của
`logical_identity`; mật khẩu local cố định là `Demo@12345`. Luôn lấy email từ
output của CLI hoặc phần header của file SQL thay vì hard-code identity cũ.

Tài khoản demo có nhiều đơn hàng trải đều trong lịch sử để kiểm tra Storefront.

## Chiến lược định danh

Generator giữ đúng mô hình identity của OLTP:

- PK/FK nội bộ như `customer_id`, `product_id`, `order_id` vẫn là
  `BIGINT` surrogate key để join, index và bulk import hiệu quả;
- `public_id` được sinh bằng UUIDv5 deterministic và ghi vào MySQL
  `BINARY(16)` qua `UUID_TO_BIN('<uuid>')`;
- `logical_identity`, `generation_run_id`, checkout/payment/refund
  idempotency key và `payment_reference` đều là UUID canonical;
- `order_number`, SKU, slug và coupon code vẫn là business key dễ đọc,
  không đổi thành UUID.

UUIDv5 được dùng thay UUID ngẫu nhiên vì cùng config và generator version phải
sinh lại đúng cùng identity. Khi config, phân phối, seed hoặc generator version
thay đổi, `logical_identity` và toàn bộ UUID thuộc dataset cũng thay đổi.
Các file SQL sinh bằng generator trước `0.6.0` chưa theo contract archive/review hiện
hành và phải được export lại trước khi dùng script import hiện hành.

## Chạy trực tiếp bằng uv

```bash
uv run --locked \
  --package data-generator -- \
  generator export-sql \
  --config generator/configs/small.yml \
  --output data/generator/small.sql
```

## Kiểm tra

```bash
uv run --locked \
  --package data-generator --extra dev -- \
  pytest generator/tests
```

## Phân phối dữ liệu TMĐT Việt Nam (`distributions`)

Các profile trong `configs/` mô phỏng hành vi phổ biến của sàn TMĐT Việt Nam theo
quy tắc có kiểm soát, không sao chép dữ liệu hay thuật toán nội bộ của một sàn cụ
thể. Nếu config không khai báo `distributions`, generator dùng profile mặc định
trong `src/generator/config.py`.

| Tham số | Ý nghĩa |
|---|---|
| `business_timezone` | Múi giờ nghiệp vụ, chốt là `Asia/Ho_Chi_Minh`; SQL vẫn lưu UTC |
| `day_of_week` | 7 hệ số Thứ 2..Chủ nhật, cuối tuần cao hơn |
| `hour_of_day` | 24 hệ số giờ địa phương, peak thường ngày 19h–22h |
| `campaign_hour_of_day` | Phân phối riêng cho ngày campaign, có spike 0h–2h, 12h và 20h–23h |
| `seasonality.tet` | Cửa sổ Tết, `peak` là hệ số nhân nhu cầu ở trung tâm mùa vụ |
| `seasonality.sales` | Sale ngày đôi 1/1..12/12 và Black Friday; 9/9..12/12 có boost cao hơn |
| `categories` | Trọng số 8 danh mục thời trang nữ |
| `price_bands` | Histogram giá VND; giá variant làm tròn tới 1.000đ |
| `order_size` | Tỷ lệ đơn có 1/2/3/4 dòng hàng |
| `quantity_per_item` | Tỷ lệ quantity 1/2/3 trên mỗi dòng hàng |
| `customers` | Nhóm `loyal`, `regular`, `one_off`; có tần suất mua và `campaign_affinity` riêng |
| `coupons` | Tỷ lệ dùng coupon thường/campaign/0h/đơn đầu, hệ số theo nhóm khách và mệnh giá |
| `reviews` | Tỷ lệ review theo nhóm khách, phân phối rating, trạng thái hiển thị/ẩn hậu kiểm và độ trễ sau mua |
| `cancellations` | Tỷ lệ hủy thường/campaign, phần tăng khi dùng coupon, hệ số nhóm khách và lý do VN |

### Quan hệ dữ liệu có chủ đích

- Order tăng vào cuối tuần, mùa Tết, ngày đôi và Black Friday; ngày campaign ưu tiên các khung 0h, 12h và buổi tối theo giờ Việt Nam.
- Khách loyal/regular/one-off khác nhau về số lần mua, khoảng cách giữa đơn, khả năng bám campaign, dùng coupon, review và hủy đơn.
- Coupon 0h chỉ hiệu lực 00:00–02:00 giờ Việt Nam; coupon campaign theo ngày đôi; welcome ưu tiên đơn đầu; coupon thường có ngưỡng subtotal cao hơn.
- Đơn campaign, đơn dùng coupon và khách one-off có xác suất hủy cao hơn; lý do hủy dùng nội dung nghiệp vụ tiếng Việt. Đơn hủy tạo full refund và release redemption.
- Review chỉ phát sinh từ item thuộc order `completed`; rating và nội dung tiếng Việt
  luôn khớp nhau, có độ trễ sau giao hàng và được hiển thị ngay. Tỷ lệ synthetic mặc
  định gồm 94% đang hiển thị và 6% đã bị admin ẩn hậu kiểm, không có trạng thái chờ duyệt.
- Một phần wishlist được tạo trước lần mua đầu của cùng sản phẩm rồi đánh dấu removed tại lúc mua; phần còn lại vẫn present hoặc bị gỡ không chuyển đổi. Nhờ đó có thể tính wishlist-to-purchase conversion.
- Archive dùng RNG riêng để không làm xáo trộn order distribution: cứ 20 product có một
  product archive tại `anchor_time`; coupon campaign/0h có `ends_at <= anchor_time` được
  archive tại `ends_at`. Cả hai đều inactive, lưu admin synthetic và lý do archive,
  trong khi order item/redemption lịch sử không bị xóa.

Các pattern trên tạo được câu hỏi phân tích rõ ràng: revenue lift ngày sale, hiệu quả
coupon theo khung giờ/segment, chi phí discount, cancellation rate, review rate/rating,
wishlist conversion và repurchase propensity. Đây là dữ liệu synthetic có giả định,
không được diễn giải như thống kê thực tế của thị trường.

Lưu ý:

- Mốc 0h Việt Nam được chuyển thành UTC trước khi ghi `DATETIME(6)`; dashboard phải chuyển lại `Asia/Ho_Chi_Minh` khi phân tích giờ/ngày nghiệp vụ.
- `logical_identity` phụ thuộc generator version và toàn bộ `distributions`; thay đổi phân phối tạo dataset mới. Hãy đổi `scenario_id`/`seed` hoặc reset DB trước khi import lại.
- Sau khi sửa config phải build lại image: `docker compose --profile tools build generator`.

## Chiến lược import theo quy mô

Exporter hiện gom tối đa 1.000 dòng trong mỗi multi-row `INSERT` và giữ toàn bộ
dataset trong một transaction. Cách này phù hợp cho `small.yml` và `medium.yml`
vì đơn giản, giữ FK/CHECK và rollback toàn bộ khi lỗi.

Với `large-local.yml` hoặc `large-10m.yml`, nên bổ sung một export mode riêng:

1. xuất CSV/TSV theo từng bảng theo đúng thứ tự parent trước child;
2. dùng `LOAD DATA LOCAL INFILE` vào staging tables;
3. kiểm tra count, FK, amount và inventory tại staging;
4. promote sang OLTP theo batch có checkpoint và `generation_run_id`;
5. chỉ đánh dấu generation run hoàn tất sau reconciliation.

`mysqlsh util.loadDump()` với nhiều thread là phương án thay thế nếu generator
xuất MySQL dump directory. Không nên tắt `FOREIGN_KEY_CHECKS` trên bảng OLTP chỉ
để tăng tốc; nếu cần tối ưu local, hãy thực hiện ở staging và validate trước khi
promote.
