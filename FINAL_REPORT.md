# **CHƯƠNG 2. CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ SỬ DỤNG**

## **2.1. Tổng quan về thương mại điện tử và bán hàng đa kênh**

### **2.1.1. Mô hình thương mại điện tử và bán hàng đa kênh**

Thương mại điện tử (TMĐT) là hoạt động mua bán hàng hóa, dịch vụ mà quá trình đặt hàng được thực hiện qua phương tiện điện tử, trong khi khâu thanh toán và giao nhận có thể diễn ra trực tuyến hoặc ngoại tuyến [1]. Trong đó, mô hình B2C (Business-to-Consumer) cho phép doanh nghiệp phân phối sản phẩm trực tiếp đến người tiêu dùng qua website và các nền tảng số.

Khi mở rộng sang bán hàng đa kênh (Multichannel Retailing) kết hợp giữa website và cửa hàng vật lý, việc quản lý dữ liệu phân tán ở từng kênh riêng lẻ dễ dẫn đến sai lệch tồn kho và gây khó khăn khi tổng hợp doanh thu. Để khắc phục, đồ án này tích hợp kênh bán hàng trực tuyến (Storefront) và hệ thống bán hàng tại quầy (POS) trên cùng một hệ thống Backend và cơ sở dữ liệu giao dịch. Kiến trúc hợp nhất này đảm bảo đồng bộ dữ liệu sản phẩm, giá bán, tồn kho và khách hàng theo quy tắc nghiệp vụ chung, đồng thời chuẩn hóa nguồn dữ liệu giao dịch và hành vi để dễ dàng đối chiếu hiệu quả kinh doanh giữa các kênh trên cùng một hệ quy chiếu chỉ số.

### **2.1.2. Quy trình quản lý bán hàng, đơn hàng và tồn kho**

Dù khác biệt về giao diện và luồng tương tác giữa khách hàng đặt trực tuyến và nhân viên thu ngân tại quầy, cả hai kênh đều chia sẻ chung các nghiệp vụ cốt lõi: kiểm tra tính hợp lệ của giá bán, xác nhận tồn kho khả dụng và cập nhật trạng thái đơn hàng theo quy chuẩn thống nhất.

Về quản lý trạng thái, vòng đời đơn hàng được định nghĩa chặt chẽ qua các giai đoạn (*mới tạo, đã xác nhận, đang xử lý, đang giao, hoàn thành, đã hủy*) và phân tách độc lập thành ba luồng trạng thái: **đơn hàng, giao nhận và thanh toán**. Việc tách biệt này—đặc biệt với phương thức thanh toán khi nhận hàng (COD) chờ đối soát tiền thu hộ hoặc khi phát sinh hủy đơn, giao thất bại, đổi trả—giúp hệ thống tránh ghi nhận doanh thu hay hoàn tiền sai thời điểm, đảm bảo độ chính xác cho báo cáo vận hành.

Về dữ liệu giao dịch và kiểm soát tồn kho, tổng giá trị đơn hàng (đơn giá, số lượng, chiết khấu, phí vận chuyển) phải được tính toán và lưu cố định (snapshot) tại bảng chi tiết đơn hàng ngay thời điểm xác nhận mua để bảo toàn lịch sử khi giá niêm yết thay đổi. Song song đó, để ngăn chặn tình trạng bán vượt số lượng (overselling) khi có giao dịch đồng thời, tồn kho được bóc tách thành ba đại lượng: *số lượng thực tế trong kho (on-hand)*, *số lượng đang tạm giữ (reserved)* và *số lượng khả dụng (available)*, được cập nhật đồng bộ xuyên suốt mọi tác vụ thanh toán, hủy đơn và nhập kho.

### **2.1.3. Vai trò của phân tích dữ liệu trong hoạt động kinh doanh**

Dữ liệu phát sinh từ đơn hàng, sản phẩm, tồn kho và hành vi tương tác trên website là đầu vào quan trọng để nhận diện xu hướng tiêu thụ, xác định nhóm hàng bán chạy hoặc tồn đọng và đánh giá hành trình mua sắm của khách hàng. Do cơ sở dữ liệu giao dịch (OLTP) được tối ưu cho các tác vụ đọc/ghi tức thời thay vì truy vấn tổng hợp lớn, việc đồng bộ dữ liệu sang một nền tảng phân tích chuyên biệt (OLAP) là yêu cầu tất yếu nhằm giảm tải cho hệ thống vận hành chính và tạo bước đệm để làm sạch, chuẩn hóa chỉ số trước khi trực quan hóa.

Về phương pháp tiếp cận, khai thác dữ liệu gồm ba cấp độ: *phân tích mô tả (Descriptive Analytics)* làm rõ những gì đã diễn ra; *phân tích chẩn đoán (Diagnostic Analytics)* tìm hiểu nguyên nhân gốc rễ; và *phân tích dự báo (Predictive Analytics)* ứng dụng học máy. Trong phạm vi đồ án, hệ thống tập trung vào phân tích mô tả và bước đầu hỗ trợ phân tích chẩn đoán nhằm phát hiện sớm các điểm bất thường. Để kết quả phân tích có giá trị đối chiếu giữa kênh trực tuyến và tại quầy, hệ thống thiết lập tầng ngữ nghĩa thống nhất (Single Source of Truth), quy chuẩn hóa các chiều dữ liệu và độ đo cốt lõi trước khi xây dựng Dashboard.

### **2.1.4. Hệ thống chỉ số KPI trong thương mại điện tử**

KPI (Key Performance Indicator) là chỉ số đo lường mức độ đạt mục tiêu kinh doanh và vận hành, bao gồm các nhóm chính: bán hàng (doanh thu, số đơn, giá trị đơn trung bình), vận hành (đơn hủy, giao thất bại, đổi trả), tồn kho và hành vi người dùng (lượt xem, thêm giỏ hàng, chuyển đổi).

*Bảng 2.1. Một số KPI tiêu biểu trong hệ thống thương mại điện tử*

| Chỉ số | Cách xác định |
| :---- | :---- |
| AOV | Tổng giá trị đơn hợp lệ / Số đơn hợp lệ |
| Tỷ lệ hủy đơn | Số đơn bị hủy / Tổng số đơn thuộc phạm vi đánh giá $\times 100\%$ |
| Tỷ lệ chuyển đổi | Số phiên có phát sinh đơn / Tổng số phiên hợp lệ $\times 100\%$ |
| Tỷ lệ trả hàng | Số đơn có phát sinh trả hàng / Số đơn đủ điều kiện đánh giá $\times 100\%$ |

Mỗi KPI cần được quy định thống nhất về nguồn dữ liệu, khoảng thời gian, điều kiện lọc và lập thành danh mục chuẩn để sử dụng xuyên suốt trong thiết kế Data Mart và kiểm thử:
- **Quy tắc tính toán:** Số lượng đơn hàng phải đếm theo mã đơn duy nhất thay vì số dòng sản phẩm chi tiết; doanh thu cần phân biệt rõ giữa giá trị đặt hàng với doanh thu đã hoàn tất (sau khi tính phí vận chuyển, chiết khấu, hoàn trả); chỉ số hành vi cần xác định rõ cách gom phiên truy cập, loại trừ truy cập nội bộ và khử sự kiện trùng lặp.
- **Chu kỳ cập nhật:** Các KPI có độ trễ khác nhau (số đơn đặt hàng ghi nhận tức thời, nhưng doanh thu hoàn thành hoặc tỷ lệ trả hàng phụ thuộc vào diễn biến nghiệp vụ tiếp theo). Do đó, Dashboard cần công bố rõ mốc thời gian cập nhật để người dùng hiểu đúng độ mới của số liệu.

## **2.2. Kiến trúc và công nghệ phát triển hệ thống thương mại điện tử**

### **2.2.1. Kiến trúc Web Client–Server và REST API (Next.js, React, FastAPI)**

Kiến trúc Client–Server phân tách độc lập giữa tầng giao diện người dùng (Frontend) và tầng xử lý nghiệp vụ (Backend), giao tiếp qua REST API dựa trên định danh tài nguyên và các phương thức HTTP tiêu chuẩn (GET, POST, PUT, PATCH, DELETE). Trong đồ án này, Frontend sử dụng thư viện **React** kết hợp framework **Next.js** để xây dựng giao diện dựa trên các thành phần (components) tái sử dụng, tối ưu hóa định tuyến và kết xuất (rendering) cho cả ba phân hệ: Storefront, Admin và POS [2]. Phía máy chủ sử dụng **FastAPI** (Python) để xây dựng REST API hiệu năng cao, tự động kiểm tra dữ liệu đầu vào (validation), khởi tạo tài liệu chuẩn OpenAPI và đảm nhận toàn bộ nghiệp vụ xác thực, sản phẩm, đơn hàng, tồn kho và giao vận [3].

Trong kiến trúc phân lớp, Frontend tập trung thu thập tương tác và hiển thị trạng thái, còn Backend đóng vai trò chốt chặn bảo mật và thực thi logic cốt lõi. Khi đặt hàng, Client chỉ gửi định danh sản phẩm và số lượng; Backend tự truy vấn kiểm chứng lại đơn giá hiện hành, tồn kho khả dụng và quyền truy cập để đảm bảo tính toàn vẹn cho cả Storefront và POS. Ngoài ra, API được thiết kế tuân thủ chuẩn mã trạng thái HTTP, ẩn cấu trúc nội bộ khi báo lỗi, áp dụng cơ chế chống lặp yêu cầu (idempotency) cho các tác vụ nhạy cảm (khởi tạo đơn hàng, thanh toán) và hỗ trợ xử lý bất đồng bộ cho các tiến trình tốn thời gian.

### **2.2.2. Cơ sở dữ liệu giao dịch OLTP (MySQL, SQLAlchemy)**

Hệ thống xử lý giao dịch trực tuyến (OLTP) phục vụ các tác vụ tần suất cao, đòi hỏi phản hồi tức thời và đảm bảo tính nhất quán dữ liệu theo bốn thuộc tính ACID (Tính nguyên tử, Tính nhất quán, Tính cô lập và Tính bền vững). Đồ án lựa chọn hệ quản trị cơ sở dữ liệu **MySQL** với bộ máy lưu trữ InnoDB nhằm tận dụng khả năng quản lý giao dịch (transaction), khóa cấp độ dòng (row-level locking) và kiểm soát khóa ngoại [4]. Ở tầng ứng dụng Python, thư viện **SQLAlchemy** cung cấp cơ chế ánh xạ đối tượng - quan hệ (ORM) và quản lý vòng đời phiên làm việc (Session) [5].

Lược đồ OLTP áp dụng các dạng chuẩn hóa (Normalization) như tách bảng đơn hàng và chi tiết đơn hàng nhằm triệt tiêu dư thừa dữ liệu và bảo vệ toàn vẹn tham chiếu. Tuy nhiên, cấu trúc phân mảnh này khiến các truy vấn báo cáo đa chiều phải thực hiện nhiều phép kết nối (JOIN) và tổng hợp phức tạp, đòi hỏi phải sao chép dữ liệu sang kiến trúc Lakehouse để tách biệt tải phân tích khỏi giao dịch thời gian thực. Bên cạnh đó, để ngăn chặn xung đột khi nhiều giao dịch cùng đặt mua sản phẩm cuối cùng trong kho (race condition), hệ thống kết hợp các ràng buộc toàn vẹn (tồn kho không âm) với cơ chế khóa bản ghi và quản lý ngữ cảnh giao dịch (Commit/Rollback) chặt chẽ ở tầng ứng dụng [4], [5].

### **2.2.3. Xác thực, phân quyền và bảo mật hệ thống**

Hệ thống tách biệt rõ giữa xác thực danh tính người dùng (Authentication) và phân quyền thao tác (Authorization) dựa trên mô hình kiểm soát truy cập theo vai trò (RBAC) cho bốn nhóm tác nhân: khách hàng, thu ngân POS, quản lý cửa hàng và quản trị viên hệ thống.

Tuân thủ khuyến nghị bảo mật API của OWASP, mọi cơ chế kiểm soát truy cập đều được thực thi tại Backend kết hợp kiểm soát quyền sở hữu ở cấp độ bản ghi (Object-level Authorization) và phạm vi nghiệp vụ [6]. Cụ thể, nhân viên quản lý chỉ xem được báo cáo doanh thu thuộc chi nhánh mình phụ trách, và khách hàng chỉ truy xuất được thông tin đơn hàng thuộc tài khoản của chính mình.

Về bảo mật dữ liệu và quyền riêng tư (Data Privacy), mật khẩu người dùng bắt buộc phải băm (hash) một chiều an toàn tại cơ sở dữ liệu nguồn. Trước khi trích xuất dữ liệu sang tầng phân tích Lakehouse hoặc ghi nhận nhật ký (Logging), hệ thống lọc bỏ hoàn toàn các trường nhạy cảm (chuỗi mật khẩu băm, mã khôi phục, Access Token) và cân nhắc áp dụng kỹ thuật ẩn danh hóa (Anonymization) hoặc giả danh hóa (Pseudonymization) đối với thông tin định danh cá nhân (PII).

## **2.3. Kiến trúc và công nghệ lưu trữ Data Lakehouse**

### **2.3.1. Tổng quan về Data Lakehouse**

Khác với hệ thống OLTP tối ưu cho cập nhật đơn lẻ, các hệ thống phân tích (OLAP) ưu tiên hiệu năng đọc và tổng hợp trên tập dữ liệu lớn. Kế thừa ưu điểm của Kho dữ liệu (Data Warehouse) và Hồ dữ liệu (Data Lake), kiến trúc **Data Lakehouse** kết hợp không gian lưu trữ mở, chi phí thấp của Data Lake với khả năng quản trị siêu dữ liệu, đảm bảo toàn vẹn giao dịch (ACID) và hiệu năng truy vấn mạnh mẽ của Data Warehouse thông qua các định dạng bảng mở (Open Table Format) [7].

Trong đồ án, việc lựa chọn Data Lakehouse xuất phát từ bài toán tích hợp các nguồn dữ liệu không đồng nhất (heterogeneous data): dữ liệu tác nghiệp từ MySQL mang cấu trúc bảng quan hệ cố định; bản tin bắt thay đổi dữ liệu (CDC) có cấu trúc lồng nhau (nested) chứa trạng thái trước/sau cập nhật kèm siêu dữ liệu giao dịch; và nhật ký truy cập (Access Log) ghi nhận luồng hành vi người dùng ở dạng bán cấu trúc (semi-structured). Lakehouse cho phép thu thập nguyên bản toàn bộ các nguồn dữ liệu này về một nền tảng lưu trữ vật lý thống nhất, sau đó làm sạch và chuẩn hóa theo phân lớp để phục vụ báo cáo thông minh (BI), giúp giải phóng OLTP khỏi các truy vấn nặng và cho phép nhiều công cụ tính toán cùng khai thác chung một định dạng bảng mà không cần nhân bản dữ liệu.

### **2.3.2. Kiến trúc dữ liệu Landing – Bronze – Silver – Gold**

Dữ liệu trong Lakehouse được tổ chức theo bốn tầng phân tách rõ ràng dựa trên mức độ xử lý:
- **Tầng Landing:** Tiếp nhận dữ liệu thô nguyên bản từ nguồn, phục vụ đối chiếu trực tiếp và chạy lại tiến trình khi cần thiết.
- **Tầng Bronze:** Lưu trữ bản ghi nguồn hoặc sự kiện thô kèm hệ thống siêu dữ liệu (thời điểm thu thập, loại thao tác `insert/update/delete`, định danh nguồn), bảo toàn lịch sử sự kiện để truy vết lỗi.
- **Tầng Silver:** Thực hiện kiểm tra tính hợp lệ, làm sạch dữ liệu bẩn, khử trùng lặp, chuẩn hóa định dạng và hợp nhất các nguồn dữ liệu phân tán.
- **Tầng Gold:** Xây dựng mô hình dữ liệu chiều (Dimension, Fact), các cấu trúc Data Mart chuyên biệt và tập dữ liệu tổng hợp sẵn sàng phục vụ tính toán KPI.

Kiến trúc phân tầng giúp truy vết nguồn gốc dữ liệu (data lineage) tường minh và cô lập phạm vi ảnh hưởng khi gặp sự cố: nếu phát hiện logic tính KPI sai, hệ thống chỉ cần điều chỉnh và chạy lại tầng Gold từ dữ liệu sạch ở Silver mà không phải thu thập lại từ nguồn. Luồng dữ liệu có tính linh hoạt theo đặc thù kỹ thuật (ví dụ luồng CDC có thể ghi trực tiếp vào Bronze), và độ mới (freshness) giữa các tầng sẽ khác nhau do Bronze cập nhật liên tục còn Silver và Gold vận hành theo lịch định kỳ (batch). Ngoài ra, tùy theo mục đích phân tích vòng đời nghiệp vụ (như đơn hàng chuyển từ hoàn thành sang trả hàng), dữ liệu tại Silver và Gold sẽ được định hình theo mô hình lưu trạng thái hiện tại (Current State) hoặc lưu lịch sử sự kiện (History/SCD).

### **2.3.3. Lưu trữ và quản lý dữ liệu (MinIO, Apache Iceberg, Apache Polaris)**

Hạ tầng lưu trữ và quản trị dữ liệu của hệ thống kết hợp đồng bộ ba thành phần công nghệ cốt lõi:
- **MinIO:** Hệ thống lưu trữ đối tượng (Object Storage) tương thích chuẩn S3, chuyên trách lưu trữ vật lý các tệp dữ liệu (Parquet) và siêu dữ liệu [8].
- **Apache Iceberg:** Định dạng bảng mở (Open Table Format) bổ sung tầng siêu dữ liệu lên trên tệp Parquet nhằm quản lý lược đồ, kiểm soát thay đổi đồng thời (`insert/update/delete`) và duy trì cơ chế Snapshot theo dõi phiên bản bảng [9].
- **Apache Polaris:** Đóng vai trò là Iceberg REST Catalog trung tâm, quản lý tập trung thông tin bảng để các engine tính toán phân tán như Spark, Flink và Trino tương tác liền mạch trên cùng một nền tảng [10], [18].

Về vận hành dài hạn, việc ghi dữ liệu liên tục dễ phát sinh nhiều tệp kích thước nhỏ (*small file problem*) làm tăng chi phí lập kế hoạch truy vấn, đồng thời các Snapshot cũ sẽ gây tốn dung lượng lưu trữ. Do đó, kiến trúc Lakehouse cần tích hợp các tác vụ bảo trì định kỳ như gộp tệp (*compaction*) và dọn dẹp phiên bản cũ (*snapshot expiration*) theo chính sách lưu giữ (*retention policy*) hợp lý, vừa tối ưu hiệu năng vừa đảm bảo khả năng khôi phục dữ liệu khi cần.

### **2.3.4. Mô hình dữ liệu phân tích (Dimension, Fact, Data Mart)**

Tại tầng Gold, mô hình dữ liệu chiều (Dimensional Modeling) được áp dụng với cấu trúc hình sao (Star Schema) nhằm tối ưu hóa hiệu năng cho các truy vấn phân tích BI [11]:
- **Bảng chiều (Dimension):** Chứa các thuộc tính mô tả bối cảnh nghiệp vụ (sản phẩm, cửa hàng, kênh bán hàng, thời gian), sử dụng khóa đại diện (Surrogate Keys) và quy định rõ quy tắc xử lý giá trị khuyết (Unknown/Missing Members).
- **Bảng sự thật (Fact):** Lưu trữ các sự kiện giao dịch hoặc đại lượng định lượng đo lường được (số lượng bán, doanh thu, giá trị hoàn trả). Khi thiết kế bảng Fact, việc xác định rõ mức độ chi tiết (Grain)—ví dụ mỗi bản ghi ứng với đúng một dòng sản phẩm trong đơn hàng—là yếu tố tiên quyết để ngăn chặn tình trạng đếm trùng chỉ số.
- **Data Mart:** Tập hợp các bảng Fact và Dimension được thiết kế hướng đến một nhu cầu phân tích chuyên biệt như bán hàng, tồn kho hoặc hành vi khách hàng.

