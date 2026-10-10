# D&K E-Commerce Lakehouse – Bộ Trình Diễn Tín Hiệu Biến Động CDC Thời Gian Thực
> **Real-Time CDC Business Signals Simulation & Interactive MIS Dashboard Demonstration**  
> Tài liệu kỹ thuật & kịch bản thực hành phục vụ bảo vệ Đồ án Tốt nghiệp Kỹ sư / Cử nhân Hệ thống Thông tin.

---

## 1. Tổng quan & Đặt vấn đề

Trong kiến trúc **Modern Data Lakehouse**, hệ thống xử lý phân tích theo lô (Batch Pipeline như Apache Spark, Trino, Apache Polaris) định kỳ tải và chuyển đổi dữ liệu từ tầng Bronze $\rightarrow$ Silver $\rightarrow$ Gold theo các chu kỳ (15 phút, 1 giờ hoặc hàng ngày).

Tuy nhiên, trong hoạt động thương mại điện tử đa kênh thực tế (Omnichannel Retailing), các nhà quản lý nghiệp vụ không thể đợi chu kỳ batch kết thúc để đưa ra quyết định:
- **Trưởng phòng Marketing** không thể để voucher Flash Sale bị bot cào hết sạch ngân sách rồi mới phát hiện.
- **Quản lý Kho vận** không thể để khách tiếp tục thanh toán những sản phẩm đã hết sạch trong kho (Bán vượt tồn / Overselling).
- **Trưởng phòng Vận hành** không thể để tỷ lệ bom hàng COD tại một quận bùng phát mất kiểm soát suốt cả ngày.
- **Cửa hàng trưởng (Store Manager)** cần biết nhịp độ doanh số tại quầy POS từng giờ để kịp thời tư vấn và đẩy bán phụ kiện.
- **Giám đốc Điều hành (CEO)** cần giám sát tức thì lượng tiền mặt COD đang nằm trên các xe tải giao hàng để chủ động dòng vốn lưu động.

**Bộ công cụ CDC Demo** này cung cấp các kịch bản phát sinh giao dịch OLTP thực tế trên cơ sở dữ liệu MySQL, kích hoạt các dòng log nhị phân (**MySQL Binlog / CDC Events**), từ đó hệ thống cập nhật tức thì lên **Dashboard Quản trị MIS** của 6 vai trò quản lý.

---

## 2. Kiến trúc luồng dữ liệu (Data Architecture)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TẦNG TÁC NGHIỆP OLTP                            │
│  [Script Mô Phỏng Giao Dịch] ➔ MySQL Database (orders, inventory, ...)  │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ MySQL Binary Log (Row-based CDC)
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       CDC SIGNALS INGESTION ENGINE                     │
│  - Binlog Stream Monitor (Debezium / Kafka CDC)                        │
│  - Intra-day Real-Time Aggregator & State Store                        │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ Real-Time Signal Enrichment
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 BACKEND SERVICE: ecommerce-api (FastAPI)               │
│  Endpoint: GET /api/v1/admin/analytics/role-metrics?target_role={role} │
│  - Phối hợp: Trino DWH (Lịch sử Gold) + OLTP CDC Signals (Thời gian thực) │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ Auto-refresh / Real-time Poll
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│               FRONTEND STOREFRONT: Next.js MIS Dashboard               │
│  URL: http://localhost:3000/admin/analytics                            │
│  - Huy hiệu Cảnh báo Đỏ / Vàng                                         │
│  - Biểu đồ nhịp độ tăng trưởng, bản đồ điểm nóng bom hàng, radar tồn kho│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Danh mục 6 Kịch bản Demo chi tiết

