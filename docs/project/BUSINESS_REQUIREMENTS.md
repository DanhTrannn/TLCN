# C — Yêu cầu nghiệp vụ của hệ thống D&K

D&K là ứng dụng bán lẻ thời trang kết hợp website và POS, cung cấp dữ liệu cho đồ án Data Engineering. Tài liệu mô tả hành vi đang được xử lý trong code; không coi thao tác mô phỏng là giao dịch ngân hàng hoặc giao nhận thực tế.

## 1. Đối tượng và phạm vi

Người mua có tài khoản để quản lý giỏ, đặt hàng và theo dõi đơn. Nhân viên dùng các role quản trị theo phân hệ và cửa hàng được gán. `delivery_staff` lưu nhân viên giao vận nội bộ, chưa là tài khoản có giao diện riêng. Chi tiết phân quyền xem [phân tích hệ thống A](../design-analysis/OOSAD_ANALYSIS.md).

Ứng dụng quản lý catalog, hai loại tồn kho, đơn online/POS, thanh toán mô phỏng, coupon, review, nhập kho, giao vận và trả hàng/hoàn tiền. Danh mục, city/store được seed hoặc nạp từ nguồn dữ liệu; chưa có bộ API CRUD đầy đủ cho tất cả bảng tham chiếu.

## 2. Mua hàng online

### Tài khoản và khám phá sản phẩm

Khách đăng ký bằng email, mật khẩu và tên hiển thị; đăng nhập để xem thông tin tài khoản và lịch sử đơn. Chưa có API tự sửa hồ sơ khách trong module auth.

Catalog hỗ trợ tìm kiếm, lọc danh mục/kích cỡ/màu/giá/tồn và xem biến thể. Tra cứu theo city/store cho biết tồn chi nhánh. Đây là thông tin tham khảo mua trực tiếp; checkout online lấy từ kho trung tâm, không tự chuyển sang lấy hàng ở cửa hàng.

Wishlist lưu sản phẩm theo khách. Giỏ lưu variant, số lượng và trạng thái hiện diện; thêm vào giỏ không giữ hoặc trừ tồn.

### Báo giá, coupon và đặt hàng

API báo giá tính subtotal, discount, shipping và total. Mỗi đơn áp dụng tối đa một coupon, kiểm tra hiệu lực, mức tối thiểu và giới hạn lượt dùng tổng/theo khách. Không có trường mức giảm tối đa riêng cho coupon phần trăm trong schema hiện tại.

Checkout yêu cầu đăng nhập, CSRF và `Idempotency-Key`. Trong transaction, hệ thống kiểm tra lại customer/cart/catalog/giá/coupon/tồn, khóa dữ liệu cần thiết, tạo order/items/payment/history/redemption, trừ kho tổng và ghi ledger `outbound_order`. Tên/SKU/giá bán/giá vốn được lưu vào order item để giữ ngữ cảnh lúc mua.

Địa chỉ giao nhận gồm người nhận, điện thoại, tỉnh/thành, phường/xã và phần địa chỉ; bộ chọn địa chỉ UI dùng dữ liệu trong [vietnam-addresses.ts](../../apps/storefront/src/lib/vietnam-addresses.ts). Không suy ra có tích hợp kiểm chứng địa chỉ với đơn vị bên ngoài.

### Thanh toán và trạng thái ban đầu

| Phương thức | Order sau checkout | Payment | Cơ chế hiện tại |
|---|---|---|---|
| `vietqr` | `paid` | `succeeded` | Mô phỏng thành công trong service; chưa có callback xác nhận ngân hàng |
| `cod` | `confirmed` | `pending` | Đánh dấu thành công khi khách hoàn tất đơn sau giao |

Customer bị chặn COD vẫn có thể dùng VietQR. Idempotency checkout tránh tạo thêm đơn/trừ kho khi yêu cầu cùng khóa được trả lại; tài khoản vẫn được kiểm tra trước khi trả kết quả cũ.

## 3. Xử lý đơn và giao vận

