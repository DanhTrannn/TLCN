# OLTP Schema Reference

Tài liệu tham chiếu schema vật lý từ [database/schema.sql](../../database/schema.sql), cấu hình extract từ [default.yml](../../pipelines/config/default.yml) và nghiệp vụ từ [API modules](../../services/ecommerce-api/app/modules). DDL là nguồn xác định kiểu cột, khóa và CHECK; model ORM không tự nâng cấp database.

## 1. Phạm vi và khởi tạo

MySQL có **28 bảng, 50 khóa ngoại vật lý, 49 UNIQUE key và 79 CHECK constraint**. Batch và CDC lấy 27 bảng, bỏ `customer_credentials`. Fact/dimension/mart nằm ở Iceberg; metadata Airflow/Polaris nằm ở PostgreSQL.

Schema chỉ chạy tự động khi MySQL data directory trống. API startup seed catalog/admin, không tạo hoặc ALTER bảng. Database đang có dữ liệu cần so sánh DDL và áp dụng thay đổi riêng; xem [database guide](../../database/README.md).

ERD hiện tại: [28 bảng và 50 FK](../diagram/13-erd-mysql-physical.drawio). Quan hệ `orders.staff_id → customers.customer_id` có trong ORM nhưng **không được khai báo FK trong DDL**; không dùng số quan hệ ORM thay cho số FK vật lý.

## 2. Quy ước và tính nhất quán

- PK dùng số nguyên; xem từng bảng để biết khóa và AUTO_INCREMENT. `store_inventory` có PK ghép `(store_id, variant_id)`; `store_inventory_id` là cột AUTO_INCREMENT có UNIQUE và được pipeline dùng làm khóa cursor.
- Public ID lưu `BINARY(16)`. Generator dùng UUIDv5 deterministic; runtime API còn dùng UUIDv7. Không mặc định mọi public ID là UUIDv5 hoặc mọi response đều giấu surrogate key.
- Tiền là số nguyên VND; kiểu/null/default cụ thể lấy theo DDL bên dưới. Thời gian dùng DATETIME(6), dịch vụ cấu hình UTC.
- InnoDB và API connection dùng READ COMMITTED; các service khóa hàng khi quyết định dựa trên tồn/coupon/trạng thái mutable.
- CHECK/UNIQUE/FK bảo vệ các ràng buộc được khai báo; điều kiện như quyền chủ đơn, chuyển trạng thái, số lượng trả tích lũy và số tiền hoàn còn cần service kiểm tra.
- FK có nhiều hành vi ON DELETE theo từng quan hệ; không coi tất cả là RESTRICT.
- Nhật ký/định danh giao dịch phục vụ truy vết; không có trigger tự bảo đảm mọi thay đổi trực tiếp bằng SQL đều tạo ledger/history.

## 3. Bảng và cursor trích xuất

Cursor dưới đây là cấu hình thực tế `(cursor_field, pk)`, không phải danh sách PK ghép suy ra từ nghiệp vụ. Trường `pk` của pipeline có thể dùng khóa UNIQUE kỹ thuật như store_inventory_id, không nhất thiết là PK vật lý. `mutability` là cách pipeline xử lý theo cấu hình, không chứng minh bản ghi sẽ không bao giờ đổi ở runtime.

| Bảng | PK vật lý | Cursor batch | Mutability trong pipeline |
|---|---|---|---|
| ``cart_items`` | ``(`cart_item_id`)`` | ``(updated_at, cart_item_id)`` | mutable |
| ``carts`` | ``(`cart_id`)`` | ``(updated_at, cart_id)`` | mutable |
| ``categories`` | ``(`category_id`)`` | ``(updated_at, category_id)`` | mutable |
| ``cities`` | ``(`city_id`)`` | ``(updated_at, city_id)`` | mutable |
| ``coupon_redemptions`` | ``(`coupon_redemption_id`)`` | ``(updated_at, coupon_redemption_id)`` | mutable |
| ``coupons`` | ``(`coupon_id`)`` | ``(updated_at, coupon_id)`` | mutable |
| ``customer_credentials`` | ``(`customer_id`)`` | Không trích xuất | Thông tin xác thực |
| ``customers`` | ``(`customer_id`)`` | ``(updated_at, customer_id)`` | mutable |
| ``delivery_staff`` | ``(`staff_id`)`` | ``(updated_at, staff_id)`` | mutable |
| ``inbound_receipt_items`` | ``(`item_id`)`` | ``(created_at, item_id)`` | append_only |
| ``inbound_receipts`` | ``(`receipt_id`)`` | ``(updated_at, receipt_id)`` | mutable |
| ``inventory`` | ``(`variant_id`)`` | ``(updated_at, variant_id)`` | mutable |
| ``inventory_transactions`` | ``(`transaction_id`)`` | ``(created_at, transaction_id)`` | append_only |
| ``order_items`` | ``(`order_item_id`)`` | ``(created_at, order_item_id)`` | append_only |
| ``order_status_history`` | ``(`order_status_history_id`)`` | ``(created_at, order_status_history_id)`` | append_only |
| ``orders`` | ``(`order_id`)`` | ``(updated_at, order_id)`` | mutable |
| ``payments`` | ``(`payment_id`)`` | ``(created_at, payment_id)`` | append_only |
| ``product_reviews`` | ``(`review_id`)`` | ``(updated_at, review_id)`` | mutable |
| ``product_variants`` | ``(`variant_id`)`` | ``(updated_at, variant_id)`` | mutable |
| ``products`` | ``(`product_id`)`` | ``(updated_at, product_id)`` | mutable |
| ``refunds`` | ``(`refund_id`)`` | ``(updated_at, refund_id)`` | mutable |
| ``return_items`` | ``(`return_item_id`)`` | ``(updated_at, return_item_id)`` | mutable |
| ``return_requests`` | ``(`return_id`)`` | ``(updated_at, return_id)`` | mutable |
| ``shipment_attempts`` | ``(`attempt_id`)`` | ``(created_at, attempt_id)`` | append_only |
| ``shipments`` | ``(`shipment_id`)`` | ``(updated_at, shipment_id)`` | mutable |
| ``store_inventory`` | ``(`store_id`,`variant_id`)`` | ``(updated_at, store_inventory_id)`` | mutable |
| ``stores`` | ``(`store_id`)`` | ``(updated_at, store_id)`` | mutable |
| ``wishlist_items`` | ``(`wishlist_item_id`)`` | ``(updated_at, wishlist_item_id)`` | mutable |

