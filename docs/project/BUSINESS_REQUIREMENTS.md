# TÀI LIỆU ĐẶC TẢ NGHIỆP VỤ BÀI TOÁN KINH DOANH
## Hệ thống Bán lẻ & Thương mại Điện tử Thời trang Đa kênh (D&K E-Commerce)

---

## LỜI NÓI ĐẦU & MỤC TIÊU TÀI LIỆU

Tài liệu này mô tả toàn diện bài toán nghiệp vụ kinh doanh của hệ thống bán lẻ thời trang **D&K**, kết hợp hài hòa giữa mô hình bán hàng trực tuyến trên website và chuỗi cửa hàng bán lẻ truyền thống. 

Mục tiêu chính của tài liệu là trình bày rõ ràng dòng chảy công việc, vai trò của từng bộ phận tham gia, các quy tắc vận hành kinh doanh và giá trị phân tích dữ liệu phục vụ quản trị doanh nghiệp, bằng văn phong mô tả tự nhiên, dễ hiểu, không phụ thuộc vào các thuật ngữ lập trình hay kỹ thuật chuyên sâu.

Tài liệu gồm 3 phần:
- **Phần I: Các nghiệp vụ vận hành hiện có** (Mô hình đang hoạt động trên hệ thống).
- **Phần II: Các nghiệp vụ đề xuất bổ sung** (Mở rộng bám sát thực tế thị trường bán lẻ tại Việt Nam, không bao gồm chính sách tích điểm).
- **Phần III: Vòng đời đơn hàng và ma trận phối hợp giữa các bộ phận**.

---

## CÁC ĐỐI TƯỢNG THAM GIA VÀO HỆ THỐNG

1. **Khách hàng (Người mua sắm trực tuyến)**: Người tiêu dùng tìm kiếm, xem mẫu mã, kiểm tra kích cỡ, đặt mua hàng qua website hoặc tra cứu địa chỉ cửa hàng còn hàng để đến mua trực tiếp.
2. **Nhân viên thu ngân tại cửa hàng**: Người phụ trách tính tiền, in hóa đơn và bàn giao sản phẩm trực tiếp cho khách tại quầy bán lẻ của từng chi nhánh.
3. **Quản lý cửa hàng chi nhánh**: Người chịu trách nhiệm theo dõi doanh thu bán tại quầy, nắm bắt số lượng hàng tồn tại cửa hàng và quản lý nhân viên của chi nhánh mình.
4. **Bộ phận quản trị & vận hành kinh doanh (Quản trị viên)**: Người điều phối toàn bộ hoạt động của doanh nghiệp: quản lý danh mục mẫu mã, duyệt chương trình giảm giá, xử lý đơn hàng trực tuyến, điều chuyển hàng giữa các kho và giám sát báo cáo tài chính.
5. **Đối tác vận chuyển (Shipper / Đơn vị giao nhận)**: Đơn vị trung gian chịu trách nhiệm nhận hàng đã đóng gói từ kho của doanh nghiệp và đi giao đến tận tay khách hàng.
6. **Nhà cung ứng / Xưởng may gia công**: Đơn vị sản xuất và cung ứng các lô sản phẩm may mặc đầu vào cho kho trung tâm của doanh nghiệp.

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
- Đơn hàng được hệ thống ghi nhận đã thanh toán thành công và chuyển sang trạng thái "Đã thanh toán", sẵn sàng chờ bộ phận vận hành tiếp nhận và xử lý.

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

# PHẦN II: CÁC NGHIỆP VỤ BỔ SUNG ĐỀ XUẤT ĐỂ HOÀN THIỆN MÔ HÌNH THỰC TẾ
*(Tập trung vào khâu vận chuyển, rủi ro giao nhận, đổi trả sau mua và quản lý nguồn hàng nhập)*

Trong thực tế ngành bán lẻ thời trang tại Việt Nam, hệ thống hiện tại còn thiếu các mắt xích quan trọng trong khâu giao nhận và sau bán hàng. Dưới đây là 4 nghiệp vụ bổ sung cần thiết:

---

## 1. Nghiệp vụ Quản lý Giao vận & Theo dõi Vận đơn (Logistics & Shipments)