| Thao tác | Điều kiện và kết quả |
|---|---|
| Xác nhận | `paid → confirmed` |
| Xuất giao | Từ `paid` hoặc `confirmed` → `shipping`; tạo shipment và gán delivery staff |
| Giao thành công | `shipping → delivered`; ghi thời gian và dữ liệu COD ở shipment |
| Khách xác nhận đã nhận | `delivered → completed`; COD pending chuyển thành succeeded |
| Hủy sớm | Chỉ `paid → cancelled`; hoàn tồn, giải phóng coupon và ghi refund thành công |
| Giao thất bại | Ghi từng lần; trước lần thứ ba vẫn shipping; lần thứ ba → failed_delivery và hoàn tồn |

Không mô tả `confirmed` là trạng thái được hủy trong luồng hiện tại. Admin xác nhận/giao hàng; khách thực hiện hoàn tất đơn online. POS đi thẳng completed và không có hành trình shipment.

### Rủi ro COD và giao thất bại

Mỗi lần thất bại lưu lý do và phân loại `is_buyer_fault` trong `shipment_attempts`. Service xác định nguyên nhân ngoài lỗi khách bằng danh sách lý do trong code. Tới lần thứ ba, service cập nhật shipment failed, đơn failed_delivery, cộng tồn và ledger `return_boom` ngay trong xử lý; chưa có bước xác nhận hàng hoàn vật lý riêng trước khi cộng kho.

Khi nguyên nhân ở lần kết thúc được phân loại lỗi khách, `boom_count` tăng; đạt ba thì bật `is_cod_blocked`. Logic hiện nằm trong xử lý giao thất bại, không nên diễn giải là mô hình ML chấm điểm rủi ro. Admin có thể mở lại COD với lý do/audit và đưa bộ đếm về mức thử thách theo service. Không có cơ chế khóa toàn bộ quyền mua hàng chỉ vì cờ COD.

## 4. Bán tại quầy

POS tra sản phẩm theo SKU hoặc tên, kiểm tra catalog/cửa hàng và tồn chi nhánh. Khách có thể là người đăng ký hoặc khách vãng lai (`customer_id` nullable). Phương thức thanh toán quầy gồm cash/card/vietqr; đây là ghi nhận trong ứng dụng, chưa tích hợp thiết bị thanh toán.

Transaction POS tạo đơn completed và payment succeeded, chụp giá vốn, trừ `store_inventory`, ghi `outbound_pos`; không dùng coupon hoặc phí ship online. Tiền mặt có kiểm tra số tiền nhận. Service tự sinh khóa idempotency theo đơn mới; retry cùng payload từ client chưa có cam kết chống tạo đơn trùng như checkout online.

UI có trang POS và dữ liệu hóa đơn. Chưa xác nhận có tích hợp máy quét mã vạch, máy in hóa đơn hoặc cổng thanh toán, nên không đưa các thiết bị đó vào danh sách tính năng đã triển khai.

## 5. Nhập và điều phối tồn kho

Kho tổng nằm ở `inventory`, tồn chi nhánh ở `store_inventory`. Checkout/POS/nhập/trả hàng có ledger trong `inventory_transactions`; không phải mọi chỉnh sửa tồn đều được tự động ghi sổ. Admin có route điều chỉnh/cấp hàng chi nhánh, nhưng hai route hiện chỉ flush mà chưa commit trong router hoặc dependency nên không được coi response 204 là xác nhận đã lưu. PATCH điều chỉnh cũng chưa ghi ledger; luồng cấp hàng có tạo cặp transfer_to_store/transfer_received trước flush. Xem [admin router](../../services/ecommerce-api/app/modules/admin/router.py).

Phiếu nhập gồm header và các dòng variant/số lượng/đơn giá. Khi nhận hàng, service cộng tồn kho tổng và tính giá vốn bình quân gia quyền di động:

$$C_{new} = rac{Q_{current} C_{current} + Q_{inbound} C_{inbound}}{Q_{current} + Q_{inbound}}$$

Giá lưu là số nguyên VND với quy tắc làm tròn của service; khi tồn hiện tại không dương dùng giá lô mới. Phiếu chi tiết giữ giá vốn trước/sau. Đơn cũ dùng `order_items.cost_price_vnd`, không dùng giá vốn mới để sửa lịch sử đã bán. Đây là quản lý nhập thành phẩm, chưa phải hệ thống lập kế hoạch sản xuất hoặc quản lý nhà cung cấp đầy đủ.

