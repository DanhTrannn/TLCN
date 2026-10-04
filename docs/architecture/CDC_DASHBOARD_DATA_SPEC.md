# ĐẶC TẢ CÁC TÍN HIỆU NGHIỆP VỤ BIẾN ĐỘNG (CDC) CHO HỆ THỐNG DASHBOARD
## (Change Data Capture Business Signals & Operational Use Cases by Role)

> **Tài liệu thuộc đồ án:** D&K E-Commerce Hybrid Lakehouse Platform  
> **Phiên bản:** 2.0.0 (Cập nhật chuyên sâu cho 6 vai trò nghiệp vụ kinh doanh)  
> **Trạng thái:** Chính thức (Approved Specification)

---

## 1. Tổng quan & Triết lý ứng dụng CDC trong Dashboard

Trong hệ thống bán lẻ và thương mại điện tử, **CDC (Change Data Capture)** không đơn thuần là một giải pháp kỹ thuật di chuyển dữ liệu, mà là công cụ trực tiếp phục vụ cho việc **ra quyết định tác nghiệp tức thì (Actionable Intelligence)**.

### Tại sao các Dashboard này bắt buộc phải sử dụng CDC?
* **Không thể query trực tiếp MySQL OLTP:** Các truy vấn phân tích, gom nhóm (`GROUP BY`, `SUM`) theo thời gian thực trên các bảng lớn như `orders`, `order_items`, `inventory` sẽ gây khóa bảng (lock contention), làm tăng đột biến CPU và làm sập hoặc chậm trễ tiến trình thanh toán của khách trên Web/POS.
* **Không thể chờ Batch ETL cuối ngày:** Nếu chỉ chạy Batch ban đêm, người quản lý chỉ biết được số liệu quá khứ khi mọi sự việc đã rồi (hết voucher, cháy hàng, giao trễ, sụt giảm lợi nhuận).
* **CDC mang lại giá trị:** Bắt trọn các sự kiện `INSERT` và `UPDATE` từ MySQL Binlog với độ trễ tính bằng giây/phút ($< 1-5$ phút) nạp vào Lakehouse (Iceberg), giúp Dashboard cập nhật nóng các chỉ số mà không gây ảnh hưởng đến hệ thống bán hàng.

```text
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐       ┌───────────────────┐
│ MySQL 8.4 OLTP  │ Binlog│  CDC Engine     │ Kafka │ Lakehouse       │ Trino │ BI Analytics Hub  │
│ (27 Tables)     ├──────>│ (Debezium/Flink)├──────>│ (Iceberg Bronze ├──────>│ (/admin/analytics)│
│                 │       │                 │       │  Silver -> Gold)│       │ (6 Business Roles)│
└─────────────────┘       └─────────────────┘       └─────────────────┘       └───────────────────┘
```

---

## 2. Chi tiết các Tín hiệu CDC và Tình huống Thực tế theo 6 Vai trò

---

### Vai trò 1: Marketing Manager (Tiếp thị & Tăng trưởng)
> **Mối quan tâm cốt lõi:** Quản trị ngân sách khuyến mãi theo thời gian thực, tốc độ chuyển đổi và phản ứng chất lượng từ khách hàng.

#### 1.1. Tốc độ đốt ngân sách Voucher trong Flash Sale (Voucher Burn Rate)
* **Tình huống thực tế:** Trong khung giờ vàng Mega Sale (12h00 – 13h00), bộ phận Marketing kích hoạt mã giảm giá `SALE50K` với ngân sách tối đa 1,000 lượt (tương đương 50 triệu đồng).
* **Thông tin CDC thu thập:**
  * Bắt sự kiện `INSERT INTO coupon_redemptions`.
  * Đo đếm tốc độ tiêu thụ theo từng phút: *Mã `SALE50K` đã tiêu thụ 850/1,000 lượt chỉ sau 15 phút (vận tốc ~56 lượt/phút)*.