### 1.1. Vấn đề Thực tiễn Cần giải quyết
Hiện tại, đơn hàng sau khi được xác nhận thì gần như được coi là "xong", bỏ qua hoàn toàn quá trình giao hàng thực tế. Trong đời thực, từ lúc người bán đóng gói đến khi người mua nhận được đồ mất từ 1 đến 4 ngày qua các đơn vị chuyển phát, và đây là khâu thường xuyên phát sinh khiếu nại (chậm trễ, thất lạc hàng).

### 1.2. Dòng chảy Nghiệp vụ Đề xuất
- **Mở rộng các bước của đơn hàng**:
  - Sau khi đơn được xác nhận, bộ phận kho in phiếu đóng gói và bàn giao kiện hàng cho shipper. Đơn hàng chuyển sang trạng thái **Đang giao hàng**.
  - Khi người mua ký nhận đồ: Đơn hàng chuyển sang **Đã giao thành công** (sau đó chuyển thành **Hoàn tất**).
  - Nếu shipper đi giao nhiều lần mà không giao được: Đơn hàng chuyển sang **Giao hàng thất bại**.
- **Liên kết với các đối tác vận chuyển chuyên nghiệp**:
  - Hỗ trợ các đơn vị vận chuyển quen thuộc tại Việt Nam: Giao Hàng Nhanh (GHN), Giao Hàng Tiết Kiệm (GHTK), Viettel Post, Bưu điện Việt Nam (VNPost).
  - Mỗi gói hàng xuất kho được cấp một **Mã vận đơn riêng biệt** để cả khách hàng lẫn doanh nghiệp có thể theo dõi vị trí kiện hàng theo thời gian thực.
  - Ghi nhận đầy đủ các mốc thời gian: Giờ xuất kho gửi hàng, giờ dự kiến giao tới nơi và giờ giao thành công thực tế.

### 1.3. Ý nghĩa Dữ liệu đối với Quản trị Doanh nghiệp
- Đo lường được **Tỷ lệ giao hàng đúng hẹn**: Tỉnh thành nào hay bị giao chậm? Đơn vị vận chuyển nào giao nhanh nhất vào dịp lễ Tết?
- So sánh hiệu quả giữa các đối tác vận chuyển để doanh nghiệp chủ động lựa chọn đối tác có chi phí tốt nhất và dịch vụ uy tín nhất cho từng vùng miền.

---

## 2. Nghiệp vụ Thanh toán Linh hoạt & Xử lý "Boom Hàng" khi Giao tiền mặt (COD)

### 2.1. Vấn đề Thực tiễn Cần giải quyết
Tại thị trường Việt Nam, hình thức **Thanh toán tiền mặt khi nhận hàng (COD - Cash On Delivery)** vẫn chiếm tỷ trọng rất cao trong ngành thời trang. Đi kèm với hình thức này là bài toán nan giải: **Khách hàng từ chối nhận hàng hoặc không nghe máy khi shipper gọi giao (thường gọi là "boom hàng")**, khiến người bán chịu thiệt hại nặng về chi phí vận chuyển hai chiều và giam vốn hàng tồn.

### 2.2. Dòng chảy Nghiệp vụ Đề xuất
- **Đa dạng hóa lựa chọn thanh toán khi đặt hàng**:
  - Lựa chọn 1: Thanh toán khi nhận hàng (COD).
  - Lựa chọn 2: Chuyển khoản ngân hàng tức thời qua mã quét VietQR.
- **Quy trình thu tiền và đối soát cho đơn COD**:
  - Khi khách đặt đơn COD, đơn hàng được ghi nhận là "Chờ thu tiền khi giao".
  - Tiền bán hàng chỉ thực sự được xác nhận thu đủ sau khi shipper giao đồ thành công và chuyển tiền đối soát về cho công ty.