## 6. Trả hàng và hoàn tiền

Khách tạo yêu cầu cho đơn của mình có trạng thái delivered/completed; API hiện chỉ xử lý `action_type='refund'`. Các trường exchange trong schema dành cho mở rộng.

Cửa sổ hiện được kiểm tra là **7 ngày từ `order.completed_at`, hoặc `order.updated_at` nếu chưa completed**. Code chưa dùng riêng `shipment.delivered_at` làm mốc duy nhất, nên không viết chính sách hiện có là luôn bảy ngày tính từ giao hàng. Đây là giới hạn của triển khai cần giữ khi mô tả báo cáo.

| Giai đoạn | Trạng thái request / xử lý |
|---|---|
| Gửi yêu cầu | `pending_review`; kiểm tra lượng đã/đang trả và lưu lý do, image URLs |
| Khách hủy khi đang chờ | `cancelled` |
| Admin xem xét | `approved` hoặc `rejected` |
| Nhận hàng gửi về | `goods_received` |
| Kiểm định và giải quyết | `completed`; từng item có passed/failed |

Image URLs là tham chiếu ảnh; chưa có dịch vụ upload ảnh riêng trong luồng này. Chỉ item passed được cộng lại kho tổng bằng `return_customer` và tính hoàn tiền. Giá hoàn dựa trên đơn giá đã phân bổ giảm giá; không mặc định hoàn toàn bộ phí ship cho từng trả lẻ. Một refund/payment được cộng dồn qua các lần trả, giới hạn bởi số tiền thanh toán. Request có thể completed dù có item không đạt; trạng thái returned của **đơn** chỉ đặt khi đã trả đủ toàn bộ lượng mua đạt kiểm định.

## 7. Đánh giá và quản trị catalog/promotion

Khách chỉ đánh giá order item thuộc đơn completed, rating từ 1 đến 5, mỗi item một review. Review mới approved và hiển thị ngay; marketing/admin được hậu kiểm chuyển approved/rejected, lý do bắt buộc khi từ chối.

Sản phẩm và coupon có archive metadata để giữ tham chiếu lịch sử. Category có `is_active` trong schema và API đọc; chưa có category archive/CRUD như sản phẩm. Admin quản lý tài khoản; inventory/admin quản lý sản phẩm và nhập kho; marketing/admin quản lý coupon/review. API đơn/giao vận/trả hàng vẫn giới hạn admin.

## 8. Yêu cầu dữ liệu phân tích và giới hạn

28 bảng OLTP là nguồn; batch và CDC lấy 27 bảng, bỏ `customer_credentials`. Giá bán/giá vốn và audit giao dịch hỗ trợ đối soát; log không ghi body, cookie hoặc token. Dữ liệu PII của nguồn thô vẫn cần kiểm soát trước khi phục vụ phân tích.

Không dùng một công thức net revenue chung để thay thế mọi chỉ số: Gold order, sales mart và OLTP fallback hiện có quy tắc khác nhau. Trả lẻ và refund không tự đồng nghĩa toàn bộ doanh thu đơn bằng 0. Xem [Metrics Catalog](../architecture/METRICS_CATALOG.md) trước khi tính hoặc diễn giải kết quả.

ML dự báo/tái mua, thanh toán thực, đổi size/màu, target kinh doanh và các chỉ tiêu hiệu năng chưa được triển khai/đo không thuộc kết quả đã hoàn thành.

## Nguồn đối chiếu

- [DDL MySQL](../../database/schema.sql), [tham chiếu schema](../architecture/OLTP_SCHEMA.md).
- [Checkout](../../services/ecommerce-api/app/modules/checkout/service.py), [orders](../../services/ecommerce-api/app/modules/orders/service.py), [POS](../../services/ecommerce-api/app/modules/pos/service.py).
- [Returns](../../services/ecommerce-api/app/modules/returns/service.py), [inbound](../../services/ecommerce-api/app/modules/inbound/service.py), [reviews](../../services/ecommerce-api/app/modules/reviews/service.py).
- [Admin router](../../services/ecommerce-api/app/modules/admin/router.py), [admin service](../../services/ecommerce-api/app/modules/admin/service.py).