Bên cạnh giao dịch tài chính, hành vi tương tác trực tuyến trên Storefront (xem sản phẩm, thêm giỏ hàng) được tổ chức thành bảng Fact riêng biệt với mức hạt (Grain) ứng với từng sự kiện. Hệ thống tuyệt đối không kết nối (JOIN) trực tiếp hai bảng Fact khác Grain để tránh làm nhân bản sai lệch số liệu, mà thực hiện đối chiếu thông qua các bảng chiều dùng chung (Conformed Dimensions) như thời gian, sản phẩm và kênh bán hàng.

## **2.4. Công nghệ thu thập và xử lý dữ liệu**

### **2.4.1. Thu thập và xử lý dữ liệu theo lô (Apache Spark)**

Xử lý theo lô (Batch Processing) vận hành trên tập dữ liệu quy mô lớn theo lịch định kỳ. Trong đồ án, **Apache Spark** đóng vai trò là engine tính toán phân tán chủ lực cho toàn bộ luồng Batch nhờ hệ thống API DataFrame, Spark SQL và khả năng kết nối cơ sở dữ liệu quan hệ qua giao thức JDBC [12]. Spark đảm nhận việc trích xuất định kỳ từ MySQL, làm sạch và biến đổi dữ liệu từ tầng Bronze sang Silver, đồng thời xây dựng các bảng Dimension, Fact và Data Mart tại tầng Gold.

Một pipeline Batch chuẩn gồm các bước: đọc dữ liệu nguồn, kiểm tra lược đồ (schema validation), thực hiện các phép biến đổi nghiệp vụ (kết nối bảng đơn hàng và chi tiết, chuẩn hóa mã trạng thái, tính toán chỉ số tài chính) và ghi kết quả theo cơ chế lũy đẳng (idempotent writes) nhằm ngăn chặn trùng lặp bản ghi khi chạy lại tiến trình.

Khi trích xuất dữ liệu từ MySQL, phương pháp đọc toàn bộ bảng (Full Load) chỉ phù hợp với các bảng danh mục nhỏ. Đối với các bảng giao dịch lớn, hệ thống áp dụng phương pháp trích xuất gia tăng (Incremental Load) dựa trên cột thời gian `updated_at` hoặc khóa tuần tự kết hợp cơ chế lưu mốc thời gian đã xử lý (Watermark). Chiến lược này đi kèm phương án xử lý dữ liệu đến muộn (late-arriving data) và kịch bản đối soát định kỳ nhằm nhận diện các thao tác xóa vật lý (hard delete) tại nguồn.

### **2.4.2. Thu thập dữ liệu thay đổi CDC + Access Log (Debezium, Kafka, Flink)**

Để thu thập dữ liệu thời gian thực hướng vào tầng Bronze của Lakehouse, hệ thống kết hợp **Debezium** (chụp ảnh ban đầu và đọc MySQL binlog để bắt thay đổi dữ liệu - CDC) [13], **Apache Kafka** (truyền tải sự kiện phân tán theo Topic và đảm bảo thứ tự trong từng Partition) [14] cùng **Apache Flink** (xử lý luồng có trạng thái và khôi phục lỗi dựa trên Checkpoint) [15] qua hai luồng chính:
- **Luồng CDC ($\text{MySQL} \rightarrow \text{Debezium} \rightarrow \text{Kafka} \rightarrow \text{Flink} \rightarrow \text{Iceberg Bronze}$):** Phản ánh các biến động `INSERT`, `UPDATE`, `DELETE` từ cơ sở dữ liệu. Khi xử lý tại Bronze, hệ thống phải phân biệt rõ sự kiện từ tiến trình đọc Snapshot ban đầu với sự kiện thay đổi thực tế từ binlog để tránh hiểu nhầm thành hai giao dịch độc lập, đồng thời giám sát chặt chẽ độ trễ (binlog lag) và thời gian lưu trữ binlog của MySQL [13].
- **Luồng Access Log ($\text{App} \rightarrow \text{Kafka} \rightarrow \text{Flink} \rightarrow \text{Iceberg Bronze}$):** Ghi nhận sự kiện tương tác người dùng (`view_product`, `add_to_cart`) với cấu trúc chuẩn hóa gồm tên hành động, mốc thời gian, `session_id` và ngữ cảnh đi kèm. Do dữ liệu từ phía trình duyệt (Client-side) có nguy cơ thất lạc hoặc gửi lặp, chúng chỉ phục vụ phân tích hành vi; mọi chỉ số doanh thu bắt buộc phải đối chiếu từ bản ghi giao dịch chính thức tại MySQL.

Trên Kafka, các Topic được gán khóa bản ghi (record key) theo thực thể nghiệp vụ (đơn hàng, sản phẩm) để định tuyến vào cùng một Partition nhằm bảo toàn thứ tự xử lý [14]. Khi tính toán trạng thái tại tầng Silver, hệ thống tiếp tục tích hợp cơ chế chống trùng lặp (de-duplication), loại bỏ thông tin nhạy cảm và sắp xếp lại chuỗi thay đổi dựa trên khóa nghiệp vụ cùng siêu dữ liệu thời gian nguồn.

### **2.4.3. Điều phối Pipeline (Apache Airflow)**

**Apache Airflow** là công cụ điều phối luồng công việc (workflow orchestration) cho phép mô hình hóa chuỗi tác vụ phụ thuộc dưới dạng Đồ thị có hướng không có chu trình (DAG), hỗ trợ lập lịch thực thi, giám sát trạng thái và tự động chạy lại khi gặp sự cố [16].

Trong đồ án, Airflow đóng vai trò điều phối trung tâm cho các pipeline Batch (gọi tác vụ Spark) và kiểm tra chất lượng dữ liệu theo trình tự: kích hoạt trích xuất Batch $\rightarrow$ chờ dữ liệu tại Bronze ghi nhận thành công $\rightarrow$ gọi Spark làm sạch dữ liệu lên Silver $\rightarrow$ xây dựng mô hình tầng Gold $\rightarrow$ thực thi tập lệnh kiểm tra chất lượng. Để cơ chế tự động chạy lại hoạt động an toàn, mọi tác vụ đều phải được thiết kế đạt tính lũy đẳng (idempotent) [16]. Ngoài ra, các DAG cần tích hợp cơ chế kiểm tra điều kiện sẵn sàng của dữ liệu nguồn (sensor/check) thay vì chỉ dựa vào đồng hồ thời gian thực, đồng thời cân đối lịch chạy hợp lý để tối ưu tài nguyên khi các dịch vụ cùng chia sẻ hạ tầng container Docker.

### **2.4.4. Kiểm soát chất lượng dữ liệu và xử lý lỗi**

Chất lượng dữ liệu (Data Quality) trong hệ thống được đánh giá qua bốn tiêu chí: tính đầy đủ (completeness), tính hợp lệ (validity), tính nhất quán (consistency) và tính kịp thời (timeliness) [17], được phân bổ kiểm soát theo từng tầng của Lakehouse:
- **Tầng Bronze:** Kiểm tra cấu trúc lược đồ và khả năng đọc bản ghi thô.
- **Tầng Silver:** Kết hợp kiểm tra kỹ thuật (kiểu dữ liệu, trường bắt buộc `not-null`, tính duy nhất của khóa, định dạng thời gian) và kiểm tra nghiệp vụ (số lượng bán $> 0$, tổng chi tiết khớp tổng đơn hàng, mã trạng thái hợp lệ).
- **Tầng Gold:** Đối chiếu chéo kết quả tổng hợp với dữ liệu nền tảng trên cùng một mốc thời gian, công thức KPI và quy tắc lọc thống nhất.

Các bản ghi không đạt chuẩn sẽ được điều hướng vào vùng cách ly (Quarantine) kèm nguyên nhân chi tiết để gỡ lỗi, hoặc kích hoạt cảnh báo chặn xuất bản dữ liệu lên tầng Gold nếu vi phạm ngưỡng nghiêm trọng [17]. Quy trình đối soát cũng xét đến sự khác biệt ngữ cảnh giữa các tầng (ví dụ: số bản ghi trạng thái hiện tại ở Silver ít hơn tổng sự kiện CDC ở Bronze, và doanh thu hoàn tất ở Gold đã loại trừ đơn hủy/hoàn trả so với tổng tiền đặt hàng ban đầu), đồng thời lưu vết kết quả kiểm thử theo từng lần chạy để dễ dàng truy tìm nguyên nhân sai lệch.

## **2.5. Công nghệ phân tích và trực quan hóa dữ liệu**

### **2.5.1. Truy vấn dữ liệu phân tích (Apache Trino)**

**Apache Trino** là công cụ truy vấn SQL phân tán hiệu năng cao, cho phép đọc và thực thi truy vấn độ trễ thấp trực tiếp trên các bảng dữ liệu tầng Gold thông qua Iceberg Connector, Polaris Catalog và hạ tầng lưu trữ MinIO [18].

Trong kiến trúc hệ thống, ứng dụng Frontend không kết nối trực tiếp đến Trino mà giao tiếp qua lớp Backend API phân tích trung gian. Khi nhận yêu cầu báo cáo, Backend tiến hành xác thực quyền hạn người dùng, kiểm tra tham số đầu vào, biên dịch và gửi câu lệnh SQL tới Trino, sau đó chuẩn hóa kết quả trả về thành cấu trúc JSON [18]. Để tối ưu hiệu năng và chi phí tính toán khi nhiều người dùng truy cập đồng thời, các truy vấn phục vụ Dashboard luôn được giới hạn theo phạm vi thời gian cần thiết và khai thác trực tiếp trên các bảng tổng hợp sẵn (pre-aggregated tables / Data Mart) tại tầng Gold nhằm hạn chế tối đa các phép kết nối bảng (JOIN) phức tạp.

### **2.5.2. Trực quan hóa dữ liệu và thiết kế Dashboard (Apache ECharts)**

Hệ thống sử dụng **Apache ECharts**—thư viện trực quan hóa JavaScript hỗ trợ tương tác mạnh mẽ và tích hợp linh hoạt với React/Next.js—để hiển thị dữ liệu từ Backend API thành các Dashboard quản trị [20]. Thiết kế bố cục Dashboard bám sát nhu cầu từng vai trò, đi từ tổng quan đến chi tiết và chọn loại biểu đồ đúng mục đích: đặt các thẻ KPI tổng quan ở phần đầu, tiếp theo là biểu đồ đường (line chart) thể hiện xu hướng theo thời gian, biểu đồ cột (bar chart) so sánh theo sản phẩm/cửa hàng/kênh bán, và bảng dữ liệu (table) khi cần tra cứu chi tiết [19].

Giao diện Dashboard cung cấp các bộ lọc đồng nhất có giá trị mặc định rõ ràng, hiển thị trạng thái rỗng (empty state) khi không có dữ liệu thay vì số $0$ thiếu ngữ cảnh, đồng thời công bố rõ mốc thời gian cập nhật để người dùng đánh giá đúng độ mới của KPI [19]. Quá trình triển khai BI luôn thực hiện kiểm thử song song giữa cấu hình biểu đồ, quy tắc lọc, đơn vị hiển thị, phân quyền phía Server và độ chính xác của số liệu gốc tại tầng Gold [20].

# **CHƯƠNG 3. PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG**

## **3.1. Phân tích yêu cầu hệ thống**

### **3.1.1. Bối cảnh và phát biểu bài toán**

Hệ thống được thiết kế và xây dựng phục vụ doanh nghiệp bán lẻ thời trang D&K hoạt động theo mô hình bán hàng đa kênh (Omnichannel), kết hợp giữa kênh trực tuyến (Web Storefront) và chuỗi cửa hàng vật lý (POS) [1]. Hoạt động kinh doanh phát sinh khối lượng lớn dữ liệu giao dịch trải rộng trên 28 bảng quan hệ (người dùng, danh mục đa cấp, sản phẩm đa biến thể, kho bãi đa điểm, đơn hàng, hóa đơn POS, thanh toán, vận chuyển, đổi trả, khuyến mãi và đánh giá).

Qua quá trình khảo sát thực tế và phân tích vận hành, hệ thống giải quyết ba bài toán cốt lõi sau:
1. **Tránh suy giảm hiệu năng giao dịch do truy vấn phân tích (OLTP Workload Isolation)**: Việc tính toán các chỉ số kinh doanh (KPI) phức tạp trực tiếp trên cơ sở dữ liệu giao dịch MySQL InnoDB gây nghẽn tài nguyên, gia tăng xung đột khóa dòng/bảng (locking) và làm chậm các thao tác nghiệp vụ thiết yếu của khách hàng lẫn thu ngân [4].
2. **Hợp nhất dữ liệu đa cấu trúc và phân mảnh (Eliminating Data Silos)**: Doanh nghiệp cần phân tích song song giữa dữ liệu giao dịch có cấu trúc chặt chẽ từ cơ sở dữ liệu quan hệ và dữ liệu hành vi người dùng (clickstream, access log) có cấu trúc bán cấu trúc (JSON) với thông lượng lớn từ các dịch vụ web.
3. **Chuẩn hóa tầng dữ liệu ngữ nghĩa (Unified Semantic Layer)**: Các quy tắc nghiệp vụ đặc thù—như tính giá trị tồn kho theo phương pháp bình quân gia quyền di động, kiểm soát rủi ro giao hàng thu tiền hộ (COD), chính sách hoàn trả trong 7 ngày, hay phễu chuyển đổi giỏ hàng—cần được tập trung hóa vào một nguồn chân lý dữ liệu duy nhất (Single Source of Truth).

Để giải quyết triệt để các thách thức trên, giải pháp đặt ra là xây dựng một nền tảng dữ liệu mở (Data Lakehouse) theo kiến trúc Medallion (Landing $\rightarrow$ Bronze $\rightarrow$ Silver $\rightarrow$ Gold) trên nền tảng Apache Iceberg và Apache Polaris Catalog [7], [9], [10]. Nền tảng vừa duy trì vận hành ổn định hệ thống ứng dụng bán lẻ trực tuyến và tại quầy (FastAPI, Next.js, MySQL), vừa xử lý dữ liệu lớn theo luồng (Kafka, Flink) và theo mẻ (Spark, Airflow), phục vụ báo cáo BI qua Trino và ECharts [18], [20].

### **3.1.2. Các tác nhân và phạm vi hệ thống**

#### **a. Các tác nhân hệ thống (Actors)**
Hệ thống xác định 4 nhóm tác nhân chính tham gia tương tác:
* **Khách hàng (Customer)**: Bao gồm khách vãng lai (*Guest*) và khách hàng đã đăng ký/đăng nhập (*Authenticated Customer*). Thực hiện duyệt danh mục sản phẩm, tìm kiếm, quản lý giỏ hàng, đặt hàng trực tuyến, thanh toán, theo dõi vận đơn và gửi yêu cầu hoàn trả.
* **Thu ngân (POS Cashier)**: Nhân viên tại quầy cửa hàng, thực hiện tra cứu sản phẩm, chọn cửa hàng phục vụ, tạo đơn bán lẻ trực tiếp, áp dụng khuyến mãi, ghi nhận thanh toán và in/xuất hóa đơn bán lẻ.
* **Người quản lý nghiệp vụ (Business Managers)**: Tiếp cận các báo cáo BI và công cụ vận hành theo cơ chế phân quyền dựa trên vai trò (RBAC):
  * *Quản lý cửa hàng (`store_manager`)*: Theo dõi doanh thu, dòng tiền ca làm việc và nhân viên tại cửa hàng phụ trách.
  * *Quản lý kinh doanh (`sales_manager`)*: Giám sát toàn diện doanh thu đa kênh, tỷ lệ hủy/boom đơn và hiệu suất đơn hàng.
  * *Quản lý tiếp thị (`marketing_manager`)*: Phân tích lưu lượng truy cập, phễu chuyển đổi giỏ hàng và hiệu quả của các chương trình khuyến mãi.
  * *Quản lý kho (`inventory_manager`)*: Giám sát biến động nhập - xuất - chuyển kho, định giá trị vốn hàng tồn và cảnh báo rủi ro hết hàng.
  * *Quản lý vận hành (`operations_manager`)*: Điều phối quy trình đóng gói, giao vận và thẩm định xử lý hoàn trả hàng.
  * *Quản trị viên (`admin` / `system_admin`)*: Quản lý tài khoản, cấu hình tham số hệ thống và cấp phát quyền hạn.
* **Kỹ sư dữ liệu / Quản trị hạ tầng (Data Engineer / System Operator)**: Vận hành, điều phối các pipeline dữ liệu (Batch ETL, CDC, Stream Ingestion), giám sát chất lượng dữ liệu và sức khỏe hạ tầng.

#### **b. Phạm vi hệ thống (System Scope)**
* **Trong phạm vi (In-Scope)**:
  * Xây dựng trọn vẹn ứng dụng thương mại điện tử (Web Storefront) và phân hệ bán hàng tại quầy (POS) với 28 bảng cơ sở dữ liệu quan hệ chuẩn hóa trên MySQL InnoDB [4].
  * Vận hành mô hình tồn kho 2 cấp (kho tổng trung tâm và chuỗi cửa hàng vật lý) áp dụng công thức giá vốn bình quân gia quyền di động (Moving Weighted Average Cost) cho từng biến thể:
    $$C_{new} = \frac{Q_{current} \times C_{current} + Q_{incoming} \times P_{incoming}}{Q_{current} + Q_{incoming}}$$
  * Kiểm soát rủi ro thanh toán khi nhận hàng (COD): Tự động đánh dấu rủi ro và chặn phương thức COD nếu khách hàng có lịch sử từ chối nhận hàng (boom đơn) từ 3 lần trở lên ($count_{boom} \ge 3$).
  * Quy định thời hạn yêu cầu hoàn trả hàng trực tuyến hợp lệ trong vòng 7 ngày kể từ thời điểm đơn hàng chuyển sang trạng thái đã giao thành công (`delivered`).
  * Xây dựng nền tảng Lakehouse: Thu thập 27 bảng dữ liệu nghiệp vụ (loại trừ bảng chứa thông tin nhạy cảm `customer_credentials`), xử lý luồng nhật ký truy cập (Access Log); xây dựng 6 conformed dimensions, 5 core facts, 4 OLTP data marts, 3 access log data marts và bộ kiểm tra chất lượng tự động 18 chỉ tiêu theo ISO/IEC 25012 [17].
  * Trực quan hóa dữ liệu Dashboard theo vai trò quản trị qua giao diện Next.js tích hợp thư viện Apache ECharts [2], [20].
* **Ngoài phạm vi (Out-of-Scope)**:
  * Không tích hợp cổng thanh toán thực tế trực tiếp với ngân hàng đối tác (sử dụng cổng thanh toán mô phỏng sandbox/mock payment).
  * Không kết nối trực tiếp với phần cứng máy in nhiệt hoặc máy quét mã vạch chuyên dụng tại điểm bán vật lý.
  * Không triển khai các mô hình Machine Learning gợi ý sản phẩm theo thời gian thực (chỉ tập trung vào phân tích mô tả và chẩn đoán kinh doanh).