**Giới hạn quan trọng:** `payments` dùng cursor `created_at`, trong khi COD completion cập nhật `payments.status` và `orders.paid_at`. Một cập nhật trên payment cũ ngoài cửa sổ lookback có thể không được batch bắt lại. `refunds` và `return_items` dùng `updated_at`; chúng không phải append-only trong cấu hình. Batch tăng dần cũng chưa tự áp dụng mọi hard delete. CDC có lưu các thay đổi đó ở Bronze nhưng chưa tự sửa Silver/Gold.

## 4. Tham chiếu cột và khóa

Các định nghĩa cột được chép từ DDL, giữ nguyên kiểu, nullability, default và generated expression. Danh sách UNIQUE/FK theo SQL vật lý; index thường và biểu thức CHECK đầy đủ xem file DDL. Đây là snapshot tài liệu, cần cập nhật cùng SQL khi thay schema.

### `cart_items`

| Cột | Định nghĩa MySQL |
|---|---|
| ``cart_item_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``cart_id`` | ``bigint unsigned NOT NULL`` |
| ``variant_id`` | ``bigint unsigned NOT NULL`` |
| ``quantity`` | ``int unsigned NOT NULL`` |
| ``is_present`` | ``tinyint(1) NOT NULL DEFAULT '1'`` |
| ``first_added_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``removed_at`` | ``datetime(6) DEFAULT NULL`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |

- ``PRIMARY KEY (`cart_item_id`)``.
- ``UNIQUE KEY `uq_cart_items_cart_id_variant_id` (`cart_id`,`variant_id`)``.
- ``FOREIGN KEY (`cart_id`) REFERENCES `carts` (`cart_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`variant_id`) REFERENCES `product_variants` (`variant_id`) ON DELETE RESTRICT``.
- Có 2 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `carts`

| Cột | Định nghĩa MySQL |
|---|---|
| ``cart_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``public_id`` | ``binary(16) NOT NULL`` |
| ``customer_id`` | ``bigint unsigned NOT NULL`` |
| ``status`` | ``varchar(16) NOT NULL DEFAULT 'active'`` |
| ``active_customer_guard`` | ``bigint unsigned GENERATED ALWAYS AS ((case when (`status` = _utf8mb4'active') then `customer_id` else NULL end)) STORED`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |
| ``checked_out_at`` | ``datetime(6) DEFAULT NULL`` |

- ``PRIMARY KEY (`cart_id`)``.
- ``UNIQUE KEY `uq_carts_public_id` (`public_id`)``.
- ``UNIQUE KEY `uq_carts_active_customer_guard` (`active_customer_guard`)``.
- ``FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE RESTRICT``.
- Có 1 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `categories`

| Cột | Định nghĩa MySQL |
|---|---|
| ``category_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``public_id`` | ``binary(16) NOT NULL`` |
| ``parent_category_id`` | ``bigint unsigned DEFAULT NULL`` |
| ``code`` | ``varchar(64) NOT NULL`` |
| ``name`` | ``varchar(160) NOT NULL`` |
| ``is_active`` | ``tinyint(1) NOT NULL DEFAULT '1'`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |

- ``PRIMARY KEY (`category_id`)``.
- ``UNIQUE KEY `uq_categories_code` (`code`)``.
- ``UNIQUE KEY `uq_categories_public_id` (`public_id`)``.
- ``FOREIGN KEY (`parent_category_id`) REFERENCES `categories` (`category_id`) ON DELETE RESTRICT``.

### `cities`

| Cột | Định nghĩa MySQL |
|---|---|
| ``city_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``code`` | ``varchar(32) NOT NULL`` |
| ``name`` | ``varchar(120) NOT NULL`` |
| ``is_active`` | ``tinyint(1) NOT NULL DEFAULT '1'`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |

- ``PRIMARY KEY (`city_id`)``.
- ``UNIQUE KEY `uq_cities_code` (`code`)``.

### `coupon_redemptions`

| Cột | Định nghĩa MySQL |
|---|---|
| ``coupon_redemption_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``coupon_id`` | ``bigint unsigned NOT NULL`` |
| ``order_id`` | ``bigint unsigned NOT NULL`` |
| ``customer_id`` | ``bigint unsigned NOT NULL`` |
| ``status`` | ``varchar(16) NOT NULL`` |
| ``redeemed_at`` | ``datetime(6) NOT NULL`` |
| ``released_at`` | ``datetime(6) DEFAULT NULL`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |

