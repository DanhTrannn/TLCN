# Đặc tả tín hiệu tác nghiệp thời gian thực cho Dashboard

> Tên tệp được giữ lại để không làm hỏng các liên kết cũ. Bản triển khai hiện tại **không có MySQL binlog CDC, Debezium hoặc Kafka Connect**.

## 1. Ranh giới triển khai

Hệ thống có hai đường dữ liệu độc lập:

```text
Giao dịch nghiệp vụ
MySQL OLTP ── FastAPI query ──> Admin BI Hub (tín hiệu tác nghiệp hiện thời)

Nhật ký truy cập
FastAPI access log ── Kafka ── Flink ── Iceberg ── Trino (phân tích log)

Dữ liệu lịch sử
MySQL OLTP ── Spark batch ── Bronze/Silver/Gold Iceberg ── Trino (BI lịch sử)
```

- Các endpoint “real-time signal” đọc trạng thái hiện thời từ MySQL qua FastAPI. Đây là truy vấn tác nghiệp có giới hạn, không phải CDC.
- Kafka/Flink chỉ vận chuyển access logs theo contract `ecommerce.access:1.0.0`.
- Dữ liệu giao dịch đi vào Lakehouse bằng Spark batch incremental với composite cursor và lookback.
- Không được mô tả dashboard hiện tại là nhận sự kiện `INSERT/UPDATE` từ binlog.

## 2. Danh mục tín hiệu theo vai trò

| Vai trò | Tín hiệu | Bảng OLTP chính | Cách phát hiện hiện tại | Hành động |
|---|---|---|---|---|
| Executive | Xói mòn biên lợi nhuận nội ngày | `orders`, `order_items` | FastAPI tổng hợp COGS và doanh thu của cửa sổ gần nhất | Điều chỉnh mức giảm giá |
| Executive | Tiền COD đang luân chuyển | `orders`, `shipments`, `payments` | Tổng COD của đơn đang giao/chưa hoàn tất | Lập lịch đối soát |
| Sales | Sản phẩm tăng tốc bất thường | `orders`, `order_items` | So tốc độ bán gần nhất với baseline lịch sử | Đưa sản phẩm lên banner |
| Sales | Lệch nhịp online/POS | `orders` | So sánh `channel='online'` và `channel='pos'` | Kích hoạt chương trình tại quầy |
| Store | Hết tồn tại quầy | `store_inventory`, `inventory` | Tồn chi nhánh bằng 0 trong khi kho trung tâm còn hàng | Tạo yêu cầu điều chuyển |
| Store | Tiến độ doanh thu ngày | `orders` | Doanh thu POS trong ngày so với mục tiêu | Gợi ý upsell |
| Inventory | Runway tồn kho thấp | `inventory`, `inventory_transactions` | Tồn hiện tại chia tốc độ xuất gần nhất | Tạo phiếu nhập xưởng khẩn |
| Inventory | Nguy cơ oversell | `inventory` | Cảnh báo khi tồn dưới ngưỡng; checkout vẫn khóa hàng trong transaction | Khóa/bật lại bán web |
| Operations | Tỷ lệ boom COD theo khu vực | `orders`, `shipments` | Tỷ lệ đơn `failed_delivery` sau đủ 3 lần giao | Hạn chế COD khu vực rủi ro |
| Operations | Hàng đợi đóng gói | `orders`, `order_status_history` | Tuổi đơn ở `paid/confirmed` vượt SLA | Điều phối nhân sự |
| Marketing | Tốc độ dùng voucher | `coupons`, `coupon_redemptions`, `orders` | Mức sử dụng và tổng chiết khấu trong cửa sổ gần nhất | Đóng mã/điều chỉnh ngân sách |
| Marketing | Cụm review tiêu cực | `product_reviews` | Đếm review 1–2 sao gần nhất | Tạm dừng quảng cáo |

Mọi hành động ghi dữ liệu phải đi qua endpoint có RBAC, CSRF, transaction và audit log tương ứng; dashboard không ghi trực tiếp vào MySQL.

## 3. Độ tươi và tải truy vấn

- Tín hiệu tác nghiệp chỉ quét cửa sổ thời gian ngắn, dùng index và trả tập kết quả giới hạn.
- Dashboard lịch sử, xu hướng dài hạn và đối soát phải dùng Trino/Gold, không dùng OLTP.
- Access-log dashboards dùng các fact/mart log trong Iceberg.
- Nếu truy vấn tác nghiệp trở thành tải đáng kể, cần read replica hoặc cache trước khi mở rộng tần suất polling.

## 4. Phân biệt transaction signals và clickstream

| Loại | Ví dụ | Nguồn hiện tại | Đích |
|---|---|---|---|
| Trạng thái giao dịch | đơn, tồn, coupon, shipment, return | MySQL qua FastAPI; Spark batch vào Lakehouse | Dashboard tác nghiệp và Gold lịch sử |
| Hành vi truy cập | route, latency, HTTP status, search action | Structured access logs qua Kafka/Flink | Iceberg log facts/marts |

Không suy diễn thay đổi tồn kho hoặc doanh thu từ access log; cũng không dùng truy vấn OLTP dài hạn để thay thế Gold marts.

## 5. CDC trong tương lai (ngoài phạm vi hiện tại)

Nếu triển khai CDC sau này, thay đổi đó phải bổ sung đầy đủ:

1. MySQL row-based binlog và tài khoản có quyền tối thiểu.
2. Debezium/Kafka Connect hoặc một connector tương đương.
3. Envelope contract, schema evolution, tombstone/delete semantics và DLQ.
4. Exactly-once/idempotent sink, checkpoint, replay và quan sát lag.
5. Kiểm thử đối soát giữa MySQL, CDC topics và Iceberg.
6. Cập nhật tài liệu, Docker Compose và runbook vận hành trước khi gọi tính năng là “CDC”.

Cho đến khi các mục này tồn tại trong mã nguồn và hạ tầng, thuật ngữ chuẩn của đồ án là **tín hiệu tác nghiệp từ OLTP**, không phải CDC.