![Bối cảnh và phạm vi hệ thống](docs/diagram/context.svg)
*Hình 3.0: Bối cảnh, tác nhân và phạm vi hệ thống D&K (docs/diagram/context.svg).*

### **3.1.3. Yêu cầu chức năng**

Yêu cầu chức năng của hệ thống được phân rã theo 3 phân hệ chủ chốt:

#### **a. Phân hệ ứng dụng giao dịch (E-Commerce & POS Application)**
* **FR-APP-01 (Quản lý sản phẩm & danh mục)**: Quản lý danh mục đa cấp, quản lý thông tin sản phẩm và các biến thể chi tiết (SKU) theo kích thước, màu sắc, giá bán, giá vốn và bộ sưu tập ảnh.
* **FR-APP-02 (Giỏ hàng & Đặt hàng trực tuyến)**: Hỗ trợ giỏ hàng theo phiên và tài khoản; kiểm tra số lượng tồn khả dụng (`available_quantity`); áp dụng phiếu giảm giá hợp lệ; tạo đơn hàng và quản lý chuyển đổi trạng thái đơn theo máy trạng thái hữu hạn.
* **FR-APP-03 (Bán lẻ tại quầy POS)**: Tra cứu nhanh sản phẩm qua mã SKU; tạo đơn hàng tại quầy; tự động trừ tồn kho tức thời tại cửa hàng thực hiện giao dịch; hỗ trợ đa phương thức thanh toán.
* **FR-APP-04 (Quản lý kho hàng & điều chuyển)**: Ghi nhận phiếu nhập kho, xuất kho, điều chuyển hàng giữa kho tổng và các cửa hàng; tự động tính lại giá vốn bình quân gia quyền.
* **FR-APP-05 (Thanh toán & Vận chuyển)**: Tiếp nhận thanh toán COD, chuyển khoản mô phỏng; sinh mã vận đơn và cập nhật tiến trình giao hàng theo từng mốc thời gian.
* **FR-APP-06 (Hoàn trả & Đánh giá)**: Tiếp nhận yêu cầu hoàn trả trong hạn 7 ngày; ghi nhận lý do và bằng chứng hình ảnh; cập nhật hoàn tiền và hoàn kho; cho phép khách hàng đánh giá và bình luận sản phẩm đã mua.
* **FR-APP-07 (Quản trị & Phân quyền)**: Xác thực người dùng bằng JWT; phân quyền truy cập chức năng và dữ liệu theo RBAC [6].

#### **b. Phân hệ kỹ thuật dữ liệu (Data Lakehouse Platform)**
* **FR-DE-01 (Thu thập dữ liệu mẻ - Batch Ingestion)**: Airflow điều phối trích xuất định kỳ dữ liệu từ 27 bảng MySQL sang định dạng Parquet trên MinIO Landing, sau đó nạp vào tầng Bronze Iceberg [8], [9], [16].
* **FR-DE-02 (Thu thập dữ liệu thay đổi - CDC Ingestion)**: Debezium bắt sự kiện thay đổi trên MySQL binlog và chuyển tiếp vào Kafka topics tương ứng [13], [14].
* **FR-DE-03 (Thu thập dữ liệu truy cập - Log Ingestion)**: Ghi nhận sự kiện clickstream/HTTP access log từ Storefront vào Kafka; Flink thực hiện chuẩn hóa và ghi liên tục vào Bronze log table [15].
* **FR-DE-04 (Làm sạch & Chuẩn hóa tầng Silver)**: Khử trùng lặp bản ghi (deduplication); chuẩn hóa định dạng thời gian và tiền tệ; giải mã các trường bán cấu trúc JSON; mã hóa một chiều thông tin định danh cá nhân (PII pseudonymization) [6].
* **FR-DE-05 (Mô hình hóa dữ liệu tầng Gold)**: Xây dựng kho dữ liệu theo mô hình hình sao (Star Schema) gồm 6 bảng chiều (`dim_date`, `dim_customer`, `dim_product`, `dim_store`, `dim_order_status`, `dim_device`) và 5 bảng sự kiện (`fact_order_item`, `fact_inventory_daily_snapshot`, `fact_payment`, `fact_return`, `fact_pageview`) [11].
* **FR-DE-06 (Tổng hợp Data Marts)**: Tổng hợp định kỳ 4 marts phân tích nghiệp vụ (`mart_sales_overview`, `mart_product_performance`, `mart_inventory_health`, `mart_customer_behavior`) và 3 marts phân tích hành vi truy cập (`mart_hourly_traffic`, `mart_cart_funnel`, `mart_top_viewed_products`).
* **FR-DE-07 (Kiểm định chất lượng dữ liệu)**: Tự động thực thi bộ kiểm tra 18 chỉ tiêu chất lượng dữ liệu (Data Quality Checks) về tính đầy đủ, tính duy nhất, tính hợp lệ và tính toàn vẹn tham chiếu trước khi công bố dữ liệu lên Data Marts [17].

#### **c. Phân hệ phân tích và báo cáo (BI & Analytics)**
* **FR-BI-01 (Báo cáo doanh thu & bán hàng)**: Cung cấp các chỉ số doanh thu gộp (Gross Revenue), doanh thu thuần (Net Sales), chiết khấu, số lượng đơn hoàn tất và so sánh hiệu suất giữa kênh Web và POS.
* **FR-BI-02 (Báo cáo hiệu quả sản phẩm)**: Thống kê số lượng bán, doanh thu, lợi nhuận gộp theo từng SKU, danh mục, sản phẩm bán chạy nhất (Top Sellers) và tỷ lệ hủy/trả theo dòng sản phẩm.
* **FR-BI-03 (Báo cáo sức khỏe tồn kho)**: Hiển thị giá trị vốn tồn kho toàn hệ thống, số lượng tồn thực tế, tỷ lệ sẵn sàng bán và đưa ra cảnh báo sớm các mặt hàng dưới ngưỡng an toàn.
* **FR-BI-04 (Báo cáo hành vi truy cập & phễu chuyển đổi)**: Trực quan hóa lượng truy cập theo khung giờ, trang xem nhiều nhất và tỷ lệ chuyển đổi qua từng bước trong phễu mua hàng (Xem sản phẩm $\rightarrow$ Thêm giỏ hàng $\rightarrow$ Bắt đầu thanh toán $\rightarrow$ Đặt hàng thành công).

### **3.1.4. Yêu cầu phi chức năng**

Các yêu cầu phi chức năng được xác lập nhằm đảm bảo chất lượng kỹ thuật, tính ổn định và khả năng vận hành lâu dài của hệ thống:

* **NFR-01: Tính nhất quán và toàn vẹn dữ liệu (Data Consistency & Integrity)**:
  * Hệ thống giao dịch đảm bảo tuân thủ đầy đủ thuộc tính ACID trên công cụ lưu trữ MySQL InnoDB [4].
  * Tầng lưu trữ Data Lakehouse đảm bảo tính bất biến của tệp dữ liệu gốc và hỗ trợ giao dịch ACID ở cấp độ bảng thông qua Apache Iceberg v2 kết hợp Apache Polaris REST Catalog [9], [10].
  * Các pipeline ETL/ELT phải đảm bảo tính chất lũy kế vô hại (Idempotency): kết quả dữ liệu tại tầng Silver và Gold không bị nhân bản hay sai lệch khi thực thi lại một tác vụ nhiều lần trên cùng một khoảng thời gian [16].
* **NFR-02: Tính bảo mật và an toàn thông tin (Security & Privacy)**:
  * Áp dụng xác thực không trạng thái (Stateless Authentication) qua JSON Web Token (JWT) và kiểm soát truy cập dựa trên vai trò (RBAC) cho toàn bộ các API quản trị [6].
  * Cách ly dữ liệu nhạy cảm: Tuyệt đối không trích xuất bảng `customer_credentials` vào nền tảng Data Lakehouse.
  * Các thuộc tính định danh cá nhân (PII) như số điện thoại và email khách hàng phải được băm (hashing với Salt) hoặc ẩn danh hóa trước khi đưa vào các bảng chiều phân tích [6].
* **NFR-03: Hiệu năng và khả năng mở rộng (Performance & Scalability)**:
  * Phản hồi API giao dịch: Thời gian đáp ứng của các API duyệt sản phẩm và tạo đơn hàng đạt ngưỡng $P_{95} \le 200\text{ ms}$ ở tải hoạt động tiêu chuẩn [3].
  * Thời gian phản hồi truy vấn phân tích: Các câu truy vấn báo cáo từ Dashboard thông qua Trino trên các bảng Data Mart tầng Gold đạt thời gian phản hồi dưới $2\text{ giây}$ [18].
  * Tối ưu hóa kích thước tệp: Apache Iceberg duy trì kích thước tệp dữ liệu Parquet mục tiêu trong khoảng $128\text{ MiB} - 256\text{ MiB}$, tránh tình trạng phân mảnh tệp nhỏ (Small Files Problem) làm suy giảm hiệu năng đọc [9].
* **NFR-04: Tính sẵn sàng và khả năng chịu lỗi (Availability & Fault Tolerance)**:
  * Toàn bộ hệ thống (dịch vụ ứng dụng, lưu trữ, xử lý luồng, xử lý mẻ, truy vấn) được container hóa độc lập bằng Docker Compose, có chính sách tự khởi động lại khi gặp sự cố (`restart: unless-stopped` hoặc `on-failure`).
  * Hệ thống xử lý luồng Apache Flink kích hoạt cơ chế kiểm tra điểm (Checkpointing) với chu kỳ $10\text{ giây}$, đảm bảo ngữ nghĩa xử lý chính xác một lần (Exactly-Once Semantics) khi có sự cố ngắt quãng [15].
  * Apache Airflow được cấu hình cơ chế tự động thử lại (retry với exponential backoff) và ghi nhận nhật ký lỗi chi tiết cho từng task [16].
* **NFR-05: Khả năng tương tác và tiêu chuẩn mở (Interoperability & Open Architecture)**:
  * Hệ thống sử dụng các chuẩn công nghệ mở công nghiệp: định dạng bảng mở Apache Iceberg, giao thức REST Catalog của Apache Polaris, định dạng lưu trữ cột Parquet trên giao thức tương thích Amazon S3 (MinIO) [8], [9], [10].
  * Tránh ràng buộc nhà cung cấp (Vendor Lock-in), cho phép các công cụ tính toán khác nhau (Apache Spark, Trino, Apache Flink) cùng chia sẻ một không gian siêu dữ liệu và đọc/ghi dữ liệu đồng thời một cách an toàn [7], [18].

## **3.2. Phân tích chức năng và quy trình nghiệp vụ**

### **3.2.1. Sơ đồ Use Case**

Các ca sử dụng của hệ thống được phân rã theo 3 phân hệ độc lập tương ứng với các nhóm tác nhân đã xác định: Phân hệ Khách hàng (Storefront), Phân hệ Quản trị vận hành & Điểm bán (Admin & POS), và Phân hệ Kỹ thuật dữ liệu & Báo cáo BI (Data Engineering & Analytics) [docs/diagram/02-use-cases.drawio](docs/diagram/02-use-cases.drawio).

#### **a. Phân hệ Khách hàng (Storefront Use Cases)**
Tác nhân Khách vãng lai (*Guest*) và Khách hàng đã đăng nhập (*Authenticated Customer*) tương tác với nền tảng thông qua giao diện Web Storefront [2]:
* **Khách vãng lai**: Duyệt danh mục phân cấp, tìm kiếm sản phẩm theo từ khóa/bộ lọc, xem chi tiết biến thể và bảng giá, tra cứu danh sách cửa hàng còn hàng gần nhất theo khu vực, và xem đánh giá công khai.
* **Khách hàng đã đăng nhập**: Quản lý giỏ hàng và danh sách yêu thích (*Wishlist*); thực hiện đặt hàng trực tuyến (*Checkout*); tra cứu trạng thái đơn hàng và lịch sử mua sắm; xác nhận đã nhận hàng (`delivered` $\rightarrow$ `completed`); gửi yêu cầu hoàn trả/đổi hàng trong thời hạn 7 ngày; viết bài đánh giá kèm điểm số xếp hạng cho từng sản phẩm đã mua.

![Use Case — Người mua hàng](docs/diagram/uc-storefront.svg)
*Hình 3.1: Sơ đồ Use Case phân hệ người mua hàng (docs/diagram/uc-storefront.svg).*

#### **b. Phân hệ Quản trị & Bán lẻ tại quầy (Admin & POS Use Cases)**
Hệ thống quản trị áp dụng cơ chế kiểm soát truy cập dựa trên vai trò (RBAC) nghiêm ngặt [6]:
* **Thu ngân / Quản lý cửa hàng (`store_manager`)**: Tra cứu sản phẩm theo mã SKU, chọn cửa hàng phục vụ, tạo đơn hàng bán lẻ tại quầy POS, tự động trừ tồn kho khả dụng tại cửa hàng và xuất hóa đơn bán lẻ [4].
* **Quản lý kho (`inventory_manager`)**: Quản lý sản phẩm, danh mục và các biến thể; lập phiếu nhập kho (Inbound Receipt) và kích hoạt tính toán lại giá vốn bình quân gia quyền di động; điều chuyển hàng hóa giữa các kho.
* **Quản trị viên / Quản lý vận hành (`admin` / `operations_manager`)**: Quản lý vòng đời đơn hàng, phân công nhân sự giao hàng (`delivery_staff`), cập nhật tiến trình vận chuyển, thẩm định và duyệt phiếu hoàn trả hàng kèm hoàn tiền.
* **Quản lý tiếp thị (`marketing_manager`)**: Quản lý chiến dịch khuyến mại, phát hành mã giảm giá (Coupon) và kiểm duyệt nội dung đánh giá sản phẩm.
* **Quản trị hệ thống (`admin`)**: Quản lý tài khoản nhân viên, cấu hình phân quyền và mở lại quyền COD cho khách hàng sau khi đối soát rủi ro.

![Use Case — Quản trị và cửa hàng](docs/diagram/uc-admin.svg)
*Hình 3.2: Sơ đồ Use Case phân hệ quản trị và cửa hàng (docs/diagram/uc-admin.svg).*

#### **c. Phân hệ Kỹ thuật dữ liệu & Báo cáo BI (Data & Analytics Use Cases)**
Phân hệ phục vụ hai nhóm đối tượng: Đội ngũ kỹ sư dữ liệu vận hành nền tảng Lakehouse và các cấp quản lý nghiệp vụ khai thác thông tin phân tích [7], [18]:
* **Kỹ sư dữ liệu (Data Engineer)**: Khởi chạy và giám sát đường ống trích xuất mẻ định kỳ (Batch ETL); kiểm soát luồng thu thập CDC từ MySQL binlog qua Debezium/Kafka/Flink; điều phối dòng Access Log từ Storefront; thực thi kiểm tra chất lượng tự động (Data Quality Gate) và chạy các tác vụ bảo trì định dạng bảng Iceberg (Compaction, Expire Snapshots) [9], [13], [16].
* **Các cấp quản lý nghiệp vụ (Business Managers)**: Tiếp cận báo cáo Dashboard đa chiều được lọc và bảo mật theo vai trò: Executive Dashboard (`admin`), Sales Trend (`sales_manager`), Funnel & Traffic (`marketing_manager`), Store Performance (`store_manager`), Inventory Aging (`inventory_manager`), Logistics & COD Risk (`operations_manager`), và System Reconciliation (`system_admin`).

![Use Case — Data Engineering và BI](docs/diagram/uc-data-bi.svg)
*Hình 3.3: Sơ đồ Use Case phân hệ Data Engineering và BI (docs/diagram/uc-data-bi.svg).*

---

### **3.2.2. Activity Diagram**

Hệ thống được chuẩn hóa dựa trên ba quy trình nghiệp vụ trọng yếu: Quy trình Đặt hàng trực tuyến, Quy trình Bán lẻ tại quầy POS, và Quy trình Tiếp nhận & Xử lý hoàn trả hàng.

#### **a. Quy trình Đặt hàng trực tuyến (Online Checkout Activity)**
Quy trình đặt hàng trực tuyến được thực thi theo mô hình hai pha: Pha thẩm định & kiểm soát rủi ro (Validation & Risk Check) và Pha cam kết giao dịch (Transaction Commit & Allocation) nhằm đảm bảo tính toàn vẹn tuyệt đối của dữ liệu tồn kho và doanh thu [docs/diagram/03-activity-checkout.drawio](docs/diagram/03-activity-checkout.drawio):

1. **Pha thẩm định**: Khách hàng gửi yêu cầu kèm mã bảo vệ `Idempotency-Key`. Hệ thống xác thực danh tính qua JWT và chống giả mạo với CSRF Token. Mở giao dịch, khóa dòng bản ghi khách hàng (`Customer`) bằng cơ chế `SELECT ... FOR UPDATE` [4]. Nếu khách hàng chọn thanh toán COD nhưng cờ `is_cod_blocked = True` (do có số lần từ chối nhận hàng $\ge 3$), hệ thống lập tức từ chối và yêu cầu chuyển sang thanh toán chuyển khoản VietQR. Khóa dòng kiểm tra tồn kho sẵn sàng bán (`available_quantity`) của từng SKU trong kho tổng. Xác thực điều kiện sử dụng mã giảm giá và tính toán số tiền thanh toán cuối cùng.
2. **Pha cam kết**: Khởi tạo bản ghi `orders` (trạng thái ban đầu `pending_payment` hoặc `paid` đối với VietQR), sinh các dòng `order_items` lưu vết ảnh chụp giá bán và giá vốn tại thời điểm giao dịch (`cost_price_snapshot`). Khởi tạo bản ghi thanh toán `payments`. Giảm trừ số lượng tồn kho khả dụng và ghi nhật ký biến động kho `inventory_transactions`. Đóng phiên giỏ hàng hiện tại (`status = closed`) và thực hiện `COMMIT` giao dịch. Nếu xảy ra bất kỳ lỗi hoặc xung đột khóa nào, toàn bộ giao dịch được `ROLLBACK` an toàn [5].

![Activity — Đặt hàng trực tuyến](docs/diagram/activity-checkout-validate.svg)
*Hình 3.4: Sơ đồ hoạt động xác thực yêu cầu đặt hàng (docs/diagram/activity-checkout-validate.svg).*

![Activity — Xử lý đặt hàng](docs/diagram/activity-checkout-commit.svg)
*Hình 3.5: Sơ đồ hoạt động cam kết giao dịch đặt hàng và trừ tồn kho (docs/diagram/activity-checkout-commit.svg).*

#### **b. Quy trình Bán lẻ tại quầy POS (In-store POS Activity)**
Quy trình bán hàng tại quầy được thiết kế tối ưu cho tốc độ và tính tức thời của cửa hàng vật lý [docs/diagram/04-activity-pos.drawio](docs/diagram/04-activity-pos.drawio):
1. Thu ngân xác thực ca làm việc và chọn chi nhánh cửa hàng phụ trách (`store_id`).
2. Nhập hoặc quét mã SKU sản phẩm. Hệ thống truy vấn thông tin sản phẩm và khóa dòng dữ liệu tại bảng `StoreInventory` tương ứng với chi nhánh đó.
3. Kiểm tra số lượng tồn thực tế tại cửa hàng: nếu số lượng yêu cầu vượt quá tồn hiện tại (`on_hand`), hệ thống lập tức thông báo hết hàng tại quầy và gợi ý tra cứu kho tổng hoặc chi nhánh lân cận.
4. Khi khách thanh toán thành công (tiền mặt hoặc quét mã QR), hệ thống tạo đơn hàng với trạng thái hoàn tất tức thì (`status = 'completed'`), thanh toán ghi nhận `status = 'succeeded'`.
5. Tự động trừ số lượng tồn kho của chi nhánh, ghi sổ nhật ký biến động kho với loại giao dịch xuất bán quầy (`outbound_pos`), in hóa đơn bán lẻ và bàn giao hàng cho khách.

