# D&K E-Commerce – Bộ trình diễn tín hiệu tác nghiệp

> Các tên kỹ thuật cũ như `simulate_cdc.py`, `print_cdc_event` và tiền tố `ORD-CDC-*` được giữ để tương thích với script/reset hiện có. Bộ demo này **ghi giao dịch trực tiếp vào MySQL và dashboard đọc lại qua FastAPI**; nó không sử dụng MySQL binlog, Debezium hay Kafka CDC.

## Luồng dữ liệu thực tế

```text
Demo scenarios ── SQLAlchemy transaction ──> MySQL OLTP
                                                │
Admin BI Hub <── FastAPI operational queries ───┘

FastAPI access logs ──> Kafka ──> Flink ──> Iceberg
MySQL historical data ──> Spark batch ──> Iceberg Gold ──> Trino
```

Các kịch bản tạo dữ liệu OLTP có kiểm soát để làm thay đổi chỉ số mà endpoint analytics tính tại thời điểm truy vấn. Sau khi chạy, bấm **Làm mới dữ liệu** trên dashboard để quan sát kết quả.

## Sáu kịch bản

| # | Vai trò | Tình huống | Bảng chính |
|---|---|---|---|
| 1 | Marketing | Voucher gần hết ngân sách và review 1 sao tăng | `coupons`, `coupon_redemptions`, `product_reviews` |
| 2 | Inventory | Tốc độ rút kho cao và hết hàng | `inventory` |
| 3 | Operations | Boom COD theo khu vực và hàng đợi đóng gói | `shipments`, `orders` |
| 4 | Store | Hết hàng tại quầy và cao điểm POS | `store_inventory`, `orders` |
| 5 | Sales | Sản phẩm tăng tốc và lệch pha kênh | `orders`, `order_items` |
| 6 | Executive | COD đang luân chuyển và biên lợi nhuận giảm | `shipments`, `orders`, `order_items` |

## Chạy demo

Khởi động core stack:

```bash
docker compose --profile core up -d
```

Mở menu tương tác:

```bash
./demo/run_demo.sh
```

Hoặc chạy trực tiếp:

```bash
./demo/run_demo.sh 1
./demo/run_demo.sh all
./demo/run_demo.sh reset
```

Dashboard: [http://localhost:3000/admin/analytics](http://localhost:3000/admin/analytics).

## Quy trình trình diễn

1. Mở dashboard và chọn vai trò tương ứng.
2. Chạy một scenario trong terminal.
3. Làm mới dashboard; API sẽ tính lại tín hiệu từ trạng thái OLTP vừa thay đổi.
4. Chạy `./demo/run_demo.sh reset` sau buổi demo.

Reset chỉ thu hồi các bản ghi được đánh dấu dành cho demo. Nếu đã chạy batch ingestion sau khi tạo dữ liệu demo, cần chạy lại pipeline sau reset để Lakehouse phản ánh trạng thái nguồn mới; reset MySQL không tự xóa snapshot Iceberg đã xuất bản.

## Ranh giới thuật ngữ

- “Operational signal”: đã triển khai, đọc MySQL qua API.
- “Access-log streaming”: đã triển khai, Kafka/Flink/Iceberg.
- “MySQL CDC”: chưa triển khai; chỉ được xem là hướng mở rộng tương lai.