- ``PRIMARY KEY (`coupon_redemption_id`)``.
- ``UNIQUE KEY `uq_coupon_redemptions_order_id` (`order_id`)``.
- ``FOREIGN KEY (`coupon_id`) REFERENCES `coupons` (`coupon_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE RESTRICT``.
- Có 2 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `coupons`

| Cột | Định nghĩa MySQL |
|---|---|
| ``coupon_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``public_id`` | ``binary(16) NOT NULL`` |
| ``code_normalized`` | ``varchar(64) NOT NULL`` |
| ``discount_type`` | ``varchar(24) NOT NULL`` |
| ``discount_value`` | ``bigint unsigned NOT NULL`` |
| ``minimum_subtotal_vnd`` | ``bigint unsigned NOT NULL DEFAULT '0'`` |
| ``starts_at`` | ``datetime(6) NOT NULL`` |
| ``ends_at`` | ``datetime(6) NOT NULL`` |
| ``is_active`` | ``tinyint(1) NOT NULL DEFAULT '1'`` |
| ``total_usage_limit`` | ``bigint unsigned DEFAULT NULL`` |
| ``per_customer_usage_limit`` | ``int unsigned DEFAULT NULL`` |
| ``used_count`` | ``bigint unsigned NOT NULL DEFAULT '0'`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |
| ``archived_at`` | ``datetime(6) DEFAULT NULL`` |
| ``archived_by_customer_id`` | ``bigint unsigned DEFAULT NULL`` |
| ``archive_reason`` | ``varchar(500) DEFAULT NULL`` |

- ``PRIMARY KEY (`coupon_id`)``.
- ``UNIQUE KEY `uq_coupons_public_id` (`public_id`)``.
- ``UNIQUE KEY `uq_coupons_code_normalized` (`code_normalized`)``.
- ``FOREIGN KEY (`archived_by_customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE RESTRICT``.
- Có 8 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `customer_credentials`

| Cột | Định nghĩa MySQL |
|---|---|
| ``customer_id`` | ``bigint unsigned NOT NULL`` |
| ``email_normalized`` | ``varchar(320) NOT NULL`` |
| ``password_hash`` | ``varchar(255) NOT NULL`` |
| ``is_enabled`` | ``tinyint(1) NOT NULL DEFAULT '1'`` |
| ``password_changed_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |

- ``PRIMARY KEY (`customer_id`)``.
- ``UNIQUE KEY `uq_customer_credentials_email_normalized` (`email_normalized`)``.
- ``FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE RESTRICT``.

### `customers`

| Cột | Định nghĩa MySQL |
|---|---|
| ``customer_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``public_id`` | ``binary(16) NOT NULL`` |
| ``display_name`` | ``varchar(120) NOT NULL`` |
| ``status`` | ``varchar(16) NOT NULL DEFAULT 'active'`` |
| ``data_origin`` | ``varchar(16) NOT NULL DEFAULT 'manual'`` |
| ``generation_run_id`` | ``varchar(64) DEFAULT NULL`` |
| ``anonymized_at`` | ``datetime(6) DEFAULT NULL`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |
| ``role`` | ``varchar(32) NOT NULL DEFAULT 'customer'`` |
| ``city_id`` | ``bigint unsigned DEFAULT NULL`` |
| ``store_id`` | ``bigint unsigned DEFAULT NULL`` |
| ``is_cod_blocked`` | ``tinyint(1) NOT NULL DEFAULT '0'`` |
| ``boom_count`` | ``int unsigned NOT NULL DEFAULT '0'`` |
| ``cod_reinstated_at`` | ``datetime(6) DEFAULT NULL`` |
| ``cod_reinstated_by`` | ``bigint unsigned DEFAULT NULL`` |
| ``cod_reinstatement_reason`` | ``varchar(255) DEFAULT NULL`` |

- ``PRIMARY KEY (`customer_id`)``.
- ``UNIQUE KEY `uq_customers_public_id` (`public_id`)``.
- ``FOREIGN KEY (`city_id`) REFERENCES `cities` (`city_id`) ON DELETE SET NULL``.
- ``FOREIGN KEY (`cod_reinstated_by`) REFERENCES `customers` (`customer_id`) ON DELETE SET NULL``.
- ``FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE SET NULL``.
- Có 3 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `delivery_staff`

| Cột | Định nghĩa MySQL |
|---|---|
| ``staff_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``public_id`` | ``binary(16) NOT NULL`` |
| ``full_name`` | ``varchar(100) NOT NULL`` |
| ``phone`` | ``varchar(20) NOT NULL`` |
| ``vehicle_plate`` | ``varchar(30) DEFAULT NULL`` |
| ``is_active`` | ``tinyint(1) NOT NULL DEFAULT '1'`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |

- ``PRIMARY KEY (`staff_id`)``.
- ``UNIQUE KEY `uq_delivery_staff_public_id` (`public_id`)``.
- ``UNIQUE KEY `uq_delivery_staff_phone` (`phone`)``.

### `inbound_receipt_items`

| Cột | Định nghĩa MySQL |
|---|---|
| ``item_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``public_id`` | ``binary(16) NOT NULL`` |
| ``receipt_id`` | ``bigint unsigned NOT NULL`` |
| ``variant_id`` | ``bigint unsigned NOT NULL`` |
| ``quantity`` | ``int unsigned NOT NULL`` |
| ``unit_cost_vnd`` | ``bigint unsigned NOT NULL DEFAULT '0'`` |
| ``total_cost_vnd`` | ``bigint unsigned NOT NULL DEFAULT '0'`` |
| ``previous_cost_price_vnd`` | ``bigint unsigned NOT NULL DEFAULT '0'`` |
| ``new_cost_price_vnd`` | ``bigint unsigned NOT NULL DEFAULT '0'`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |

- ``PRIMARY KEY (`item_id`)``.
- ``UNIQUE KEY `uq_inbound_items_public_id` (`public_id`)``.
- ``FOREIGN KEY (`receipt_id`) REFERENCES `inbound_receipts` (`receipt_id`) ON DELETE CASCADE``.
- ``FOREIGN KEY (`variant_id`) REFERENCES `product_variants` (`variant_id`) ON DELETE RESTRICT``.
- Có 3 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `inbound_receipts`

| Cột | Định nghĩa MySQL |
|---|---|
| ``receipt_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``public_id`` | ``binary(16) NOT NULL`` |
| ``receipt_code`` | ``varchar(64) NOT NULL`` |
| ``batch_name`` | ``varchar(255) NOT NULL`` |
| ``status`` | ``varchar(24) NOT NULL DEFAULT 'completed'`` |
| ``total_items_count`` | ``int unsigned NOT NULL DEFAULT '0'`` |
| ``total_cost_vnd`` | ``bigint unsigned NOT NULL DEFAULT '0'`` |
| ``notes`` | ``text`` |
| ``created_by_customer_id`` | ``bigint unsigned NOT NULL`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |

- ``PRIMARY KEY (`receipt_id`)``.
- ``UNIQUE KEY `uq_inbound_receipts_public_id` (`public_id`)``.
- ``UNIQUE KEY `uq_inbound_receipts_code` (`receipt_code`)``.
- ``FOREIGN KEY (`created_by_customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE RESTRICT``.
- Có 3 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `inventory`

| Cột | Định nghĩa MySQL |
|---|---|
| ``variant_id`` | ``bigint unsigned NOT NULL`` |
| ``opening_on_hand`` | ``bigint unsigned NOT NULL`` |
| ``on_hand`` | ``bigint unsigned NOT NULL`` |
| ``version`` | ``bigint unsigned NOT NULL DEFAULT '0'`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |

- ``PRIMARY KEY (`variant_id`)``.
- ``FOREIGN KEY (`variant_id`) REFERENCES `product_variants` (`variant_id`) ON DELETE RESTRICT``.
- Có 3 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `inventory_transactions`

| Cột | Định nghĩa MySQL |
|---|---|
| ``transaction_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``public_id`` | ``binary(16) NOT NULL`` |
| ``variant_id`` | ``bigint unsigned NOT NULL`` |
| ``location_type`` | ``varchar(24) NOT NULL`` |
| ``store_id`` | ``bigint unsigned DEFAULT NULL`` |
| ``movement_type`` | ``varchar(32) NOT NULL`` |
| ``quantity_delta`` | ``int NOT NULL`` |
| ``reference_code`` | ``varchar(64) DEFAULT NULL`` |
| ``notes`` | ``varchar(255) DEFAULT NULL`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |

- ``PRIMARY KEY (`transaction_id`)``.
- ``UNIQUE KEY `uq_inventory_tx_public_id` (`public_id`)``.
- ``FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`variant_id`) REFERENCES `product_variants` (`variant_id`) ON DELETE RESTRICT``.
- Có 5 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `order_items`

| Cột | Định nghĩa MySQL |
|---|---|
| ``order_item_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``order_id`` | ``bigint unsigned NOT NULL`` |
| ``variant_id`` | ``bigint unsigned NOT NULL`` |
| ``product_public_id_snapshot`` | ``binary(16) NOT NULL`` |
| ``category_code_snapshot`` | ``varchar(64) NOT NULL`` |
| ``category_name_snapshot`` | ``varchar(160) NOT NULL`` |
| ``product_name_snapshot`` | ``varchar(200) NOT NULL`` |
| ``sku_snapshot`` | ``varchar(64) NOT NULL`` |
| ``size_code_snapshot`` | ``varchar(32) NOT NULL`` |
| ``color_code_snapshot`` | ``varchar(64) NOT NULL`` |
| ``unit_price_vnd`` | ``bigint unsigned NOT NULL`` |
| ``quantity`` | ``int unsigned NOT NULL`` |
| ``line_total_vnd`` | ``bigint unsigned NOT NULL`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``public_id`` | ``binary(16) NOT NULL`` |
| ``cost_price_vnd`` | ``bigint unsigned NOT NULL DEFAULT '0'`` |

- ``PRIMARY KEY (`order_item_id`)``.
- ``UNIQUE KEY `uq_order_items_order_id_variant_id` (`order_id`,`variant_id`)``.
- ``UNIQUE KEY `uq_order_items_public_id` (`public_id`)``.
- ``FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`variant_id`) REFERENCES `product_variants` (`variant_id`) ON DELETE RESTRICT``.
- Có 3 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `order_status_history`

| Cột | Định nghĩa MySQL |
|---|---|
| ``order_status_history_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``order_id`` | ``bigint unsigned NOT NULL`` |
| ``from_status`` | ``varchar(24) DEFAULT NULL`` |
| ``to_status`` | ``varchar(24) NOT NULL`` |
| ``transition_source`` | ``varchar(32) NOT NULL`` |
| ``reason`` | ``varchar(500) DEFAULT NULL`` |
| ``transition_idempotency_key`` | ``varchar(64) NOT NULL`` |
| ``transitioned_at`` | ``datetime(6) NOT NULL`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |

- ``PRIMARY KEY (`order_status_history_id`)``.
- ``UNIQUE KEY `uq_order_status_history_transition_idempotency_key` (`transition_idempotency_key`)``.
- ``UNIQUE KEY `uq_order_status_history_order_id_to_status` (`order_id`,`to_status`)``.
- ``FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE RESTRICT``.
- Có 3 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `orders`

| Cột | Định nghĩa MySQL |
|---|---|
| ``order_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``order_number`` | ``varchar(32) NOT NULL`` |
| ``cart_id`` | ``bigint unsigned DEFAULT NULL`` |
| ``customer_id`` | ``bigint unsigned DEFAULT NULL`` |
| ``checkout_idempotency_key`` | ``varchar(64) NOT NULL`` |
| ``status`` | ``varchar(24) NOT NULL`` |
| ``currency_code`` | ``char(3) NOT NULL DEFAULT 'VND'`` |
| ``subtotal_vnd`` | ``bigint unsigned NOT NULL`` |
| ``shipping_fee_vnd`` | ``bigint unsigned NOT NULL`` |
| ``total_vnd`` | ``bigint unsigned NOT NULL`` |
| ``receiver_name`` | ``varchar(160) NOT NULL`` |
| ``receiver_phone`` | ``varchar(32) NOT NULL`` |
| ``shipping_address_text`` | ``varchar(1000) NOT NULL`` |
| ``data_origin`` | ``varchar(16) NOT NULL DEFAULT 'manual'`` |
| ``generation_run_id`` | ``varchar(64) DEFAULT NULL`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |
| ``paid_at`` | ``datetime(6) DEFAULT NULL`` |
| ``completed_at`` | ``datetime(6) DEFAULT NULL`` |
| ``coupon_id`` | ``bigint unsigned DEFAULT NULL`` |
| ``coupon_code_snapshot`` | ``varchar(64) DEFAULT NULL`` |
| ``coupon_type_snapshot`` | ``varchar(24) DEFAULT NULL`` |
| ``coupon_value_snapshot`` | ``bigint unsigned DEFAULT NULL`` |
| ``discount_amount_vnd`` | ``bigint unsigned NOT NULL DEFAULT '0'`` |
| ``confirmed_at`` | ``datetime(6) DEFAULT NULL`` |
| ``cancelled_at`` | ``datetime(6) DEFAULT NULL`` |
| ``store_id`` | ``bigint unsigned DEFAULT NULL`` |
| ``channel`` | ``varchar(16) NOT NULL DEFAULT 'online'`` |
| ``staff_id`` | ``bigint unsigned DEFAULT NULL`` |
| ``payment_method`` | ``varchar(16) NOT NULL DEFAULT 'vietqr'`` |

- ``PRIMARY KEY (`order_id`)``.
- ``UNIQUE KEY `uq_orders_order_number` (`order_number`)``.
- ``UNIQUE KEY `uq_orders_checkout_idempotency_key` (`checkout_idempotency_key`)``.
- ``UNIQUE KEY `uq_orders_cart_id` (`cart_id`)``.
- ``FOREIGN KEY (`cart_id`) REFERENCES `carts` (`cart_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`coupon_id`) REFERENCES `coupons` (`coupon_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`)``.
- Có 15 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `payments`