| STT | Kịch bản | Vai trò Quản trị | Bảng dữ liệu tác động | Tín hiệu CDC kích hoạt | Tác động trực quan trên Dashboard |
|:---:|:---|:---|:---|:---|:---|
| **1** | **Flash Sale & Review Spike** | Marketing Manager | `coupons`<br>`coupon_redemptions`<br>`product_reviews` | - `coupons` UPDATE `used_count` $\rightarrow$ 96%<br>- `product_reviews` INSERT đánh giá 1 sao | 🚨 **Bật cảnh báo đỏ**: Ngân sách Voucher cạn >95%.<br>🚨 **Bùng phát Review xấu**: Sản phẩm bị dính review lỗi đường may, gợi ý tạm dừng Ads. |
| **2** | **Tốc độ Rút kho & Cháy hàng** | Inventory Manager | `inventory` | - `inventory` UPDATE `on_hand` $\rightarrow$ 8 cái<br>- `inventory` UPDATE `on_hand` $\rightarrow$ 0 cái | 🚨 **Vận tốc rút hàng cực hạn**: Dự kiến cháy hàng trong 2 phút (Alert: Critical).<br>🛡 **Overselling Prevention**: Kích hoạt khóa nút giỏ hàng, gắn nhãn Sold Out. |
| **3** | **Điểm nóng Boom COD & Ùn tắc Đóng gói** | Operations Manager | `shipments`<br>`orders` | - `shipments` UPDATE `status='failed'` tại Bình Tân<br>- `orders` INSERT 25 đơn chờ xử lý >2h | 🚨 **Điểm nóng Boom hàng**: Quận Bình Tân tỷ lệ thất bại nhảy vọt lên 100%.<br>🚨 **Ùn tắc khâu đóng gói**: Hàng đợi >20 đơn tồn đọng quá 2 giờ (Chờ TB 2.5h). |
| **4** | **Cháy sào quầy POS & Giờ cao điểm Bán lẻ** | Store Manager | `store_inventory`<br>`orders` (channel POS) | - `store_inventory` UPDATE `on_hand` $\rightarrow$ 0 cái<br>- `orders` INSERT 6 đơn POS (+7.5tr đ) | 🛎 **Hết hàng tại sào**: POS báo hết áo tại sào, gợi ý nhân viên tạo đơn ship kho tổng.<br>📈 **Tiến độ Run-Rate**: Đạt 59.1% chỉ tiêu ngày, nhịp độ chuyển sang **On Track**. |
| **5** | **Sản phẩm Viral & Lệch pha Kênh** | Sales Manager | `orders`<br>`order_items` | - `orders` INSERT 250 sản phẩm Online | 🔥 **Huy hiệu Viral Item**: Sản phẩm tăng tốc x4.2 lần, chiếm Top 1 bán chạy nhất.<br>⚠️ **Lệch pha kênh**: Kênh Online tăng trưởng 99.4% áp đảo chuỗi cửa hàng. |
| **6** | **Dòng tiền COD & Xói mòn Biên Lợi Nhuận** | Ban Giám Đốc (CEO) | `shipments`<br>`orders` | - `shipments` INSERT 5 kiện COD giá trị lớn (+350tr đ) | 💰 **Dòng tiền trôi nổi (Cash in Transit)**: Tăng vọt lên 690+ triệu đồng.<br>📉 **Xói mòn Gross Margin**: Biên lợi nhuận gộp hạ từ 77.3% về 71.6% do áp mã sale. |

---

## 4. Hướng dẫn Chạy Trình Diễn (Quick Start)

Mọi kịch bản đều có thể kích hoạt trực tiếp từ máy tính của bạn qua script chạy duy nhất: `demo/run_demo.sh`.

### 4.1. Điều kiện tiên quyết
Hệ thống Docker core đang hoạt động:
```bash
docker compose --profile core up -d
```
Đảm bảo container `tlcn-ecommerce-api-1` và `tlcn-storefront-1` đang chạy.

### 4.2. Chế độ Menu Tương tác (Interactive CLI)
Mở terminal và thực thi:
```bash
./demo/run_demo.sh
```
Màn hình điều khiển sẽ hiển thị:
```text
════════════════════════════════════════════════════════════════════════════
  D&K E-COMMERCE LAKEHOUSE – TRÌNH MÔ PHỎNG TÍN HIỆU BIẾN ĐỘNG CDC
════════════════════════════════════════════════════════════════════════════
  [1] Marketing: Cháy ngân sách Flash Sale (95%) & Bùng phát 1-Star Review Spam
  [2] Inventory: Tốc độ rút kho nguy cấp (<10p) & Cháy hàng kích hoạt Sold Out
  [3] Operations: Điểm nóng Boom COD Bình Tân (100%) & Ùn tắc đóng gói >20 đơn
  [4] Store POS: Cháy hàng tại quầy POS & Giờ cao điểm bán lẻ kéo Run-Rate đạt chỉ tiêu
  [5] Sales: Mẫu sản phẩm Viral tăng tốc x4.8 lần & Cảnh báo lệch pha kênh Online
  [6] Executive: Tiền mặt COD shipper trôi nổi (+350tr) & Xói mòn biên lợi nhuận gộp
  ──────────────────────────────────────────────────────────────────────────
  [A] Chạy TẤT CẢ các kịch bản theo thứ tự
  [R] RESET TOÀN BỘ dữ liệu về trạng thái sạch ban đầu
  [Q] Thoát trình mô phỏng
════════════════════════════════════════════════════════════════════════════
👉 Nhập lựa chọn của bạn [1-6, A, R, Q]: 
```

