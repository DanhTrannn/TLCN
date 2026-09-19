# TÀI LIỆU ĐẶC TẢ NGHIỆP VỤ BÀI TOÁN KINH DOANH
## Hệ thống Bán lẻ & Thương mại Điện tử Thời trang Đa kênh (D&K E-Commerce)

---

## LỜI NÓI ĐẦU & MỤC TIÊU TÀI LIỆU

Tài liệu này mô tả toàn diện bài toán nghiệp vụ kinh doanh của hệ thống bán lẻ thời trang **D&K**, kết hợp hài hòa giữa mô hình bán hàng trực tuyến trên website và chuỗi cửa hàng bán lẻ truyền thống. 

Mục tiêu chính của tài liệu là trình bày rõ ràng dòng chảy công việc, vai trò của từng bộ phận tham gia, các quy tắc vận hành kinh doanh và giá trị phân tích dữ liệu phục vụ quản trị doanh nghiệp, bằng văn phong mô tả tự nhiên, dễ hiểu, không phụ thuộc vào các thuật ngữ lập trình hay kỹ thuật chuyên sâu.

Tài liệu gồm 3 phần:
- **Phần I: Các nghiệp vụ vận hành hiện có** (Mô hình đang hoạt động trên hệ thống).
- **Phần II: Các nghiệp vụ bổ sung đã triển khai** (Giao vận nội bộ D&K, xử lý COD boom, đổi trả 7 ngày, sổ cái kho — đã được implement đầy đủ).
- **Phần III: Vòng đời đơn hàng và ma trận phối hợp giữa các bộ phận**.

---

## CÁC ĐỐI TƯỢNG THAM GIA VÀO HỆ THỐNG

1. **Khách hàng (Người mua sắm trực tuyến)**: Người tiêu dùng tìm kiếm, xem mẫu mã, kiểm tra kích cỡ, đặt mua hàng qua website hoặc tra cứu địa chỉ cửa hàng còn hàng để đến mua trực tiếp.
2. **Nhân viên thu ngân tại cửa hàng**: Người phụ trách tính tiền, in hóa đơn và bàn giao sản phẩm trực tiếp cho khách tại quầy bán lẻ của từng chi nhánh.
3. **Quản lý cửa hàng chi nhánh**: Người chịu trách nhiệm theo dõi doanh thu bán tại quầy, nắm bắt số lượng hàng tồn tại cửa hàng và quản lý nhân viên của chi nhánh mình.
4. **Bộ phận quản trị & vận hành kinh doanh (Quản trị viên)**: Người điều phối toàn bộ hoạt động của doanh nghiệp: quản lý danh mục mẫu mã, duyệt chương trình giảm giá, xử lý đơn hàng trực tuyến, điều chuyển hàng giữa các kho và giám sát báo cáo tài chính.
5. **Đội ngũ Shipper nội bộ D&K (Nhân viên Giao vận)**: Nhân viên giao hàng trực thuộc biên chế của doanh nghiệp, chịu trách nhiệm nhận kiện hàng từ kho trung tâm và giao trực tiếp đến tận tay khách hàng. D&K không sử dụng dịch vụ của các đơn vị vận chuyển bên thứ ba.
6. **Quản lý Kho trung tâm**: Người phụ trách vận hành kho tổng — đây là kho duy nhất cung cấp hàng cho cả hệ thống bán hàng online lẫn tái cung ứng cho các cửa hàng chi nhánh. Chịu trách nhiệm ghi nhận nhập kho (inbound), xuất kho (outbound), và theo dõi sổ cái tồn kho.

---

# PHẦN I: CÁC NGHIỆP VỤ HIỆN CÓ CỦA HỆ THỐNG

## 1. Nghiệp vụ Mua sắm Trực tuyến dành cho Khách hàng