![Activity — Bán hàng POS tại cửa hàng](docs/diagram/activity-pos.svg)
*Hình 3.6: Sơ đồ hoạt động bán lẻ tại quầy POS (docs/diagram/activity-pos.svg).*

#### **c. Quy trình Tiếp nhận và Xử lý trả hàng (Returns & Refund Activity)**
Quy trình xử lý hoàn trả hàng được kiểm soát chặt chẽ qua khung thời gian và kiểm định chất lượng sản phẩm thực tế [docs/diagram/05-activity-returns.drawio](docs/diagram/05-activity-returns.drawio):
1. **Khởi tạo yêu cầu**: Khách hàng chỉ có thể tạo yêu cầu trả hàng khi đơn hàng đang ở trạng thái đã giao (`delivered`) hoặc hoàn thành (`completed`), và thời điểm yêu cầu nằm trong khoảng thời gian quy định 7 ngày (`RETURN_WINDOW_DAYS = 7`) kể từ lúc nhận hàng. Số lượng trả cho từng sản phẩm không được vượt quá số lượng đã mua khả hoàn.
2. **Thẩm định ban đầu**: Phiếu trả hàng được khởi tạo với trạng thái chờ duyệt (`pending_review`) kèm ảnh minh chứng và thông tin tài khoản ngân hàng thụ hưởng. Bộ phận quản trị vận hành (`admin` / `operations_manager`) xem xét lý do và phê duyệt (`approved`) hoặc từ chối (`rejected`).
3. **Nhận hàng & Kiểm định (Inspection)**: Khách hàng gửi hàng về kho trung tâm; nhân viên kho cập nhật trạng thái đã nhận kiện hàng (`goods_received`). Tiến hành kiểm định thực tế chất lượng sản phẩm:
   * Nếu sản phẩm đạt tiêu chuẩn hoàn trả (nguyên tem mác, lỗi nhà sản xuất): Cập nhật trạng thái `inspected_passed`, tự động cộng lại tồn kho khả dụng tại kho tổng, tạo giao dịch hoàn tiền (`refunds` liên kết với `payments`).
   * Nếu sản phẩm hư hại do khách hàng sử dụng: Đánh dấu `inspected_failed`, từ chối hoàn kho và không hoàn tiền cho sản phẩm đó.
4. **Đóng đơn hoàn trả**: Đơn hàng ban đầu chỉ chuyển sang trạng thái đã hoàn trả (`status = 'returned'`) khi toàn bộ các sản phẩm trong đơn đã được xử lý hoàn tất và đạt kiểm định trả hàng.

![Activity — Trả hàng và hoàn tiền](docs/diagram/activity-returns.svg)
*Hình 3.7: Sơ đồ hoạt động tiếp nhận và xử lý trả hàng (docs/diagram/activity-returns.svg).*

---

### **3.2.3. Sequence Diagram**

Để mô tả sự tương tác chi tiết theo thời gian giữa các thành phần phần mềm, hai biểu đồ tuần tự tiêu biểu được thiết kế: Tuần tự Đặt hàng trực tuyến (xử lý giao dịch ACID phía Backend) và Tuần tự Tải báo cáo BI theo vai trò (truy vấn kết hợp Lakehouse và OLTP).

#### **a. Biểu đồ tuần tự Đặt hàng trực tuyến (Online Checkout Sequence)**
Biểu đồ mô tả sự phối hợp giữa Client Browser, API Router, Checkout Service, Transaction Manager (Unit of Work), các Repositories và Cơ sở dữ liệu MySQL [docs/diagram/06-sequence-checkout.drawio](docs/diagram/06-sequence-checkout.drawio):

![Sequence — Checkout thành công](docs/diagram/seq-checkout.svg)
*Hình 3.8: Sơ đồ tuần tự đặt hàng trực tuyến thành công (docs/diagram/seq-checkout.svg).*

#### **b. Biểu đồ tuần tự Tải Dashboard BI theo vai trò với cơ chế Fallback (Role-based Dashboard Query Sequence)**
Biểu đồ thể hiện cơ chế phục vụ dữ liệu phân tích thông minh: định tuyến quyền truy cập tại API Layer, truy vấn tầng Gold Lakehouse thông qua Trino, và tự động chuyển đổi dự phòng (Graceful Degradation / OLTP Fallback) sang MySQL khi Trino gặp sự cố [docs/diagram/07-sequence-dashboard.drawio](docs/diagram/07-sequence-dashboard.drawio):

![Sequence — Đọc KPI theo vai trò](docs/diagram/seq-dashboard.svg)
*Hình 3.9: Sơ đồ tuần tự đọc KPI Dashboard theo vai trò với cơ chế Fallback (docs/diagram/seq-dashboard.svg).*

## **3.3. Thiết kế kiến trúc tổng thể**

### **3.3.1. Kiến trúc tổng thể hệ thống**

Hệ thống được thiết kế theo mô hình kiến trúc lai hợp nhất (Enterprise Hybrid Platform) kết hợp chặt chẽ giữa hai trụ cột: Phân hệ ứng dụng giao dịch thương mại điện tử đa kênh (Online & POS OLTP) và Phân hệ dữ liệu lớn mở (Modern Data Lakehouse) [docs/diagram/08-system-architecture.drawio](docs/diagram/08-system-architecture.drawio). Mô hình này giải quyết triệt để sự đánh đổi truyền thống giữa tốc độ giao dịch thời gian thực và năng lực phân tích báo cáo chuyên sâu.

![Kiến trúc tổng thể D&K](docs/diagram/architecture-system.svg)
*Hình 3.10: Kiến trúc tổng thể hệ thống D&K (docs/diagram/architecture-system.svg).*

Kiến trúc tổng thể được cấu thành từ ba phân lớp chức năng rõ ràng:

1. **Khối Ứng dụng giao dịch (Transactional Application Tier)**:
   * **Giao diện đa kênh (Client Interfaces)**: Phát triển trên nền tảng Next.js 15 kết hợp React 19 [2], cung cấp giao diện Storefront cho khách hàng duyệt hàng/đặt hàng trực tuyến, giao diện POS bán hàng nhanh tại quầy cho thu ngân, và bảng điều khiển quản trị tổng thể (Admin Panel).
   * **Tầng dịch vụ ứng dụng (FastAPI Backend)**: Giao tiếp qua chuẩn REST/JSON không trạng thái [3]. Phụ trách xác thực phiên làm việc, phân quyền RBAC [6], thực thi nghiệp vụ bán hàng, quản lý đơn hàng, điều phối giao vận và kiểm soát rủi ro COD.
   * **Cơ sở dữ liệu vận hành (Operational Database)**: Sử dụng hệ quản trị MySQL 8.4 với công cụ lưu trữ InnoDB [4], lưu trữ 28 bảng quan hệ chuẩn hóa cao nhằm đảm bảo tính toàn vẹn giao dịch (ACID) và hiệu năng ghi tối đa qua cơ chế khóa dòng (Row-level Locking) và MVCC.

2. **Khối Nền tảng Dữ liệu Lakehouse (Lakehouse Core Tier)**:
   * **Thu thập dữ liệu thời gian thực (Real-time Stream Ingestion)**:
     * *Luồng thay đổi dữ liệu (CDC)*: Debezium MySQL Connector [13] lắng nghe trực tiếp từ MySQL binary log (binlog) ở định dạng bản ghi hàng chi tiết (`ROW`), chuyển tiếp các sự kiện thay đổi (`INSERT`, `UPDATE`, `DELETE`) vào cụm Apache Kafka [14].
     * *Luồng nhật ký truy cập (Access Log)*: Middleware tích hợp trên FastAPI thu thập toàn bộ sự kiện truy cập HTTP (clickstream) và phát tán trực tiếp vào Kafka topic tương ứng.
     * *Động cơ xử lý luồng*: Apache Flink 1.19 [15] tiêu thụ liên tục các dòng dữ liệu từ Kafka, thực hiện chuẩn hóa và nạp dữ liệu vào các bảng Apache Iceberg tương ứng với cơ chế bảo vệ kiểm tra điểm (Checkpointing) chu kỳ 10 giây.
   * **Thu thập và xử lý theo mẻ (Batch Processing & Orchestration)**:
     * Apache Airflow 2.10 [16] điều phối định kỳ các pipeline dữ liệu theo lịch trình và thứ tự phụ thuộc.
     * Apache Spark 3.5 [12] trích xuất mẻ định kỳ từ 27 bảng nghiệp vụ MySQL qua JDBC sang vùng lưu trữ trung gian (Landing Parquet) trên MinIO, sau đó thực hiện các biến đổi phức tạp, khử trùng lặp và làm giàu dữ liệu để nạp vào các tầng Bronze, Silver và Gold.
   * **Hạ tầng lưu trữ và quản trị bảng mở (Storage & Open Table Format)**:
     * MinIO Object Storage [8] cung cấp kho lưu trữ đối tượng tương thích chuẩn Amazon S3 API, đóng vai trò là kho dữ liệu thô và kho lưu trữ tệp dữ liệu phân tích Parquet.
     * Apache Iceberg v2 [9] định nghĩa cấu trúc bảng mở, quản lý cây snapshot, hỗ trợ tính năng time-travel, và bảo đảm tính chất ACID cho toàn bộ các thao tác ghi/đọc dữ liệu lớn.
     * Apache Polaris Catalog [10] đóng vai trò là máy chủ REST Catalog tập trung, sử dụng PostgreSQL nội bộ để quản trị siêu dữ liệu, phân quyền truy cập danh tính workload độc lập và cô lập tài nguyên lưu trữ.

3. **Khối Phân tích và Phục vụ (Analytics & Serving Tier)**:
   * **Động cơ truy vấn SQL phân tán (MPP Engine)**: Trino 483 [18] đóng vai trò là công cụ tính toán phân tán hiệu năng cao, đọc siêu dữ liệu từ Polaris Catalog và trực tiếp quét các tệp dữ liệu Parquet của Iceberg trên MinIO để phục vụ các truy vấn phân tích tổng hợp phức tạp với độ trễ thấp ($< 2\text{s}$).
   * **Cổng phục vụ phân tích (Analytics API & Semantic Serving)**: Tầng API của FastAPI tiếp nhận yêu cầu từ Dashboard quản trị, thẩm định quyền truy cập RBAC, thực thi truy vấn tới Trino trên các bảng Data Mart tầng Gold, và cung cấp cơ chế tự động chuyển đổi dự phòng (Graceful Degradation / OLTP Fallback) sang MySQL khi Trino gián đoạn [19].
   * **Trực quan hóa dữ liệu (BI Dashboard Hub)**: Tích hợp thư viện Apache ECharts [20] trên giao diện Next.js, hiển thị các biểu đồ tương tác, phễu chuyển đổi và chỉ số KPI kinh doanh trực quan cho các cấp quản lý nghiệp vụ.

---

### **3.3.2. Kiến trúc hệ thống thương mại điện tử**

Phân hệ thương mại điện tử và điểm bán được kiến trúc theo mô hình phân tầng chặt chẽ (Layered Architecture), tách biệt rõ ràng giữa tầng giao diện hiển thị, tầng điều phối định tuyến, tầng logic nghiệp vụ cốt lõi và tầng quản lý giao dịch bền vững [docs/diagram/09-web-architecture.drawio](docs/diagram/09-web-architecture.drawio).

![Kiến trúc website thương mại điện tử](docs/diagram/architecture-web.svg)
*Hình 3.11: Thiết kế kiến trúc phân tầng hệ thống thương mại điện tử (docs/diagram/architecture-web.svg).*

Chi tiết trách nhiệm và sự liên kết giữa các tầng thành phần:

1. **Tầng Giao diện người dùng (Presentation Layer)**:
   * Được xây dựng trên nền tảng Next.js 15 (React 19) [2] theo mô hình App Router, tối ưu hóa quá trình kết xuất phía máy chủ (Server-Side Rendering - SSR) cho các trang danh mục công khai và kết xuất phía máy khách (Client-Side Rendering - CSR) cho các trang giỏ hàng, đặt hàng và thanh toán tương tác cao.
   * Phân tách hai giao diện độc lập: Storefront phục vụ người mua hàng trực tuyến và Admin/POS phục vụ nhân viên cửa hàng, quản trị viên vận hành và người dùng phân tích BI.
   * Giao tiếp hoàn toàn với tầng ứng dụng Backend thông qua các HTTP API theo giao thức RESTful chuẩn hóa; không cho phép Client kết nối trực tiếp vào cơ sở dữ liệu MySQL hay các dịch vụ lưu trữ nội bộ.

2. **Tầng Điều phối và Bảo mật (Router, Authentication & RBAC Layer)**:
   * Triển khai bằng FastAPI [3], áp dụng cơ chế tiêm phụ thuộc (Dependency Injection) để thẩm định xác thực và kiểm soát quyền truy cập trước khi chuyển giao yêu cầu cho tầng nghiệp vụ:
     * *Xác thực danh tính*: Sử dụng JSON Web Token (JWT) được bảo vệ trong HttpOnly Cookie nhằm triệt tiêu nguy cơ bị đánh cắp qua tấn công XSS [6].
     * *Chống giả mạo yêu cầu (CSRF Protection)*: Triển khai kỹ thuật Double-Submit CSRF Cookie Token cho toàn bộ các phương thức thay đổi trạng thái (`POST`, `PUT`, `DELETE`, `PATCH`).
     * *Phân quyền truy cập theo vai trò (RBAC)*: Bộ phụ thuộc `require_role` xác minh quyền hạn của tài khoản so với vai trò được định cấu hình cho endpoint nghiệp vụ (`admin`, `store_manager`, `inventory_manager`, `marketing_manager`, `operations_manager`).

3. **Tầng Nghiệp vụ ứng dụng (Domain Service Layer)**:
   * Các dịch vụ nghiệp vụ được module hóa theo từng phạm vi bài toán chuyên biệt: Quản lý danh mục & sản phẩm (`catalog`), Giỏ hàng & Danh sách yêu thích (`cart`, `wishlist`), Đặt hàng & Báo giá (`checkout`), Quản lý vòng đời đơn hàng (`orders`), Bán lẻ tại quầy (`pos`), Nhập kho & Giá vốn (`inbound`), Giao vận (`logistics`), Đổi trả hàng (`returns`), Khuyến mại (`coupons`), và Đánh giá sản phẩm (`reviews`).
   * Tầng nghiệp vụ chứa toàn bộ các quy tắc logic trọng yếu: thuật toán tính giá vốn bình quân gia quyền di động, kiểm tra hạn mức và chặn phương thức COD khi số lần từ chối nhận hàng vượt ngưỡng ($count \ge 3$), kiểm tra cửa sổ trả hàng trong hạn 7 ngày, và kiểm tra tính hợp lệ của mã giảm giá.

4. **Tầng Quản lý giao dịch và Lưu trữ (Persistence & Unit of Work Layer)**:
   * Sử dụng SQLAlchemy 2.0 [5] làm công cụ ánh xạ quan hệ đối tượng (ORM) tương tác với cơ sở dữ liệu MySQL InnoDB.
   * Áp dụng mẫu thiết kế Unit of Work thông qua hàm tiện ích `run_in_transaction` (`app/db/uow.py`). Toàn bộ các thao tác ghi dữ liệu đa bảng trong quy trình Đặt hàng, Bán hàng POS và Trả hàng đều được gói gọn trong một Transaction ngữ cảnh duy nhất:
     * Thiết lập cơ chế tự động thử lại (Retry Mechanism) khi phát hiện tranh chấp khóa hoặc deadlock từ hệ thống cơ sở dữ liệu (`pymysql.constants.CR.CR_SERVER_LOST`, `1213 Deadlock`).
     * Áp dụng câu lệnh khóa chọn lọc `SELECT ... FOR UPDATE` trên các bảng tài nguyên có tính tranh chấp cao như `customers`, `inventories` (kho tổng) và `store_inventories` (kho chi nhánh) nhằm loại trừ triệt để tình trạng Race Condition và bán vượt quá tồn kho (Overselling) [4].

5. **Tích hợp Dữ liệu và Nhật ký truy cập (Event & Log Integration)**:
   * *FastAPI Analytics Router*: Cung cấp các endpoint phục vụ dữ liệu báo cáo cho BI Hub (`/api/v1/admin/analytics/*`), thực hiện chuyển tiếp truy vấn tới Trino Engine và hỗ trợ dự phòng linh hoạt sang MySQL khi Trino bị suy giảm hiệu năng.
   * *Access Log Middleware*: Bắt chặn các request HTTP đến hệ thống (loại bỏ các tuyến tĩnh và kiểm tra sức khỏe), trích xuất thông tin định danh phiên, IP, User-Agent, đường dẫn và thời gian phản hồi, sau đó đóng gói payload JSON và phát tán bất đồng bộ vào Kafka topic `ecommerce.access-logs`.

---

### **3.3.3. Kiến trúc nền tảng Data Lakehouse và BI**

Nền tảng Data Lakehouse được thiết kế dựa trên nguyên lý cốt lõi: **Tách biệt hoàn toàn giữa Năng lực tính toán (Compute) và Tầng lưu trữ (Storage)** [7], giải phóng hệ thống khỏi các rào cản về khả năng mở rộng độc lập và phụ thuộc công nghệ độc quyền (Vendor Lock-in) [docs/diagram/10-lakehouse-architecture.drawio](docs/diagram/10-lakehouse-architecture.drawio).

![Kiến trúc nền tảng Lakehouse và BI](docs/diagram/architecture-lakehouse.svg)
*Hình 3.12: Thiết kế kiến trúc nền tảng Data Lakehouse và phục vụ BI (docs/diagram/architecture-lakehouse.svg).*

Chi tiết các thành phần hạ tầng và cơ chế tương tác:

1. **Tầng Lưu trữ đối tượng tập trung (Object Storage Tier)**:
   * Triển khai MinIO Object Storage [8] cung cấp hệ thống lưu trữ phân tán hiệu năng cao tương thích hoàn toàn chuẩn Amazon S3 API.
   * Cấu trúc bucket `lakehouse` được tổ chức thành các không gian phân vùng rõ rệt:
     * `s3://lakehouse/landing/`: Lưu trữ các tệp trích xuất Parquet thô từ MySQL và các tệp JSONL nhật ký truy cập lịch sử.
     * `s3://lakehouse/warehouse/`: Không gian lưu trữ chính của định dạng bảng Apache Iceberg, bao gồm các tệp dữ liệu dạng cột Parquet (data files), tệp xóa vị trí/định danh (delete files), các tệp chỉ mục danh mục (manifest files), danh sách chỉ mục (manifest lists) và tệp mô tả siêu dữ liệu (metadata JSON files).
     * `s3://lakehouse/cursors/`: Lưu trữ vị trí con trỏ đồng bộ dữ liệu tăng dần (Incremental Checkpoint Cursors) của các pipeline ETL/ELT.