- **Quy trình xử lý khi khách boom hàng (Giao thất bại)**:
  1. Khi shipper liên lạc bất thành quá 3 lần hoặc khách từ chối nhận đồ vì đổi ý, đơn hàng được đánh dấu là **Giao hàng thất bại**.
  2. Kiện hàng được đơn vị vận chuyển đóng gói để chuyển hoàn ngược lại về kho trung tâm của công ty.
  3. Nhân viên kho mở kiện hàng kiểm tra: nếu sản phẩm còn nguyên vẹn, hệ thống tiến hành nhập lại đúng số lượng đó vào kho tổng để tiếp tục bán cho người khác.
  4. Hệ thống lưu lại lý do boom hàng (khách không nghe máy, khách chê tiền ship cao, khách đổi ý không thích nữa).
  5. Tài khoản của người mua bị ghi nhận lịch sử không nhận hàng để cảnh báo rủi ro cho các đơn hàng tiếp theo.

### 2.3. Ý nghĩa Dữ liệu đối với Quản trị Doanh nghiệp
- Thống kê chi tiết **Tỷ lệ từ chối nhận hàng theo địa lý**: Khu vực nào hay boom hàng nhất? Loại váy áo nào dễ bị từ chối nhất?
- Nhận diện những tài khoản có tiền sử từ chối nhận đồ nhiều lần để tự động yêu cầu họ phải chuyển khoản trước nếu muốn tiếp tục đặt hàng trong tương lai.

---

## 3. Nghiệp vụ Đổi / Trả hàng Sau khi Mua (Chăm sóc Sau Bán hàng)

### 3.1. Vấn đề Thực tiễn Cần giải quyết
Trong mua sắm quần áo online, khách nhận đồ mặc thử không vừa vặn (quá rộng, quá chật) hoặc phát hiện đường may lỗi là chuyện rất phổ biến. Nếu không có chính sách và quy trình đổi trả rõ ràng, khách hàng sẽ ngần ngại khi mua sắm và doanh nghiệp dễ mất khách trung thành.

### 3.2. Dòng chảy Nghiệp vụ Đề xuất
- **Chính sách đổi trả rõ ràng**:
  - Khách hàng có quyền gửi yêu cầu đổi hoặc trả hàng trong vòng **7 ngày** kể từ ngày ký nhận kiện hàng thành công.
  - Điều kiện: Sản phẩm chưa qua giặt ủi, còn nguyên tem mác của thương hiệu.
- **Quy trình gửi yêu cầu từ khách hàng**:
  - Khách vào lịch sử đơn hàng, chọn món đồ cần đổi trả, nêu rõ lý do (chọn nhầm size, vải bị lỗi, giao nhầm màu) và tải lên hình ảnh chụp thực tế.
  - Khách được chọn 1 trong 2 hình thức:
    - *Đổi hàng*: Đổi sang size khác vừa hơn hoặc đổi sang màu khác.
    - *Trả hàng hoàn tiền*: Gửi trả lại đồ và nhận lại tiền qua tài khoản ngân hàng.
- **Quy trình xét duyệt và xử lý của Cửa hàng**:
  1. Quản trị viên duyệt sơ bộ yêu cầu dựa trên hình ảnh khách gửi.
  2. Hướng dẫn khách gửi bưu kiện về địa chỉ kho của công ty.
  3. Nhân viên kho nhận hàng, kiểm định xem tem mác và tình trạng đồ có đạt chuẩn hay không:
     - Nếu đạt chuẩn và khách muốn trả đồ: Kho nhập lại hàng vào kho tổng, kế toán làm lệnh hoàn lại tiền cho khách.
     - Nếu đạt chuẩn và khách muốn đổi size: Kho xuất chiếc áo size mới gửi lại cho khách (đơn hàng đổi mới được miễn phí cước).
     - Nếu hàng đã bị giặt ủi, rách do người dùng: Từ chối yêu cầu và gửi trả lại đồ cho khách.

### 3.3. Ý nghĩa Dữ liệu đối với Quản trị Doanh nghiệp
- Đo lường được **Tỷ lệ hàng bị trả lại theo từng mẫu mã và size số**: Giúp phát hiện kịp thời những mẫu áo có bảng thông số size bị sai lệch so với vóc dáng thực tế của người Việt để gửi phản hồi cho xưởng may chỉnh sửa rập may.
- Tính toán chính xác **Doanh thu Thực tế (Doanh thu thuần)**:
  $$\text{Doanh thu thực tế} = \text{Tổng tiền thu bán hàng} - \text{Tiền giảm giá} - \text{Tiền các đơn bị boom} - \text{Tiền hoàn trả cho khách đổi trả}$$
  Đây mới là con số chuẩn xác phản ánh hiệu quả kinh doanh của công ty.