### 1.1. Tạo tài khoản và Quản lý Hồ sơ cá nhân
- Khách hàng có thể đăng ký tài khoản thành viên bằng địa chỉ thư điện tử (email) và mật khẩu để lưu lại thông tin nhận hàng cho những lần mua sắm sau.
- Hệ thống duy trì trạng thái đăng nhập an toàn, cho phép khách hàng xem lại hồ sơ cá nhân và lịch sử tất cả các đơn hàng mình từng mua.

### 1.2. Khám phá Mẫu mã, Tìm kiếm và Lọc sản phẩm
- **Cấu trúc danh mục thời trang**: Sản phẩm được phân loại khoa học theo nhóm lớn (ví dụ: Trang phục nam, Trang phục nữ, Phụ kiện) và các nhóm con chi tiết (như Áo sơ mi, Đầm thiết kế, Quần tây).
- **Tìm kiếm thông minh**: Khách hàng có thể gõ từ khóa tên món đồ để tìm kiếm nhanh sản phẩm mong muốn.
- **Bộ lọc đa chiều**: Giúp người mua nhanh chóng tìm đúng món đồ phù hợp với vóc dáng và sở thích thông qua các tiêu chí:
  - Chọn theo kích cỡ (Size: S, M, L, XL...).
  - Chọn theo màu sắc (Trắng, Đen, Be, Xanh...).
  - Giới hạn khoảng giá tiền phù hợp với ngân sách cá nhân.
- **Xem chi tiết sản phẩm**: Mỗi sản phẩm hiển thị đầy đủ hình ảnh thực tế, chất liệu, bảng hướng dẫn chọn size, giá niêm yết tính bằng tiền Việt Nam Đồng (VNĐ) và danh sách các biến thể kích cỡ / màu sắc đang có sẵn.

### 1.3. Tra cứu Cửa hàng gần nhất còn hàng
- Khách hàng chọn thành phố mình đang sinh sống (ví dụ: Thành phố Hồ Chí Minh, Hà Nội, Đà Nẵng).
- Tại trang chi tiết của từng chiếc áo hoặc chiếc váy, hệ thống hiển thị rõ ràng: Trong thành phố đó, những cửa hàng chi nhánh nào đang còn đúng kích cỡ và màu sắc mà khách quan tâm, kèm số lượng thực tế tại quầy.
- *Nguyên tắc nghiệp vụ*: Tính năng này giúp khách hàng thuận tiện ghé cửa hàng để thử đồ trực tiếp. Đơn hàng khách đặt qua mạng sẽ được xuất đi từ kho tổng, không ảnh hưởng đến số lượng quần áo đang trưng bày trên kệ của các cửa hàng.

### 1.4. Danh sách Sản phẩm Yêu thích (Wishlist)
- Người mua có thể bấm biểu tượng "Yêu thích" để lưu lại những mẫu thiết kế mình ưng ý nhưng chưa muốn mua ngay, thuận tiện cho việc xem lại và đặt hàng sau này.

### 1.5. Quản lý Giỏ hàng
- Khách hàng có thể chọn nhiều món đồ, thay đổi kích cỡ, tăng giảm số lượng hoặc xóa bớt món đồ khỏi giỏ hàng trước khi tính tiền.
- *Quy tắc giữ hàng*: Việc bỏ đồ vào giỏ hàng **hoàn toàn không giữ trước số lượng trong kho**. Điều này nhằm đảm bảo tính công bằng: hàng hóa chỉ thực sự được dành riêng cho người thực hiện thao tác bấm nút đặt hàng sớm nhất.

### 1.6. Áp dụng Mã Phiếu Giảm giá (Coupon)
- Doanh nghiệp thường xuyên phát hành các mã giảm giá để kích cầu mua sắm. Khách hàng có thể xem danh sách mã đang có hiệu lực và nhập vào đơn hàng.
- Có hai hình thức giảm trừ:
  - Giảm theo tỷ lệ phần trăm (ví dụ: Giảm 10%, có quy định mức giảm tối đa không vượt quá một số tiền nhất định).
  - Giảm trừ trực tiếp một số tiền cố định (ví dụ: Giảm ngay 50.000 VNĐ).