| Cột | Định nghĩa MySQL |
|---|---|
| ``payment_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``payment_reference`` | ``varchar(64) NOT NULL`` |
| ``order_id`` | ``bigint unsigned NOT NULL`` |
| ``payment_idempotency_key`` | ``varchar(64) NOT NULL`` |
| ``status`` | ``varchar(16) NOT NULL`` |
| ``currency_code`` | ``char(3) NOT NULL DEFAULT 'VND'`` |
| ``amount_vnd`` | ``bigint unsigned NOT NULL`` |
| ``failure_code`` | ``varchar(64) DEFAULT NULL`` |
| ``attempted_at`` | ``datetime(6) NOT NULL`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |

- ``PRIMARY KEY (`payment_id`)``.
- ``UNIQUE KEY `uq_payments_payment_reference` (`payment_reference`)``.
- ``UNIQUE KEY `uq_payments_order_id` (`order_id`)``.
- ``UNIQUE KEY `uq_payments_payment_idempotency_key` (`payment_idempotency_key`)``.
- ``FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE RESTRICT``.
- Có 4 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `product_reviews`

| Cột | Định nghĩa MySQL |
|---|---|
| ``review_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``public_id`` | ``binary(16) NOT NULL`` |
| ``order_item_id`` | ``bigint unsigned NOT NULL`` |
| ``customer_id`` | ``bigint unsigned NOT NULL`` |
| ``product_id`` | ``bigint unsigned NOT NULL`` |
| ``rating`` | ``int unsigned NOT NULL`` |
| ``content`` | ``text`` |
| ``status`` | ``varchar(16) NOT NULL DEFAULT 'approved'`` |
| ``moderation_reason`` | ``varchar(500) DEFAULT NULL`` |
| ``moderated_by_customer_id`` | ``bigint unsigned DEFAULT NULL`` |
| ``moderated_at`` | ``datetime(6) DEFAULT NULL`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |

- ``PRIMARY KEY (`review_id`)``.
- ``UNIQUE KEY `uq_product_reviews_public_id` (`public_id`)``.
- ``UNIQUE KEY `uq_product_reviews_order_item_id` (`order_item_id`)``.
- ``FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`moderated_by_customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`order_item_id`) REFERENCES `order_items` (`order_item_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE RESTRICT``.
- Có 3 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `product_variants`

| Cột | Định nghĩa MySQL |
|---|---|
| ``variant_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``public_id`` | ``binary(16) NOT NULL`` |
| ``product_id`` | ``bigint unsigned NOT NULL`` |
| ``sku`` | ``varchar(64) NOT NULL`` |
| ``size_code`` | ``varchar(32) NOT NULL`` |
| ``color_code`` | ``varchar(64) NOT NULL`` |
| ``price_vnd`` | ``bigint unsigned NOT NULL`` |
| ``is_active`` | ``tinyint(1) NOT NULL DEFAULT '1'`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |
| ``cost_price_vnd`` | ``bigint unsigned NOT NULL DEFAULT '0'`` |

- ``PRIMARY KEY (`variant_id`)``.
- ``UNIQUE KEY `uq_product_variants_sku` (`sku`)``.
- ``UNIQUE KEY `uq_product_variants_public_id` (`public_id`)``.
- ``UNIQUE KEY `uq_product_variants_product_size_color` (`product_id`,`size_code`,`color_code`)``.
- ``FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE RESTRICT``.
- Có 1 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `products`

| Cột | Định nghĩa MySQL |
|---|---|
| ``product_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``public_id`` | ``binary(16) NOT NULL`` |
| ``category_id`` | ``bigint unsigned NOT NULL`` |
| ``slug`` | ``varchar(180) NOT NULL`` |
| ``name`` | ``varchar(200) NOT NULL`` |
| ``description`` | ``text`` |
| ``image_url`` | ``varchar(1024) DEFAULT NULL`` |
| ``is_active`` | ``tinyint(1) NOT NULL DEFAULT '1'`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |
| ``archived_at`` | ``datetime(6) DEFAULT NULL`` |
| ``archived_by_customer_id`` | ``bigint unsigned DEFAULT NULL`` |
| ``archive_reason`` | ``varchar(500) DEFAULT NULL`` |