2. **Tầng Quản trị siêu dữ liệu mở (Open Metadata & REST Catalog Tier)**:
   * **Apache Iceberg v2 [9]**: Cung cấp định dạng bảng phân tích mở hỗ trợ đầy đủ ngữ nghĩa giao dịch ACID ở cấp độ bảng thông qua kỹ thuật ghi nhận snapshot nguyên tử (Atomic Snapshot Isolation). Định dạng bảng này hỗ trợ các tính năng hiện đại: tiến hóa cấu trúc bảng an toàn (Schema Evolution mà không cần ghi lại dữ liệu cũ), phân vùng ẩn (Hidden Partitioning giúp loại trừ sai sót khi truy vấn), và truy vấn lịch sử dữ liệu (Time-Travel).
   * **Apache Polaris Catalog [10]**: Đóng vai trò là Catalog điều phối trung tâm tuân theo đặc tả chuẩn mở Iceberg REST Catalog Specification. Polaris duy trì trạng thái siêu dữ liệu bảng trong cơ sở dữ liệu quan hệ PostgreSQL nội bộ, giúp các công cụ xử lý khác nhau (Spark, Flink, Trino) luôn nhìn thấy một trạng thái dữ liệu đồng nhất và tức thời.

3. **Cơ chế Phân quyền danh tính Workload (Workload RBAC) trên Polaris**:
   Hệ thống thiết lập các vai trò ủy quyền chi tiết (`infrastructure/polaris/rbac.yml`) nhằm phân lập ranh giới an toàn cho từng công cụ tính toán:
   * `spark_writer`: Cấp phát quyền tạo bảng, cập nhật cấu trúc schema, ghi đè và commit snapshot cho các tiến trình xử lý mẻ Apache Spark [12].
   * `flink_writer`: Cấp quyền ghi nối tiếp (append) liên tục các sự kiện theo luồng cho Apache Flink [15].
   * `trino_reader`: Cấp quyền chỉ đọc (read-only) trên siêu dữ liệu và tệp dữ liệu, phục vụ các truy vấn phân tích SQL tương tác của người dùng cuối [18].
   * `trino_admin`: Cấp quyền quản trị và thực thi các truy vấn đối soát nâng cao cho người quản trị hệ thống.

4. **Tầng Động cơ tính toán phân tán (Compute Engines Tier)**:
   * **Apache Airflow 2.10 [16]**: Đóng vai trò là bộ não điều phối lịch trình, quản lý luồng phụ thuộc DAG, kích hoạt các tiến trình Spark, theo dõi lỗi và kích hoạt cơ chế retry tự động.
   * **Apache Spark 3.5 [12]**: Động cơ tính toán phân tán trên bộ nhớ RAM, đảm nhiệm các tác vụ Batch nặng: trích xuất dữ liệu mẻ, chuyển đổi dữ liệu phức tạp giữa các tầng Bronze/Silver/Gold, thực thi `MERGE INTO`, tính toán các bảng chiều (Dimensions), bảng sự kiện (Facts), tổng hợp Data Marts và thực thi bộ kiểm tra chất lượng dữ liệu (Quality Gates).
   * **Apache Flink 1.19 [15]**: Động cơ tính toán luồng có trạng thái (Stateful Stream Processing), đảm nhiệm việc tiêu thụ liên tục các dòng sự kiện từ Kafka (CDC và Access Log), áp dụng cơ chế Checkpointing 10 giây để đảm bảo ngữ nghĩa xử lý chính xác một lần (Exactly-Once Semantics), và ghi trực tiếp vào các bảng Iceberg tương ứng.
   * **Trino 483 [18]**: Động cơ truy vấn SQL phân tán kiến trúc MPP (Massively Parallel Processing). Trino kết nối trực tiếp với Polaris Catalog và MinIO, tối ưu hóa các kế hoạch truy vấn SQL phân tích, bỏ qua các tệp không chứa dữ liệu cần tìm thông qua chỉ mục min/max của Iceberg (Data Skipping), mang lại tốc độ truy vấn vượt trội cho các ứng dụng BI.

5. **Tầng Phục vụ và Trực quan hóa dữ liệu (Serving & Visualization Tier)**:
   * **FastAPI Analytics Service**: Đóng vai trò là tầng ngữ nghĩa trung gian (Semantic Layer). Thay vì để tầng Client kết nối trực tiếp vào Trino, API Service chịu trách nhiệm thẩm định vai trò người dùng (RBAC), gắn thêm các bộ lọc phạm vi chi nhánh (`store_id`), biên dịch yêu cầu thành các câu lệnh SQL tối ưu tới Trino, và định dạng kết quả trả về tương thích với biểu đồ hiển thị [19].
   * **BI Hub (Apache ECharts)**: Ứng dụng bảng điều khiển quản trị trên Next.js [2], [20], trực quan hóa các bộ chỉ số kinh doanh thành các biểu đồ đường xu hướng doanh thu, biểu đồ cột so sánh kênh bán, phễu chuyển đổi giỏ hàng và bảng đối soát chất lượng dữ liệu.

---

### **3.3.4. Luồng dữ liệu và tương tác giữa các thành phần**

Nền tảng tích hợp ba luồng vận chuyển và tương tác dữ liệu độc lập nhưng bổ trợ chặt chẽ cho nhau: Luồng Batch OLTP, Luồng CDC OLTP và Luồng Access Log [docs/diagram/11-data-ingestion.drawio](docs/diagram/11-data-ingestion.drawio).

#### **a. Luồng trích xuất và xử lý dữ liệu mẻ (Batch OLTP Ingestion Flow)**
Luồng xử lý mẻ chịu trách nhiệm trích xuất định kỳ toàn bộ dữ liệu nghiệp vụ có cấu trúc từ 27 bảng quan hệ MySQL (loại trừ bảng nhạy cảm `customer_credentials`) để xây dựng kho dữ liệu phân tích chuẩn hóa theo kiến trúc Medallion [docs/diagram/11-data-ingestion.drawio](docs/diagram/flow-batch.svg).

![Luồng Batch OLTP](docs/diagram/flow-batch.svg)
*Hình 3.13: Luồng thu thập và xử lý dữ liệu mẻ Batch OLTP (docs/diagram/flow-batch.svg).*

Quy trình thực thi chi tiết bao gồm 7 giai đoạn tuần tự:
1. **Trích xuất tăng dần (Incremental Extraction)**: DAG `lakehouse_oltp_pipeline` trên Apache Airflow được kích hoạt định kỳ vào lúc 02:00 sáng hàng ngày (giờ Việt Nam). Tác vụ khởi động Spark Job đọc dữ liệu từ MySQL qua kết nối JDBC. Sử dụng cơ chế con trỏ tăng dần (Incremental Cursor) dựa trên mốc thời gian cập nhật `updated_at` hoặc `created_at` của từng bảng (với khoảng thời gian đối soát an toàn lookback window 3 ngày), chỉ trích xuất các bản ghi mới hoặc có biến động kể từ mốc commit trước đó [12], [16].
2. **Ghi nhận vùng Landing**: Dữ liệu trích xuất từ MySQL được nạp nguyên trạng ra các tệp định dạng Parquet tại vùng lưu trữ tạm `s3://lakehouse/landing/oltp/<table>/<batch_id>/` trên MinIO. Đồng thời, một tệp mô tả manifest JSON được khởi tạo ghi nhận số lượng dòng dữ liệu, kích thước và mã băm kiểm tra (Checksum) nhằm đảm bảo tệp không bị lỗi trong quá trình truyền tải.
3. **Nạp tầng Bronze (Raw Append)**: Spark đọc các tệp Parquet từ Landing và thực hiện thao tác nạp nối tiếp (Append-only) vào các bảng Bronze Iceberg tương ứng (`lakehouse.bronze.<table_name>`). Tại tầng này, cấu trúc bảng được giữ nguyên vẹn như nguồn, đồng thời bổ sung các trường siêu dữ liệu truy vết nguồn gốc (Data Lineage Metadata): `_ingested_at` (thời điểm nạp) và `_source_file` (đường dẫn tệp Landing nguồn) [9].
4. **Cam kết con trỏ (Commit Cursor)**: Sau khi toàn bộ 27 bảng Bronze được ghi và commit snapshot thành công trên Iceberg, Airflow tiến hành lưu mốc con trỏ thời gian mới nhất vào MinIO (`s3://lakehouse/cursors/oltp/<table>.json`). Quy trình cam kết sau Bronze đảm bảo tính lũy kế vô hại (Idempotency): nếu tiến trình gặp sự cố ở các tầng sau, pipeline có thể phục hồi trực tiếp từ dữ liệu Bronze đã ghi mà không phải trích xuất lại từ cơ sở dữ liệu nguồn MySQL [16].
5. **Làm sạch và Chuẩn hóa tầng Silver (Cleanse & MERGE)**: Spark thực thi các biến đổi nghiệp vụ trên dữ liệu Bronze:
   * Khử trùng lặp bản ghi (Deduplication) dựa trên khóa chính nghiệp vụ và mốc thời gian cập nhật mới nhất.
   * Chuẩn hóa múi giờ sang UTC, chuyển đổi các trường tiền tệ sang số nguyên `bigint` (đơn vị VNĐ), giải mã các trường bán cấu trúc JSON (như thuộc tính sản phẩm, hình ảnh).
   * Mã hóa bảo vệ quyền riêng tư (PII Pseudonymization): Áp dụng thuật toán băm bảo mật SHA-256 có thêm chuỗi muối (Salt) cho số điện thoại và địa chỉ email khách hàng [6].
   * Thực thi câu lệnh `MERGE INTO` để cập nhật trạng thái mới nhất của các thực thể vào bảng Silver (`SCD Type 1`).
6. **Đối soát dữ liệu nguồn - đích (Reconciliation Gate)**: Spark tự động thực hiện phép kiểm tra đối soát chéo (Reconciliation Check) giữa dữ liệu gốc trên MySQL và dữ liệu tại tầng Silver: so sánh tổng số lượng bản ghi và tổng giá trị các trường tiền tệ trọng yếu (tổng tiền đơn hàng, giá trị thanh toán). Nếu tỷ lệ sai lệch vượt ngưỡng cho phép ($\text{variance} > 1\%$), pipeline lập tức phát tín hiệu cảnh báo và dừng tiến trình.
7. **Mô hình hóa tầng Gold & Kiểm tra chất lượng (Gold Marts & Quality Gate)**:
   * Spark thực hiện chuyển đổi dữ liệu từ Silver sang mô hình hình sao (Star Schema), xây dựng 6 bảng chiều (Conformed Dimensions) và 5 bảng sự kiện (Core Facts) [11].
   * Từ các bảng Fact và Dimension, Spark tự động tổng hợp trước dữ liệu thành 4 bảng Data Mart phục vụ nghiệp vụ bán hàng, hiệu suất sản phẩm, tồn kho và hành vi khách hàng.
   * Kích hoạt bộ kiểm định chất lượng dữ liệu tự động (Quality Gate) gồm 18 chỉ tiêu theo chuẩn ISO/IEC 25012 [17]. Kết quả kiểm tra được ghi vào bảng `lakehouse.system.data_quality_results`. Nếu phát hiện lỗi vi phạm nghiêm trọng (khóa chính trùng lặp, giá trị doanh thu âm bất thường), tác vụ sẽ đánh dấu thất bại và ngăn chặn việc công bố dữ liệu lên Dashboard.

#### **b. Luồng thu thập dữ liệu thay đổi (CDC OLTP Ingestion Flow)**
Luồng CDC được thiết kế nhằm bắt trọn vẹn toàn bộ lịch sử biến động dữ liệu giao dịch theo thời gian thực mà không gây ảnh hưởng đến hiệu năng truy vấn của MySQL [docs/diagram/11-data-ingestion.drawio](docs/diagram/flow-cdc.svg).

![Luồng CDC OLTP](docs/diagram/flow-cdc.svg)
*Hình 3.14: Luồng thu thập dữ liệu thay đổi CDC OLTP (docs/diagram/flow-cdc.svg).*

Quy trình vận hành:
1. **Lắng nghe Binary Log**: Cơ sở dữ liệu MySQL được cấu hình kích hoạt `binlog_format = ROW` và `binlog_row_image = FULL`. Debezium MySQL Connector [13] hoạt động như một máy khách sao chép (Replication Client), kết nối trực tiếp vào MySQL binlog và ghi nhận liên tục từng thao tác ghi dữ liệu (`INSERT`, `UPDATE`, `DELETE`) trên 27 bảng quan hệ.
2. **Xuất bản vào Apache Kafka**: Debezium đóng gói mỗi thay đổi thành một thông điệp sự kiện JSON chuẩn hóa (chứa ảnh chụp trạng thái trước thay đổi `before`, trạng thái sau thay đổi `after`, loại thao tác `op`, và mốc thời gian giao dịch) và đẩy vào các topic tương ứng trên Apache Kafka (`cdc.ecommerce.<table>`) [14].
3. **Tiêu thụ và Nạp bảng Iceberg qua Apache Flink**: Job xử lý luồng Flink CDC (`flink_cdc_stream`) liên tục tiêu thụ các thông điệp từ Kafka topics. Flink tiến hành chuẩn hóa cấu trúc dữ liệu và thực hiện ghi nối tiếp (append-only) vào bảng `lakehouse.bronze.oltp_cdc_events` trên Apache Iceberg [15].
4. **Bảo toàn lịch sử giao dịch (Audit Trail & Replay)**: Bảng `bronze.oltp_cdc_events` đóng vai trò là kho lưu trữ lịch sử bất biến ghi nhận mọi diễn biến của dữ liệu giao dịch. Khác với luồng Batch (chỉ giữ trạng thái mới nhất tại Silver qua `MERGE`), luồng CDC bảo toàn toàn bộ các trạng thái trung gian, cho phép tái hiện lại chính xác lịch sử hệ thống tại bất kỳ thời điểm nào trong quá khứ phục vụ mục đích kiểm toán và đối soát dữ liệu.

#### **c. Luồng thu thập và xử lý nhật ký truy cập (Access Log Streaming Ingestion Flow)**
Luồng Access Log được thiết kế chuyên biệt để xử lý dữ liệu hành vi người dùng (clickstream, request HTTP) có tần suất phát sinh lớn và tính chất bán cấu trúc [docs/diagram/11-data-ingestion.drawio](docs/diagram/flow-access-log.svg).

![Luồng Access Log](docs/diagram/flow-access-log.svg)
*Hình 3.15: Luồng thu thập và xử lý dòng nhật ký truy cập Access Log (docs/diagram/flow-access-log.svg).*

Quy trình xử lý theo thời gian thực và tổng hợp mẻ:
1. **Bắt sự kiện tại tầng ứng dụng**: Middleware tùy biến gắn trên FastAPI tự động ghi nhận thông tin của mọi yêu cầu HTTP gửi đến Storefront: mã định danh phiên làm việc (Session ID), định danh khách hàng (nếu đã đăng nhập), địa chỉ IP, User-Agent, mã phản hồi HTTP, thời gian thực thi (Latency), và các tham số truy vấn tìm kiếm/sản phẩm.
2. **Truyền dẫn qua Kafka**: Middleware đóng gói dữ liệu thành payload JSON tuân thủ chặt chẽ JSON Schema nghiệp vụ (`docs/contracts/ecommerce-access-v1.schema.json`) và gửi bất đồng bộ vào Apache Kafka topic `ecommerce.access-logs` [14].
3. **Đa kênh ghi nhận đồng thời với Flink StatementSet**:
   * Job Flink Streaming (`access_logs_stream`) sử dụng cơ chế `StatementSet` để đọc một lần từ Kafka topic và phân phối ghi đồng thời vào 4 bảng đích trên Apache Iceberg nhằm tối ưu tài nguyên [15]:
     * `lakehouse.landing.access_logs`: Lưu trữ nguyên trạng thông điệp log thô (Raw JSON payload) phục vụ lưu trữ lưu trữ dài hạn.
     * `lakehouse.bronze.web_events`: Bảng sự kiện thô có định dạng cột cơ bản.
     * `lakehouse.silver.silver_logs`: Bảng sự kiện đã được làm sạch, chuẩn hóa múi giờ UTC, phân tích chi tiết thông tin thiết bị/trình duyệt từ User-Agent, và ẩn danh hóa địa chỉ IP khách hàng.
     * `lakehouse.gold.fact_web_events`: Bảng sự kiện mức phân tích, đánh chỉ mục và phân vùng theo ngày và giờ (`event_date`, `event_hour`).
   * Flink kích hoạt Checkpoint định kỳ 10 giây ghi nhận trạng thái vào MinIO, đảm bảo tính bền vững và khả năng phục hồi tức thì khi có lỗi gián đoạn mạng.
4. **Tổng hợp dữ liệu mẻ (Spark Log Rollup)**:
   * Định kỳ, Apache Spark thực thi các tác vụ tổng hợp mẻ từ bảng sự kiện `gold.fact_web_events` để tính toán các bảng Data Mart phục vụ báo cáo tiếp thị và phân tích hành vi:
     * `mart_hourly_traffic`: Thống kê lưu lượng truy cập, số lượt xem trang và độ trễ phản hồi trung bình theo từng khung giờ trong ngày.
     * `mart_cart_funnel`: Tổng hợp số lượng người dùng qua từng giai đoạn của phễu mua hàng (Duyệt trang $\rightarrow$ Xem sản phẩm $\rightarrow$ Thêm vào giỏ hàng $\rightarrow$ Bắt đầu thanh toán $\rightarrow$ Đặt hàng thành công), tính toán tỷ lệ rớt phễu (Drop-off Rate) và tỷ lệ chuyển đổi (Conversion Rate).
     * `mart_top_viewed_products`: Thống kê tần suất xem và thời gian tương tác của khách hàng trên từng sản phẩm, cung cấp dữ liệu đầu vào cho đội ngũ kinh doanh và marketing đánh giá mức độ quan tâm của thị trường.

## **3.4. Thiết kế cơ sở dữ liệu giao dịch**

### **3.4.1. Phân tích các thực thể và mối quan hệ**

Cơ sở dữ liệu giao dịch (OLTP Database) của nền tảng D&K được thiết kế dựa trên mô hình quan hệ chuẩn hóa cao trên hệ quản trị MySQL 8.4 InnoDB [4]. Hệ thống bao gồm 28 bảng vật lý được phân rã thành 7 cụm thực thể nghiệp vụ chặt chẽ:

1. **Cụm Định danh và Địa điểm (Identity & Locations)**:
   * `cities`: Danh mục thành phố/tỉnh thành hoạt động của doanh nghiệp.
   * `stores`: Chuỗi cửa hàng vật lý trực thuộc các thành phố, đóng vai trò là điểm bán lẻ POS và điểm giao hàng cục bộ.
   * `customers`: Thực thể người dùng trung tâm, lưu trữ hồ sơ khách hàng, phân quyền vai trò nhân sự (`role`), vị trí cửa hàng phụ trách, cùng các trường giám sát rủi ro COD (`is_cod_blocked`, `boom_count`).
   * `customer_credentials`: Tách biệt lưu trữ thông tin nhạy cảm (mật khẩu đã băm `password_hash`, email chuẩn hóa) nhằm cách ly an toàn khỏi các bảng phân tích [6].
2. **Cụm Danh mục và Sản phẩm (Catalog & Products)**:
   * `categories`: Cấu trúc danh mục sản phẩm phân cấp đệ quy ($1-N$ qua `parent_category_id`).
   * `products`: Thông tin sản phẩm tổng quát (tên, mô tả, danh mục, trạng thái).
   * `product_variants`: Biến thể chi tiết có thể bán (SKU) với sự kết hợp cụ thể giữa kích thước, màu sắc, giá niêm yết (`price_vnd`) và giá vốn hiện hành.
   * `wishlist_items` & `product_reviews`: Danh sách yêu thích và các bài đánh giá sản phẩm sau mua kèm điểm xếp hạng.