- *Quy tắc áp dụng*: Mỗi đơn hàng chỉ được sử dụng tối đa 1 phiếu giảm giá. Phiếu chỉ hợp lệ khi tổng giá trị tiền hàng đạt mức tối thiểu theo quy định và mã đó còn trong thời hạn sử dụng.

### 1.7. Đặt hàng và Cung cấp Thông tin Giao nhận
- **Tạm tính minh bạch**: Trước khi xác nhận đặt, hệ thống tính toán chi tiết: tiền hàng, số tiền được giảm giá, phí vận chuyển và tổng số tiền cuối cùng người mua cần trả.
- **Địa chỉ giao hàng chuẩn hóa**: Khách hàng điền họ tên, số điện thoại người nhận, địa chỉ nhà gắn liền với danh mục 34 tỉnh/thành phố của Việt Nam.
- **Trừ kho kho tổng tức thời**: Ngay khoảnh khắc người mua bấm "Xác nhận đặt hàng", hệ thống lập tức trừ đi số lượng sản phẩm tương ứng trong kho hàng trung tâm để tránh tình trạng nhiều người cùng mua một món đồ mà kho không đủ đáp ứng.
- **Lưu giữ lịch sử bất biến**: Mọi thông tin về giá bán, tiền giảm giá và tên sản phẩm tại thời điểm mua được cố định vĩnh viễn trên đơn hàng. Doanh nghiệp sau này có tăng giá hay giảm giá sản phẩm thì hóa đơn cũ của khách hàng vẫn được giữ nguyên tính trung thực.

### 1.8. Thanh toán Đơn hàng
- Hệ thống D&K hỗ trợ hai hình thức thanh toán:
  - **VietQR (Chuyển khoản trước)**: Khách hàng quét mã QR để chuyển khoản ngân hàng tức thời trước khi hàng được xử lý. Đơn hàng được ghi nhận trạng thái thanh toán là `paid` ngay lập tức và sẵn sàng để bộ phận kho tiếp nhận đóng gói.
  - **COD (Tiền mặt khi nhận hàng)**: Khách hàng chọn thanh toán khi shipper giao hàng đến tay. Đơn hàng được tạo với trạng thái `pending_cod`. Tiền chỉ được xác nhận thu đủ sau khi shipper nội bộ giao thành công và đối soát về kho.
- Sau khi đặt hàng thành công theo bất kỳ hình thức nào, đơn hàng sẵn sàng chuyển sang giai đoạn xử lý kho.

### 1.9. Theo dõi Đơn hàng và Chính sách Hủy đơn
- Khách hàng có thể theo dõi xem đơn của mình đang ở bước nào (Đã thanh toán, Đã xác nhận hay Đã hoàn tất).
- **Quy tắc hủy đơn**:
  - Khách hàng (hoặc nhân viên quản trị) **chỉ được phép hủy khi đơn hàng còn ở trạng thái "Đã thanh toán" và chưa được người bán bấm xác nhận**. Khi hàng đã được xác nhận đóng gói thì không thể hủy tùy tiện.
  - Khi hủy đơn thành công: Hệ thống tự động trả lại toàn bộ số lượng quần áo vào kho tổng, hoàn trả lại mã giảm giá cho khách, tạo phiếu ghi nhận hoàn trả 100% tiền cho khách và ghi lại nhật ký lý do hủy.

### 1.10. Đánh giá và Nhận xét Sản phẩm sau khi Mua
- Nhằm xây dựng cộng đồng mua sắm minh bạch, chỉ những khách hàng đã thực sự mua và đơn hàng đã chuyển sang trạng thái "Hoàn tất" mới có quyền viết nhận xét và chấm điểm (từ 1 đến 5 sao) cho đúng món đồ mình đã nhận.
- Mỗi sản phẩm trong một đơn hàng chỉ được đánh giá một lần duy nhất.
- Đánh giá sau khi gửi sẽ xuất hiện công khai ngay lập tức để người mua khác tham khảo mà không cần chờ đợi xét duyệt.