### 4.3. Chạy Nhanh theo Tham số (Non-interactive CLI)
Dành cho trình diễn tự động hoặc viết script tự động hóa:
```bash
# Chạy từng kịch bản cụ thể:
./demo/run_demo.sh 1    # Kịch bản Marketing
./demo/run_demo.sh 2    # Kịch bản Kho vận (Inventory)
./demo/run_demo.sh 3    # Kịch bản Vận hành (Operations)
./demo/run_demo.sh 4    # Kịch bản Cửa hàng POS (Store Manager)
./demo/run_demo.sh 5    # Kịch bản Bán hàng (Sales Manager)
./demo/run_demo.sh 6    # Kịch bản Ban Giám Đốc (Executive / CEO)

# Chạy toàn bộ 6 kịch bản liên tiếp:
./demo/run_demo.sh all

# Hoàn nguyên / Reset dữ liệu sạch:
./demo/run_demo.sh reset
```

---

## 5. Quy trình Kiểm thử & Trực quan hóa trên Trình duyệt

Để trình diễn mượt mà nhất trong buổi báo cáo:

1. **Bước 1**: Mở trình duyệt tại địa chỉ Dashboard:  
   👉 [http://localhost:3000/admin/analytics](http://localhost:3000/admin/analytics)  
   Đăng nhập bằng tài khoản Quản trị: `admin@web.local` / Mật khẩu: `Admin@12345`.
2. **Bước 2**: Trên giao diện Web, chọn Tab vai trò tương ứng (ví dụ: *Marketing* hoặc *Vận hành* hoặc *Kho vận*). Quan sát các chỉ số lúc bình thường.
3. **Bước 3**: Tại cửa sổ Terminal bên cạnh, chạy kịch bản:
   ```bash
   ./demo/run_demo.sh 1
   ```
4. **Bước 4**: Bấm nút **"Làm mới dữ liệu"** (hoặc để trang web tự động tải lại).  
   👉 **Hiện tượng**: Các thẻ cảnh báo đỏ, chỉ số tốc độ rút kho, tỷ lệ bom hàng hoặc huy hiệu Viral ngay lập tức xuất hiện.
5. **Bước 5**: Kết thúc buổi demo, chạy lệnh khôi phục để đưa toàn bộ hệ thống về trạng thái sạch ban đầu:
   ```bash
   ./demo/run_demo.sh reset
   ```

---

## 6. Gợi ý Thuyết trình Bảo vệ Đồ án (Defense Talking Points)

Dưới đây là các luận điểm đắt giá để giải thích cho Hội đồng Giám khảo:

### 1. Tại sao cần kết hợp CDC Thời gian thực khi đã có Data Lakehouse?
> *"Data Lakehouse xử lý qua Spark/Trino rất mạnh mẽ trong việc phân tích lượng dữ liệu khổng lồ (hàng triệu đơn hàng, tính xu hướng tháng, quý, phân khúc RFM). Tuy nhiên, kiến trúc Lakehouse thuần túy có độ trễ (latency) từ 15 phút đến vài giờ. Nếu doanh nghiệp đang trong chiến dịch Flash Sale hoặc ngày đôi 11.11, việc đợi 1 giờ để biết kho đã cháy hàng hay voucher đã vỡ ngân sách là quá muộn. Do đó, đồ án áp dụng kiến trúc Lambda/Kappa kết hợp: Tầng Lakehouse chịu trách nhiệm phân tích lịch sử sâu, còn CDC Binlog Stream xử lý các tín hiệu biến động nội nhật (Intra-day Operational Signals), giúp cấp quản trị ra quyết định theo từng phút."*

### 2. Cơ chế CDC có gây quá tải cơ sở dữ liệu MySQL không?
> *"Không. Thay vì liên tục truy vấn SELECT COUNT(*) nặng nề trực tiếp lên database nghiệp vụ làm khóa bảng (Table Lock), cơ chế CDC chỉ đọc luồng Binary Log nhị phân phát sinh tự nhiên từ các giao dịch Commit của MySQL (Row-based Binlog). Thao tác này hoàn toàn bất đồng bộ (Asynchronous) và không tạo bất kỳ tải dư thừa nào lên hệ thống bán hàng cốt lõi."*

### 3. Dữ liệu thử nghiệm có làm sai lệch dữ liệu báo cáo DWH không?
> *"Các đơn hàng giả lập trong bộ script demo đều được gắn tiền tố định danh chuẩn `ORD-CDC-...` và đánh dấu cờ dữ liệu. Khi chạy lệnh `reset`, toàn bộ các bản ghi giả lập này được thu hồi triệt để, đảm bảo tính toàn vẹn và sạch sẽ 100% cho các tầng dữ liệu Bronze/Silver/Gold của Lakehouse."*

---

*© 2026 D&K E-Commerce Lakehouse Platform. All rights reserved.*