3. **Cụm Giỏ hàng và Đơn hàng (Carts & Orders)**:
   * `carts` & `cart_items`: Quản lý phiên giỏ hàng hoạt động của khách hàng; áp dụng cột tính toán bảo vệ `active_customer_guard` để bảo đảm mỗi khách hàng chỉ có duy nhất một giỏ hàng hoạt động tại một thời điểm.
   * `orders`: Thực thể đơn hàng trung tâm ghi nhận nguồn bán (`order_source`: Web hoặc POS), địa chỉ giao hàng, thông tin thanh toán, chiết khấu và tổng giá trị thanh toán cuối cùng.
   * `order_items`: Chi tiết từng dòng mặt hàng trong đơn, lưu vết ảnh chụp giá bán (`unit_price_vnd`) và giá vốn bình quân tại thời điểm mua (`cost_price_vnd`).
   * `order_status_history`: Nhật ký máy trạng thái hữu hạn ghi lại toàn bộ tiến trình chuyển dịch trạng thái đơn hàng.
4. **Cụm Khuyến mại (Promotions & Coupons)**:
   * `coupons`: Quản lý mã giảm giá, hình thức chiết khấu (phần trăm hoặc cố định VNĐ), điều kiện giá trị đơn tối thiểu, khung thời gian hiệu lực và giới hạn số lần sử dụng.
   * `coupon_redemptions`: Ghi nhận việc áp dụng mã giảm giá cho từng đơn hàng cụ thể, bảo đảm mỗi đơn chỉ áp dụng một coupon duy nhất.
5. **Cụm Thanh toán và Hoàn tiền (Payments & Refunds)**:
   * `payments`: Quản lý giao dịch thanh toán gắn với đơn hàng (`payment_method`: COD, VietQR), lưu vết mã giao dịch đối tác và trạng thái thành công/thất bại.
   * `refunds`: Quản lý các giao dịch hoàn tiền xuất phát từ các yêu cầu trả hàng được phê duyệt và kiểm định đạt chuẩn.
   * `order_payment_events`: Ghi nhận chi tiết lịch sử tương tác thanh toán và webhook mô phỏng.
6. **Cụm Quản lý Tồn kho 2 cấp và Nhập kho (Multi-tier Inventory & Inbound)**:
   * `inventory`: Quản lý số lượng tồn thực tế (`on_hand`) tại kho tổng trung tâm cho từng biến thể SKU.
   * `store_inventory`: Quản lý số lượng tồn thực tế của từng SKU tại từng cửa hàng chi nhánh vật lý ($N-N$ giữa `stores` và `product_variants`).
   * `inventory_transactions`: Sổ cái nhật ký bất biến (Ledger) ghi nhận mọi biến động xuất/nhập/điều chuyển hàng hóa kèm loại giao dịch (`inbound_purchase`, `outbound_order`, `outbound_pos`, `inbound_return`).
   * `inbound_receipts` & `inbound_receipt_items`: Phiếu nhập kho từ nhà cung cấp vào kho tổng, ghi nhận số lượng và đơn giá nhập để kích hoạt công thức tính lại giá vốn bình quân di động.
7. **Cụm Giao vận và Xử lý Trả hàng (Logistics & Returns)**:
   * `delivery_staff`: Đội ngũ nhân viên giao hàng nội bộ của doanh nghiệp.
   * `shipments` & `shipment_attempts`: Quản lý kiện hàng vận chuyển, lịch sử giao hàng từng lần và ghi nhận nguyên nhân khi giao thất bại (Failed Delivery).
   * `return_requests` & `return_items`: Quản lý phiếu yêu cầu trả hàng trực tuyến trong hạn 7 ngày, ảnh minh chứng, lý do và kết quả kiểm định chất lượng sản phẩm (Inspection).

---

### **3.4.2. Thiết kế sơ đồ ERD**

Mô hình dữ liệu quan niệm được phân tách thành hai miền nghiệp vụ chính nhằm làm rõ ranh giới tương tác và sự luân chuyển thông tin trong hệ thống [docs/diagram/12-erd-conceptual.drawio](docs/diagram/12-erd-conceptual.drawio).

#### **a. ERD quan niệm — Bán hàng và Dịch vụ sau bán**
Sơ đồ thể hiện chu trình xuyên suốt từ khi Khách hàng đặt hàng, thanh toán, nhận hàng đến khi phát sinh các yêu cầu đổi trả và hoàn tiền:

![ERD quan niệm — Bán hàng và sau bán](docs/diagram/erd-conceptual-sales.svg)
*Hình 3.16: Sơ đồ ERD quan niệm phân hệ Bán hàng và Dịch vụ sau bán (docs/diagram/erd-conceptual-sales.svg).*

Mối quan hệ bản chất giữa các thực thể:
* Một `Khách hàng` sở hữu nhiều `Đơn hàng` ($1 \rightarrow 0..N$), nhưng mỗi đơn hàng thuộc về duy nhất một khách hàng.
* Một `Đơn hàng` bao gồm nhiều `Chi tiết đơn` ($1 \rightarrow 1..N$); mỗi dòng chi tiết liên kết tới một `Biến thể SKU` cụ thể.
* Một `Đơn hàng` liên kết với một bản ghi `Thanh toán` chính ($1 \rightarrow 0..1$). Khi phát sinh đổi trả, đơn hàng có thể có một `Yêu cầu trả` ($1 \rightarrow 0..1$).
* Từ một `Yêu cầu trả`, hệ thống quản lý nhiều `Chi tiết trả` ($1 \rightarrow 1..N$) và liên kết tới giao dịch `Hoàn tiền` ($1 \rightarrow 0..1$) khi sản phẩm được kiểm định đạt tiêu chuẩn.

#### **b. ERD quan niệm — Danh mục sản phẩm và Quản lý tồn kho**
Sơ đồ thể hiện chu trình phân cấp hàng hóa, quản lý tồn kho hai cấp (kho tổng trung tâm và chuỗi cửa hàng chi nhánh) cùng quy trình nhập kho bổ sung hàng hóa:

![ERD quan niệm — Danh mục và tồn kho](docs/diagram/erd-conceptual-stock.svg)
*Hình 3.17: Sơ đồ ERD quan niệm phân hệ Danh mục và Quản lý tồn kho (docs/diagram/erd-conceptual-stock.svg).*

Mối quan hệ bản chất:
* Một `Danh mục` chứa nhiều `Sản phẩm` ($1 \rightarrow 0..N$); một sản phẩm được phát triển thành nhiều `Biến thể sản phẩm` ($1 \rightarrow 1..N$) theo các tổ hợp kích cỡ và màu sắc.
* Mỗi `Biến thể sản phẩm` có duy nhất một bản ghi `Tồn kho trung tâm` tại kho tổng ($1 \rightarrow 0..1$), đồng thời phân bổ tồn kho đến nhiều `Cửa hàng` thông qua thực thể liên kết `Tồn cửa hàng` ($1 \rightarrow 0..N$).
* Khi nhập hàng từ nhà cung cấp, một `Phiếu nhập kho` chứa nhiều dòng `Chi tiết nhập` ($1 \rightarrow 1..N$), mỗi dòng cập nhật trực tiếp số lượng và giá vốn của một biến thể tương ứng.

---

### **3.4.3. Thiết kế lược đồ cơ sở dữ liệu MySQL**

Cơ sở dữ liệu vật lý gồm **28 bảng quan hệ, 50 khóa ngoại (Foreign Keys), 49 chỉ mục UNIQUE và 79 ràng buộc CHECK** được triển khai chi tiết qua mã nguồn DDL tại `database/schema.sql` [4], [docs/diagram/13-erd-mysql-physical.drawio](docs/diagram/13-erd-mysql-physical.drawio).

#### **a. Bảng tổng hợp 28 bảng vật lý và cấu hình trích xuất**

| STT | Tên bảng | Khóa chính (PK) | Cột con trỏ Batch (Cursor) | Chế độ trích xuất | Mục đích nghiệp vụ |
|:---:|---|---|---|:---:|---|
| 1 | `cities` | `city_id` | `(updated_at, city_id)` | mutable | Danh mục tỉnh thành/khu vực |
| 2 | `stores` | `store_id` | `(updated_at, store_id)` | mutable | Điểm bán lẻ vật lý & kho chi nhánh |
| 3 | `customers` | `customer_id` | `(updated_at, customer_id)` | mutable | Hồ sơ người dùng, vai trò & rủi ro COD |
| 4 | `customer_credentials` | `customer_id` | *Không trích xuất* | bảo mật | Mật khẩu hash & xác thực |
| 5 | `categories` | `category_id` | `(updated_at, category_id)` | mutable | Danh mục sản phẩm phân cấp |
| 6 | `products` | `product_id` | `(updated_at, product_id)` | mutable | Thông tin sản phẩm chung |
| 7 | `product_variants` | `variant_id` | `(updated_at, variant_id)` | mutable | Biến thể SKU, giá niêm yết & giá vốn |
| 8 | `wishlist_items` | `wishlist_item_id` | `(updated_at, wishlist_item_id)` | mutable | Danh sách sản phẩm quan tâm |
| 9 | `product_reviews` | `review_id` | `(updated_at, review_id)` | mutable | Đánh giá & xếp hạng sau mua |
| 10 | `carts` | `cart_id` | `(updated_at, cart_id)` | mutable | Phiên giỏ hàng người dùng |
| 11 | `cart_items` | `cart_item_id` | `(updated_at, cart_item_id)` | mutable | Mặt hàng được thêm vào giỏ |
| 12 | `orders` | `order_id` | `(updated_at, order_id)` | mutable | Đơn hàng tổng hợp (Web & POS) |
| 13 | `order_items` | `order_item_id` | `(created_at, order_item_id)` | append_only | Dòng mặt hàng đơn & snapshot giá/vốn |
| 14 | `order_status_history` | `order_status_history_id` | `(created_at, order_status_history_id)` | append_only | Lịch sử chuyển trạng thái đơn hàng |
| 15 | `coupons` | `coupon_id` | `(updated_at, coupon_id)` | mutable | Phiếu giảm giá & khuyến mại |
| 16 | `coupon_redemptions` | `coupon_redemption_id` | `(updated_at, coupon_redemption_id)` | mutable | Lịch sử sử dụng mã coupon |
| 17 | `payments` | `payment_id` | `(created_at, payment_id)` | append_only | Giao dịch thanh toán đơn hàng |
| 18 | `refunds` | `refund_id` | `(updated_at, refund_id)` | mutable | Giao dịch hoàn tiền trả hàng |
| 19 | `order_payment_events`| `event_id` | `(created_at, event_id)` | append_only | Sự kiện tương tác cổng thanh toán |
| 20 | `inventory` | `variant_id` | `(updated_at, variant_id)` | mutable | Tồn kho thực tế tại kho tổng |
| 21 | `store_inventory` | `(store_id, variant_id)` | `(updated_at, store_inventory_id)` | mutable | Tồn kho thực tế tại chuỗi cửa hàng |
| 22 | `inventory_transactions`| `transaction_id` | `(created_at, transaction_id)` | append_only | Sổ cái nhật ký biến động kho |
| 23 | `inbound_receipts` | `receipt_id` | `(updated_at, receipt_id)` | mutable | Phiếu nhập kho từ nhà cung cấp |
| 24 | `inbound_receipt_items`| `item_id` | `(created_at, item_id)` | append_only | Chi tiết mặt hàng nhập kho |
| 25 | `delivery_staff` | `staff_id` | `(updated_at, staff_id)` | mutable | Nhân sự giao nhận hàng hóa |
| 26 | `shipments` | `shipment_id` | `(updated_at, shipment_id)` | mutable | Vận đơn và tiến trình giao vận |
| 27 | `shipment_attempts` | `attempt_id` | `(created_at, attempt_id)` | append_only | Nhật ký các lần giao hàng thất bại |
| 28 | `return_requests` | `return_id` | `(updated_at, return_id)` | mutable | Phiếu yêu cầu hoàn trả đơn hàng |

*(Lưu ý: Bảng chi tiết trả hàng `return_items` thuộc thực thể `return_requests` nâng tổng số bảng quản lý trong schema lên mức hoàn chỉnh).*

#### **b. Chi tiết 7 phân hệ lược đồ vật lý MySQL**

##### **1. Phân hệ Tài khoản và Địa điểm (Identity & Locations)**
Quản lý thực thể địa lý, cửa hàng, tài khoản người dùng và cơ chế bảo mật thông tin xác thực:

![MySQL — Tài khoản và địa điểm](docs/diagram/erd-physical-identity.svg)
*Hình 3.18: Lược đồ vật lý phân hệ Tài khoản và Địa điểm (docs/diagram/erd-physical-identity.svg).*

* Khóa ngoại chính: `stores.city_id → cities.city_id` (RESTRICT), `customers.city_id → cities.city_id` (SET NULL), `customers.store_id → stores.store_id` (SET NULL), `customers.cod_reinstated_by → customers.customer_id` (SET NULL), `customer_credentials.customer_id → customers.customer_id` (RESTRICT).

##### **2. Phân hệ Danh mục, Wishlist và Đánh giá (Catalog, Wishlist & Reviews)**
Quản lý phân cấp danh mục, thông tin sản phẩm, các biến thể SKU, danh sách yêu thích và phản hồi khách hàng:

![MySQL — Danh mục, wishlist và đánh giá](docs/diagram/erd-physical-catalog.svg)
*Hình 3.19: Lược đồ vật lý phân hệ Danh mục, Wishlist và Đánh giá (docs/diagram/erd-physical-catalog.svg).*

* Khóa ngoại chính: `categories.parent_category_id → categories.category_id` (RESTRICT), `products.category_id → categories.category_id` (RESTRICT), `product_variants.product_id → products.product_id` (RESTRICT), `wishlist_items.customer_id → customers.customer_id` (RESTRICT), `product_reviews.order_item_id → order_items.order_item_id` (RESTRICT).

##### **3. Phân hệ Đơn hàng, Giỏ và Khuyến mại (Orders, Carts & Promotions)**
Quản lý giao dịch mua sắm trực tuyến, giỏ hàng hoạt động và áp dụng mã giảm giá:

![MySQL — Đơn hàng, giỏ và khuyến mại](docs/diagram/erd-physical-orders.svg)
*Hình 3.20: Lược đồ vật lý phân hệ Đơn hàng, Giỏ và Khuyến mại (docs/diagram/erd-physical-orders.svg).*

* Khóa ngoại chính: `carts.customer_id → customers.customer_id` (RESTRICT), `cart_items.cart_id → carts.cart_id` (RESTRICT), `orders.customer_id → customers.customer_id` (RESTRICT), `order_items.order_id → orders.order_id` (RESTRICT), `coupon_redemptions.coupon_id → coupons.coupon_id` (RESTRICT), `coupon_redemptions.order_id → orders.order_id` (RESTRICT).

##### **4. Phân hệ Thanh toán và Hoàn tiền (Payments & Refunds)**
Quản lý các giao dịch tài chính phát sinh từ đơn hàng và quy trình giải quyết đổi trả:

![MySQL — Thanh toán và hoàn tiền](docs/diagram/erd-physical-payment.svg)
*Hình 3.21: Lược đồ vật lý phân hệ Thanh toán và Hoàn tiền (docs/diagram/erd-physical-payment.svg).*

* Khóa ngoại chính: `payments.order_id → orders.order_id` (RESTRICT), `refunds.payment_id → payments.payment_id` (RESTRICT), `refunds.order_id → orders.order_id` (RESTRICT).

##### **5. Phân hệ Tồn kho và Nhập kho (Multi-tier Inventory & Inbound)**
Quản lý mức tồn kho 2 cấp, chứng từ nhập kho và sổ cái nhật ký xuất/nhập/chuyển kho:

![MySQL — Tồn kho và nhập kho](docs/diagram/erd-physical-inventory.svg)
*Hình 3.22: Lược đồ vật lý phân hệ Tồn kho và Nhập kho (docs/diagram/erd-physical-inventory.svg).*

* Khóa ngoại chính: `inventory.variant_id → product_variants.variant_id` (RESTRICT), `store_inventory.store_id → stores.store_id` (RESTRICT), `store_inventory.variant_id → product_variants.variant_id` (RESTRICT), `inbound_receipt_items.receipt_id → inbound_receipts.receipt_id` (CASCADE), `inbound_receipt_items.variant_id → product_variants.variant_id` (RESTRICT), `inventory_transactions.variant_id → product_variants.variant_id` (RESTRICT).

##### **6. Phân hệ Giao vận và Nhân sự (Logistics & Delivery)**
Quản lý đội ngũ nhân viên giao hàng, đơn vận chuyển và nhật ký xử lý giao thất bại:

![MySQL — Giao vận và nhân sự](docs/diagram/erd-physical-logistics.svg)
*Hình 3.23: Lược đồ vật lý phân hệ Giao vận và Nhân sự (docs/diagram/erd-physical-logistics.svg).*

* Khóa ngoại chính: `shipments.order_id → orders.order_id` (RESTRICT), `shipments.assigned_staff_id → delivery_staff.staff_id` (SET NULL), `shipment_attempts.shipment_id → shipments.shipment_id` (CASCADE).

##### **7. Phân hệ Trả hàng và Kiểm định (Returns & Inspection)**
Quản lý các yêu cầu hoàn trả hàng trực tuyến và kết quả kiểm định chất lượng:

![MySQL — Trả hàng và kiểm định](docs/diagram/erd-physical-returns.svg)
*Hình 3.24: Lược đồ vật lý phân hệ Trả hàng và Kiểm định (docs/diagram/erd-physical-returns.svg).*

* Khóa ngoại chính: `return_requests.order_id → orders.order_id` (RESTRICT), `return_requests.customer_id → customers.customer_id` (RESTRICT), `return_items.return_id → return_requests.return_id` (CASCADE), `return_items.order_item_id → order_items.order_item_id` (RESTRICT).

---

### **3.4.4. Ràng buộc dữ liệu và tính nhất quán giao dịch**

Hệ thống thiết lập một khung bảo vệ nhất quán dữ liệu đa tầng (Multi-layered Consistency Framework) kết hợp giữa các ràng buộc cưỡng chế tại động cơ lưu trữ MySQL InnoDB và các mẫu hình kiểm soát giao dịch tại tầng ứng dụng Backend [docs/diagram/14-transaction-consistency.drawio](docs/diagram/14-transaction-consistency.drawio).

![Ràng buộc và tính nhất quán giao dịch](docs/diagram/transaction-consistency.svg)
*Hình 3.25: Ràng buộc toàn vẹn và tính nhất quán giao dịch ACID (docs/diagram/transaction-consistency.svg).*

Các trụ cột kỹ thuật đảm bảo tính nhất quán dữ liệu:

1. **Tuân thủ thuộc tính ACID và Mức cô lập giao dịch**:
   * Toàn bộ kết nối cơ sở dữ liệu từ FastAPI và SQLAlchemy thiết lập mức cô lập giao dịch **`READ COMMITTED`** [4], giúp loại bỏ hiện tượng đọc rác (Dirty Read) đồng thời tối ưu hóa thông lượng xử lý song song thông qua cơ chế đa phiên bản (MVCC - Multi-Version Concurrency Control).
   * Mọi thao tác làm thay đổi trạng thái hệ thống phức tạp (Đặt hàng, Bán lẻ POS, Nhập kho, Hoàn trả) đều được thực thi trong một ranh giới giao dịch duy nhất (Transaction Boundary) theo mẫu Unit of Work (`app/db/uow.py`) [5]. Nếu xảy ra lỗi tại bất kỳ bước trung gian nào, toàn bộ các bảng liên quan đều được `ROLLBACK` nguyên tử về trạng thái ban đầu.