---

## 2. Nghiệp vụ Bán hàng Trực tiếp tại Cửa hàng (POS)

### 2.1. Thanh toán Nhanh tại Quầy
- Nhân viên thu ngân tại từng chi nhánh sử dụng màn hình thu ngân chuyên dụng để phục vụ khách mua trực tiếp.
- Thu ngân tra cứu sản phẩm bằng cách gõ tên hoặc quét mã vạch sản phẩm, hệ thống hiển thị ngay đơn giá và số lượng sẵn có trên kệ.
- Thu ngân tạo hóa đơn, nhận tiền mặt hoặc chuyển khoản từ khách hàng và in biên lai giao hàng cho khách. Đơn hàng tại quầy được hoàn tất ngay lập tức.

### 2.2. Trừ Kho Cửa hàng Độc lập
- Việc bán hàng tại quầy **chỉ trừ vào số lượng tồn kho của chính cửa hàng đó**.
- Kho hàng bán lẻ tại cửa hàng và kho hàng bán online trên website được quản lý tách biệt, giúp cửa hàng chủ động nguồn hàng trưng bày mà không lo bị đơn hàng trên mạng lấy mất.

---

## 3. Nghiệp vụ Quản trị và Điều hành Doanh nghiệp (Admin)

### 3.1. Quản lý Mẫu mã Thời trang & Biến thể Sản phẩm
- Quản trị viên thực hiện đăng tải mẫu thiết kế mới, tải lên hình ảnh, mô tả phong cách chất liệu, thiết lập giá bán và khai báo danh sách kích cỡ, màu sắc.
- **Nguyên tắc bảo toàn dữ liệu tài chính (Lưu trữ thay vì Xóa)**:
  - Doanh nghiệp **tuyệt đối không xóa vĩnh viễn** bất kỳ sản phẩm nào đã từng phát sinh đơn hàng trong quá khứ, nhằm bảo toàn số liệu kế toán và hóa đơn của khách.
  - Khi một mẫu áo ngừng sản xuất hoặc hết vòng đời, quản trị viên đưa sản phẩm vào trạng thái "Lưu trữ ngừng kinh doanh". Sản phẩm sẽ biến mất khỏi website để khách không thấy nữa, nhưng toàn bộ lịch sử mua sắm trước đây vẫn được lưu trữ nguyên vẹn.

### 3.2. Quản lý Chương trình Khuyến mãi
- Quản trị viên tạo ra các chiến dịch ưu đãi theo mùa (như Giảm giá mùa hè, Siêu sale đôi ngày 9/9, 11/11 hay Xả hàng cuối năm), giới hạn ngân sách chiết khấu tối đa và thời gian bắt đầu/kết thúc chương trình.

### 3.3. Quy trình Tiếp nhận và Phê duyệt Đơn hàng
- Đơn hàng trực tuyến vận hành theo trình tự kiểm soát chặt chẽ:
  1. Khách đặt mua thành công: Đơn ở trạng thái **Đã thanh toán**.
  2. Nhân viên kiểm tra đơn, địa chỉ và gọi điện xác nhận (nếu cần): Chuyển sang **Đã xác nhận**.
  3. Đơn hàng hoàn tất và khách nhận được hàng: Chuyển sang **Hoàn tất**.
  4. Nếu có sự cố trước khi đóng gói: Chuyển sang **Đã hủy** (hoàn kho và hoàn tiền).

### 3.4. Kiểm duyệt Đánh giá Khách hàng
- Do hệ thống cho phép đánh giá hiển thị ngay, quản trị viên giữ vai trò hậu kiểm. Nếu phát hiện bình luận dùng từ ngữ thô tục, quảng cáo spam hoặc nội dung không lành mạnh, quản trị viên có quyền ẩn đánh giá đó khỏi website.