- ``PRIMARY KEY (`product_id`)``.
- ``UNIQUE KEY `uq_products_slug` (`slug`)``.
- ``UNIQUE KEY `uq_products_public_id` (`public_id`)``.
- ``FOREIGN KEY (`archived_by_customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`) ON DELETE RESTRICT``.
- Có 2 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `refunds`

| Cột | Định nghĩa MySQL |
|---|---|
| ``refund_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``public_id`` | ``binary(16) NOT NULL`` |
| ``payment_id`` | ``bigint unsigned NOT NULL`` |
| ``refund_idempotency_key`` | ``varchar(64) NOT NULL`` |
| ``status`` | ``varchar(16) NOT NULL`` |
| ``currency_code`` | ``char(3) NOT NULL DEFAULT 'VND'`` |
| ``amount_vnd`` | ``bigint unsigned NOT NULL`` |
| ``reason`` | ``varchar(500) NOT NULL`` |
| ``requested_by_customer_id`` | ``bigint unsigned NOT NULL`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``completed_at`` | ``datetime(6) DEFAULT NULL`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |

- ``PRIMARY KEY (`refund_id`)``.
- ``UNIQUE KEY `uq_refunds_public_id` (`public_id`)``.
- ``UNIQUE KEY `uq_refunds_payment_id` (`payment_id`)``.
- ``UNIQUE KEY `uq_refunds_refund_idempotency_key` (`refund_idempotency_key`)``.
- ``FOREIGN KEY (`payment_id`) REFERENCES `payments` (`payment_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`requested_by_customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE RESTRICT``.
- Có 4 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `return_items`

| Cột | Định nghĩa MySQL |
|---|---|
| ``return_item_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``public_id`` | ``binary(16) NOT NULL`` |
| ``return_id`` | ``bigint unsigned NOT NULL`` |
| ``order_item_id`` | ``bigint unsigned NOT NULL`` |
| ``variant_id`` | ``bigint unsigned NOT NULL`` |
| ``quantity`` | ``int unsigned NOT NULL DEFAULT '1'`` |
| ``exchange_variant_id`` | ``bigint unsigned DEFAULT NULL`` |
| ``refund_amount_vnd`` | ``bigint unsigned NOT NULL DEFAULT '0'`` |
| ``inspection_status`` | ``varchar(16) NOT NULL DEFAULT 'pending'`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |

- ``PRIMARY KEY (`return_item_id`)``.
- ``UNIQUE KEY `uq_return_items_public_id` (`public_id`)``.
- ``FOREIGN KEY (`exchange_variant_id`) REFERENCES `product_variants` (`variant_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`order_item_id`) REFERENCES `order_items` (`order_item_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`return_id`) REFERENCES `return_requests` (`return_id`) ON DELETE CASCADE``.
- ``FOREIGN KEY (`variant_id`) REFERENCES `product_variants` (`variant_id`) ON DELETE RESTRICT``.
- Có 1 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `return_requests`

| Cột | Định nghĩa MySQL |
|---|---|
| ``return_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``public_id`` | ``binary(16) NOT NULL`` |
| ``return_code`` | ``varchar(64) NOT NULL`` |
| ``order_id`` | ``bigint unsigned NOT NULL`` |
| ``customer_id`` | ``bigint unsigned NOT NULL`` |
| ``action_type`` | ``varchar(16) NOT NULL`` |
| ``status`` | ``varchar(32) NOT NULL DEFAULT 'pending_review'`` |
| ``customer_reason`` | ``text NOT NULL`` |
| ``image_urls`` | ``json DEFAULT NULL`` |
| ``admin_note`` | ``text`` |
| ``reviewed_at`` | ``datetime(6) DEFAULT NULL`` |
| ``resolved_at`` | ``datetime(6) DEFAULT NULL`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |

- ``PRIMARY KEY (`return_id`)``.
- ``UNIQUE KEY `uq_return_requests_public_id` (`public_id`)``.
- ``UNIQUE KEY `uq_return_requests_code` (`return_code`)``.
- ``FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE RESTRICT``.
- Có 2 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `shipment_attempts`

| Cột | Định nghĩa MySQL |
|---|---|
| ``attempt_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``public_id`` | ``binary(16) NOT NULL`` |
| ``shipment_id`` | ``bigint unsigned NOT NULL`` |
| ``attempt_number`` | ``int unsigned NOT NULL`` |
| ``delivery_staff_id`` | ``bigint unsigned DEFAULT NULL`` |
| ``status`` | ``varchar(32) NOT NULL`` |
| ``failure_reason`` | ``varchar(255) DEFAULT NULL`` |
| ``is_buyer_fault`` | ``tinyint(1) NOT NULL DEFAULT '1'`` |
| ``idempotency_key`` | ``varchar(64) NOT NULL`` |
| ``attempted_at`` | ``datetime(6) NOT NULL`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |

- ``PRIMARY KEY (`attempt_id`)``.
- ``UNIQUE KEY `uq_shipment_attempts_public_id` (`public_id`)``.
- ``UNIQUE KEY `uq_shipment_attempts_idempotency_key` (`idempotency_key`)``.
- ``UNIQUE KEY `uq_shipment_attempts_shipment_attempt_number` (`shipment_id`,`attempt_number`)``.
- ``FOREIGN KEY (`delivery_staff_id`) REFERENCES `delivery_staff` (`staff_id`) ON DELETE SET NULL``.
- ``FOREIGN KEY (`shipment_id`) REFERENCES `shipments` (`shipment_id`) ON DELETE RESTRICT``.
- Có 2 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `shipments`

| Cột | Định nghĩa MySQL |
|---|---|
| ``shipment_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``public_id`` | ``binary(16) NOT NULL`` |
| ``shipment_code`` | ``varchar(64) NOT NULL`` |
| ``order_id`` | ``bigint unsigned NOT NULL`` |
| ``delivery_staff_id`` | ``bigint unsigned DEFAULT NULL`` |
| ``status`` | ``varchar(32) NOT NULL DEFAULT 'assigned'`` |
| ``attempt_count`` | ``int unsigned NOT NULL DEFAULT '1'`` |
| ``cod_amount_vnd`` | ``bigint unsigned NOT NULL DEFAULT '0'`` |
| ``cod_collected_vnd`` | ``bigint unsigned NOT NULL DEFAULT '0'`` |
| ``dispatched_at`` | ``datetime(6) DEFAULT NULL`` |
| ``delivered_at`` | ``datetime(6) DEFAULT NULL`` |
| ``failed_at`` | ``datetime(6) DEFAULT NULL`` |
| ``failure_reason`` | ``varchar(255) DEFAULT NULL`` |
| ``notes`` | ``text`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |

- ``PRIMARY KEY (`shipment_id`)``.
- ``UNIQUE KEY `uq_shipments_public_id` (`public_id`)``.
- ``UNIQUE KEY `uq_shipments_code` (`shipment_code`)``.
- ``FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`delivery_staff_id`) REFERENCES `delivery_staff` (`staff_id`) ON DELETE SET NULL``.
- Có 3 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `store_inventory`