* **Bảng & Trường dữ liệu nguồn:**
  * `coupon_redemptions`: `coupon_id`, `order_id`, `discount_amount_vnd`, `created_at`
  * `coupons`: `code`, `usage_limit`, `is_active`
* **Hành động can thiệp tức thì (Action):**
  * Marketing Manager phát hiện ngân sách sắp cạn kiệt sớm hơn 40 phút so với dự kiến.
  * *Quyết định:* Hoặc bấm nút hạ mức chiết khấu/đóng mã sớm để tránh vỡ quỹ ngân sách, hoặc kịp thời liên hệ Ban Giám đốc xin cấp bổ sung hạn mức ngay trong khung giờ vàng.

#### 1.2. Cảnh báo bùng phát Review tiêu cực (Negative Review Spikes)
* **Tình huống thực tế:** Một dòng sản phẩm thời trang mới vừa mở bán, nhưng có lỗi đường may hoặc chất vải sai lệch so với mô tả.
* **Thông tin CDC thu thập:**
  * Bắt sự kiện `INSERT INTO product_reviews` lọc các đánh giá `rating <= 2`.
  * Dashboard phát hiện có 6 review 1 sao xuất hiện liên tiếp trong vòng 45 phút cho cùng một mã sản phẩm.
* **Bảng & Trường dữ liệu nguồn:**
  * `product_reviews`: `product_id`, `rating`, `review_text`, `created_at`
* **Hành động can thiệp tức thì (Action):**
  * Tạm dừng ngay chiến dịch quảng cáo (Facebook/TikTok Ads) đang đổ tiền kéo traffic vào sản phẩm đó để tránh lãng phí chi phí marketing.
  * Báo cho bộ phận QA/Kho kiểm tra lại chất lượng lô hàng.

---

### Vai trò 2: Inventory Manager (Kho & Chuỗi cung ứng)
> **Mối quan tâm cốt lõi:** Tốc độ tiêu thụ hàng tồn, nguy cơ đứt hàng (Stockout) và phòng ngừa bán vượt tồn.

#### 2.1. Tốc độ rút hàng tồn kho (Depletion Velocity) & Cảnh báo cháy hàng
* **Tình huống thực tế:** Mẫu áo *"Áo Polo Basic Cotton Đen Size L"* có số lượng tồn kho đầu ngày là 120 chiếc tại Kho tổng. Trong sự kiện khuyến mãi, khách đặt liên tục cả Online lẫn tại quầy POS.
* **Thông tin CDC thu thập:**
  * Bắt các sự kiện `UPDATE inventory SET on_hand = on_hand - X` liên tục.
  * Thuật toán tính vận tốc bán: 8 sản phẩm/phút $\rightarrow$ Dashboard bật cảnh báo đỏ: **Dự kiến hết sạch tồn kho sau 15 phút nữa**.
* **Bảng & Trường dữ liệu nguồn:**
  * `inventory`: `variant_id`, `on_hand`, `safety_stock`, `updated_at`
  * `product_variants`: `sku`, `size`, `color`, `cost_price_vnd`
* **Hành động can thiệp tức thì (Action):**
  * Phát lệnh khẩn cấp cho xưởng may nội bộ (`Inbound`) kích hoạt ngay chuyền cắt may lô thành phẩm bổ sung.
  * Kịp thời ra lệnh điều chuyển nội bộ một phần hàng từ các cửa hàng vệ tinh vắng khách về kho trung tâm để bù đắp.

#### 2.2. Chặn đứng nguy cơ bán vượt tồn (Overselling Prevention)
* **Tình huống thực tế:** Khi số lượng tồn thực tế của một biến thể vừa chạm về 0 (`on_hand = 0`).
* **Thông tin CDC thu thập:**
  * Bắt ngay sự kiện `UPDATE inventory SET on_hand = 0`.