### 3.5. Điều chuyển Hàng hóa từ Kho tổng về Cửa hàng
- Khi một cửa hàng chi nhánh báo sắp hết một mẫu đầm hay một size áo nào đó, quản trị viên tạo lệnh điều chuyển:
  - Hệ thống kiểm tra kho trung tâm xem còn đủ số lượng yêu cầu hay không.
  - Nếu đủ, hệ thống tự động trừ bớt số lượng ở kho trung tâm và cộng thêm số lượng tương ứng vào kho của cửa hàng nhận.

### 3.6. Quản lý Hoạt động Cửa hàng Chi nhánh
- Quản lý cửa hàng theo dõi được số tiền bán lẻ thu được trong ngày tại chi nhánh mình, nắm được danh sách nhân viên thu ngân và kiểm kê lượng hàng thực tế đang nằm trên kệ của cửa hàng.

---

## 4. Nghiệp vụ Phục vụ Phân tích Dữ liệu và Dự báo Quản trị

### 4.1. Thu thập Nhật ký Tương tác Khách hàng và Bảo mật Thông tin
- Hệ thống tự động ghi nhận lại các tương tác của người dùng trên website (như khách vừa xem chiếc váy nào, tìm kiếm từ khóa gì, có thêm đồ vào giỏ hay không) để giúp doanh nghiệp hiểu rõ hành vi mua sắm.
- **Nguyên tắc bảo vệ quyền riêng tư**: Trước khi lưu trữ để phân tích, hệ thống tự động lọc bỏ hoặc làm mờ toàn bộ thông tin nhạy cảm của khách hàng (số điện thoại, mật khẩu, địa chỉ nhà, email cá nhân), đảm bảo tuân thủ đạo đức dữ liệu và an toàn thông tin.

### 4.2. Phân tích Hiệu quả Bán hàng và Nhu cầu Thị trường
- Theo dõi các chỉ số sức khỏe của website: lưu lượng khách ghé thăm theo từng khung giờ trong ngày, tỷ lệ xảy ra lỗi khi khách bấm mua hàng.
- **Phân tích phễu mua hàng**: Thống kê sản phẩm nào được khách xem nhiều nhất nhưng ít người bấm mua, sản phẩm nào khách hay bỏ vào giỏ hàng nhất để bộ phận kinh doanh có kế hoạch điều chỉnh giá hoặc chụp lại hình ảnh hấp dẫn hơn.

### 4.3. Dự báo Xu hướng Mua lại của Khách hàng
- Dựa trên lịch sử mua hàng sạch đã được lưu trữ qua nhiều tháng, doanh nghiệp xây dựng bài toán dự báo xem sau 30 ngày kể từ đơn hàng đầu tiên, những khách hàng nào có khả năng cao sẽ quay lại mua sắm tiếp, từ đó lên kế hoạch gửi thông báo ưu đãi đúng thời điểm.

---

# PHẦN II: CÁC NGHIỆP VỤ BỔ SUNG ĐÃ TRIỂN KHAI

*(Giao vận nội bộ D&K, xử lý rủi ro COD boom, đổi trả 7 ngày và sổ cái kho)*

Trong thực tế ngành bán lẻ thời trang tại Việt Nam, hệ thống ban đầu còn thiếu các mắt xích quan trọng trong khâu giao nhận và sau bán hàng. Tất cả 4 nghiệp vụ dưới đây đã được thiết kế và triển khai đầy đủ vào hệ thống:

---

## 1. Nghiệp vụ Quản lý Giao vận Nội bộ & Theo dõi Vận đơn

### 1.1. Mô hình Giao vận D&K
D&K không sử dụng đơn vị vận chuyển bên thứ ba (GHN, GHTK, Viettel Post, v.v.). Thay vào đó, doanh nghiệp vận hành đội ngũ **shipper nội bộ** trực thuộc biên chế, mỗi shipper được gán mã nhân viên riêng trong bảng `delivery_staff`.

