# Structured access logs

## Quyết định kiến trúc

Nguồn log chính thức là **một JSON event cho mỗi HTTP request hoàn tất tại FastAPI**.
Storefront chỉ gọi API và không tự suy diễn status/latency phía server. MySQL vẫn là
nguồn sự thật cho order, payment, coupon, inventory, cart, wishlist và review; access
log chỉ trả lời traffic, nhu cầu search/product, độ trễ và lỗi theo route.

```text
Browser → FastAPI middleware → compact JSON trên stdout Docker
                               ↓
              Fluent Bit tail + persistent disk buffer
                               ↓ đóng file tối đa khoảng 15 phút
              MinIO landing/logs/*.jsonl.gz (immutable)
                               ↓
          Airflow/Spark manifest → Bronze → Silver → Gold
```

Trong phạm vi thay đổi này, producer web, Fluent Bit → Landing, generator và manifest
của dữ liệu synthetic đã được triển khai. DAG tạo manifest cho log thật và các bảng
Bronze/Silver/Gold vẫn là bước pipeline tiếp theo, chưa được mô tả như đã hoàn tất.

Không đặt OpenTelemetry Collector trong đường đi hiện tại. Contract dùng cách đặt tên
gần OpenTelemetry và dành sẵn `trace_id`/`span_id`, nhưng hai field được phép `null`.
Khi hệ thống cần distributed tracing hoặc OTLP metrics/traces, có thể thêm Collector mà
không đổi grain hay khóa dedup của access log. Fluent Bit được chọn vì nhiệm vụ hiện tại
chỉ là thu log container, buffer, nén, retry và đẩy S3-compatible MinIO.

## Contract v1

Contract máy đọc nằm tại
[`ecommerce-access-v1.schema.json`](../contracts/ecommerce-access-v1.schema.json).

- Grain: một completed request tại `ecommerce-api`.
- Khóa logic Silver: `request.id` do server tạo; không nhận ID do client cung cấp.
- Thời gian: UTC; `timestamp` là lúc hoàn tất và `event.duration_ns` dùng monotonic clock.
- Route: template FastAPI như `/api/v1/products/{slug}`; route không match dùng
  `__unmatched__`, không lưu raw path.
- Actor: `anonymous`, `customer`, `admin`, `system`; key lấy sau khi server xác thực.
- Commerce context: action và tập search/filter/product/variant đã allowlist.
- Admin archive dùng action `admin_product_archive` hoặc `admin_coupon_archive`; actor
  được resolve từ session server-side như mọi request đã xác thực.
- Privacy: không lưu IP, raw query, body, cookie, Authorization, CSRF, idempotency key,
  email, phone, địa chỉ, payment detail hoặc exception message/stack trace.
- `data_origin`: `observed` cho web thật, `synthetic` cho generator.

Schema version là `ecommerce.access/1.0.0`. Thay đổi tương thích có thể thêm optional
field trong minor version; đổi nghĩa, grain hoặc kiểu field phải tăng major version và
giữ parser song song trong thời gian replay còn hiệu lực.

## Ý nghĩa của 15 phút

`FLUENT_BIT_UPLOAD_TIMEOUT=15m` làm Fluent Bit đóng và upload object đang mở sau khoảng
15 phút. Đây là micro-batch vật lý, **không bảo đảm object đúng biên đồng hồ** `:00`,
`:15`, `:30`, `:45`; file có thể đóng sớm khi đạt 128 MiB hoặc đóng muộn khi retry.
Airflow/Spark phải gán request vào cửa sổ logic half-open
`[window_start, window_end)` bằng `event.timestamp`, tạo manifest/checksum trước Bronze
và dùng watermark cho log đến trễ.

Fluent Bit lưu offset tail, chunk buffer và S3 staging trong ba Docker volume riêng.
Khi MinIO tạm ngừng, agent retry từ buffer; Bronze vẫn giữ duplicate nếu delivery được
replay và Silver mới dedup bằng `request.id`.

Mặc định `FLUENT_BIT_READ_FROM_HEAD=false` để một collector mới chỉ nhận log phát sinh
sau khi khởi động. Lần bootstrap/backfill local có thể đặt biến này thành `true`; tail DB
bền vững sẽ giữ offset cho các lần restart tiếp theo.

## Landing và Medallion

Cả Log thật (Fluent Bit) và Log lịch sử (Generator) được ghi đồng bộ dưới cùng một layout phân vùng chuẩn Hive:

```text
landing/logs/date=YYYY-MM-DD/hour=HH/service=ecommerce-api/<part_or_uuid>.jsonl.gz
```

- Generator ghi file đóng theo UTC event window (15 phút), kèm manifest cạnh file.
- Fluent Bit ghi micro-batch đóng sau mỗi khoảng 15 phút (`upload_timeout: 15m`).
- Downstream Spark/Airflow đọc đồng nhất dưới `landing/logs/date=*/hour=*/*`, phân biệt nguồn qua trường `data_origin` (`observed` hoặc `synthetic`).

- Landing: object gzip đã đóng, immutable, lưu đệm tạm thời.
- Bronze: giữ raw lineage, source path/checksum/line number và cả duplicate.
- Silver: validate schema, quarantine lỗi, pseudonymize actor, parse user-agent, dedup request ID, chuẩn hóa route/search/filter.
- Gold: volume/error/latency theo route-hour, product demand, search/filter demand và
  authenticated coverage. Revenue/conversion nghiệp vụ phải reconcile với OLTP.

### Không suy diễn archive từ access log

Một log `DELETE` status 2xx chỉ chứng minh API đã xử lý request thành công. Nó không
chứng minh row vừa đổi trạng thái: request có thể là replay idempotent, hoặc transaction
nghiệp vụ có thể thay đổi trong một phiên bản khác. Vì vậy:

- trạng thái archive của product/coupon lấy từ `archived_at`,
  `archived_by_customer_id`, `archive_reason` và `is_active` trong MySQL;
- `updated_at` cùng PK là cursor để Silver merge current state;
- access log chỉ đo số request archive, tỷ lệ lỗi, latency và admin workload;
- lý do archive chỉ nằm trong MySQL, không đưa request body vào log;
- Gold dimension Type 1 có thể expose `is_archived` và `archived_at`; order/order item
  snapshot giữ lịch sử bán hàng trước archive. Không dựng SCD2 chỉ từ chuỗi request.

## Vận hành local

Khởi động nguồn web và collector:

```bash
docker compose --profile core --profile batch up -d --build
docker compose --profile batch logs -f fluent-bit
```

Sau khi tạo request trên Storefront/API và chờ agent đóng file, kiểm tra object bằng
MinIO Console tại `http://localhost:9001`. Mount
`/var/lib/docker/containers` yêu cầu Docker Engine kiểu Linux dùng `json-file`; với
rootless Docker phải đổi host path theo Docker data-root thực tế.

Generator tạo payload Landing local:

```bash
docker compose --profile tools run --rm generator export-logs \
  --config /app/configs/small.yml \
  --output-directory /data/generator/access-logs \
  --expected-requests 60000
./scripts/upload_generated_logs.sh data/generator/access-logs
```

Cùng config và expected count tạo byte-identical gzip/manifest. `expected-requests` là
kỳ vọng của mô hình Poisson theo từng 15 phút nên số event thực tế có dao động
deterministic quanh giá trị này. Đây là giả định synthetic, không phải thống kê của một
sàn cụ thể hay của thị trường Việt Nam.