* **Hành động can thiệp tức thì (Action):**
  * Hệ thống đồng bộ tức thời trạng thái "Hết hàng" (Sold Out) lên Storefront, vô hiệu hóa nút "Thêm vào giỏ", loại bỏ rủi ro khách đã thanh toán tiền nhưng kho không còn hàng để giao.

---

### Vai trò 3: Operations & Logistics Manager (Vận hành & Giao hàng)
> **Mối quan tâm cốt lõi:** Ùn tắc đóng gói tại kho, điểm nóng giao hàng thất bại (Boom COD) và các vi phạm cam kết thời gian giao (SLA).

#### 3.1. Điểm nóng bùng phát Boom hàng COD theo khu vực (Regional Boom Rate Spike)
* **Tình huống thực tế:** Shipper đi giao các đơn thanh toán tiền mặt khi nhận hàng (COD). Tại một khu vực (ví dụ Quận Bình Tân), tỷ lệ đơn bị khách từ chối nhận hoặc không liên lạc được tăng vọt.
* **Thông tin CDC thu thập:**
  * Bắt sự kiện `UPDATE shipments SET status = 'failed', failure_reason = ...`
  * Dashboard thống kê theo cửa sổ trượt 2 giờ: *Tỷ lệ giao thất bại tại khu vực đạt tới 38% (bình thường < 5%)*.
* **Bảng & Trường dữ liệu nguồn:**
  * `shipments`: `shipment_id`, `order_id`, `status`, `delivery_attempts`, `failure_reason`, `updated_at`
  * `orders`: `shipping_address`, `channel`
* **Hành động can thiệp tức thì (Action):**
  * Trưởng vận hành ra lệnh tạm dừng xuất tiếp các chuyến xe giao hàng đến khu vực đó trong buổi chiều (do mưa ngập đường hoặc nghi vấn có nhóm khách tạo đơn ảo).
  * Chỉ đạo tổng đài CSKH gọi điện xác nhận lại 100% với người nhận trước khi tiếp tục cho shipper xuất kho.

#### 3.2. Ùn tắc khâu đóng gói xuất kho (Fulfillment Bottleneck)
* **Tình huống thực tế:** Số lượng đơn hàng khách đã thanh toán thành công (`orders.status = 'paid'`) tăng rất nhanh, nhưng tốc độ nhân viên kho in phiếu đóng gói và tạo đơn vận chuyển (`shipments`) bị chậm.
* **Thông tin CDC thu thập:**
  * Bắt chênh lệch giữa số lượng đơn `status = 'paid'` mới phát sinh và số bản ghi `shipments` mới tạo.
  * Dashboard cảnh báo: *Đang tồn đọng 250 đơn chưa được xử lý quá 2 giờ*.
* **Hành động can thiệp tức thì (Action):**
  * Điều phối tức thì 3 nhân viên từ khu vực kiểm kê sang bàn đóng gói để kịp giờ lấy hàng của các đối tác bưu cục (Cut-off time 17h00).

---

### Vai trò 4: Store Manager (Quản lý Cửa hàng POS)
> **Mối quan tâm cốt lõi:** Tình trạng sẵn có của hàng hóa tại quầy bán trực tiếp, tiến độ doanh số trong ngày và chăm sóc khách tại cửa hàng.

#### 4.1. Cháy hàng cục bộ tại quầy lúc đông khách (Intra-day Counter Stockout)
* **Tình huống thực tế:** Khách đến cửa hàng thử đồ đông vào buổi tối. Mẫu *"Quần Jean Regular Fit Size 32"* vừa được bán chiếc cuối cùng qua máy tính tiền POS.
* **Thông tin CDC thu thập:**
  * Bắt sự kiện `UPDATE store_inventory SET on_hand = 0 WHERE store_id = X AND variant_id = Y`.
* **Bảng & Trường dữ liệu nguồn:**
  * `store_inventory`: `store_id`, `variant_id`, `on_hand`, `updated_at`
  * `product_variants`: `sku`, `size`, `color`