### 1.2. Dòng chảy Nghiệp vụ
- **Mở rộng các bước của đơn hàng**:
  - Sau khi đơn được xác nhận, kho in phiếu đóng gói và phân công shipper nội bộ. Đơn hàng chuyển sang trạng thái **`shipping`**.
  - Khi khách ký nhận: Đơn hàng chuyển sang **`delivered`** → sau 7 ngày không có khiếu nại → **`completed`**.
  - Nếu shipper không giao được (khách không nghe máy, từ chối nhận): Đơn hàng chuyển sang **`failed_delivery`** (boom hàng).
- **Thông tin vận đơn**: Bảng `shipments` lưu trữ toàn bộ thông tin: shipper phụ trách (`delivery_staff_id`), thời gian giao (`shipped_at`, `delivered_at`), địa chỉ giao nhận và trạng thái vận chuyển.
- **Ghi nhận mốc thời gian đầy đủ**: Giờ xuất kho (`shipped_at`), giờ giao thành công (`delivered_at`).

### 1.3. Ý nghĩa Phân tích Dữ liệu
- Đo lường **tỷ lệ giao hàng thành công** theo từng shipper nội bộ, theo khu vực địa lý.
- Đo lường **thời gian giao hàng trung bình** (từ `shipped_at` đến `delivered_at`).
- Phân tích **hiệu suất từng shipper** qua bảng Gold `fact_shipment` và mart `mart_logistics_performance`.

---

## 2. Nghiệp vụ Thanh toán Linh hoạt & Xử lý "Boom Hàng" COD

### 2.1. Vấn đề Thực tiễn
Tại thị trường Việt Nam, **Thanh toán tiền mặt khi nhận hàng (COD)** vẫn chiếm tỷ trọng cao trong ngành thời trang. Rủi ro đặc thù là **boom hàng** — khách hàng từ chối nhận hàng hoặc không liên lạc được khi shipper giao, khiến doanh nghiệp chịu thiệt hại về chi phí vận chuyển và vốn hàng tồn.

### 2.2. Dòng chảy Nghiệp vụ
- **Hai hình thức thanh toán**:
  - `vietqr`: Chuyển khoản trước qua mã QR → đơn được xử lý ngay.
  - `cod`: Trả tiền mặt khi shipper giao → tiền đối soát sau khi giao thành công.
- **Xử lý boom hàng (`failed_delivery`)**:
  1. Shipper không giao được sau nhiều lần liên hệ → đánh dấu `status='failed_delivery'`.
  2. Hàng được shipper mang về kho trung tâm.
  3. Nhân viên kho kiểm tra hàng còn nguyên vẹn → nhập lại vào kho qua `inventory_transactions` với `movement_type='inbound'`.
  4. `net_revenue = 0` cho toàn bộ đơn boom; doanh thu gộp không được tính vào doanh thu thực tế.
  5. Lịch sử boom được ghi nhận theo `order_id` phục vụ phân tích rủi ro khách hàng.

### 2.3. Ý nghĩa Phân tích Dữ liệu
- Thống kê **tỷ lệ boom hàng theo khu vực, loại sản phẩm, khung giờ**.
- Nhận diện tài khoản khách hàng có tần suất boom cao để cảnh báo rủi ro.
- `fact_order` trong Gold lưu `is_boom` (boolean) và tách biệt `gross_revenue_vnd` vs `net_revenue_vnd`.

---

## 3. Nghiệp vụ Đổi / Trả hàng Sau khi Mua (Chính sách 7 Ngày)

### 3.1. Vấn đề Thực tiễn
Trong mua sắm quần áo online, khách nhận đồ mặc thử không vừa hoặc phát hiện đường may lỗi là chuyện phổ biến. Cần quy trình đổi trả rõ ràng để giữ chân khách trung thành và tính toán doanh thu thuần chính xác.