| Cột | Định nghĩa MySQL |
|---|---|
| ``store_id`` | ``bigint unsigned NOT NULL`` |
| ``variant_id`` | ``bigint unsigned NOT NULL`` |
| ``on_hand`` | ``bigint unsigned NOT NULL`` |
| ``opening_on_hand`` | ``bigint unsigned NOT NULL`` |
| ``version`` | ``bigint unsigned NOT NULL DEFAULT '0'`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |
| ``store_inventory_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |

- ``PRIMARY KEY (`store_id`,`variant_id`)``.
- ``UNIQUE KEY `uq_store_inventory_store_id_variant_id` (`store_id`,`variant_id`)``.
- ``UNIQUE KEY `uq_store_inventory_id` (`store_inventory_id`)``.
- ``FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`variant_id`) REFERENCES `product_variants` (`variant_id`) ON DELETE RESTRICT``.
- Có 3 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

### `stores`

| Cột | Định nghĩa MySQL |
|---|---|
| ``store_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``city_id`` | ``bigint unsigned NOT NULL`` |
| ``code`` | ``varchar(32) NOT NULL`` |
| ``name`` | ``varchar(120) NOT NULL`` |
| ``address`` | ``varchar(500) NOT NULL`` |
| ``phone`` | ``varchar(32) NOT NULL`` |
| ``is_active`` | ``tinyint(1) NOT NULL DEFAULT '1'`` |
| ``created_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |

- ``PRIMARY KEY (`store_id`)``.
- ``UNIQUE KEY `uq_stores_code` (`code`)``.
- ``FOREIGN KEY (`city_id`) REFERENCES `cities` (`city_id`) ON DELETE RESTRICT``.

### `wishlist_items`

| Cột | Định nghĩa MySQL |
|---|---|
| ``wishlist_item_id`` | ``bigint unsigned NOT NULL AUTO_INCREMENT`` |
| ``customer_id`` | ``bigint unsigned NOT NULL`` |
| ``product_id`` | ``bigint unsigned NOT NULL`` |
| ``is_present`` | ``tinyint(1) NOT NULL DEFAULT '1'`` |
| ``first_added_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``last_added_at`` | ``datetime(6) NOT NULL DEFAULT (now(6))`` |
| ``removed_at`` | ``datetime(6) DEFAULT NULL`` |
| ``updated_at`` | ``datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`` |

- ``PRIMARY KEY (`wishlist_item_id`)``.
- ``UNIQUE KEY `uq_wishlist_items_customer_id_product_id` (`customer_id`,`product_id`)``.
- ``FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE RESTRICT``.
- ``FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE RESTRICT``.
- Có 3 CHECK constraint; biểu thức đầy đủ nằm trong DDL.

## 5. Giao dịch và vòng đời dữ liệu

| Luồng | Thay đổi chính trong service |
|---|---|
| Checkout online | Khóa customer/cart/catalog/coupon/tồn; tạo order/items/payment/history/redemption; trừ kho tổng, ledger outbound_order, đóng cart |
| POS | Kiểm tra cửa hàng/catalog/tồn; tạo completed order và succeeded payment, cost snapshot, trừ tồn cửa hàng, ledger outbound_pos |
| Hủy đơn | Chỉ từ paid; hoàn tồn, giải phóng redemption/used_count, tạo refund, history cancelled |
| Dispatch/deliver/complete | Shipment và attempts theo luồng; paid/confirmed → shipping → delivered → completed; COD payment đổi sang succeeded khi complete |
| Giao thất bại | Ghi từng attempt; lần thứ ba failed_delivery và hoàn kho return_boom; risk counter theo phân loại lỗi ở lần kết thúc |
| Trả hàng | Request/items; duyệt/nhận/kiểm định, chỉ passed restock/refund; refund/payment được cộng dồn khi trả lẻ |
| Nhập kho | Receipt/items, cộng tồn tổng, ledger inbound và cập nhật giá vốn bình quân |
| Cấp hàng chi nhánh | Cập nhật tồn tổng/cửa hàng và ledger theo admin service |

Hai route PATCH branch-inventory và POST inventory/refill hiện chỉ flush, không commit; get_db cũng chỉ đóng session. Bảng trên mô tả logic ghi trong code, không xác nhận hai thao tác này đã lưu. PATCH điều chỉnh tồn chưa có ledger riêng. Các luồng dùng Unit of Work hoặc commit rõ ràng phải được phân biệt với các route này.

Runtime tạo VietQR/payment thành công bằng mô phỏng nội bộ. `payments` và `refunds` là hai loại bản ghi; hoàn tiền không có nghĩa payment gốc đổi thành một trạng thái refund không tồn tại trong CHECK. Một payment có tối đa một refund theo UNIQUE, nhưng số tiền refund có thể được cập nhật/cộng dồn cho nhiều lần trả lẻ.

Giá bán/giá vốn order item giữ ngữ cảnh mua. Các trạng thái schema cho phép không đồng nghĩa đều có API chuyển tới. Cancel hiện chỉ paid; dispatch từ paid hoặc confirmed; review chỉ completed. Trả hàng nhận delivered/completed và kiểm tra 7 ngày từ completed_at hoặc updated_at; order chỉ returned khi đã trả đủ lượng đạt kiểm định.

Chi tiết điều kiện và quyền: [Business Requirements](../project/BUSINESS_REQUIREMENTS.md), [API README](../../services/ecommerce-api/README.md), [orders service](../../services/ecommerce-api/app/modules/orders/service.py), [returns service](../../services/ecommerce-api/app/modules/returns/service.py).

## 6. Biên giới phân tích

Bronze batch và Bronze CDC có thể chứa dữ liệu cá nhân thô. Silver pseudonymize theo cấu hình, không biến toàn bộ nguồn thành dữ liệu vô danh ngay từ MySQL. Không xuất customer_credentials vào nguồn phân tích.

Source–Silver reconciliation và Gold quality checks là tác vụ pipeline, không phải constraint MySQL. Cần phân biệt số dòng Bronze history, Silver hiện tại, fact order, fact item và sự kiện CDC; xem [Lakehouse Design](../project/LAKEHOUSE_DESIGN_PLAN.md) và [Metrics Catalog](METRICS_CATALOG.md).