---

## 4. Nghiệp vụ Nhập hàng từ Xưởng Sản xuất / Nhà Cung ứng (Quản lý Đầu vào)

### 4.1. Vấn đề Thực tiễn Cần giải quyết
Hiện tại kho hàng chỉ có số lượng tồn có sẵn để xuất bán ra, chưa có quy trình ghi nhận nguồn hàng nhập vào định kỳ từ các xưởng may gia công. Việc thiếu khâu này khiến doanh nghiệp không theo dõi được **Giá vốn nhập hàng (giá gốc)**, từ đó không thể tính toán được mình đang lãi hay lỗ thực sự trên từng chiếc áo bán ra.

### 4.2. Dòng chảy Nghiệp vụ Đề xuất
- **Quản lý danh sách đối tác sản xuất**: Quản lý thông tin các nhà cung cấp, xưởng cắt may, xưởng dệt vải gia công cho thương hiệu.
- **Quy trình Tạo phiếu Đặt hàng Nhập kho (Đơn mua hàng)**:
  - Khi cần bổ sung bộ sưu tập mới, người phụ trách kho tạo phiếu nhập hàng: ghi rõ xưởng nào may, số lượng từng size/màu cần nhập, ngày giao hàng dự kiến và **đơn giá vốn gốc nhập vào** (ví dụ: Một chiếc áo sơ mi may gia công với giá vốn 120.000 VNĐ, giá niêm yết bán ra web là 350.000 VNĐ).
- **Kiểm đếm và Nhập kho Thực tế**:
  - Khi xe tải của xưởng may giao hàng tới kho trung tâm: Nhân viên kho kiểm đếm số lượng thực tế, kiểm tra chất lượng đường kim mũi chỉ.
  - Bấm xác nhận "Đã nhập kho": Hệ thống tự động cộng thêm số lượng quần áo vào kho trung tâm và ghi nhận giá vốn hàng hóa vào sổ sách.
- **Tự động Cảnh báo khi Hàng sắp cạn**:
  - Thiết lập mức tồn kho an toàn cho từng món đồ (ví dụ: Áo thun trắng size M luôn cần duy trì tối thiểu 20 chiếc trong kho).
  - Khi số lượng hàng trên web bán gần chạm mốc cảnh báo, hệ thống hiển thị nhắc nhở màu đỏ trên màn hình của người quản lý để kịp thời liên hệ xưởng may sản xuất thêm đợt mới.

### 4.3. Ý nghĩa Dữ liệu đối với Quản trị Doanh nghiệp
- Đo lường **Tốc độ quay vòng hàng tồn kho**: Sản phẩm nào vừa nhập về đã bán hết ngay (bán chạy)? Sản phẩm nào nằm lưu kho quá 60 ngày không ai ngó tới (hàng ứ đọng) để kịp thời lên kế hoạch đại hạ giá giải phóng vốn?
- Đo lường **Lợi nhuận Gộp thực tế**:
  $$\text{Lợi nhuận gộp} = \text{Giá bán ra cho khách} - \text{Giá vốn gốc nhập từ xưởng}$$
  Giúp ban lãnh đạo nhìn thấy rõ ràng biên lợi nhuận của từng dòng sản phẩm thời trang.

---

# PHẦN III: VÒNG ĐỜI ĐƠN HÀNG VÀ MA TRẬN PHỐI HỢP TOÀN DIỆN

## 1. Hành trình Trọn vẹn của một Đơn hàng Mua sắm (Từ Đặt hàng đến Sau Bán)

Dưới đây là mô tả dòng chảy vận hành tự nhiên từ lúc khách hàng bắt đầu lựa chọn cho tới khi kết thúc mọi giao dịch:

1. **Giai đoạn Đặt mua**: Khách hàng chọn size, màu, nhập mã giảm giá và chọn hình thức thanh toán (chuyển khoản hoặc nhận hàng trả tiền mặt COD). Khi bấm đặt hàng, kho tổng lập tức trừ hàng và lưu lại đơn với trạng thái **Đã thanh toán** (hoặc Đã nhận đơn COD).
2. **Giai đoạn Hủy đơn sớm**: Nếu khách đổi ý ngay sau khi vừa đặt, khách có thể tự bấm hủy trên web (chỉ khi đơn chưa được duyệt). Đơn chuyển sang **Đã hủy**, hàng được tự động trả lại kho và tiền được hoàn trả.
3. **Giai đoạn Duyệt và Đóng gói**: Nhân viên kho kiểm tra thông tin, bấm xác nhận đơn hàng, đóng kiện và dán mã vận chuyển. Đơn chuyển sang **Đã xác nhận**.
4. **Giai đoạn Giao hàng**: Shipper nhận kiện hàng từ kho và mang đi giao. Đơn chuyển sang **Đang giao hàng**.
5. **Kịch bản Giao thành công**: Khách nhận đồ và trả tiền (nếu là đơn COD). Đơn hàng chuyển sang **Đã giao thành công**. Khách có thể bắt đầu đánh giá sản phẩm.
6. **Kịch bản Khách không nhận (Boom hàng)**: Sau các lần giao không thành công, đơn chuyển sang **Giao thất bại**. Kiện hàng chuyển hoàn về kho, nhân viên kho nhận lại và hoàn hàng vào kho để bán tiếp, đóng đơn hàng.
7. **Giai đoạn Sau bán hàng (7 ngày đổi trả)**:
   - Trong vòng 7 ngày sau khi nhận, nếu khách thử không vừa, khách gửi yêu cầu đổi trả.
   - Cửa hàng nhận hàng về kiểm tra: nếu đạt yêu cầu, tiến hành đổi chiếc mới gửi lại cho khách HOẶC hoàn lại tiền nếu khách muốn trả đồ.
8. **Hoàn tất Giao dịch**: Sau khi hết 7 ngày mà khách không có khiếu nại đổi trả, đơn hàng chính thức chuyển sang trạng thái **Hoàn tất**, khép lại toàn bộ vòng đời kinh doanh của một giao dịch bán lẻ.

---

## 2. Bảng Phân công Trách nhiệm giữa các Bộ phận

| Hành động & Nghiệp vụ | Khách hàng | Thu ngân Cửa hàng | Quản lý Chi nhánh | Nhân viên Kho & Quản trị | Đối tác Giao vận |
|---|:---:|:---:|:---:|:---:|:---:|
| Tìm kiếm, xem mẫu mã, chọn size quần áo | Thực hiện | - | - | - | - |
| Tra cứu cửa hàng chi nhánh gần mình còn đồ | Xem thông tin | - | - | - | - |
| Bỏ vào giỏ, nhập mã giảm giá, đặt hàng qua mạng | Thực hiện | - | - | - | - |
| Hủy đơn hàng sớm khi chưa được duyệt | Thực hiện | - | - | Giám sát | - |
| Gửi đánh giá, chấm điểm sau khi nhận đồ | Thực hiện | - | - | Hậu kiểm ẩn/hiện | - |
| Gửi yêu cầu đổi size hoặc trả hàng trong 7 ngày | Thực hiện | - | - | Tiếp nhận & Duyệt | - |
| Bán hàng và in hóa đơn trực tiếp tại quầy | - | Thực hiện | Giám sát | - | - |
| Kiểm kê hàng trên kệ và nhân sự tại cửa hàng | - | Báo cáo | Thực hiện | Giám sát | - |
| Duyệt đơn hàng online và in phiếu đóng gói | - | - | - | Thực hiện | - |
| Bàn giao bưu kiện cho shipper và cấp mã vận đơn | - | - | - | Thực hiện | Tiếp nhận |
| Đi giao hàng đến tận nhà và thu tiền COD | - | - | - | Theo dõi tiến độ | Thực hiện |
| Tiếp nhận hàng hoàn do khách không nhận (boom) | - | - | - | Kiểm tra & Nhập kho | Giao trả lại |
| Kiểm định hàng đổi trả từ khách gửi về và hoàn tiền | - | - | - | Thực hiện | Vận chuyển về |
| Lập phiếu nhập thêm hàng mới từ xưởng sản xuất | - | - | - | Thực hiện | - |
| Chuyển hàng từ kho tổng về chi nhánh cửa hàng | - | Nhận hàng | Phối hợp | Điều lệnh chuyển | - |