### 3.2. Chính sách Đổi trả D&K
- **Thời hạn**: 7 ngày kể từ ngày giao hàng thành công (`delivered_at`).
- **Điều kiện**: Sản phẩm chưa qua giặt ủi, còn nguyên tem mác thương hiệu.
- **Hình thức**: Đổi size/màu khác (khách chịu phí vận chuyển chiều về) hoặc trả hàng hoàn tiền.

### 3.3. Dòng chảy Nghiệp vụ
- Khách gửi yêu cầu qua hệ thống (chọn đơn hàng → chọn sản phẩm → nêu lý do + upload ảnh).
- Quản trị viên duyệt và hướng dẫn khách gửi hàng về kho trung tâm.
- Nhân viên kho kiểm định hàng:
  - Đạt chuẩn + trả hàng → `status='returned'` trong `return_requests`; nhập lại vào `inventory_transactions`; `net_revenue = 0`.
  - Đạt chuẩn + đổi size → xuất hàng mới, tạo `return_items` với lý do `exchanged`.
  - Không đạt chuẩn → từ chối, ghi nhận `status='rejected'`.
- Dữ liệu đổi trả được lưu trong bảng `return_requests` và `return_items`.

### 3.4. Ý nghĩa Phân tích Dữ liệu
- **Tỷ lệ hàng bị trả theo từng mẫu mã và size**: Phát hiện lỗi bảng thông số size.
- **Doanh thu thuần thực tế**:
  $$\text{Net Revenue} = \text{Gross Revenue} - \text{Discount} - \text{Boom Orders} - \text{Returned Orders}$$
- Gold mart `mart_product_returns` tổng hợp số liệu đổi trả theo sản phẩm và lý do.

---

## 4. Nghiệp vụ Quản lý Kho & Sổ cái Nhập/Xuất hàng

### 4.1. Mô hình Kho D&K
D&K vận hành **1 kho trung tâm duy nhất** cung cấp hàng cho:
- Đơn hàng online (xuất kho → giao khách).
- Tái cung ứng cho các cửa hàng chi nhánh (điều chuyển nội bộ).

Không có bảng `suppliers` (nhà cung ứng riêng). Thay vào đó, mọi biến động kho đều được ghi nhận qua bảng **`inventory_transactions`** với các loại giao dịch:

### 4.2. Các loại giao dịch kho (`movement_type`)
| Loại | Mô tả | Tác động tồn kho |
|------|-------|-----------------|
| `inbound` | Nhập hàng giả lập (không cần nhà cung ứng thực tế) | Cộng kho tổng |
| `outbound_sale` | Xuất hàng cho đơn online | Trừ kho tổng |
| `outbound_transfer` | Điều chuyển kho → cửa hàng chi nhánh | Trừ kho tổng + cộng store |
| `return_inbound` | Nhập lại hàng boom/đổi trả | Cộng kho tổng |
| `adjustment` | Điều chỉnh tồn kho (kiểm kê) | Thay đổi theo thực tế |

### 4.3. Ý nghĩa Phân tích Dữ liệu
- **Tốc độ quay vòng hàng tồn kho**: Sản phẩm nào bán nhanh, sản phẩm nào ứ đọng.
- **Tồn kho snapshot hàng ngày**: Gold table `fact_inventory_daily_snapshot` ghi nhận tồn kho theo từng biến thể tại từng cửa hàng mỗi ngày.
- **Cảnh báo hàng sắp cạn**: `mart_inventory_health` theo dõi các variant có số lượng dưới ngưỡng an toàn.
- **COGS (Giá vốn hàng bán)**: Cột `unit_cost_vnd` trong `inventory_transactions` và `order_items` lưu giá vốn để tính lợi nhuận gộp.

---

# PHẦN III: VÒNG ĐỜI ĐƠN HÀNG VÀ MA TRẬN PHỐI HỢP TOÀN DIỆN