* **Hành động can thiệp tức thì (Action):**
  * Màn hình POS/Tablet của nhân viên bán hàng hiển thị ngay nhãn "Hết hàng tại sào".
  * Nhân viên không mất thời gian vào kho tìm kiếm, đồng thời chủ động gợi ý khách: *"Mẫu này tại quầy vừa hết, em hỗ trợ anh/chị tạo đơn ship hỏa tốc từ kho tổng về nhà miễn phí"*.

#### 4.2. Nhịp độ doanh số theo giờ so với mục tiêu ngày (Hourly Run-Rate)
* **Tình huống thực tế:** Cửa hàng được giao chỉ tiêu 15,000,000 đ/ngày. Đến 16h00 chiều, tổng doanh thu các đơn POS mới đạt 4,200,000 đ (28%).
* **Thông tin CDC thu thập:**
  * Bắt các bản ghi `orders` hoàn tất tại quầy (`channel = 'pos'` và `store_id = X`).
* **Hành động can thiệp tức thì (Action):**
  * Quản lý cửa hàng họp nhanh 5 phút với nhân viên ca tối, triển khai ngay kịch bản up-sell phụ kiện (tất, ví, thắt lưng) ngay tại quầy thanh toán để kéo doanh số đạt chỉ tiêu.

---

### Vai trò 5: Sales Manager (Giám đốc Kinh doanh & Chiến lược)
> **Mối quan tâm cốt lõi:** Phát hiện sớm sản phẩm bán chạy đột biến (Viral Items) và điều phối cơ cấu hàng bán giữa các kênh.

#### 5.1. Phát hiện sản phẩm "ngựa ô" bán chạy bất ngờ (Unexpected Best-Seller Velocity)
* **Tình huống thực tế:** Một mẫu *"Áo Sơ Mi Oxford Màu Be"* vốn có sức mua bình thường, nhưng bỗng nhiên CDC ghi nhận lượng bán tăng vọt gấp 8 lần chỉ trong vòng 2 tiếng (do một KOL thời trang vừa mặc xuất hiện trên mạng xã hội).
* **Thông tin CDC thu thập:**
  * CDC gom nhóm `order_items.quantity` theo từng khung 30 phút.
  * Dashboard hiển thị sản phẩm này nhảy vọt từ vị trí số 15 lên Top 1 sản phẩm bán chạy nhất trong ngày.
* **Bảng & Trường dữ liệu nguồn:**
  * `order_items`: `variant_id`, `quantity`, `line_total_vnd`, `created_at`
  * `products`: `product_id`, `product_name`
* **Hành động can thiệp tức thì (Action):**
  * Giám đốc kinh doanh lập tức chỉ đạo đẩy sản phẩm này lên Banner chính trang chủ Storefront.
  * Tạo nhanh chương trình combo: Mua áo Sơ Mi tặng kèm voucher giảm giá quần tây để nhân đôi hiệu ứng doanh thu.

#### 5.2. Lệch pha doanh số giữa kênh Online và chuỗi Cửa hàng
* **Tình huống thực tế:** Doanh số kênh Online tăng trưởng 180% nhưng chuỗi cửa hàng vật lý giảm 40% do thời tiết mưa lớn toàn thành phố.
* **Hành động can thiệp tức thì (Action):**
  * Chuyển hướng tập trung nhân lực hỗ trợ tư vấn khách hàng Online (Chatbox, Direct Messages).
  * Tạm hoãn các chương trình khuyến mãi riêng biệt chỉ áp dụng tại cửa hàng sang tích hợp áp dụng cả trên Web.

---

### Vai trò 6: Executive / CEO (Ban Giám Đốc)
> **Mối quan tâm cốt lõi:** Bảo vệ biên lợi nhuận gộp trong ngày khuyến mãi và kiểm soát dòng tiền mặt thu hộ COD đang lưu thông.