2. **Chiến lược Khóa dòng bi quan (Pessimistic Row Locking)**:
   * Nhằm loại bỏ triệt để hiện tượng tranh chấp dữ liệu (Race Condition) và bán âm hàng tồn (Overselling), hệ thống sử dụng cú pháp **`SELECT ... FOR UPDATE`** [4]:
     * *Khi Đặt hàng*: Khóa bản ghi khách hàng (`Customer`) để kiểm tra quyền COD, sau đó khóa các dòng tồn kho tương ứng trong bảng `inventory` (kho tổng) để thẩm định số lượng khả dụng trước khi trừ hàng.
     * *Khi Bán hàng POS*: Khóa trực tiếp dòng tồn kho chi nhánh tương ứng trong bảng `store_inventory` theo cặp `(store_id, variant_id)`.
   * Bộ điều phối Unit of Work tích hợp cơ chế tự động thử lại (Deadlock Retry) với thuật toán ngắt quãng lũy thừa (Exponential Backoff), tự động giải phóng và tái thực thi giao dịch khi gặp mã lỗi deadlock từ MySQL (`Error 1213`).

3. **Hệ thống Ràng buộc Toàn vẹn tại tầng Cơ sở dữ liệu (Database Constraints)**:
   * **50 Khóa ngoại (Foreign Keys)**: Ràng buộc quan hệ thực thể chặt chẽ; áp dụng có chủ đích các hành vi `ON DELETE`:
     * `RESTRICT`: Cấm xóa các thực thể gốc (Category, Product, Customer, Order) nếu đang có dữ liệu con tham chiếu đến, ngăn chặn tình trạng mồ côi dữ liệu (Orphan Records).
     * `CASCADE`: Tự động xóa các dòng chi tiết phụ thuộc khi chứng từ cha bị hủy (áp dụng cho `inbound_receipt_items` theo `inbound_receipts`, `shipment_attempts` theo `shipments`, `return_items` theo `return_requests`).
     * `SET NULL`: Tự động gán `NULL` cho các trường tham chiếu tùy chọn khi thực thể gốc bị gỡ bỏ (ví dụ: hủy nhân viên giao hàng trên vận đơn `assigned_staff_id`, xóa cửa hàng trên hồ sơ khách hàng `store_id`).
   * **49 Chỉ mục DUY NHẤT (UNIQUE Constraints)**: Bảo vệ tính độc bản của các trường kinh doanh: mã định danh công khai `public_id` (UUID BINARY(16)), mã vạch SKU `sku`, mã giảm giá `code_normalized`, số điện thoại giao hàng `phone`, và cột ảo `active_customer_guard` (bảo đảm mỗi khách hàng chỉ có duy nhất một giỏ hàng active).
   * **79 Ràng buộc Kiểm tra (CHECK Constraints)**: Cưỡng chế quy tắc miền giá trị tại tầng vật lý: số tiền không âm (`subtotal_vnd >= 0`, `total_vnd >= 0`), số lượng nguyên dương (`quantity > 0`), tỷ lệ phần trăm hợp lệ ($0 \le \text{discount} \le 100$), và tính hợp lệ của các chuỗi trạng thái máy hữu hạn.

4. **Cơ chế Ảnh chụp Lịch sử (Snapshotting Mechanism)**:
   * Nhằm đảm bảo tính bất biến của dữ liệu kế toán và phân tích tài chính, khi một đơn hàng được xác lập, hệ thống không chỉ lưu khóa ngoại `variant_id` mà thực hiện chụp ảnh toàn bộ thông tin tại thời điểm giao dịch vào bảng `order_items`:
     * `unit_price_vnd`: Giá bán thực tế tại thời điểm mua.
     * `cost_price_vnd`: Giá vốn bình quân gia quyền di động của SKU tại thời điểm đặt hàng.
     * `product_name_snapshot`, `sku_snapshot`, `size_code_snapshot`, `color_code_snapshot`.
   * Nhờ cơ chế Snapshot, mọi sự thay đổi giá bán, việc điều chỉnh giá vốn do các đợt nhập kho sau này, hoặc hành động đổi tên/xóa mềm sản phẩm trong tương lai đều **không làm thay đổi số liệu doanh thu và lợi nhuận gộp lịch sử** của các đơn hàng đã hoàn tất.

## **3.5. Thiết kế nền tảng Data Lakehouse**

### **3.5.1. Xác định nguồn dữ liệu**

Để xây dựng nền tảng phân tích kinh doanh đa chiều phục vụ cả báo cáo điều hành chiến lược lẫn quyết định vận hành thời gian thực, hệ thống Data Lakehouse của D&K tiếp nhận và tích hợp dữ liệu từ hai nhóm nguồn phát sinh độc lập [7]:

1. **Nguồn dữ liệu quan hệ giao dịch (OLTP RDBMS)**:
   * **Phạm vi nguồn**: Xuất phát từ cơ sở dữ liệu quan hệ MySQL 8.4 InnoDB của hệ thống bán hàng, bao gồm 27 bảng nghiệp vụ thuộc 7 cụm phân hệ (đã được chuẩn hóa ở mục 3.4): Định danh tài khoản khách hàng, Danh mục sản phẩm & tồn kho biến thể, Quản lý đơn hàng & chi tiết đơn, Thanh toán, Tồn kho cửa hàng & nhập hàng, Giao vận đơn hàng, và Tiếp nhận đổi trả.
   * **Ngoại lệ bảo mật (Zero-Knowledge Exclusion)**: Bảng `customer_credentials` (chứa chuỗi băm mật khẩu `argon2id` và muối bảo mật) **bị loại trừ hoàn toàn** khỏi mọi quy trình trích xuất và lưu trữ Lakehouse theo quy tắc an toàn thông tin NFR-02 và khuyến nghị của OWASP [6]. Hồ sơ khách hàng đưa vào phân tích chỉ sử dụng khóa định danh kỹ thuật `customer_id` cùng các thông tin nhân khẩu học đã được che giấu hoặc băm một chiều.
   * **Đặc tính dữ liệu**: Dữ liệu có cấu trúc định dạng mạnh (strongly-typed schema), có tính toàn vẹn tham chiếu cao (ACID compliant), phản ánh trạng thái hiện tại (state-based) của thực thể kinh doanh.

2. **Nguồn nhật ký truy cập và tương tác người dùng (Web Clickstream & Access Logs)**:
   * **Phạm vi nguồn**: Phát sinh từ toàn bộ các yêu cầu HTTP/HTTPS của người dùng truy cập giao diện Storefront (Next.js 15) và tương tác với máy chủ API (FastAPI) [2], [3].
   * **Cấu trúc sự kiện**: Được chuẩn hóa theo lược đồ JSON nghiêm ngặt (`ecommerce-access-v1.schema.json`). Mỗi bản ghi sự kiện bao gồm: định danh phiên truy cập (`session_id`), người dùng (`user_id`), mã tuyến đường API (`route_pattern`), phương thức HTTP (`method`), mã phản hồi (`status_code`), thời gian xử lý (`duration_ms`), địa chỉ IP, chuỗi User-Agent, và payload tham số ngữ cảnh (như mã sản phẩm xem, danh mục tìm kiếm, biến thể được đưa vào giỏ).
   * **Đặc tính dữ liệu**: Dữ liệu chuỗi thời gian bất biến (immutable time-series event streams), lưu lượng lớn, tần suất phát sinh liên tục theo hành vi người dùng trực tuyến.

Bảng 3.7 tổng hợp thông số kỹ thuật của các nguồn dữ liệu đi vào nền tảng Lakehouse:

| Nhóm nguồn | Thực thể dữ liệu | Cơ chế thu thập | Định dạng tại nguồn | Tần suất đẩy / nạp | Mục đích phân tích |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OLTP Batch** | 27 bảng nghiệp vụ MySQL | Spark JDBC Incremental Pull | Quan hệ (InnoDB B+Tree) | Định kỳ hàng ngày (02:00 UTC+7) | Báo cáo tài chính, hiệu suất bán hàng, đối soát kho và giao vận. |
| **OLTP CDC** | 27 bảng nghiệp vụ MySQL | Debezium MySQL Connector [13] | Row-based Binary Log (`binlog`) | Thời gian thực (Streaming sub-second) | Kiểm toán thay đổi dữ liệu, truy vết trạng thái đơn, tái tạo dòng lịch sử. |
| **Access Logs** | Nhật ký truy cập & tương tác Web | FastAPI Middleware $\rightarrow$ Kafka | Chuỗi sự kiện JSON | Thời gian thực (Streaming qua Kafka [14]) | Phân tích phễu chuyển đổi (Conversion Funnel), tải hệ thống, nhu cầu sản phẩm. |

---

### **3.5.2. Thiết kế luồng thu thập Batch, CDC và Access Log**

Hệ thống triển khai ba cơ chế thu thập dữ liệu chuyên biệt hóa nhằm đáp ứng đồng thời tính chính xác tuyệt đối của kế toán giao dịch và tính kịp thời của dữ liệu hành vi tương tác:

1. **Luồng thu thập Batch tăng dần (OLTP Batch Ingestion)**:
   * Được điều phối tự động bởi Apache Airflow thông qua DAG `lakehouse_oltp_pipeline` [16], kích hoạt định kỳ lúc 02:00 sáng (UTC+7) khi giao dịch trực tiếp trên hệ thống giảm xuống mức thấp nhất.
   * **Cơ chế đọc tăng dần (Incremental Read)**: Động cơ Apache Spark đọc dữ liệu qua kết nối JDBC [12] sử dụng cặp con trỏ watermark: `(cursor_field, primary_key)`. Đối với các bảng có cột mốc thời gian cập nhật `updated_at`, truy vấn sẽ lọc các bản ghi có giá trị lớn hơn mốc watermark của lần chạy trước.
   * **Cơ chế Lookback Window chống rò rỉ giao dịch**: Nhằm loại bỏ hoàn toàn hiện tượng mất mát dữ liệu do độ trễ commit giao dịch (transaction commit latency) hoặc lệch đồng hồ hệ thống (clock drift), Spark tự động áp dụng cửa sổ lùi:
     $$\text{Watermark}_{\text{start}} = \text{Watermark}_{\text{previous}} - \Delta t_{\text{lookback}}$$
     Hệ thống thiết lập $\Delta t_{\text{lookback}} = 10\text{ phút}$ cho các bảng danh mục chuẩn và $\Delta t_{\text{lookback}} = 3\text{ ngày}$ cho các bảng giao dịch có chu kỳ cập nhật kéo dài như `orders`, `shipments` và `refunds`.
   * **Ghi nguyên tử xuống Landing**: Dữ liệu đọc từ MySQL được Spark nạp vào vùng lưu trữ Landing (`s3://lakehouse/landing/oltp/<table>/<batch_id>/`) dưới định dạng Apache Parquet, đi kèm tệp kê khai nguyên tử `manifest.json` ghi nhận chính xác: tổng số bản ghi (`record_count`), thời điểm quét, phạm vi con trỏ, và mã phiên chạy (`run_id`).

2. **Luồng Change Data Capture thời gian thực (CDC)**:
   * Trình kết nối Debezium MySQL Connector [13] đọc trực tiếp các bản ghi nhị phân của MySQL (`binlog_format = ROW`, `binlog_row_image = FULL`).
   * Mỗi thao tác cơ sở dữ liệu (`INSERT`, `UPDATE`, `DELETE`) được chuyển đổi thành một thông điệp sự kiện JSON gồm hình ảnh trạng thái trước (`before`) và sau (`after`) của dòng dữ liệu, phát tán trực tiếp vào các topic Kafka tương ứng theo quy ước: `cdc.ecommerce.<table>` [14].
   * Job streaming của Apache Flink tiêu thụ các sự kiện CDC từ Kafka, thực hiện ghi chép nối tiếp (Append-only) vào bảng Iceberg `bronze.oltp_cdc_events` với chu kỳ kiểm tra trạng thái (checkpoint interval) là 10 giây [15], bảo toàn lịch sử biến động dữ liệu phục vụ tái lập trạng thái và kiểm toán.

3. **Luồng thu thập nhật ký truy cập (Access Log Streaming)**:
   * Middleware trên FastAPI đánh chặn mọi luồng yêu cầu/phản hồi HTTP, đóng gói thông tin ngữ cảnh vào cấu trúc sự kiện JSON và gửi bất đồng bộ qua Kafka Producer vào topic `ecommerce.access-logs`.
   * Một tác vụ luồng Flink chuyên biệt (`StatementSet`) tiêu thụ từ Kafka và phân tán dữ liệu đồng thời (Multi-Sink Pipeline) xuống các bảng Iceberg trong nền tảng Lakehouse: ghi nhận thô vào `landing.access_logs`, làm giàu thông tin và gán watermark thời gian tại `bronze.web_events`, chuẩn hóa schema tại `silver.silver_logs`, và tổng hợp tính toán các chỉ số lưu lượng theo khung cửa sổ vào `gold.fact_web_events`.

---

### **3.5.3. Thiết kế các lớp Landing, Bronze, Silver và Gold**

Kiến trúc hồ dữ liệu của D&K tuân thủ mô hình Huy chương (Medallion Architecture) [7], phân chia dữ liệu thành các phân tầng chất lượng lũy tiến nhằm đảm bảo tính toàn vẹn, khả năng kiểm toán nguồn gốc (lineage) và tối ưu hóa hiệu năng truy vấn phân tích:

![Các tầng dữ liệu Lakehouse](docs/diagram/medallion.svg)

1. **Phân tầng Landing (Vùng tiếp nhận đệm - Staging Storage)**:
   * **Vị trí và định dạng**: Đặt trên MinIO S3 Object Storage [8], lưu trữ dữ liệu trích xuất dưới định dạng tệp Parquet nguyên bản (đối với luồng Batch OLTP) hoặc JSON nguyên thủy (đối với luồng Access Logs).
   * **Nguyên tắc hoạt động**: Vùng đệm mang tính bất biến (immutable) và ngắn hạn. Mỗi mẻ trích xuất được đóng gói thành một thư mục độc lập gắn mã định danh phiên chạy `_run_id` kèm tệp `manifest.json`. Landing đóng vai trò ranh giới an toàn, cô lập hoạt động trích xuất khỏi quy trình nạp bảng phân tích, cho phép phát lại (replay) toàn bộ mẻ dữ liệu khi xảy ra sự cố xử lý mà không cần đọc lại từ MySQL nguồn.

2. **Phân tầng Bronze (Vùng thô dạng bảng - Raw Iceberg Tables)**:
   * **Vị trí và định dạng**: Được quản lý dưới dạng bảng Apache Iceberg [9] trong namespace `lakehouse.bronze`.
   * **Nguyên tắc hoạt động**: Toàn bộ dữ liệu từ Landing được nạp vào Bronze theo phương thức **chỉ ghi thêm (Append-only)**. Dữ liệu tại Bronze bảo toàn nguyên vẹn kiểu dữ liệu nguồn (hoặc chuyển thành chuỗi an toàn) nhằm tránh thất thoát thông tin.
   * **Truy vết nguồn gốc (Lineage Enrichment)**: Mỗi dòng dữ liệu được tự động bổ sung ba cột siêu dữ liệu kiểm toán hệ thống:
     * `_ingested_at`: Mốc thời gian bản ghi được nạp vào Bronze.
     * `_source_file`: Đường dẫn tệp Parquet nguồn tại Landing.
     * `_source_run_id`: Mã định danh phiên chạy Airflow (`run_id`) đã nạp bản ghi.
   * **Tiến hóa lược đồ (Schema Evolution)**: Bảng Bronze hỗ trợ tự động bổ sung cột (`ADD COLUMN`) khi bảng MySQL phát sinh thuộc tính mới mà không cần xây dựng lại bảng hoặc làm gián đoạn tiến trình. Con trỏ watermark của hệ thống chỉ được cập nhật và lưu vết sau khi dữ liệu đã ghi nhận thành công vào Bronze.

3. **Phân tầng Silver (Vùng dữ liệu sạch và chuẩn hóa - Conformed Operational Tables)**:
   * **Vị trí và định dạng**: Không gian tên `lakehouse.silver` gồm 27 bảng tương ứng với các thực thể OLTP và 1 bảng nhật ký web (`silver_logs`).
   * **Chức năng xử lý**:
     * **Ép kiểu và chuẩn hóa cấu trúc**: Chuyển đổi các kiểu dữ liệu chuỗi thô thành các kiểu dữ liệu định dạng chuẩn của Spark SQL (`TIMESTAMP`, `DECIMAL(12, 2)`, `INTEGER`, `BOOLEAN`). Các cột chứa chuỗi JSON (như `attributes_json`, `metadata_json`) được bóc tách thành các cột cấu trúc có định dạng.
     * **Khử trùng lặp (Deduplication)**: Loại bỏ các bản ghi trùng lặp sinh ra do cơ chế trích xuất có cửa sổ lùi (Lookback Window) bằng cách xếp hạng theo thời gian cập nhật mới nhất: `ROW_NUMBER() OVER (PARTITION BY pk ORDER BY updated_at DESC) = 1`.
     * **Cập nhật dữ liệu biến đổi (SCD Type 1)**: Thực thi câu lệnh `MERGE INTO` của Apache Iceberg để đồng bộ trạng thái mới nhất của bản ghi dựa trên khóa chính:
       $$\text{WHEN MATCHED AND target.updated\_at} < \text{source.updated\_at THEN UPDATE SET } *$$
       $$\text{WHEN NOT MATCHED THEN INSERT } *$$
     * **Bảo vệ quyền riêng tư (PII Pseudonymization)**: Các thông tin nhạy cảm của khách hàng và nhân viên (`email`, `phone`, `full_name`) được mã hóa một chiều qua thuật toán băm có muối: $\text{SHA-256}(\text{value} + \text{salt})$, đảm bảo không lưu thông tin nhận dạng cá nhân dạng văn bản rõ.
     * **Cách ly dữ liệu dị biệt (Quarantine Pattern)**: Các bản ghi vi phạm tính toàn vẹn (như khóa ngoại không tồn tại, định dạng thời gian sai lệch, hoặc số tiền âm bất hợp lý) được định tuyến tự động vào namespace `lakehouse.quarantine` để ghi vết cảnh báo mà không làm gián đoạn toàn bộ đường ống dẫn dữ liệu.

4. **Phân tầng Gold (Vùng mô hình hóa phân tích - Dimensional & Mart Layer)**:
   * **Vị trí và định dạng**: Không gian tên `lakehouse.gold`, tổ chức theo mô hình hình sao (Star Schema) [11] gồm các bảng Chiều chuẩn hóa (Conformed Dimensions), bảng Sự kiện (Fact Tables) và các Data Marts tổng hợp phục vụ trực tiếp cho BI Hub.
   * **Tối ưu hóa tệp dữ liệu lưu trữ**: Toàn bộ bảng Gold được cấu hình tham số dung lượng tệp Parquet mục tiêu đạt $128\text{ MiB}$ (`write.parquet.target-file-size-bytes = 134217728`), đồng thời thiết lập chiến lược phân vùng tối ưu theo ngày giao dịch (`order_date`, `shipping_date`, `snapshot_date`), giúp Trino và Spark giảm thiểu chi phí quét dữ liệu (Data Pruning / Partition Elimination) khi xử lý các truy vấn tổng hợp phân tích quy mô lớn.