## 1. Hành trình Trọn vẹn của một Đơn hàng Mua sắm (Từ Đặt hàng đến Sau Bán)

Dưới đây là mô tả dòng chảy vận hành thực tế và các trạng thái đơn hàng tương ứng trong hệ thống:

| Giai đoạn | Trạng thái hệ thống | Mô tả |
|-----------|-------------------|-------|
| Đặt mua (VietQR) | `paid` | Kho trừ hàng ngay, tiền đã về tài khoản |
| Đặt mua (COD) | `pending_cod` | Kho trừ hàng, tiền chờ thu khi giao |
| Hủy đơn sớm | `cancelled` | Kho hoàn hàng, tiền hoàn (nếu có) |
| Duyệt & đóng gói | `confirmed` | Nhân viên kho xác nhận, in phiếu đóng gói |
| Đang giao | `shipping` | Shipper nội bộ nhận kiện, đang trên đường giao |
| Giao thành công | `delivered` | Khách ký nhận; COD đã thu tiền |
| Boom hàng | `failed_delivery` | Shipper không giao được; hàng mang về kho |
| Đổi trả chờ xử lý | `returned` | Khách gửi hàng về, kho đang kiểm định |
| Hoàn tất | `completed` | Sau 7 ngày delivered không có khiếu nại |

**State machine đơn giản hóa:**
```
pending_cod/paid → confirmed → shipping → delivered → completed
                                        ↘ failed_delivery (boom)
paid → cancelled (hủy sớm)
delivered → returned (7 ngày đổi trả)
```

---

## 2. Bảng Phân công Trách nhiệm giữa các Bộ phận

| Hành động & Nghiệp vụ | Khách hàng | Thu ngân Cửa hàng | Quản lý Chi nhánh | Nhân viên Kho & Quản trị | Shipper Nội bộ D&K |
|---|:---:|:---:|:---:|:---:|:---:|
| Tìm kiếm, xem mẫu mã, chọn size quần áo | Thực hiện | - | - | - | - |
| Tra cứu cửa hàng chi nhánh gần mình còn đồ | Xem thông tin | - | - | - | - |
| Bỏ vào giỏ, nhập mã giảm giá, đặt hàng qua mạng | Thực hiện | - | - | - | - |
| Chọn hình thức thanh toán (VietQR / COD) | Thực hiện | - | - | - | - |
| Hủy đơn hàng sớm khi chưa được duyệt | Thực hiện | - | - | Giám sát | - |
| Gửi đánh giá, chấm điểm sau khi nhận đồ | Thực hiện | - | - | Hậu kiểm ẩn/hiện | - |
| Gửi yêu cầu đổi size hoặc trả hàng trong 7 ngày | Thực hiện | - | - | Tiếp nhận & Duyệt | - |
| Bán hàng và in hóa đơn trực tiếp tại quầy | - | Thực hiện | Giám sát | - | - |
| Kiểm kê hàng trên kệ và nhân sự tại cửa hàng | - | Báo cáo | Thực hiện | Giám sát | - |
| Duyệt đơn hàng online và in phiếu đóng gói | - | - | - | Thực hiện | - |
| Phân công shipper nội bộ và bàn giao kiện hàng | - | - | - | Thực hiện | Tiếp nhận |
| Đi giao hàng đến tận nhà và thu tiền COD | - | - | - | Theo dõi tiến độ | Thực hiện |
| Tiếp nhận hàng hoàn do khách boom hàng | - | - | - | Kiểm tra & Nhập kho | Giao trả lại kho |
| Kiểm định hàng đổi trả từ khách gửi về và hoàn tiền | - | - | - | Thực hiện | - |
| Nhập hàng mới vào kho (ghi sổ cái kho) | - | - | - | Thực hiện | - |
| Chuyển hàng từ kho tổng về chi nhánh cửa hàng | - | Nhận hàng | Phối hợp | Điều lệnh chuyển | - |