#### 6.1. Xói mòn biên lợi nhuận gộp theo giờ (Intra-day Gross Margin Erosion)
* **Tình huống thực tế:** Trong ngày Black Friday, doanh số nhảy số liên tục đạt 800 triệu đồng rất ấn tượng. Tuy nhiên, do khách hàng áp dụng nhiều tầng khuyến mãi (giảm giá sản phẩm + voucher sàn + mã miễn phí vận chuyển) và các sản phẩm bán ra có giá vốn xưởng (`cost_price_vnd`) cao.
* **Thông tin CDC thu thập:**
  * CDC thu thập đồng thời `total_vnd` từ `orders` và giá vốn `cost_price_vnd` từ `order_items`.
  * Dashboard tính toán liên tục: **Tỷ suất lãi gộp (Gross Margin %) bị tụt dốc không phanh từ 52% đầu ngày xuống chỉ còn 9.5% vào lúc 14h00**!
* **Bảng & Trường dữ liệu nguồn:**
  * `orders`: `order_id`, `total_vnd`, `status`
  * `order_items`: `quantity`, `cost_price_vnd`, `unit_price_vnd`
* **Hành động can thiệp tức thì (Action):**
  * CEO nhận được tín hiệu báo động đỏ về xói mòn lợi nhuận ngay trong ngày.
  * Chỉ đạo Giám đốc Marketing và Kinh doanh hạ ngay mức chiết khấu của các đợt mã giảm giá buổi tối, loại bỏ bớt các mã có thể cộng dồn để đảm bảo công ty có lãi ròng, không bị "bán càng nhiều càng lỗ".

#### 6.2. Kiểm soát dòng tiền thu hộ COD đang trôi nổi (Cash-in-Transit Tracking)
* **Tình huống thực tế:** Kênh bán hàng trực tuyến có tỷ lệ thanh toán COD chiếm trên 65%.
* **Thông tin CDC thu thập:**
  * CDC đếm tổng giá trị tiền mặt của các đơn hàng có trạng thái `shipments.status = 'dispatched'` hoặc `'in_transit'`.
  * Dashboard hiển thị: *Hiện có 320 triệu đồng tiền hàng đang nằm trên các xe giao của đối tác vận chuyển*.
* **Hành động can thiệp tức thì (Action):**
  * Giúp Ban Giám đốc kiểm soát rủi ro thanh khoản tiền mặt, chủ động lên lịch đối soát công nợ với đơn vị bưu cục vào 17h00 hàng ngày.

---

## 3. Ma trận Tổng kết: Role – Tín hiệu CDC – Bảng Nguồn – Quyết định Can thiệp