---

### **3.5.4. Thiết kế Dimension, Fact và Data Mart**

Tầng Gold được mô hình hóa theo phương pháp luận Kimball [11], phân tách mạch lạc giữa các bảng chiều dùng chung (Conformed Dimensions), các bảng sự kiện phản ánh nghiệp vụ giao dịch, và các Data Mart chuyên biệt:

#### **1. Hệ thống bảng chiều (Conformed Dimensions)**
* **`dim_date`**: Bảng chiều thời gian sinh trước cho chu kỳ 10 năm, chứa các thuộc tính lịch: ngày trong tuần, ngày trong tháng, tuần trong năm, tháng, quý, năm, cờ đánh dấu ngày cuối tuần (`is_weekend`), và cờ ngày lễ quốc gia.
* **`dim_customer`**: Chiều khách hàng, sử dụng khóa thay thế kỹ thuật `customer_key`. Lưu trữ thông tin phân nhóm khách hàng, ngày đăng ký, điểm tích lũy, cùng các trường PII đã được mã hóa bảo mật (`email_hash`, `phone_hash`, `full_name_hash`).
* **`dim_product`**: Chiều sản phẩm gốc, lưu trữ mã định danh sản phẩm (`product_id`), tên sản phẩm, danh mục cha, danh mục con, thương hiệu, trạng thái kích hoạt, và cờ xóa mềm.
* **`dim_variant`**: Chiều biến thể sản phẩm (SKU Grain), khóa thay thế `variant_key`. Lưu trữ mã SKU, kích thước (`size_code`), màu sắc (`color_code`), giá niêm yết hiện hành, và giá vốn tiêu chuẩn.
* **`dim_store`**: Chiều cửa hàng và kênh phân phối, phân định giữa các cửa hàng bán lẻ vật lý (kèm địa chỉ, quận, tỉnh/thành phố) và kênh bán hàng trực tuyến Storefront.
* **`dim_delivery_staff`**: Chiều nhân sự giao vận, lưu mã nhân viên, đơn vị vận chuyển (đội ngũ nội bộ hoặc đối tác thứ ba 3PL), trạng thái hoạt động, và số điện thoại đã băm bảo mật.

#### **2. Hệ thống bảng sự kiện cốt lõi (Core Fact Tables)**
Hệ thống thiết lập 5 bảng sự kiện nghiệp vụ OLTP và 1 bảng sự kiện nhật ký tương tác:
* **`fact_order`**: Sự kiện cấp độ đơn hàng (Order Grain). Đo lường: tổng tiền hàng, giá trị giảm giá voucher, phí vận chuyển, doanh thu gộp, doanh thu ròng, trạng thái đơn, phương thức thanh toán, số lượng sản phẩm trong đơn. Phân vùng theo `order_date`.
* **`fact_order_item`**: Sự kiện chi tiết mặt hàng (Line Item Grain). Đo lường: số lượng mua (`quantity`), đơn giá bán snapshot (`unit_price_vnd`), giá vốn bình quân snapshot (`cost_price_vnd`), doanh thu gộp mặt hàng, lợi nhuận gộp danh nghĩa. Phân vùng theo `order_date`.
* **`fact_shipment`**: Sự kiện thực hiện đơn hàng và giao vận (Shipment Grain). Đo lường: thời gian tiếp nhận, thời gian xuất kho, thời gian giao hàng thành công, độ trễ giao vận so với cam kết (SLA Duration), số lần giao lại, trạng thái giao vận cuối cùng. Phân vùng theo `shipping_date`.
* **`fact_return_exchange`**: Sự kiện xử lý trả hàng và đổi hàng (Return Grain). Đo lường: số lượng hàng trả, giá trị hoàn tiền (`refund_amount_vnd`), lý do trả hàng (hàng lỗi, không vừa kích cỡ, sai mô tả), thời gian từ lúc giao đến khi yêu cầu trả. Phân vùng theo `request_date`.
* **`fact_inventory_daily_snapshot`**: Sự kiện chụp ảnh tồn kho định kỳ (Periodic Snapshot Grain). Ghi nhận trạng thái tồn kho hàng ngày cho từng cặp `(store_id, variant_id)`: số lượng tồn cuối ngày (`ending_quantity`), giá trị tồn kho theo giá vốn (`inventory_value_vnd`), và cờ cảnh báo hết hàng (`is_out_of_stock`). Phân vùng theo `snapshot_date`.
* **`fact_web_events`**: Sự kiện tương tác trên nền tảng web. Ghi nhận chi tiết từng hành động của người dùng: loại sự kiện (`event_type`), mã người dùng, mã phiên, mã tuyến đường API, thời gian phản hồi máy chủ (`duration_ms`), mã trạng thái HTTP. Phân vùng theo ngày sự kiện.

Hai sơ đồ dưới đây minh họa chi tiết cấu trúc mô hình hình sao tại tầng Gold:

![Gold — Mô hình phân tích bán hàng](docs/diagram/gold-sales.svg)

![Gold — Giao vận, trả hàng và tồn kho](docs/diagram/gold-operations.svg)

#### **3. Hệ thống Data Marts phục vụ phân tích nghiệp vụ**
Nhằm tối ưu hóa tốc độ tải dữ liệu cho hệ thống Dashboard và giảm thiểu tải tính toán lặp lại trên các bảng Fact chi tiết, tầng Gold xây dựng sẵn 4 Data Marts định kỳ từ nguồn OLTP và 3 Data Marts từ nguồn nhật ký Web:

* **Các Data Mart nghiệp vụ bán lẻ (OLTP Data Marts)**:
  * **`mart_sales_daily`**: Tổng hợp doanh thu theo ngày, mã cửa hàng, kênh bán hàng và phương thức thanh toán. Tính toán sẵn: tổng số đơn đặt, số đơn thành công, số đơn hủy, doanh thu gộp (`gross_revenue_vnd`), tổng chiết khấu, doanh thu thuần, và giá trị trung bình trên một đơn hàng (AOV).
  * **`mart_logistics_performance`**: Tổng hợp hiệu năng vận chuyển theo ngày, đơn vị vận chuyển và khu vực địa lý. Đo lường: tỷ lệ giao hàng thành công lần đầu (First-Attempt Delivery Rate), thời gian giao hàng trung bình (Average Delivery Hours), và tỷ lệ đơn trễ hạn cam kết SLA.
  * **`mart_product_returns`**: Tổng hợp tỷ lệ hoàn trả theo sản phẩm, danh mục và lý do hoàn hàng. Giúp bộ phận quản lý sản phẩm phát hiện kịp thời các mã hàng có tỷ lệ lỗi cao bất thường.
  * **`mart_inventory_health`**: Tổng hợp sức khỏe hàng tồn kho theo ngày và kho hàng. Tính toán tốc độ quay vòng tồn kho (Inventory Turnover Rate), số ngày tồn kho ước tính (Days of Inventory On-Hand - DIO), và nhận diện các SKU ứ đọng, tồn kho vượt ngưỡng an toàn.

* **Các Data Mart phân tích hành vi và kỹ thuật (Log Data Marts)**:
  * **`mart_hourly_route_metrics`**: Tổng hợp theo khung giờ và tuyến đường API: tổng số yêu cầu (Request Volume), thời gian xử lý phân vị p95/p99, và tỷ lệ lỗi kỹ thuật 4xx/5xx.
  * **`mart_daily_product_demand`**: Tổng hợp mức độ quan tâm của khách hàng theo từng sản phẩm: số lượt xem trang chi tiết (Product Views), số lần thêm vào giỏ (Add-to-Cart Actions), phản ánh nhu cầu thị trường thực tế trước khi phát sinh đơn hàng.
  * **`mart_marketing_funnel_daily`**: Phân tích phễu chuyển đổi thương mại điện tử hàng ngày: đo lường tỷ lệ chuyển đổi qua các giai đoạn: $\text{Xem sản phẩm} \rightarrow \text{Thêm giỏ hàng} \rightarrow \text{Tiến hành thanh toán} \rightarrow \text{Đặt hàng thành công}$.

Mối quan hệ dẫn xuất và dòng chảy dữ liệu (Lineage) vào các Data Marts được minh họa cụ thể qua hai sơ đồ sau:

![Gold — Lineage các Data Mart OLTP](docs/diagram/gold-marts.svg)

![Gold — Fact và Mart Access Log](docs/diagram/gold-log-marts.svg)

---

### **3.5.5. Thiết kế kiểm soát chất lượng và bảo mật dữ liệu**

Một nền tảng Data Lakehouse phục vụ doanh nghiệp đòi hỏi các cơ chế kiểm định chất lượng chặt chẽ để đảm bảo số liệu kinh doanh không bao giờ bị sai lệch, song song với khung bảo vệ an toàn thông tin theo nguyên tắc đặc quyền tối thiểu [6], [17].

#### **1. Khung kiểm soát chất lượng dữ liệu hai giai đoạn (Dual-Stage Quality Gate)**
Hệ thống triển khai hai chốt kiểm soát tự động được tích hợp trực tiếp vào quy trình ETL/ELT của Apache Spark và Apache Airflow:

![Quality gate và xử lý dữ liệu lỗi](docs/diagram/quality-gates.svg)

* **Chốt đối soát tiền xuất bản (Pre-Gold Reconciliation Gate)**:
  * Kích hoạt tự động ngay sau khi hoàn tất nạp dữ liệu vào tầng Silver thông qua module `reconcile.py`.
  * **Đối soát số lượng dòng bản ghi (`check_table_counts`)**: So sánh trực tiếp tổng số dòng giữa cơ sở dữ liệu nguồn MySQL và bảng Silver Iceberg cho toàn bộ 27 bảng nghiệp vụ. Sai số dòng cho phép (Tolerance) được thiết lập ở ngưỡng khắt khe: $\tau \le 0.05\%$.
  * **Đối soát chỉ tiêu tài chính tiền tệ (`check_financial_metrics`)**: Thực hiện tính tổng giá trị tiền tệ độc lập giữa hai hệ thống trên 3 chỉ tiêu cốt lõi:
    1. Tổng doanh thu đơn hàng: $\sum \text{orders.total\_vnd}$ (với $\text{status} \ne \text{'CANCELLED'}$) so khớp với $\sum \text{silver\_orders.total\_vnd}$.
    2. Tổng tiền thanh toán thành công: $\sum \text{payments.amount\_vnd}$ (với $\text{status} = \text{'SUCCEEDED'}$) so khớp với $\sum \text{silver\_payments.amount\_vnd}$.
    3. Tổng tiền hoàn trả: $\sum \text{refunds.amount\_vnd}$ (với $\text{status} = \text{'SUCCEEDED'}$) so khớp với $\sum \text{silver\_refunds.amount\_vnd}$.
  * **Cơ chế ngắt mạch (Circuit Breaker)**: Nếu bất kỳ chỉ tiêu đối soát nào có tỷ lệ sai lệch vượt ngưỡng $0.05\%$, hệ thống lập tức ném ngoại lệ `ReconciliationGateError`, ngắt toàn bộ pipeline và phát tín hiệu cảnh báo khẩn cấp, **tuyệt đối không xuất bản dữ liệu sang tầng Gold**.

* **Chốt kiểm tra chất lượng hậu xuất bản (Post-Gold Quality Gate)**:
  * Được thực thi bởi module `quality.py` ngay sau khi các bảng Dimension, Fact và Data Mart hoàn tất ghi dữ liệu.
  * Thực hiện bộ **18 chỉ tiêu kiểm tra tự động** tuân thủ 5 khía cạnh chất lượng theo tiêu chuẩn quốc tế ISO/IEC 25012:2008 [17]:
    1. *Tính đầy đủ (Completeness)*: Kiểm tra khớp tuyệt đối số dòng giữa Silver Orders/Order Items và Fact Order/Fact Order Item (`silver_to_gold_row_count`).
    2. *Tính chính xác tài chính (Accuracy)*: Đối soát chính xác $100\%$ doanh thu gộp giữa Silver Orders và Fact Order (`silver_to_gold_gross_revenue_vnd`).
    3. *Tính duy nhất và không rỗng (Uniqueness & Non-null)*: Kiểm tra khóa chính không chứa giá trị null và không bị trùng lặp trên 5 bảng trọng yếu (`fact_order`, `fact_order_item`, `dim_customer`, `dim_product`, `dim_variant`).
    4. *Tính toàn vẹn tham chiếu (Referential Integrity)*: Thực hiện phép nối `left_anti` giữa `fact_order_item` với `dim_product` và `dim_variant`, bảo đảm không tồn tại khóa ngoại mồ côi (Zero Orphan Keys).
    5. *Tính tươi mới của mẻ nạp (Data Freshness)*: Xác nhận mã phiên chạy hiện tại `_source_run_id` xuất hiện hợp lệ trong các bảng đích (`fact_order`, `fact_order_item`, `mart_sales_daily`).
    6. *Tính hợp lệ mã hóa bảo mật (Pseudonymization Validity)*: Kiểm tra toàn bộ các trường PII (`email`, `phone`, `full_name` tại `dim_customer` và `phone`, `full_name` tại `dim_delivery_staff`) phải khớp chính xác với định dạng mã băm hex 64 ký tự của SHA-256 (`^[0-9a-f]{64}$`), bảo đảm không có dữ liệu văn bản rõ bị rò rỉ.
  * Toàn bộ kết quả đối soát của cả hai giai đoạn được ghi vết bền vững vào bảng siêu dữ liệu hệ thống `lakehouse.system.data_quality_results` để phục vụ kiểm toán và theo dõi độ tin cậy của dữ liệu theo thời gian.

#### **2. Thiết kế bảo mật đa tầng và kiểm soát truy cập (Security & RBAC)**
Kiến trúc an toàn thông tin của hệ thống Lakehouse được phân định rõ ràng thành hai bình diện: Bảo mật tầng ứng dụng và Bảo mật tầng hạ tầng tính toán:

* **Bảo mật ứng dụng và quyền dữ liệu người dùng**:
  * Phân tách nghiêm ngặt quyền hạn người dùng theo mô hình RBAC: Khách hàng (Storefront) chỉ truy xuất dữ liệu cá nhân qua mã định danh JWT; Nhân viên vận hành cửa hàng (POS/Admin) được phân quyền theo nhóm chức năng (quản lý kho, điều phối vận chuyển, chăm sóc khách hàng).
  * Hồ sơ xác thực mật khẩu người dùng (`argon2id`) được cô lập hoàn toàn tại cơ sở dữ liệu quan hệ giao dịch, không được phép chuyển tiếp vào bất kỳ tầng nào của Lakehouse. Toàn bộ các thông tin nhận dạng cá nhân khi đi vào tầng phân tích đều bắt buộc phải qua cơ chế Pseudonymization.

![Quyền ứng dụng và dữ liệu người dùng](docs/diagram/security-app.svg)

* **Bảo mật công cụ, Catalog và Phân vùng lưu trữ**:
  * **Apache Polaris REST Catalog RBAC [10]**: Toàn bộ quyền truy cập siêu dữ liệu Iceberg được quản lý tập trung theo mô hình "RBAC as Code" thông qua cấu hình `infrastructure/polaris/rbac.yml`:
    * `spark_writer`: Gán vai trò `spark_writer_catalog_role` với đặc quyền `CATALOG_MANAGE_CONTENT`, cho phép đọc/ghi dữ liệu trên toàn bộ các namespace (`landing`, `bronze`, `silver`, `gold`, `quarantine`, `system`).
    * `flink_writer`: Gán vai trò `flink_writer_catalog_role` dành riêng cho các tiến trình xử lý luồng CDC và Access Logs.
    * `trino_reader`: Gán vai trò `trino_reader_catalog_role` với các đặc quyền chỉ đọc khắt khe: `TABLE_READ_DATA`, `NAMESPACE_LIST`, `VIEW_READ_PROPERTIES`. Tuyệt đối không cấp quyền ghi (`MANAGE_CONTENT`) hay sửa đổi lược đồ bảng, bảo vệ kho dữ liệu Gold khỏi mọi hành vi can thiệp trái phép từ các công cụ BI và người dùng phân tích.
    * `trino_admin`: Gán vai trò `trino_admin_catalog_role` phục vụ các tác vụ bảo trì siêu dữ liệu và cấu hình nâng cao.
  * **Phân quyền lưu trữ đối tượng MinIO [8]**: Thiết lập 7 tài khoản định danh khối lượng công việc (Workload Identities) độc lập với các chính sách IAM chuyên biệt, ngăn chặn hoàn toàn việc chia sẻ khóa truy cập giữa các phân hệ và cô lập tài nguyên lưu trữ theo đúng phạm vi nhiệm vụ được giao.

![Quyền engine, catalog và object storage](docs/diagram/security-engines.svg)

## **3.6. Thiết kế giao diện và hệ thống Dashboard**

### **3.6.1. Thiết kế giao diện Storefront**

### **3.6.2. Thiết kế giao diện Admin**

### **3.6.3. Thiết kế Dashboard BI theo vai trò**

# **TÀI LIỆU THAM KHẢO**

[1] OECD, OECD Handbook on Compiling Digital Supply and Use Tables, 2023. https://www.oecd.org/en/publications/oecd-handbook-on-compiling-digital-supply-and-use-tables_11a0db02-en.html  
[2] Next.js, App Router Documentation. https://nextjs.org/docs/app  
[3] FastAPI, Features. https://fastapi.tiangolo.com/features/  
[4] Oracle, MySQL Reference Manual: Introduction to InnoDB. https://dev.mysql.com/doc/refman/8.4/en/innodb-introduction.html  
[5] SQLAlchemy, SQLAlchemy ORM Documentation. https://docs.sqlalchemy.org/en/20/orm/  
[6] OWASP, API Security Top 10. https://owasp.org/API-Security/  
[7] Armbrust, M. và cộng sự, Lakehouse: A New Generation of Open Platforms that Unify Data Warehousing and Advanced Analytics, CIDR, 2021. https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf  
[8] MinIO, S3 Compatibility. https://min.io/product/s3-compatibility  
[9] Apache Iceberg, Documentation. https://iceberg.apache.org/docs/latest/  
[10] Apache Polaris, Official Documentation. https://polaris.apache.org/  
[11] Microsoft Learn, Understand Star Schema and the Importance for Power BI. https://learn.microsoft.com/en-us/power-bi/guidance/star-schema  
[12] Apache Spark, JDBC To Other Databases. https://spark.apache.org/docs/latest/sql-data-sources-jdbc.html  
[13] Debezium, Connector for MySQL. https://debezium.io/documentation/reference/stable/connectors/mysql.html  
[14] Apache Kafka, Introduction. https://kafka.apache.org/intro/  
[15] Apache Flink, Stateful Stream Processing. https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/stateful-stream-processing/  
[16] Apache Airflow, DAGs. https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html  
[17] ISO/IEC, ISO/IEC 25012:2008 – Data Quality Model. https://www.iso.org/standard/35736.html  
[18] Trino, Iceberg Connector. https://trino.io/docs/current/connector/iceberg.html  
[19] Tableau, Best Practices for Effective Dashboards. https://help.tableau.com/current/pro/desktop/en-us/dashboards_best_practices.htm  
[20] Apache ECharts, Handbook. https://echarts.apache.org/handbook/en/get-started/