| Vai trò (Role) | Tín hiệu biến động cần CDC | Bảng MySQL nguồn | Quyết định can thiệp tức thì | Hậu quả nếu không dùng CDC (Chỉ chạy Batch) |
|---|---|---|---|---|
| **1. Marketing** | Tốc độ đốt voucher Flash Sale | `coupon_redemptions`<br>`coupons` | Đóng mã tránh vỡ quỹ ngân sách, hoặc xin duyệt bơm thêm mã | Vỡ quỹ ngân sách hàng chục triệu đồng trước khi hết giờ sale |
| **1. Marketing** | Bùng phát review tiêu cực (1 sao) | `product_reviews` | Tạm dừng chạy quảng cáo cho mẫu sản phẩm lỗi | Tiếp tục "đốt tiền" quảng cáo cho sản phẩm đang bị chê bai |
| **2. Inventory** | Tốc độ rút tồn kho, sắp cháy hàng | `inventory`<br>`product_variants` | Phát lệnh may gấp cho xưởng, điều chuyển kho giữa các chi nhánh | Khách đặt nhiều nhưng không có hàng giao, khách hủy đơn |
| **2. Inventory** | Tồn kho chạm mức 0 | `inventory` | Tự động đổi trạng thái "Hết hàng" trên Web ngay lập tức | Bán vượt tồn (Overselling), khiếu nại bồi thường đơn |
| **3. Operations** | Tỷ lệ boom hàng COD tăng vọt theo quận | `shipments`<br>`orders` | Dừng xuất tiếp đơn vùng ngập/ảo, tổng đài gọi xác nhận lại | Shipper tốn chi phí đi lại vô ích, hàng bị kẹt dài ngày |
| **3. Operations** | Ùn tắc hàng trăm đơn chờ đóng gói | `orders`<br>`shipments` | Điều động nhân sự hỗ trợ đóng gói trước giờ xe gom hàng | Trễ cam kết giao hàng (SLA), khách hàng đánh giá xấu |
| **4. Store Manager** | Hết hàng tại sào quầy POS | `store_inventory` | Hướng dẫn khách đặt ship online giao tận nhà | Khách thử đồ xong bỏ đi mua chỗ khác vì quầy hết size |
| **4. Store Manager** | Doanh số chậm tiến độ so với chỉ tiêu | `orders` (pos) | Chỉ đạo nhân viên đẩy mạnh mời chào phụ kiện up-sell | Hết ngày mới biết không đạt chỉ tiêu thì không cứu vãn được |
| **5. Sales** | Mẫu sản phẩm bán chạy đột biến (Viral) | `order_items`<br>`products` | Đẩy lên Banner chính trang chủ, tạo combo bán kèm | Bỏ lỡ thời điểm vàng khi xu hướng quan tâm của khách đang nóng |
| **6. Executive (CEO)** | Xói mòn biên lợi nhuận gộp theo giờ | `orders`<br>`order_items` | Hãm bớt mã giảm giá sâu trước buổi tối tránh bị lỗ ròng | Doanh số trăm triệu nhưng kết sổ lỗ ròng vì voucher chồng mã |
| **6. Executive (CEO)** | Dòng tiền COD trôi nổi ngoài đường | `shipments`<br>`orders` | Giám sát rủi ro thanh khoản, yêu cầu đối soát bưu cục | Đọng vốn lớn, phát sinh rủi ro thất thoát tiền mặt COD |

---

## 4. Phân định ranh giới: CDC từ MySQL Database vs Clickstream từ Web Logs

Để bảo vệ đồ án một cách chuẩn mực trước Hội đồng phản biện, cần nhấn mạnh sự khác biệt giữa hai nguồn dữ liệu thời gian thực:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. CDC Stream từ MySQL (Transaction / State Changes):                       │
│    • Bắt các thay đổi DỮ LIỆU CÓ CẤU TRÚC đã ghi nhận vào Database.          │
│    • Phục vụ: Voucher đã áp, Tiền đã thanh toán, Tồn kho bị trừ,             │
│      Đơn hàng chuyển trạng thái, Shipper báo giao thất bại.                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. Clickstream Event Stream từ Web/App Logs (Kafka + Flink):                 │
│    • Bắt các HÀNH VI TƯƠNG TÁC CHƯA GHI VÀO DATABASE của người dùng.        │
│    • Phục vụ: Lượt xem trang (Pageviews), Lượt bấm xem sản phẩm (Views),    │
│      Lượt bấm thêm vào giỏ (Add to Cart), Lượt bắt đầu thanh toán (Checkout).│
└─────────────────────────────────────────────────────────────────────────────┘
```

> **Kết luận:**  
> Hệ thống Dashboard đạt được tính hiệu quả cao nhất nhờ mô hình **Hybrid**: Dữ liệu hành vi người dùng ngoài Web đi qua **Kafka + Flink**, kết hợp cùng các biến động giao dịch tác nghiệp trong Database đi qua **CDC Engine**, cùng hội tụ tại hồ dữ liệu **Apache Iceberg** để các cấp quản trị đưa ra quyết định kinh doanh chuẩn xác và kịp thời.
