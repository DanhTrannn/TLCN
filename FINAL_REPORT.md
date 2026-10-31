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

Giao diện cửa hàng trực tuyến (Storefront) của D&K được xây dựng trên nền tảng Next.js 15 App Router [2], hướng đến việc tối ưu hóa tỷ lệ chuyển đổi (Conversion Rate Optimization - CRO), mang lại trải nghiệm mua sắm mượt mà với thời gian tải trang dưới $1.5\text{ giây}$ (đáp ứng NFR-01). Hệ thống áp dụng triết lý thiết kế tối giản (Minimalist Design), cấu trúc trực quan, phản hồi tức thời trên cả thiết bị di động lẫn máy tính để bàn, đồng thời tuân thủ các tiêu chuẩn về khả năng tiếp cận người dùng (WCAG 2.1).

Dưới đây là thiết kế chi tiết các màn hình nghiệp vụ trọng tâm của Storefront:

#### **1. Giao diện Danh sách sản phẩm (`/products`)**
* **Thanh điều hướng tiện ích (Global Header)**: Cố định ở đầu trang, tích hợp logo nhận diện thương hiệu D&K, ô tìm kiếm từ khóa tức thì với cơ chế giảm tải truy vấn (Debounced Search), liên kết nhanh đến danh mục yêu thích (Wishlist), biểu tượng giỏ hàng kèm huy hiệu số lượng động (Dynamic Cart Badge), và menu quản lý tài khoản người dùng.
* **Bộ lọc thuộc tính đa chiều (Faceted Filtering Sidebar)**: Bố trí ở cột bên trái, cho phép khách hàng thu hẹp phạm vi tìm kiếm theo nhiều tiêu chí kết hợp: danh mục thời trang (Áo, Quần, Phụ kiện), kích thước chuẩn (S, M, L, XL), màu sắc trực quan, thanh trượt khoảng giá linh hoạt, và công tắc lọc sản phẩm còn hàng tại kho (`in_stock_only`).
* **Khu vực hiển thị danh mục sản phẩm (Product Grid)**:
  * Trình đơn sắp xếp linh hoạt: Hỗ trợ phân loại theo "Mới nhất", "Giá tăng dần", "Giá giảm dần", hoặc "Bán chạy nhất".
  * Thẻ sản phẩm (Product Card): Trình bày ảnh đại diện sắc nét, tên sản phẩm, đơn giá niêm yết kèm nhãn giảm giá (nếu có), các nút tác vụ nhanh như "Xem nhanh" (Quick View) và "Thêm vào yêu thích".
  * Cơ chế tải thêm nội dung: Hỗ trợ nút bấm "Tải thêm" kết hợp phân trang nhằm tối ưu dung lượng tải ban đầu của trang web.

![Storefront — Danh sách sản phẩm](docs/diagram/ui-products.svg)

#### **2. Giao diện Chi tiết sản phẩm (`/products/[slug]`)**
* **Thư viện hình ảnh sản phẩm (Media Gallery)**: Đặt ở cột bên trái với khung hiển thị ảnh lớn chất lượng cao, tích hợp tính năng phóng to chi tiết (Zoom on Hover) và danh sách ảnh thu nhỏ đa góc chụp giúp khách hàng quan sát rõ chất liệu, đường may.
* **Khu vực thông tin sản phẩm và lựa chọn biến thể**:
  * Tên sản phẩm, mã định danh, thương hiệu và đơn giá bán lẻ niêm yết rõ ràng.
  * **Bộ chọn biến thể động (Dynamic Variant Selector)**: Cho phép khách hàng chọn màu sắc và kích cỡ. Hệ thống tự động liên kết với dữ liệu tồn kho thực tế của SKU để hiển thị trạng thái khả dụng (làm mờ hoặc vô hiệu hóa các tùy chọn đã hết hàng) và cập nhật đơn giá tức thời.
  * Bộ điều chỉnh số lượng mua cùng nút thao tác chính nổi bật: "Thêm vào giỏ hàng" (Add to Cart) và "Mua ngay" (Buy Now).
* **Mô tả chi tiết và Hướng dẫn chọn kích cỡ**: Bảng thông số kích thước (Size Guide) chi tiết, hướng dẫn bảo quản sản phẩm và chính sách đổi trả hàng minh bạch trong vòng 7 ngày.
* **Khu vực đánh giá từ cộng đồng (Customer Reviews)**: Điểm đánh giá trung bình tổng thể, biểu đồ phân bổ sao đánh giá (1 đến 5 sao), và danh sách phản hồi thực tế từ những khách hàng đã hoàn tất mua hàng kèm hình ảnh trải nghiệm.

![Storefront — Chi tiết sản phẩm](docs/diagram/ui-product-detail.svg)

#### **3. Giao diện Thanh toán đơn hàng (`/checkout`)**
Giao diện thanh toán được thiết kế theo mô hình Một trang hai cột (Two-Column Single Page Checkout) nhằm giảm thiểu tỷ lệ bỏ dở giỏ hàng:
* **Cột trái — Thông tin giao nhận và Phương thức thanh toán**:
  * Form nhập liệu người nhận: Họ tên, số điện thoại liên hệ, email nhận hóa đơn, địa chỉ giao hàng cụ thể (tỉnh/thành phố, quận/huyện, phường/xã, số nhà, tên đường) và ghi chú giao vận.
  * Tùy chọn giao hàng: Giao hàng tiêu chuẩn hoặc Giao hàng hỏa tốc.
  * Lựa chọn phương thức thanh toán an toàn: Thanh toán khi nhận hàng (COD) hoặc Thanh toán chuyển khoản ngân hàng tự động qua mã VietQR động sinh tức thời.
* **Cột phải — Tóm tắt đơn hàng và Mã giảm giá**:
  * Danh sách rút gọn các mặt hàng trong giỏ kèm hình ảnh, kích cỡ, màu sắc, số lượng và thành tiền.
  * Ô nhập mã khuyến mãi (Coupon Code) tích hợp nút kiểm tra tính hợp lệ tức thời qua API, tự động tính toán lại mức giảm giá.
  * Bảng phân tích chi phí minh bạch: Tạm tính tiền hàng, Mức giảm giá khuyến mãi, Phí vận chuyển, và Tổng số tiền thanh toán cuối cùng (`total_vnd`).
  * Nút hành động nổi bật: "Đặt hàng ngay" (Commit Order) với hiệu ứng khóa nút chống bấm đúp (Debounced Submit) khi đang trong tiến trình xử lý giao dịch.

![Storefront — Thanh toán đơn hàng](docs/diagram/ui-checkout.svg)

---

### **3.6.2. Thiết kế giao diện Admin**

Phân hệ Quản trị (Admin Web Console) phục vụ các bộ phận nội bộ của D&K bao gồm: Ban quản lý, Quản lý kho hàng, Nhân viên điều phối giao vận và Bộ phận bán lẻ tại cửa hàng. Giao diện được thiết kế theo nguyên tắc mật độ thông tin cao (High Information Density), giảm thiểu số lần nhấp chuột và tối ưu hóa luồng thao tác nghiệp vụ hàng ngày:

* **Thanh điều hướng bên trái (Navigation Sidebar)**: Cung cấp lối tắt truy cập nhanh vào các phân hệ nghiệp vụ độc lập: Tổng quan hệ thống, Báo cáo & Phân tích, Quản trị đơn hàng, Quản lý danh mục & sản phẩm, Quản trị nhập kho & tồn kho, Điều phối giao vận, Tiếp nhận đổi trả, và Quản lý mã giảm giá.

Dưới đây là chi tiết thiết kế 2 màn hình quản trị nghiệp vụ cốt lõi:

#### **1. Giao diện Quản lý đơn hàng (`/admin/orders`)**
* **Thanh công cụ lọc và tìm kiếm đa năng**:
  * Tìm kiếm nhanh theo mã đơn hàng (`order_number`), tên khách hàng hoặc số điện thoại người nhận.
  * Bộ lọc trạng thái đơn hàng trực quan: Toàn bộ, Chờ xác nhận (`PENDING`), Đã xác nhận (`CONFIRMED`), Đang giao hàng (`SHIPPING`), Đã giao thành công (`DELIVERED`), Đã hủy (`CANCELLED`).
  * Bộ lọc phân kênh: Kênh trực tuyến Storefront hoặc Cửa hàng bán lẻ vật lý (kèm chọn điểm bán cụ thể).
* **Bảng dữ liệu danh sách đơn hàng (Orders Data Grid)**:
  * Trình bày danh sách đơn hàng có cấu trúc: Mã đơn, Thời gian tạo, Khách hàng, Kênh bán, Trạng thái thanh toán (huy hiệu màu phân định rõ: Đã thanh toán, Chưa thanh toán, Đã hoàn tiền), Trạng thái vận chuyển, và Tổng giá trị tiền tệ.
* **Khung chi tiết đơn hàng (Drawer / Modal View)**:
  * Khi nhân viên bấm chọn một đơn hàng, màn hình trượt hiển thị toàn bộ thông tin chi tiết: danh sách sản phẩm cấu thành, lịch sử dòng thời gian biến động trạng thái (Audit Timeline), thông tin người nhận và địa chỉ giao hàng.
  * Các nút thao tác nghiệp vụ tương ứng với trạng thái hiện tại: "Xác nhận đơn", "Tạo phiếu giao vận", hoặc "Hủy đơn hàng kèm lý do".

![Admin — Quản lý đơn hàng](docs/diagram/ui-admin-orders.svg)

#### **2. Giao diện Nhập hàng và Cập nhật kho (`/admin/inbound`)**
Giao diện phục vụ trực tiếp quy trình nhập hàng hóa từ nhà cung cấp về các kho vật lý và tự động kích hoạt thuật toán tính toán lại giá vốn bình quân gia quyền di động:
* **Khối thông tin phiếu nhập hàng (Inbound Receipt Header)**:
  * Lựa chọn kho tiếp nhận (Store / Central Warehouse).
  * Nhập mã số phiếu nhập, số hóa đơn từ nhà cung cấp, ngày nhập kho thực tế và ghi chú nội bộ.
* **Bảng kê chi tiết các mặt hàng nhập kho (Inbound Line Items)**:
  * Thanh tra cứu nhanh SKU theo mã vạch hoặc tên sản phẩm.
  * Bảng nhập liệu động cho phép thêm nhiều dòng sản phẩm, chỉ định chính xác biến thể SKU, số lượng thực nhận (`quantity`), và đơn giá nhập mua trước thuế (`cost_price_vnd`).
  * Hệ thống tự động tính toán tổng số lượng mặt hàng và tổng giá trị lô hàng nhập kho.
* **Nút xác nhận "Ghi nhận phiếu nhập kho"**:
  * Kích hoạt giao dịch ACID tại máy chủ: tăng số lượng tồn kho khả dụng tại bảng `inventory_levels`, lưu lịch sử nhập hàng vào `inbound_receipts` và `inbound_items`, đồng thời tính toán lại giá vốn bình quân di động (Moving Weighted Average Cost) cho các SKU tương ứng để phục vụ tính toán lợi nhuận tại Lakehouse.

![Admin — Nhập hàng và cập nhật kho](docs/diagram/ui-admin-inbound.svg)

---

### **3.6.3. Thiết kế Dashboard BI theo vai trò**

Hệ thống Dashboard phân tích kinh doanh (BI Hub) của D&K được thiết kế dựa trên các nguyên lý chuẩn mực về trực quan hóa dữ liệu kinh doanh của Tableau [19] và thư viện Apache ECharts [20], hướng tới mục tiêu: "Tổng quan trước, lọc và thu phóng theo nhu cầu, chi tiết theo yêu cầu" (Overview first, zoom and filter, then details-on-demand).

Giao diện BI Hub kết nối trực tiếp đến động cơ truy vấn phân tán Trino [18] để khai thác các bảng Data Marts và Fact Tables tại tầng Gold của Lakehouse, đồng thời tích hợp cơ chế suy thoái có giới hạn (Bounded OLTP Fallback) giúp bảng điều khiển duy trì hoạt động ngay cả khi hồ dữ liệu đang trong chu kỳ bảo trì định kỳ.

Hệ thống phân định bảng điều khiển theo 7 vai trò người dùng trong doanh nghiệp: Điều hành (Executive), Kinh doanh (Sales), Tiếp thị (Marketing), Quản lý cửa hàng (Store), Quản lý kho (Inventory), Vận hành (Operations), và Kỹ thuật hệ thống (System).

#### **1. Bảng điều khiển Chiến lược và Kinh doanh (Executive & Sales Hub)**
Dành riêng cho Ban Giám đốc điều hành (Executive) và Trưởng phòng kinh doanh (Sales Manager):
* **Khối thẻ chỉ số hiệu suất trọng yếu (Executive KPI Cards)**:
  * **Doanh thu gộp (Gross Revenue)**: Tổng giá trị hàng hóa ghi nhận trên toàn hệ thống, kèm phần trăm tăng trưởng so với kỳ đo trước (MoM / YoY).
  * **Doanh thu thuần (Net Revenue)**: Doanh thu thực nhận sau khi trừ chiết khấu khuyến mãi và hoàn trả.
  * **Lợi nhuận gộp danh nghĩa (Gross Margin %)**: Tỷ lệ chênh lệch giữa doanh thu thuần và giá vốn hàng bán snapshot (COGS).
  * **Tổng số lượng đơn hàng (Total Orders)** và **Giá trị trung bình trên một đơn (AOV - Average Order Value)**.
* **Biểu đồ xu hướng doanh thu và lợi nhuận (Revenue & Profit Trend)**:
  * Trực quan hóa chuỗi thời gian doanh thu và chi phí vốn theo các khung thời gian linh hoạt (7 ngày, 30 ngày, 90 ngày) sử dụng biểu đồ vùng kết hợp đường (Area / Line Chart) [20].
* **Biểu đồ phân rã kênh và điểm bán (Channel & Store Distribution)**:
  * Biểu đồ tỷ trọng doanh thu giữa kênh trực tuyến Storefront và hệ thống các cửa hàng vật lý, giúp nhà điều hành so sánh hiệu quả đa kênh (Omnichannel Performance).
* **Bảng chi tiết số liệu kinh doanh**: Cho phép tìm kiếm, lọc nhanh theo từng chi nhánh/kênh bán và xuất tệp dữ liệu báo cáo dạng CSV/Excel.

![BI Hub — Executive / Sales](docs/diagram/ui-dashboard-sales.svg)

#### **2. Bảng điều khiển Vận hành đa phân hệ (Operations, Store, Inventory & System Hub)**
Thiết kế chuyên biệt cho các nhà quản lý nghiệp vụ vận hành hàng ngày:
* **Góc nhìn Quản lý cửa hàng (Store Manager View)**:
  * Theo dõi doanh số bán hàng tại quầy thu ngân POS theo ca làm việc của từng chi nhánh.
  * Giám sát danh sách các mặt hàng bán chạy nhất tại cửa hàng (Top-Selling Items) và mức tồn kho sẵn có trên quầy để kịp thời luân chuyển hàng từ kho trung tâm.
* **Góc nhìn Quản trị kho hàng (Inventory Health View)**:
  * Giám sát chỉ số ngày tồn kho bình quân (Days of Inventory On-Hand - DIO) và tốc độ quay vòng tồn kho.
  * Khối cảnh báo rủi ro hết hàng (Stock-out Risk Alert): Tự động phát hiện các SKU có tốc độ bán cao nhưng lượng tồn kho dưới ngưỡng an toàn 7 ngày để nhân viên chủ động lập phiếu nhập hàng.
  * Khối nhận diện hàng chậm luân chuyển (Dead Stock / Slow-moving Items): Liệt kê các mã hàng không phát sinh giao dịch trên 60 ngày để đề xuất chương trình khuyến mãi giải phóng mặt bằng kho.
* **Góc nhìn Điều phối giao vận & Xử lý đổi trả (Logistics & Returns View)**:
  * Theo dõi tỷ lệ đơn giao thành công ngay lần đầu (First-Attempt Delivery Rate) và thời gian giao hàng trung bình (Lead Time).
  * Bảng xếp hạng hiệu suất đối tác giao hàng (3PL SLA Performance), cảnh báo tỷ lệ giao trễ hẹn theo từng khu vực địa lý.
  * Biểu đồ phân tích cơ cấu lý do trả hàng (Hàng lỗi nhà sản xuất, khách thử không vừa kích cỡ, giao sai màu), cung cấp thông tin phản hồi giá trị cho bộ phận kiểm định chất lượng sản phẩm.
* **Góc nhìn Kỹ thuật & Chất lượng hệ thống (System & Quality View)**:
  * Theo dõi lưu lượng yêu cầu (Request Volume), thời gian xử lý phân vị p95/p99 của API và tỷ lệ mã lỗi 4xx/5xx theo từng endpoint.
  * Giám sát trạng thái thực thi của 18 chỉ tiêu Quality Gate và kết quả đối soát tự động của Lakehouse.

![BI Hub — Vận hành theo vai trò](docs/diagram/ui-dashboard-operations.svg)

# **CHƯƠNG 4. TRIỂN KHAI HỆ THỐNG**

## **4.1. Môi trường và kiến trúc triển khai**

### **4.1.1. Cấu trúc dự án và môi trường phát triển**

Hệ thống D&K E-Commerce Lakehouse Platform được tổ chức và quản lý theo mô hình kho mã nguồn hợp nhất (**Monorepo**). Cấu trúc này cho phép quản lý vòng đời phát triển của toàn bộ các phân hệ từ ứng dụng Web giao dịch, dịch vụ Backend API, đường ống kỹ thuật dữ liệu Lakehouse, cấu hình hạ tầng container, đến bộ công cụ sinh dữ liệu mô phỏng trong cùng một kho lưu trữ duy nhất, đảm bảo tính đồng bộ phiên bản và kiểm soát phụ thuộc chặt chẽ [5].

Cấu trúc cây thư mục tổng thể của dự án được phân cấp như sau:

```text
dk-ecommerce-data-platform/
├── apps/
│   └── storefront/              # Ứng dụng Web Storefront & Admin Console (Next.js 15, TypeScript, TailwindCSS)
├── services/
│   └── ecommerce-api/           # Dịch vụ Backend REST API nghiệp vụ (FastAPI, Python 3.12, SQLAlchemy 2.0 ORM)
├── pipelines/                   # Thư viện xử lý dữ liệu Lakehouse (Apache Spark & Apache Flink Streaming)
│   └── src/lakehouse/
│       ├── landing.py           # Trích xuất dữ liệu MySQL sang tệp Parquet và manifest tại Landing
│       ├── oltp/                # Pipeline xử lý dữ liệu OLTP (Bronze, Silver, Gold, Reconcile, Quality)
│       └── logs/                # Pipeline xử lý dữ liệu Access Log & Clickstream đa tầng
├── airflow/                     # Bộ điều phối quy trình trích xuất và xử lý dữ liệu định kỳ (Airflow 2.10)
│   └── dags/                    # Chứa DAG định kỳ lakehouse_oltp_pipeline
├── infrastructure/              # Tệp cấu hình hạ tầng, phân quyền và kết nối dịch vụ
│   ├── polaris/                 # Cấu hình RBAC-as-Code và đồng bộ vai trò Apache Polaris Catalog
│   ├── trino/                   # Cấu hình catalog kết nối Polaris Iceberg cho Trino
│   ├── debezium/                # Cấu hình Kafka Connect và Debezium MySQL Connector
│   └── flink/                   # Cấu hình Flink Cluster và các script submit streaming job
├── database/                    # Định nghĩa cơ sở dữ liệu quan hệ giao dịch MySQL 8.4
│   ├── schema.sql               # Kịch bản DDL khởi tạo 28 bảng dữ liệu quan hệ và 50 khóa ngoại
│   └── seeds/                   # Kịch bản sinh dữ liệu mẫu ban đầu (danh mục, cửa hàng, tài khoản)
├── generator/                   # Bộ công cụ sinh dữ liệu mô phỏng giao dịch và truy cập web đa kênh
├── scripts/                     # Kịch bản tự động hóa vận hành (start_all.sh, stop_all.sh, verify_pipeline.py)
├── docs/                        # Tài liệu kỹ thuật, tài liệu thiết kế và bộ sơ đồ kiến trúc hệ thống
├── docker-compose.yml           # Tệp điều phối toàn bộ 28 container dịch vụ của hệ thống
├── pyproject.toml / uv.lock     # Quản lý phụ thuộc môi trường Python qua công cụ Astral uv
└── Makefile                     # Lệnh tắt chuẩn hóa điều khiển và vận hành nền tảng
```

Về môi trường phát triển cục bộ và quản trị phụ thuộc:
* **Môi trường Python (Backend, Lakehouse Pipelines, Scripts)**: Sử dụng công cụ quản lý gói thế hệ mới `uv` (Astral), giúp tăng tốc độ phân giải và cài đặt gói phụ thuộc gấp 10–100 lần so với `pip` truyền thống. Toàn bộ các thư viện được định nghĩa tại `pyproject.toml` và khóa phiên bản chính xác thông qua `uv.lock`, vận hành trên nền tảng Python 3.12 và môi trường ảo hóa `.venv` độc lập.
* **Môi trường Node.js (Frontend Storefront & Admin)**: Ứng dụng giao diện được xây dựng trên Node.js v20 LTS, sử dụng `npm` quản lý các phụ thuộc Next.js 15, React 19, Lucide Icons và TailwindCSS v3.
* **Bộ công cụ kiểm định chất lượng mã nguồn (Code Quality & Testing Tooling)**:
  * `ruff`: Thực hiện kiểm tra quy chuẩn viết mã (linting) và tự động định dạng mã nguồn Python tuân thủ nghiêm ngặt tiêu chuẩn PEP 8.
  * `pytest`: Thực thi tự động hệ thống kiểm thử đơn vị (unit tests) và kiểm thử tích hợp (integration tests) cho backend API và các module tính toán Lakehouse.
  * `tsc` (TypeScript Compiler): Kiểm tra an toàn kiểu tĩnh cho toàn bộ mã nguồn giao diện người dùng Storefront (`npm run typecheck`).

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.1: Cấu trúc thư mục dự án và môi trường phát triển trên IDE]**
> * **Nội dung cần chụp**: Giao diện IDE (Visual Studio Code hoặc PyCharm) mở cây thư mục gốc của dự án `dk-ecommerce-data-platform` ở thanh bên trái (Sidebar) hiển thị rõ các thư mục `apps`, `services`, `pipelines`, `infrastructure`, `airflow`, `database`, `docker-compose.yml`.
> * **Cửa sổ Terminal tích hợp bên dưới**: Đang chạy thành công các lệnh kiểm tra phiên bản công cụ:
>   ```bash
>   python --version       # Python 3.12.x
>   uv --version           # uv 0.x.x
>   node --version         # v20.x.x
>   docker compose version # Docker Compose version v2.x.x
>   ```

---

### **4.1.2. Triển khai các dịch vụ bằng Docker Compose**

Hệ thống đóng gói và cô lập toàn bộ hạ tầng phần mềm thành 28 dịch vụ container độc lập, được khai báo tập trung trong tệp `docker-compose.yml`. Nhằm tối ưu hóa tài nguyên phần cứng máy chủ phát triển và cho phép vận hành linh hoạt theo từng kịch bản thử nghiệm, hệ thống áp dụng kỹ thuật **Compose Profiles** để phân chia các dịch vụ thành 3 nhóm phụ tải chuyên biệt:

1. **Profile `core` (Hạ tầng dịch vụ nền tảng)**: Gồm các dịch vụ cốt lõi bắt buộc để hệ thống thương mại điện tử và lưu trữ Lakehouse hoạt động cơ bản (MySQL 8.4, FastAPI Backend, Next.js Storefront, MinIO S3 Storage, PostgreSQL Metadata, Apache Polaris REST Catalog, và Trino Query Engine).
2. **Profile `batch` (Hạ tầng xử lý dữ liệu theo lô)**: Bổ sung cụm phân tán Apache Spark (Master, Worker, Client) và cụm điều phối Apache Airflow (Webserver, Scheduler).
3. **Profile `streaming` (Hạ tầng dữ liệu thời gian thực)**: Bổ sung cụm truyền thông điệp Apache Kafka (chế độ KRaft), Debezium Connect thu thập CDC, cụm tính toán luồng Apache Flink (JobManager, TaskManager), và các container nộp tác vụ luồng tự động.

Bảng 4.1 tổng hợp thông số kỹ thuật, cổng dịch vụ và trách nhiệm của 28 container trong hệ thống:

| STT | Tên dịch vụ (Service) | Hình ảnh Container (Image / Build) | Cổng Host (Port) | Profile | Vai trò và chức năng trong hệ thống |
| :---: | :--- | :--- | :---: | :---: | :--- |
| 1 | `mysql` | `mysql:8.4.3` | `3306:3306` | `core` | Cơ sở dữ liệu giao dịch OLTP chính (InnoDB Engine, bật binlog ROW). |
| 2 | `mysql-cdc-init` | Custom script container | - | `streaming` | Khởi tạo tài khoản, cấp quyền CDC và cấu hình kiểm tra trạng thái MySQL. |
| 3 | `ecommerce-api` | `./services/ecommerce-api` | `8000:8000` | `core` | Máy chủ REST API nghiệp vụ bán hàng, xác thực JWT, và ghi nhận access logs. |
| 4 | `storefront` | `./apps/storefront` | `3000:3000` | `core` | Giao diện người dùng Web Storefront, quầy POS và Admin Web Console. |
| 5 | `minio` | `minio/minio:RELEASE.2024-10-13` | `9000, 9001` | `core` | Lưu trữ đối tượng S3-compatible cho các phân tầng Lakehouse (Landing, Bronze, Silver, Gold). |
| 6 | `minio-init` | `minio/mc:RELEASE.2024-10-14` | - | `core` | Tự động tạo bucket `lakehouse`, cấu hình chính sách truy cập và tài khoản dịch vụ. |
| 7 | `postgres` | `postgres:16-alpine` | `5432:5432` | `core` | Cơ sở dữ liệu lưu siêu dữ liệu (Metadata DB) cho Apache Polaris Catalog và Apache Airflow. |
| 8 | `polaris-bootstrap` | Custom SQL client | - | `core` | Khởi tạo lược đồ quan hệ và cơ sở dữ liệu nội bộ cho Polaris trên PostgreSQL. |
| 9 | `polaris` | `apache/polaris:latest` | `8181:8181` | `core` | Máy chủ Apache Polaris REST Catalog quản lý metadata bảng Apache Iceberg theo chuẩn mở. |
| 10 | `polaris-init` | Custom Python script | - | `core` | Tự động đồng bộ cấu hình RBAC-as-Code từ `rbac.yml`, cấp quyền truy cập catalog cho các engine. |
| 11 | `polaris-console` | `ghcr.io/duckdb/duckdb:latest` | `8183:8183` | `core` | Giao diện Web Console quản lý catalog, namespace và bảng dữ liệu Iceberg của Polaris. |
| 12 | `spark-master` | `apache/spark:3.5.3` | `7077, 8080` | `batch` | Nút điều phối trung tâm của cụm tính toán phân tán Apache Spark (RPC và Web UI). |
| 13 | `spark-worker` | `apache/spark:3.5.3` | `8081:8081` | `batch` | Nút thực thi tính toán phân tán Apache Spark (chạy các tác vụ nạp và biến đổi dữ liệu). |
| 14 | `spark-client` | Custom build w/ pipeline pkg | - | `batch` | Môi trường đóng gói thư viện `lakehouse` để nộp các job Spark xử lý mẻ. |
| 15 | `airflow-init` | `apache/airflow:2.10.2` | - | `batch` | Khởi tạo cấu trúc bảng siêu dữ liệu Airflow và tạo tài khoản quản trị mặc định. |
| 16 | `airflow-webserver`| `apache/airflow:2.10.2` | `8085:8080` | `batch` | Giao diện Web quản trị và giám sát tiến độ thực thi của các DAGs Airflow. |
| 17 | `airflow-scheduler`| `apache/airflow:2.10.2` | - | `batch` | Bộ lập lịch kích hoạt định kỳ các pipeline trích xuất dữ liệu Lakehouse. |
| 18 | `trino` | `trinodb/trino:468` | `8084:8080` | `core` | Động cơ truy vấn SQL phân tán hiệu năng cao, kết nối trực tiếp đến Polaris Iceberg Catalog. |
| 19 | `trino-admin` | `trinodb/trino:468` | - | `core` | CLI client phục vụ kiểm thử truy vấn và quản trị cấu hình catalog Trino. |
| 20 | `libredb-studio` | `dbeaver/cloudbeaver:24.2.0` | `3001:8978` | `core` | Giao diện Web SQL Client trực quan giúp phân tích viên truy vấn dữ liệu MySQL và Trino. |
| 21 | `kafka` | `confluentinc/cp-kafka:7.7.1` | `9092, 9094` | `streaming`| Nền tảng phân tán luồng sự kiện (chạy chế độ KRaft độc lập, không cần Zookeeper). |
| 22 | `kafka-init` | Custom init script | - | `streaming`| Tự động tạo sẵn các topic Kafka: `cdc.ecommerce.*` và `ecommerce.access-logs`. |
| 23 | `debezium-connect`| `debezium/connect:2.7.3.Final`| `8086:8083` | `streaming`| Dịch vụ Kafka Connect chạy connector Debezium đọc log nhị phân MySQL CDC. |
| 24 | `debezium-init` | Custom curl runner | - | `streaming`| Đăng ký cấu hình MySQL CDC Connector với Debezium Connect qua REST API. |
| 25 | `flink-jobmanager`| `apache/flink:1.19.1-scala_2.12` | `8082:8081` | `streaming`| Nút điều phối chính của cụm tính toán luồng thời gian thực Apache Flink. |
| 26 | `flink-taskmanager`| `apache/flink:1.19.1-scala_2.12`| - | `streaming`| Nút công nhân thực thi các toán tử xử lý luồng sự kiện của Flink. |
| 27 | `flink-submit` | Custom submission container | - | `streaming`| Tự động nộp (submit) tác vụ luồng Flink ghi nhận và làm giàu Access Logs. |
| 28 | `flink-cdc-submit`| Custom submission container | - | `streaming`| Tự động nộp tác vụ luồng Flink tiêu thụ dữ liệu CDC và cập nhật Bronze Iceberg. |

Quy trình kích hoạt và điều phối toàn bộ hạ tầng được đóng gói thông qua kịch bản tự động hóa `scripts/start_all.sh` (hoặc lệnh tắt `make up`):
1. **Kiểm tra môi trường**: Tự động xác thực sự tồn tại của tệp `.env` và nạp toàn bộ các biến cấu hình cần thiết.
2. **Khởi chạy đồng thời**: Thực thi lệnh `docker compose --profile core --profile batch --profile streaming up -d` để khởi động đồng thời cả 3 profile.
3. **Thăm dò sức khỏe (Healthcheck Polling)**: Kịch bản liên tục thăm dò trạng thái hoạt động của các cổng dịch vụ then chốt (MySQL, MinIO, Polaris REST API, Kafka, Flink Web, Trino Engine) cho đến khi toàn bộ đạt trạng thái sẵn sàng tiếp nhận yêu cầu (`healthy`).
4. **Khởi tạo tự động lược đồ Lakehouse**: Tự động kiểm tra sự tồn tại của bảng Gold Marts (`mart_sales_daily`) trên Trino; nếu chưa có, kịch bản tự động điều phối `spark-client` thực thi tệp DDL `init_gold_marts.sql` để thiết lập trước toàn bộ cấu trúc bảng phân tích.
5. **Xuất bảng chỉ mục dịch vụ**: In bảng tra cứu trực quan toàn bộ các địa chỉ truy cập (URL) và tài khoản quản trị để người dùng sẵn sàng thao tác.

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.2: Kết quả thực thi script khởi chạy toàn bộ hệ thống `start_all.sh`]**
> * **Nội dung cần chụp**: Màn hình Terminal khi chạy hoàn tất lệnh `make up` (hoặc `./scripts/start_all.sh`), hiển thị thông báo kiểm tra sức khỏe thành công và bảng tổng hợp các dịch vụ nền tảng:
>   * Customer Storefront: `http://localhost:3000`
>   * Admin Management: `http://localhost:3000/admin`
>   * BI Analytics Hub: `http://localhost:3000/admin/analytics`
>   * FastAPI Swagger Docs: `http://localhost:8000/docs`
>   * Trino Query Engine: `http://localhost:8084`
>   * Airflow Web UI: `http://localhost:8080`
>   * Flink Streaming Dashboard: `http://localhost:8085`
>   * MinIO Storage Console: `http://localhost:9001`
>   * Apache Polaris REST Console: `http://localhost:8183`

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.3: Danh sách các container hoạt động trên Docker Compose / Docker Desktop]**
> * **Nội dung cần chụp**: Cửa sổ Terminal hiển thị kết quả lệnh `make ps` (hoặc `docker compose ps`), thể hiện danh sách đầy đủ 28 container đang ở trạng thái `Up / healthy`; hoặc ảnh chụp từ ứng dụng Docker Desktop hiển thị nhóm container `dk-ecommerce-data-platform` đang hoạt động ổn định màu xanh.

---

### **4.1.3. Cấu hình kết nối giữa các thành phần**

Để đảm bảo khả năng liên lạc thông suốt, an toàn và dễ bảo trì giữa 28 dịch vụ độc lập, kiến trúc triển khai áp dụng 3 trụ cột kỹ thuật kết nối:

#### **1. Kiến trúc mạng ảo nội bộ (Docker Bridge Network)**
Toàn bộ các container được kết nối chung vào một mạng ảo duy nhất mang tên `lakehouse-network` được khai báo trong `docker-compose.yml` (`driver: bridge`). 
* **Phân giải tên miền nội bộ (Docker Embedded DNS)**: Các dịch vụ liên lạc với nhau hoàn toàn thông qua tên định danh dịch vụ (`service hostname`) thay vì dựa vào địa chỉ IP tĩnh. Ví dụ:
  * Máy chủ FastAPI kết nối đến cơ sở dữ liệu quan hệ qua chuỗi kết nối: `mysql+pymysql://ecommerce_user:***@mysql:3306/ecommerce_db`.
  * Trino kết nối đến danh mục Polaris REST Catalog qua: `http://polaris:8181/api/catalog`.
  * Trino và Spark kết nối đến kho đối tượng S3 nội bộ qua: `http://minio:9000`.
  * Debezium kết nối đến cụm truyền thông điệp qua: `kafka:9092`.
* **Cô lập an ninh mạng**: Các cổng nhạy cảm (như cổng nội bộ của Debezium Connect `8083` hoặc cổng kết nối MySQL gốc `3306`) được giới hạn ràng buộc (bind) vào `127.0.0.1` trên máy chủ chủ quản (Host Machine) hoặc chỉ mở nội bộ trong Docker Network, ngăn chặn hoàn toàn việc thâm nhập trái phép từ bên ngoài mạng Internet.

#### **2. Quản lý cấu hình tập trung qua tệp biến môi trường (`.env`)**
Hệ thống sử dụng tệp `.env` (được sao chép và thiết lập từ `.env.example`) làm nguồn thông tin cấu hình duy nhất (**Single Source of Truth**), quản lý toàn diện các tham số hoạt động:
* **Cấu hình Cơ sở dữ liệu**: Định nghĩa tài khoản quản trị (`MYSQL_ROOT_PASSWORD`), tài khoản ứng dụng (`MYSQL_USER`, `MYSQL_PASSWORD`), tên cơ sở dữ liệu (`ecommerce_db`) và các thông số kết nối pool SQLAlchemy.
* **Cấu hình Hồ dữ liệu & Catalog**: Xác định Bucket lưu trữ chính (`LAKEHOUSE_BUCKET=lakehouse`), khóa xác thực MinIO (`MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`), địa chỉ kho hàng Polaris (`POLARIS_WAREHOUSE_LOCATION=s3://lakehouse/warehouse`) và Realm định danh (`POLARIS_REALM=POLARIS`).
* **Cấu hình Dịch vụ Luồng**: Địa chỉ máy chủ phân phối thông điệp (`KAFKA_BOOTSTRAP_SERVERS=kafka:9092`), cổng kết nối Debezium (`CDC_CONNECT_PORT=8086`), và đường dẫn lưu trữ checkpoint của Apache Flink (`FLINK_CHECKPOINT_DIR=s3://lakehouse/checkpoints`).
* **Cấu hình Bảo mật & Khóa bí mật**: Chuỗi khóa mã hóa token xác thực (`JWT_SECRET_KEY`), thời hạn hiệu lực của token, và chuỗi muối ngẫu nhiên (`SECURITY_SALT`) phục vụ việc mã hóa một chiều (Pseudonymization) các trường thông tin nhạy cảm của người dùng trước khi nạp vào Lakehouse.

#### **3. Cơ chế chia sẻ thông tin xác thực động qua Docker Volumes (Dynamic Credential Sharing)**
Nhằm tuân thủ nguyên tắc an toàn thông tin đặc quyền tối thiểu và loại bỏ nguy cơ rò rỉ khóa bí mật (Hard-coded Credentials) trong mã nguồn, hệ thống thiết kế cơ chế cấp phát quyền động thông qua Apache Polaris và chia sẻ qua Docker Volumes:
* Dịch vụ `polaris-init` (thực thi script `sync_polaris_rbac.py`) tự động đọc tệp khai báo vai trò `infrastructure/polaris/rbac.yml`, tạo lập các tài khoản ủy thác (Principals) gồm `spark_writer`, `flink_writer`, `trino_reader`, `trino_admin`.
* Polaris tự sinh các cặp khóa OAuth2 (`client_id` và `client_secret`) tạm thời và xuất ra các thư mục volume riêng biệt:
  * `/run/polaris-output/spark-client` (phân quyền gắn POSIX `uid: 185, gid: 185`) $\rightarrow$ gắn kết trực tiếp vào container `spark-client` và `airflow-scheduler`.
  * `/run/polaris-output/flink` (phân quyền `uid: 9999, gid: 9999`) $\rightarrow$ gắn kết vào `flink-jobmanager` và `flink-taskmanager`.
  * `/run/polaris-output/trino-reader` (phân quyền `uid: 1000, gid: 1000`) $\rightarrow$ gắn kết vào container `trino`.
* Nhờ cơ chế này, Trino và Spark tự động nạp thông tin xác thực định danh OAuth2 trực tiếp từ tệp volume lúc khởi động để kết nối an toàn đến Polaris Catalog mà không cần bất kỳ sự can thiệp thủ công nào từ phía quản trị viên.

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.4: Cấu trúc tệp biến môi trường mẫu `.env.example` và cấu hình mạng `lakehouse-network`]**
> * **Nội dung cần chụp**: Cửa sổ soạn thảo mã nguồn hiển thị tệp `.env.example` với các nhóm biến môi trường được phân loại mạch lạc (Database, Lakehouse Storage, Polaris, Kafka, Security); kết hợp cửa sổ Terminal chạy lệnh kiểm tra mạng nội bộ `docker network inspect dk-ecommerce-data-platform_lakehouse-network`, hiển thị danh sách các container đang kết nối cùng dải địa chỉ IP nội bộ (`172.x.x.x`).

## **4.2. Xây dựng Backend và cơ sở dữ liệu giao dịch**

### **4.2.1. Khởi tạo cơ sở dữ liệu**

Cơ sở dữ liệu giao dịch của hệ thống D&K được xây dựng trên hệ quản trị cơ sở dữ liệu quan hệ MySQL 8.4 [4]. Toàn bộ cấu trúc thực thể, quan hệ và các ràng buộc toàn vẹn được định nghĩa tập trung trong tệp kịch bản DDL `database/schema.sql`, bao gồm **28 bảng vật lý** và **50 ràng buộc khóa ngoại (Foreign Keys)** (đã được phân tích chi tiết tại mục 3.4).

Các đặc tính kỹ thuật cốt lõi trong quá trình khởi tạo cơ sở dữ liệu:
* **Chuẩn hóa bảng mã và đối chiếu ký tự**: Toàn bộ các bảng được thiết lập bảng mã ký tự `CHARACTER SET utf8mb4` kết hợp phép đối chiếu `COLLATE utf8mb4_unicode_ci`, đảm bảo hỗ trợ đầy đủ tiếng Việt có dấu, các ký tự đa ngôn ngữ và các biểu tượng cảm xúc (emoji) trong nội dung đánh giá sản phẩm của người dùng.
* **Động cơ lưu trữ và tối ưu hóa CDC**: $100\%$ các bảng sử dụng động cơ lưu trữ `InnoDB` với khả năng hỗ trợ giao dịch ACID toàn vẹn. Máy chủ MySQL được cấu hình tham số bắt buộc để phục vụ thu thập dữ liệu thay đổi (CDC) qua Debezium:
  * `binlog_format = ROW`: Ghi lại chi tiết từng dòng dữ liệu bị biến động thay vì chỉ lưu câu lệnh SQL.
  * `binlog_row_image = FULL`: Ghi nhận toàn bộ hình ảnh trạng thái trước (`before`) và sau (`after`) của dòng dữ liệu trong log nhị phân.
  * `transaction_isolation = READ-COMMITTED`: Tối ưu hóa hiệu năng khóa dòng và ngăn chặn hiện tượng đọc bẩn (dirty read).
* **Tự động hóa nạp cấu trúc (Automated Initialization)**: Tệp `database/schema.sql` được gắn kết tự động vào thư mục `/docker-entrypoint-initdb.d/` của container `mysql`. Khi container khởi động lần đầu tiên, hệ thống sẽ tự động thực thi kịch bản tạo lập toàn bộ lược đồ cơ sở dữ liệu `ecommerce_db` mà không cần can thiệp thủ công.
* **Kịch bản nạp dữ liệu mầm ban đầu (Idempotent Database Seeding)**:
  * Quá trình nạp dữ liệu mẫu được thực thi thông qua kịch bản Python `database/seeds/seed_catalog.py` (chạy qua lệnh `make seed`).
  * **Tính tất định và bất biến (Deterministic & Idempotent)**: Kịch bản sử dụng thuật toán sinh UUIDv5 dựa trên không gian tên chuẩn `uuid.NAMESPACE_URL` kết hợp khóa `web:catalog`. Nhờ đó, các mã định danh công khai (`public_id`) của danh mục, sản phẩm và biến thể luôn được sinh ra nhất quán qua các lần chạy lại, cho phép kịch bản tự động bỏ qua (skip) nếu dữ liệu danh mục đã tồn tại.
  * Dữ liệu mầm bao gồm: 3 danh mục gốc (Áo, Quần, Phụ kiện), 7 dòng sản phẩm thời trang thiết yếu kèm các biến thể kích cỡ/màu sắc, tài khoản quản trị viên gốc (`admin@web.local` với mật khẩu băm Argon2id), các cửa hàng vật lý mẫu (`store_id=1` Hà Nội, `store_id=2` TP.HCM), số dư tồn kho ban đầu, và mã giảm giá chào mừng (`WELCOME10`).

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.5: Giao diện quản trị cơ sở dữ liệu LibreDB Studio hiển thị cấu trúc 28 bảng quan hệ MySQL]**
> * **Nội dung cần chụp**: Giao diện Web SQL Client LibreDB Studio (truy cập `http://localhost:3001` hoặc DBeaver) kết nối đến cơ sở dữ liệu `ecommerce_db` tại cổng 3306.
> * **Cột cây đối tượng bên trái**: Hiển thị danh sách đầy đủ 28 bảng dữ liệu quan hệ (`orders`, `order_items`, `customers`, `products`, `product_variants`, `inventory_levels`, `shipments`, `payments`, `returns`, v.v.).
> * **Cửa sổ soạn thảo truy vấn SQL bên phải**: Thực thi câu lệnh kiểm tra:
>   ```sql
>   SELECT table_name, engine, table_rows 
>   FROM information_schema.tables 
>   WHERE table_schema = 'ecommerce_db' 
>   ORDER BY table_name;
>   ```
>   hiển thị kết quả trả về 28 bảng dữ liệu hoạt động trên động cơ InnoDB.

---

### **4.2.2. Xây dựng API xác thực và phân quyền**

Phân hệ xác thực và kiểm soát truy cập được triển khai trong module `services/ecommerce-api/app/modules/auth/` và `app/core/security.py`, tuân thủ các hướng dẫn an toàn thông tin OWASP API Security Top 10 [6]:

1. **Cơ chế băm mật khẩu chuẩn công nghiệp (Argon2id Hashing)**:
   * Hệ thống sử dụng thuật toán băm mật khẩu `Argon2id` (chuẩn RFC 9106) thông qua thư viện `pwdlib` / `passlib`.
   * Argon2id là thuật toán đạt giải nhất cuộc thi Password Hashing Competition (PHC), kết hợp cả khả năng chống tấn công kênh phụ (Side-channel Attack) của Argon2i và khả năng chống tấn công phần cứng chuyên dụng song song (ASIC/GPU Cracking) của Argon2d.
   * Mật khẩu người dùng được băm kèm chuỗi muối ngẫu nhiên (Salt) sinh tự động, lưu trữ an toàn trong bảng `customer_credentials`. Hệ thống tuyệt đối không lưu mật khẩu ở dạng văn bản rõ.

2. **Cơ chế cấp phát và kiểm thực JSON Web Token (JWT Authentication)**:
   * Khi người dùng đăng nhập thành công qua endpoint `POST /api/v1/auth/login`, hệ thống phát hành một mã khóa truy cập JWT (RFC 7519) được ký số bằng thuật toán đối xứng HMAC-SHA256 (`HS256`) với chuỗi khóa bí mật `JWT_SECRET_KEY`.
   * Cấu trúc Payload của JWT bao gồm các trường chuẩn hóa: `sub` (chứa định danh duy nhất `customer_id`), `role` (vai trò nghiệp vụ), `iat` (thời điểm phát hành) và `exp` (thời điểm hết hạn dựa trên `ACCESS_TOKEN_EXPIRE_MINUTES`).
   * **Bảo vệ Cookie đa lớp chống XSS**: Bên cạnh việc hỗ trợ gửi token qua tiêu đề `Authorization: Bearer <token>` phục vụ các API client, backend tự động đóng gói token vào Cookie mang tên `dk_access_token` với các cờ bảo vệ tối đa: `HttpOnly = True` (chặn JavaScript truy cập, triệt tiêu nguy cơ đánh cắp token qua lỗ hổng XSS), `Secure = True` (chỉ truyền qua HTTPS/môi trường phát triển an toàn), và `SameSite = 'lax'` (ngăn chặn tấn công CSRF).

3. **Cơ chế phân quyền dựa trên vai trò (Role-Based Access Control - RBAC)**:
   * Được hiện thực hóa thông qua cơ chế tiêm phụ thuộc (Dependency Injection) của FastAPI [3]:
     * `get_current_active_user`: Xác thực tính hợp lệ của token và nạp thông tin người dùng từ cơ sở dữ liệu.
     * `get_current_staff`: Ràng buộc bắt buộc tài khoản phải thuộc nhóm nhân sự nội bộ doanh nghiệp.
     * `require_roles(*roles)`: Bộ lọc kiểm tra vai trò người dùng trước khi chuyển tiếp yêu cầu vào tầng xử lý nghiệp vụ (Service Layer).
   * Hệ thống phân định rạch ròi quyền hạn giữa 6 vai trò người dùng trong doanh nghiệp:
     * `customer`: Chỉ có quyền thao tác trên giỏ hàng, thông tin cá nhân và đơn hàng do chính mình tạo ra.
     * `store_staff`: Nhân viên quầy thu ngân, được cấp quyền thao tác trên giao diện POS và tạo đơn hàng tại chi nhánh được chỉ định.
     * `store_manager`: Quản lý cửa hàng, có quyền xem báo cáo doanh số, kiểm soát tồn kho và nhân sự tại cửa hàng phụ trách.
     * `inventory_manager`: Quản lý kho trung tâm, có đặc quyền tạo và duyệt phiếu nhập hàng (`inbound_receipts`), điều chuyển tồn kho.
     * `operations_manager`: Quản lý giao vận và chăm sóc khách hàng, phụ trách điều phối phiếu giao hàng (`shipments`) và phê duyệt đổi trả (`returns`).
     * `admin`: Quản trị viên hệ thống, sở hữu toàn quyền trên mọi endpoint và phân hệ quản trị.

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.6: Tài liệu đặc tả API tương tác Swagger UI cho phân hệ Xác thực và Phân quyền]**
> * **Nội dung cần chụp**: Giao diện Swagger UI tại `http://localhost:8000/docs`, mở rộng nhóm tag **auth**, hiển thị đầy đủ danh sách các endpoint:
>   * `POST /api/v1/auth/register` (Đăng ký khách hàng mới)
>   * `POST /api/v1/auth/login` (Xác thực đăng nhập và nhận JWT token)
>   * `POST /api/v1/auth/logout` (Đăng xuất và hủy phiên làm việc)
>   * `GET /api/v1/auth/me` (Truy xuất hồ sơ định danh hiện tại)
> * Kèm nút "Authorize" ở góc trên bên phải hiển thị biểu tượng ổ khóa màu xanh lá (đã xác thực thành công Bearer Token).

---

### **4.2.3. Quản lý sản phẩm, giỏ hàng và đặt hàng**

1. **Phân hệ Danh mục và Tìm kiếm sản phẩm (`modules/catalog/`)**:
   * Cung cấp các endpoint công khai phục vụ Storefront: `GET /api/v1/products`, `GET /api/v1/products/{slug}`, và `GET /api/v1/categories`.
   * **Triệt tiêu vấn đề N+1 Query**: Ứng dụng SQLAlchemy 2.0 ORM [5] với kỹ thuật nạp dữ liệu sớm (Eager Loading) thông qua chỉ thị `selectinload(Product.variants)` và `selectinload(Product.images)`, giúp nạp toàn bộ danh mục sản phẩm và biến thể chỉ với 2 truy vấn SQL tối ưu thay vì phát sinh hàng trăm truy vấn con riêng lẻ.
   * Hỗ trợ tìm kiếm từ khóa không phân biệt hoa thường, bộ lọc đa chiều theo mức giá, danh mục, kích thước và màu sắc, kết hợp phân trang an toàn (`limit`, `offset`).

2. **Phân hệ Quản lý giỏ hàng (`modules/cart/`)**:
   * Kiến trúc hỗ trợ song song cả giỏ hàng người dùng đã đăng nhập (lưu vết trong cơ sở dữ liệu theo `customer_id`) và giỏ hàng của khách vãng lai (lưu trữ theo định danh phiên `session_id`).
   * Các API thao tác giỏ hàng: thêm sản phẩm, điều chỉnh số lượng mua, và xóa SKU khỏi giỏ. Mỗi thao tác đều tự động kiểm tra tính tương thích của biến thể và kiểm tra số lượng tồn khả dụng thực tế để cảnh báo người mua kịp thời.

3. **Phân hệ Đặt hàng và Điều phối thanh toán (`modules/checkout/`, `modules/orders/`)**:
   * **Mẫu thiết kế Unit of Work (UoW)**: Toàn bộ quy trình đặt hàng được đóng gói trong hàm `run_in_transaction` (`app/db/uow.py`), đảm bảo tính nguyên tử (Atomicity) theo chuẩn ACID: hoặc toàn bộ các bước (tạo đơn, tạo chi tiết đơn, trừ tồn kho, áp dụng voucher) thành công, hoặc tự động hoàn nguyên (Rollback) hoàn toàn nếu có bất kỳ ngoại lệ nào phát sinh.
   * **Cơ chế Khóa bi quan chống bán vượt tồn (Pessimistic Locking Anti-Overselling)**: Khi khách hàng nhấn đặt hàng, hệ thống thực thi câu lệnh SQL với khóa độc quyền:
     ```sql
     SELECT * FROM inventory_levels 
     WHERE store_id = :store_id AND variant_id = :variant_id 
     FOR UPDATE;
     ```
     Cơ chế này khóa chặn các giao dịch cạnh tranh khác đang cố gắng mua cùng một SKU tại cùng thời điểm, loại bỏ hoàn toàn hiện tượng bán vượt số lượng tồn thực tế (Race Condition / Overselling).
   * **Thuật toán cấp phát cửa hàng gần nhất (Nearest Store Allocation)**: Hệ thống tự động tính toán khoảng cách địa lý giữa địa chỉ nhận hàng của khách hàng và tọa độ các kho/cửa hàng vật lý nhằm chỉ định kho xuất hàng tối ưu nhất về chi phí và thời gian vận chuyển.
   * **Tự động thử lại lỗi giao dịch tạm thời (Transient Deadlock Retry)**: Trong môi trường chịu tải cao, nếu phát sinh lỗi tranh chấp khóa của MySQL (Mã lỗi 1213 - Deadlock hoặc 1205 - Lock wait timeout), Unit of Work tự động bắt lỗi và thực hiện thử lại giao dịch với thuật toán Exponential Backoff kết hợp độ trễ ngẫu nhiên (Jitter):
     $$\Delta t_{\text{retry}} = 2^{\text{attempt}} \times 0.05 + \text{random}(0, 0.05)\text{ (giây)}$$
   * **Chụp ảnh dữ liệu giao dịch lịch sử (Historical Snapshot)**: Tại thời điểm đơn hàng xác lập, hệ thống lưu giữ nguyên vẹn đơn giá bán (`unit_price_vnd`), giá vốn bình quân di động (`cost_price_vnd`), tên sản phẩm và mã SKU vào bảng `order_items`, bảo đảm số liệu doanh thu và lợi nhuận lịch sử không bao giờ bị sai lệch khi giá niêm yết trong danh mục thay đổi sau này.

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.7: Thao tác gửi yêu cầu Đặt hàng thành công trên Swagger UI]**
> * **Nội dung cần chụp**: Giao diện Swagger UI thực hiện thử nghiệm gọi endpoint `POST /api/v1/checkout` (hoặc `POST /api/v1/checkout/commit`), hiển thị:
>   * Cửa sổ Request Body: Dữ liệu JSON chứa thông tin người nhận, phương thức thanh toán `COD`, mã giảm giá `WELCOME10`, và danh sách các mặt hàng mua (`variant_id`, `quantity`).
>   * Cửa sổ Response: Trả về mã trạng thái HTTP `200 OK` (hoặc `201 Created`) kèm Response Body chứa mã đơn hàng thực tế (ví dụ: `ORD-20261031-XXXXX`), trạng thái đơn `PENDING`, tổng số tiền thanh toán `total_vnd`.

---

### **4.2.4. Quản lý kho, bán hàng POS và nhập hàng**

1. **Phân hệ Bán lẻ tại quầy POS (`modules/pos/`)**:
   * Phục vụ trực tiếp nhân viên thu ngân tại các cửa hàng vật lý thông qua endpoint chuyên biệt `POST /api/v1/pos/orders`.
   * Nhân viên quét mã SKU hoặc nhập mã vạch sản phẩm; hệ thống tự động kiểm tra số lượng tồn kho khả dụng tại chính cửa hàng phụ trách (`store_id` gắn với tài khoản nhân viên).
   * Khi thanh toán tiền mặt hoặc quẹt thẻ tại quầy, giao dịch được hoàn tất ngay lập tức: trạng thái đơn hàng được gán thẳng là `DELIVERED` (Đã giao khách tại quầy), thanh toán chuyển thành `PAID`, và số lượng tồn kho khả dụng tại cửa hàng được khấu trừ tức thời mà không cần tạo phiếu giao hàng qua các đơn vị 3PL.

2. **Phân hệ Nhập hàng và Điều chỉnh giá vốn (`modules/inbound/`)**:
   * Cung cấp endpoint quản trị `POST /api/v1/admin/inbound` cho phép Quản lý kho tạo lập các đợt nhập hàng từ nhà cung cấp về kho trung tâm hoặc các chi nhánh.
   * Dữ liệu phiếu nhập gồm: Kho tiếp nhận, số hóa đơn nhà cung cấp, ngày nhập kho và danh sách chi tiết các mặt hàng nhập (`inbound_items`) kèm số lượng thực nhận (`quantity`) và đơn giá nhập mua trước thuế (`cost_price_vnd`).
   * **Thuật toán tính toán lại Giá vốn bình quân gia quyền di động (Moving Weighted Average Cost)**: Được thực thi tự động bên trong giao dịch nhập hàng nhằm cập nhật giá trị vốn chuẩn cho SKU:
     $$\text{Cost}_{\text{new}} = \frac{(\text{Qty}_{\text{current}} \times \text{Cost}_{\text{current}}) + (\text{Qty}_{\text{inbound}} \times \text{Cost}_{\text{inbound}})}{\text{Qty}_{\text{current}} + \text{Qty}_{\text{inbound}}}$$
   * **Ghi nhật ký biến động kho (Inventory Audit Ledger)**: Mỗi sự kiện thay đổi số lượng tồn kho đều bắt buộc phải ghi vết một bản ghi tương ứng vào bảng `inventory_transactions` với các mã loại nghiệp vụ:
     * `INBOUND`: Nhập kho hàng mới từ nhà cung cấp (lượng biến động $> 0$).
     * `POS_SALE`: Bán hàng trực tiếp tại quầy (lượng biến động $< 0$).
     * `ONLINE_ALLOCATE`: Giữ chỗ hàng cho đơn mua trực tuyến (lượng biến động $< 0$).
     * `RETURN_RESTOCK`: Nhập lại kho hàng hoàn trả đạt chuẩn kiểm định (lượng biến động $> 0$).

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.8: Dữ liệu giao dịch biến động kho trong bảng `inventory_transactions`]**
> * **Nội dung cần chụp**: Cửa sổ truy vấn LibreDB Studio (hoặc MySQL CLI) thực thi câu lệnh SQL:
>   ```sql
>   SELECT transaction_id, store_id, variant_id, tx_type, quantity_delta, ending_quantity, created_at 
>   FROM inventory_transactions 
>   ORDER BY transaction_id DESC 
>   LIMIT 10;
>   ```
>   hiển thị danh sách các bản ghi nhật ký kho với đầy đủ các loại giao dịch `INBOUND`, `POS_SALE`, `ONLINE_ALLOCATE`, thể hiện rõ ràng số lượng thay đổi (`quantity_delta`) và số dư tồn kho cuối kỳ (`ending_quantity`).

---

### **4.2.5. Quản lý thanh toán, giao vận và đổi trả**

1. **Phân hệ Quản lý thanh toán và Hoàn tiền (`modules/payments/`)**:
   * Hỗ trợ hai phương thức thanh toán chủ đạo: Thanh toán khi nhận hàng (COD) và Thanh toán trực tuyến tự động qua mã **VietQR** (chuẩn chuyển khoản liên ngân hàng nhanh NAPAS 247).
   * Khi thanh toán thành công, hệ thống ghi nhận bản ghi tại bảng `payments`: số tiền giao dịch (`amount_vnd`), cổng thanh toán (`payment_gateway`), mã giao dịch ngân hàng đối soát (`gateway_transaction_id`) và chuyển trạng thái thành `SUCCEEDED`.
   * Nghiệp vụ hoàn tiền (`refunds`): Tự động phát hành bản ghi hoàn tiền khi đơn hàng bị hủy trước khi giao hoặc khi yêu cầu đổi trả hàng được ban quản trị phê duyệt.

2. **Phân hệ Quản lý giao vận và Điều phối (`modules/logistics/`)**:
   * Ngay khi đơn hàng trực tuyến chuyển sang trạng thái `CONFIRMED`, hệ thống tự động khởi tạo một phiếu giao vận tương ứng tại bảng `shipments`.
   * Endpoint điều phối `PATCH /api/v1/admin/logistics/shipments/{id}`: Cho phép nhân viên vận hành gán mã vận đơn (`tracking_number`), chỉ định đơn vị vận chuyển đối tác thứ ba (3PL: Giao Hàng Nhanh, Giao Hàng Tiết Kiệm, ViettelPost) hoặc đội ngũ giao hàng nội bộ (`delivery_staff_id`).
   * Quản lý tiến trình giao hàng qua các trạng thái chuẩn hóa: `PREPARING` (Đang đóng gói) $\rightarrow$ `IN_TRANSIT` (Đang vận chuyển) $\rightarrow$ `DELIVERED` (Giao thành công kèm chữ ký/hình ảnh xác nhận) hoặc `FAILED_DELIVERY` (Giao thất bại). Hệ thống tự động ghi nhận các mốc thời gian chuyển trạng thái để phục vụ tính toán các chỉ số hiệu năng vận chuyển (SLA Delivery Lead Time) tại Lakehouse.

3. **Phân hệ Tiếp nhận và Kiểm định đổi trả (`modules/returns/`)**:
   * Khách hàng hoặc bộ phận hỗ trợ gửi yêu cầu đổi trả qua endpoint `POST /api/v1/returns` trong thời hạn chính sách cho phép (7 ngày kể từ khi nhận hàng).
   * Bản ghi yêu cầu đổi trả được lưu trữ tại bảng `returns` kèm danh sách chi tiết các sản phẩm hoàn trả tại bảng `return_items`, ghi rõ phân loại lý do: `DAMAGED_ITEM` (Hàng hư hỏng), `WRONG_SIZE` (Không vừa cỡ), `NOT_AS_DESCRIBED` (Sai mô tả), hoặc `DEFECTIVE` (Lỗi kỹ thuật).
   * **Quy trình kiểm định chất lượng sản phẩm hoàn trả (Quality Inspection)**: Nhân viên kho thực hiện kiểm tra sản phẩm thực nhận và cập nhật kết quả kiểm định (`inspection_status`):
     * Nếu sản phẩm đạt chuẩn (`PASSED`): Hệ thống tự động nạp lại sản phẩm vào tồn kho khả dụng (`RETURN_RESTOCK`) tại `inventory_levels` và kích hoạt lệnh hoàn tiền tương ứng cho khách hàng.
     * Nếu sản phẩm bị hư hại do người dùng (`REJECTED`) hoặc là phế phẩm (`SCRAPPED`): Hệ thống từ chối hoàn tiền hoặc chuyển sản phẩm vào danh mục hàng hỏng cách ly, bảo vệ tính trung thực của kho hàng thương mại.

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.9: Giao diện Swagger UI quản trị phân hệ Giao vận và Tiếp nhận Đổi trả]**
> * **Nội dung cần chụp**: Giao diện Swagger UI mở rộng đồng thời 2 nhóm tag: **logistics** và **returns**, hiển thị các endpoint:
>   * `GET /api/v1/admin/logistics/shipments` (Danh sách phiếu giao vận cần điều phối)
>   * `PATCH /api/v1/admin/logistics/shipments/{id}/status` (Cập nhật trạng thái giao hàng)
>   * `POST /api/v1/returns` (Khởi tạo yêu cầu hoàn trả sản phẩm)
>   * `PATCH /api/v1/admin/returns/{return_code}/inspect` (Cập nhật kết quả kiểm định chất lượng hàng trả)

---

### **4.2.6. Ghi nhận Access Log**

Nhằm phục vụ phân tích hành vi người dùng, tối ưu hóa tỷ lệ chuyển đổi và theo dõi sức khỏe kỹ thuật của hệ thống, backend tích hợp bộ giải pháp ghi nhận nhật ký truy cập (Access Log) theo thời gian thực được thiết kế tại tầng middleware (`app/core/access_logging.py` và `app/core/middleware.py`):

1. **Cơ chế đánh chặn toàn diện (Global Request Interceptor)**:
   * Middleware được cấu hình ở lớp ngoài cùng của ứng dụng FastAPI, tự động bắt giữ toàn bộ các yêu cầu HTTP đi vào và các phản hồi HTTP trả về trước khi gửi tới trình duyệt của khách hàng.
   * Để đảm bảo không làm nhiễu dữ liệu phân tích, middleware tự động loại trừ (bypass) các yêu cầu kiểm tra sức khỏe hệ thống tự động: `GET /health/live` và `GET /health/ready`.

2. **Chuẩn hóa cấu trúc sự kiện theo lược đồ `ecommerce.access` v1.0.0**:
   * Mỗi sự kiện truy cập được đóng gói thành một cấu trúc dữ liệu JSON định dạng mạnh gồm các khối thông tin tiêu chuẩn:
     * **Siêu dữ liệu giao thức (`http`)**: Phương thức (`request_method`), mã trạng thái (`status_code`), và đặc biệt là đường dẫn tuyến đường chuẩn hóa (`canonical_route`). Việc sử dụng `canonical_route` (ví dụ `/api/v1/products/{slug}` thay vì URL cụ thể `/api/v1/products/ao-thun-basic`) giúp triệt tiêu hiện tượng nổ số lượng giá trị phân biệt (Cardinality Explosion) khi tổng hợp dữ liệu trên Lakehouse.
     * **Định danh tác nhân (`actor`)**: Phân loại đối tượng tương tác thành `anonymous` (khách vãng lai chưa đăng nhập), `customer` (khách hàng có tài khoản kèm `actor_key`), hoặc `staff` (nhân viên nội bộ).
     * **Thời gian xử lý (`event.duration_ns`)**: Đo lường thời gian xử lý yêu cầu của máy chủ với độ chính xác nano-giây.
     * **Mức độ nghiêm trọng (`severity`)**: Tự động phân loại `INFO` (mã trạng thái $2xx/3xx$), `WARN` (mã lỗi client $4xx$), hoặc `ERROR` (mã lỗi máy chủ $5xx$).

3. **Làm sạch và khử định danh dữ liệu nhạy cảm (PII Sanitization & Redaction)**:
   * Nhằm tuân thủ nguyên tắc bảo vệ quyền riêng tư người dùng (NFR-02) và các tiêu chuẩn bảo mật OWASP [6], middleware tích hợp bộ lọc biểu thức chính quy (Regex Engine) tự động nhận diện và che giấu các thông tin nhạy cảm:
     * Địa chỉ Email (`_EMAIL_PATTERN`), số điện thoại di động (`_PHONE_PATTERN`), số thẻ tín dụng (`_CARD_PATTERN`), chuỗi JWT Token (`_JWT_PATTERN`), các từ khóa chứa mật khẩu/secret (`_SECRET_PATTERN`), và địa chỉ nhà chi tiết (`_ADDRESS_PATTERN`).
     * Mọi chuỗi tìm kiếm của người dùng (`search_query`) hoặc chuỗi nhận diện trình duyệt (`user_agent`) chứa thông tin nhạy cảm đều được tự động thay thế bằng nhãn che giấu an toàn trước khi đẩy vào đường ống xử lý.

4. **Trích xuất ngữ cảnh nghiệp vụ thương mại điện tử chuyên sâu (`ecommerce_context`)**:
   * Middleware tự động ánh xạ cặp `(method, route)` thành các hành động nghiệp vụ chuẩn hóa:
     * `catalog_search`: Trích xuất từ khóa tìm kiếm và các tham số lọc kích cỡ, màu sắc, khoảng giá.
     * `product_detail`: Bóc tách mã định danh sản phẩm (`slug`).
     * `cart_item_set` / `cart_item_remove`: Bóc tách mã biến thể SKU được thêm hoặc xóa khỏi giỏ hàng.
     * `checkout_submit`: Ghi nhận sự kiện khách hàng tiến hành gửi đơn thanh toán.

5. **Phát tán luồng sự kiện bất đồng bộ vào Apache Kafka**:
   * Sử dụng cơ chế phát tán thông điệp bất đồng bộ của `AIOKafkaProducer` [14] đẩy các bản ghi sự kiện JSON vào topic `ecommerce.access-logs`.
   * Việc đẩy log vào Kafka được thực hiện hoàn toàn trong tác vụ nền bất đồng bộ (Non-blocking I/O / Background Task), đảm bảo **hoàn toàn không làm gia tăng độ trễ (Zero Overhead Latency)** đối với thời gian phản hồi giao diện người dùng.

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.10: Thông điệp sự kiện Access Log chuẩn hóa được tiêu thụ từ Kafka Topic]**
> * **Nội dung cần chụp**: Cửa sổ Terminal chạy lệnh tiêu thụ thông điệp từ Kafka Console Consumer:
>   ```bash
>   docker compose exec kafka kafka-console-consumer \
>     --bootstrap-server localhost:9092 \
>     --topic ecommerce.access-logs \
>     --from-beginning --max-messages 1
>   ```
> * Kết quả hiển thị một bản ghi sự kiện JSON có cấu trúc đẹp mắt (pretty-printed qua `jq`), thể hiện đầy đủ các trường: `schema.name = "ecommerce.access"`, `timestamp`, `event.duration_ns`, `http.route`, `http.status_code`, `actor.type`, và `ecommerce.action` (ví dụ `catalog_search` hoặc `product_detail`).

## **4.3. Xây dựng giao diện người dùng**

### **4.3.1. Giao diện Storefront**

Phân hệ giao diện cửa hàng trực tuyến (Storefront) được phát triển bằng khung làm việc **Next.js 15 App Router** kết hợp thư viện **React 19**, ngôn ngữ **TypeScript** và tiện ích thiết kế **TailwindCSS v3** [2]. Ứng dụng khai thác tối đa mô hình kết xuất hỗn hợp (Hybrid Rendering): tận dụng Server Components để kết xuất trước mã HTML tĩnh ở phía máy chủ nhằm tối ưu hóa chỉ số SEO và tốc độ hiển thị nội dung đầu tiên (First Contentful Paint - FCP), đồng thời kết hợp linh hoạt Client Components (`'use client'`) cho các khối giao diện đòi hỏi tính tương tác cao và quản lý trạng thái phức tạp.

Chi tiết hiện thực hóa các màn hình nghiệp vụ trọng tâm trên Storefront:

#### **1. Màn hình Danh mục và Tìm kiếm sản phẩm đa chiều (`/products`)**
* **Đồng bộ trạng thái tìm kiếm qua URL (Deep Linking & Bookmarkable URLs)**: Toàn bộ trạng thái của bộ lọc (từ khóa `q`, danh mục `category`, mảng kích thước `size`, mảng màu sắc `color`, khoảng giá `min_price`/`max_price`, trạng thái tồn kho `in_stock`, và tiêu chí sắp xếp `sort`) được đồng bộ hai chiều trực tiếp lên thanh địa chỉ trình duyệt qua `useSearchParams` và `useRouter`. Điều này cho phép khách hàng dễ dàng sao chép đường dẫn chia sẻ hoặc lưu lại kết quả tìm kiếm mà không bị mất trạng thái lọc.
* **Bộ lọc thuộc tính đa diện (Faceted Filter Sidebar)**: Dữ liệu bộ lọc được nạp động từ backend qua API `GET /api/v1/catalog/facets`, hiển thị chính xác số lượng sản phẩm khả dụng theo từng phân loại. Thành phần màu sắc được trực quan hóa thông qua các ô tròn màu chuẩn xác nhờ bộ tiện ích `getColorHex` và `getColorLabel`.
* **Cơ chế giảm tải truy vấn (Debounced Search)**: Khi người dùng gõ từ khóa vào thanh tìm kiếm, hệ thống áp dụng cơ chế trì hoãn (Debounce $300\text{ms}$) trước khi phát sinh yêu cầu API, ngăn chặn tình trạng gửi hàng chục request dư thừa gây nghẽn máy chủ.
* **Tối ưu hóa hình ảnh sản phẩm (Next.js Image Optimization)**: Sử dụng thành phần `next/image` với cơ chế tải lười (Lazy Loading), tự động chuyển đổi định dạng ảnh sang WebP/AVIF và tự điều chỉnh kích thước theo mật độ điểm ảnh của thiết bị (Responsive srcset), giảm trên $60\%$ dung lượng tải mạng.
* **Tương tác nhanh**: Tích hợp cửa sổ xem nhanh sản phẩm (`QuickViewModal`) và tính năng thêm vào danh sách yêu thích (`Wishlist`) cập nhật giao diện lạc quan (Optimistic UI Update) mang lại cảm giác mượt mà tức thời cho người dùng.

#### **2. Màn hình Chi tiết sản phẩm (`/products/[slug]`)**
* **Định tuyến động theo Slug thân thiện SEO**: Sử dụng tham số đường dẫn `params.slug` để truy xuất chi tiết sản phẩm qua API `GET /api/v1/products/{slug}`.
* **Bộ chọn biến thể thông minh hai chiều (Bidirectional Variant Selector)**:
  * Khi khách hàng chọn một kích thước (ví dụ: Size L), hệ thống tự động tính toán lại và làm mờ (disable) các tùy chọn màu sắc đã hết hàng của kích cỡ đó trong cơ sở dữ liệu.
  * Ngược lại, khi chọn một màu sắc, danh sách kích thước tương ứng cũng được cập nhật trạng thái khả dụng tức thời dựa trên dữ liệu thành phần `StoreAvailabilityBox`.
* **Thư viện ảnh sản phẩm độ nét cao (Zoom & Gallery)**: Cho phép chuyển đổi linh hoạt giữa các góc chụp thông qua danh sách ảnh thu nhỏ (Thumbnails) và phóng to chi tiết bề mặt vải khi di chuột.
* **Bảng hướng dẫn chọn cỡ (`SizeGuideModal`)**: Cung cấp số đo chi tiết (chiều cao, cân nặng, vòng ngực, vòng eo) giúp giảm thiểu tối đa tỷ lệ đổi trả hàng do chọn sai kích cỡ.
* **Ngăn kéo giỏ hàng động (`CartDrawer`)**: Khi người dùng nhấn nút "Thêm vào giỏ hàng", ứng dụng không chuyển trang mà kích hoạt ngăn kéo trượt mượt mà từ cạnh phải màn hình thông qua React Context (`useCartDrawer`), hiển thị tóm tắt giỏ hàng và nút tiến hành thanh toán nhanh.
* **Khối phản hồi và đánh giá cộng đồng (`ProductReviews`)**: Hiển thị điểm số trung bình (Star Rating), tỷ lệ phần trăm phân bổ sao và danh sách bình luận đã được quản trị viên kiểm duyệt (`status = 'APPROVED'`).

#### **3. Màn hình Giỏ hàng và Thanh toán hai cột (`/cart` & `/checkout`)**
* **Quản trị giỏ hàng trực quan (`/cart`)**: Cho phép người mua điều chỉnh tăng giảm số lượng mua theo thời gian thực, tự động tính toán lại mức giá ưu đãi và hiển thị thanh tiến trình thông báo điều kiện đạt mức miễn phí vận chuyển toàn quốc (Freeship).
* **Màn hình Thanh toán tinh gọn hai cột (`/checkout`)**:
  * **Cột trái (Địa chỉ nhận hàng & Phương thức)**: Tích hợp thư viện dữ liệu hành chính Việt Nam (`vietnam-addresses.ts`) hỗ trợ chọn liên hoàn: Tỉnh/Thành phố $\rightarrow$ Quận/Huyện $\rightarrow$ Phường/Xã. Khách hàng lựa chọn giữa hai hình thức: Trả tiền mặt khi nhận hàng (COD) hoặc Chuyển khoản nhanh qua VietQR.
  * **Cột phải (Báo giá thời gian thực & Mã giảm giá)**: Khi khách hàng thay đổi địa chỉ hoặc áp dụng voucher qua `CouponPickerModal`, ứng dụng gọi API báo giá `quoteCheckout` để nhận bảng phân rã chi phí minh bạch gồm: Tạm tính, Mức giảm giá voucher, Phí vận chuyển, và Tổng số tiền thanh toán cuối cùng.
  * **Thanh toán VietQR động**: Nếu chọn chuyển khoản, hệ thống tự động sinh và hiển thị mã QR theo chuẩn NAPAS 247 chứa đầy đủ thông tin: Ngân hàng thụ hưởng, Số tài khoản, Số tiền chính xác và Nội dung chuyển khoản chứa mã đơn hàng, giúp người mua quét mã thanh toán trong 3 giây mà không cần nhập liệu thủ công.

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.11: Giao diện Storefront trên trình duyệt Web (Desktop & Mobile Responsive)]**
> * **Nội dung cần chụp**: Trình duyệt Web truy cập trang chủ hoặc trang danh mục sản phẩm `http://localhost:3000/products`:
>   * Cửa sổ hiển thị thanh điều hướng Header, ô tìm kiếm từ khóa, danh mục sản phẩm.
>   * Cột bên trái hiển thị bộ lọc đa chiều (Faceted Sidebar: Danh mục, Kích thước, Màu sắc trực quan).
>   * Lưới hiển thị danh sách thẻ sản phẩm thời trang với hình ảnh WebP sắc nét, đơn giá niêm yết và nhãn giảm giá.
>   * (Tùy chọn): Bật chế độ Responsive Mode (F12 trên Chrome) cạnh bên để minh họa giao diện co giãn tối ưu trên thiết bị di động (iPhone / Android).

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.12: Quy trình chọn biến thể sản phẩm và đặt hàng thanh toán VietQR]**
> * **Nội dung cần chụp**: Ảnh ghép hoặc 2 ảnh thành phần:
>   1. Trang chi tiết sản phẩm `http://localhost:3000/products/[slug]`: Đang chọn màu sắc/kích cỡ và ngăn kéo giỏ hàng trượt ra từ bên phải màn hình (`CartDrawer`) hiển thị mặt hàng vừa chọn.
>   2. Màn hình thanh toán `http://localhost:3000/checkout`: Đã điền đầy đủ form thông tin người nhận, hiển thị khung tóm tắt đơn hàng bên phải và mã VietQR động thanh toán ngân hàng tự động.

---

### **4.3.2. Giao diện Admin**

Phân hệ Quản trị (Admin Web Console) được đặt tại không gian tuyến đường `/admin` và `/store`, phục vụ toàn bộ các hoạt động vận hành nội bộ của doanh nghiệp. Giao diện được thiết kế theo phong cách hiện đại với mật độ hiển thị dữ liệu cao, ưu tiên khả năng nắm bắt thông tin nhanh và thao tác nghiệp vụ một chạm cho nhân viên:

#### **1. Kiến trúc bố cục và Kiểm soát phân quyền (`AdminLayout`)**
* Toàn bộ các trang con trong phân hệ quản trị đều được bao bọc bởi `AdminLayout` (`apps/storefront/src/app/admin/layout.tsx`).
* **Kiểm tra phiên đăng nhập và định tuyến tự động**: Thành phần sử dụng hook `useAuth()`. Nếu phát hiện người dùng chưa đăng nhập hoặc không có vai trò nhân sự thuộc `STAFF_ROLES`, giao diện lập tức kích hoạt hiệu ứng tải bảo vệ (Security Pulse Skeleton) và chuyển hướng người dùng về trang đăng nhập `/login?returnTo=...`.
* **Thanh điều hướng Sidebar (`AdminNav`)**: Phân nhóm trực quan các phân hệ chức năng:
  * Nhóm Báo cáo: Tổng quan hệ thống (`/admin/overview`), Trung tâm phân tích BI (`/admin/analytics`).
  * Nhóm Thương mại: Quản lý đơn hàng (`/admin/orders`), Bán hàng tại quầy (`/admin/pos`), Mã giảm giá (`/admin/coupons`), Đánh giá khách hàng (`/admin/reviews`).
  * Nhóm Kho vận: Quản lý sản phẩm (`/admin/products`), Quản lý nhập kho (`/admin/inbound`), Điều phối giao vận (`/admin/logistics`), Tiếp nhận đổi trả (`/admin/returns`), Danh sách khách hàng (`/admin/customers`).
  * Tùy theo vai trò của người đăng nhập (ví dụ: nhân viên thu ngân chỉ thấy POS, quản lý kho chỉ thấy Inbound/Products), Sidebar sẽ tự động ẩn các phân hệ nằm ngoài phạm vi phân quyền.

#### **2. Màn hình Quản trị và Điều phối đơn hàng (`/admin/orders`)**
* **Hệ thống Tab trạng thái đơn hàng**: Phân chia đơn hàng thành các danh mục trực quan kèm số lượng: *Tất cả*, *Chờ xác nhận*, *Đã xác nhận*, *Đang giao hàng*, *Hoàn tất*, và *Đã hủy*.
* **Công cụ tìm kiếm và lọc kết hợp**: Hỗ trợ tìm kiếm theo mã đơn hàng (`order_number`), họ tên khách hàng, số điện thoại; kết hợp bộ lọc kênh bán lẻ (Kênh trực tuyến Storefront hoặc Cửa hàng vật lý) và khoảng thời gian tạo đơn.
* **Bảng dữ liệu tương tác (Interactive Orders Data Grid)**:
  * Hiển thị danh sách đơn hàng có cấu trúc: Mã đơn, Thời gian tạo (định dạng múi giờ Việt Nam qua `formatVietnamDateTime`), Khách hàng, Kênh bán, Trạng thái thanh toán, Trạng thái vận chuyển, và Tổng giá trị tiền tệ.
  * Các trạng thái được hiển thị dưới dạng huy hiệu màu trực quan (`OrderStatusBadge`): Xanh lá cho Đã thanh toán / Giao thành công, Vàng cam cho Đang xử lý, Đỏ cho Đã hủy.
* **Ngăn trượt / Hộp thoại xử lý đơn hàng (`AdminModal`)**:
  * Khi bấm chọn một đơn hàng, cửa sổ hiển thị đầy đủ danh sách SKU cấu thành kèm số lượng, đơn giá, địa chỉ nhận hàng và dòng thời gian lịch sử trạng thái đơn (Timeline).
  * Cung cấp các nút hành động nghiệp vụ trực tiếp tương ứng:
    * "Xác nhận đơn hàng" (`confirmAdminOrder`): Chuyển đơn sang trạng thái sẵn sàng đóng gói xuất kho.
    * "Điều phối giao vận" (`dispatchAdminOrder`): Mở danh sách chọn shipper nội bộ hoặc đối tác 3PL, gán mã vận đơn và chuyển trạng thái giao hàng.
    * "Hủy đơn hàng": Yêu cầu nhập lý do hủy đơn và tự động hoàn trả số lượng tồn kho khả dụng.
* **Tính năng xuất báo cáo CSV (`exportToCsv`)**: Cho phép nhân viên tải về toàn bộ danh sách đơn hàng theo bộ lọc hiện tại phục vụ công tác đối soát kế toán offline.

#### **3. Màn hình Quản trị Nhập kho và Cập nhật tồn (`/admin/inbound`)**
* **Khối thẻ chỉ số tổng quan (Header Metric Cards)**: Hiển thị 3 chỉ số then chốt trên đầu trang: Tổng số phiếu nhập kho (`totalCount`), Tổng số lượng sản phẩm nhập (`totalItems`), và Tổng giá trị vốn đã nhập kho (`totalCost` định dạng tiền tệ VND).
* **Bảng danh sách phiếu nhập kho phân trang**: Hỗ trợ tìm kiếm nhanh theo mã phiếu nhập hoặc số hóa đơn nhà cung cấp, hiển thị ngày nhập, kho tiếp nhận, người lập phiếu và trạng thái xử lý.
* **Hộp thoại lập phiếu nhập kho động (`CreateInboundModal`)**:
  * Giao diện cho phép chọn kho tiếp nhận (Kho trung tâm hoặc các chi nhánh cửa hàng), ngày nhập thực tế và ghi chú nguồn gốc lô hàng.
  * Bảng nhập liệu mặt hàng động (Dynamic Item Rows): Cho phép thêm/xóa nhiều dòng sản phẩm, hỗ trợ tìm kiếm nhanh theo mã vạch SKU hoặc tên sản phẩm, nhập số lượng thực nhận (`quantity`) và đơn giá nhập mua trước thuế (`cost_price_vnd`).
  * Thành phần tự động tính toán tổng thành tiền từng dòng và tổng giá trị phiếu nhập theo thời gian thực. Khi nhân viên nhấn "Ghi nhận phiếu nhập", hệ thống gửi yêu cầu API lên backend để đồng thời tăng số lượng tồn kho và tính toán lại giá vốn bình quân di động.

#### **4. Màn hình Bán lẻ tại quầy POS (`/admin/pos` hoặc `/store/pos`)**
* Được tối ưu hóa cho màn hình cảm ứng tại quầy thu ngân của các chi nhánh cửa hàng:
  * Ô quét mã vạch sản phẩm tự động thêm SKU vào giỏ hàng quầy với số lượng mặc định là 1.
  * Cột bên trái hiển thị danh mục sản phẩm trực quan kèm ảnh đại diện và số lượng tồn sẵn có tại quầy.
  * Cột bên phải là giỏ hàng quầy thu ngân: hiển thị danh sách mặt hàng, ô điều chỉnh số lượng, nút áp dụng mã giảm giá trực tiếp.
  * Khu vực thanh toán một chạm: Tự động tính tiền hàng, ô nhập số tiền khách đưa, tính tiền thừa thối lại và các nút chọn nhanh phương thức (Tiền mặt / Thẻ ngân hàng). Khi hoàn tất, hệ thống tự động ghi nhận đơn hàng POS thành công và in hóa đơn bán lẻ.

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.13: Giao diện quản trị đơn hàng `/admin/orders` và modal điều phối giao vận]**
> * **Nội dung cần chụp**: Trình duyệt Web truy cập `http://localhost:3000/admin/orders`:
>   * Thanh điều hướng Sidebar bên trái thể hiện đầy đủ các phân hệ quản trị.
>   * Bảng danh sách đơn hàng với các huy hiệu trạng thái màu sắc (`PENDING`, `CONFIRMED`, `SHIPPING`, `DELIVERED`).
>   * Cửa sổ Modal chi tiết đơn hàng đang mở hiển thị danh sách sản phẩm cấu thành, thông tin người nhận và các nút hành động "Xác nhận đơn" / "Điều phối giao vận".

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.14: Giao diện nhập kho `/admin/inbound` và màn hình bán hàng POS `/admin/pos`]**
> * **Nội dung cần chụp**: Ảnh ghép hoặc 2 ảnh thành phần:
>   1. Giao diện Nhập kho `http://localhost:3000/admin/inbound`: Hiển thị 3 thẻ chỉ số tổng quan (Tổng số phiếu, Tổng số lượng, Tổng giá trị vốn) và cửa sổ modal tạo phiếu nhập `CreateInboundModal` đang điền danh sách SKU nhập kèm số lượng và đơn giá.
>   2. Màn hình Bán hàng tại quầy POS `http://localhost:3000/admin/pos`: Hiển thị danh mục sản phẩm thời trang dạng lưới, giỏ hàng tại quầy thu ngân bên phải kèm các phím chức năng thanh toán nhanh.

## **4.4. Xây dựng hệ thống thu thập dữ liệu**

### **4.4.1. Thu thập dữ liệu MySQL theo lô**

Quy trình thu thập dữ liệu theo lô (Batch Ingestion) chịu trách nhiệm trích xuất định kỳ 27 bảng nghiệp vụ từ cơ sở dữ liệu quan hệ MySQL 8.4 [4] và nạp vào vùng lưu trữ đệm Landing trên MinIO S3 [8]. Quy trình được hiện thực hóa thông qua kịch bản Python `pipelines/src/jobs/oltp/extract_oltp.py` kết hợp thư viện lõi `pipelines/src/lakehouse/oltp/extract.py` chạy trên động cơ tính toán phân tán **Apache Spark 3.5.3** [12], dưới sự điều phối tự động của **Apache Airflow 2.10** [16].

Các cơ chế kỹ thuật cốt lõi của luồng trích xuất theo lô:
1. **Trích xuất tăng dần dựa trên Watermark (Incremental Pull)**:
   * Trạng thái con trỏ đọc (Cursor State) của từng bảng được lưu trữ bền vững dưới dạng tệp JSON tại đường dẫn: `s3a://lakehouse/state/cursor/<table>.json`.
   * Tệp con trỏ ghi nhận mốc thời gian cập nhật cao nhất (`high_watermark`) và khóa chính (`last_pk`) đã xử lý thành công ở mẻ trước. Khi khởi chạy, Spark nạp con trỏ đã cam kết thông qua hàm `read_committed_cursor` để xây dựng mệnh đề vị từ lọc dữ liệu mới phát sinh.
2. **Cơ chế Cửa sổ lùi chống rò rỉ giao dịch (Lookback Window Predicate)**:
   * Để khắc phục triệt để hiện tượng mất mát dữ liệu do độ trễ commit giao dịch (Commit Latency) hoặc sai lệch đồng hồ hệ thống giữa các máy chủ, hàm `build_range_predicate` tự động áp dụng cửa sổ lùi:
     $$\text{Watermark}_{\text{start}} = \text{Watermark}_{\text{previous}} - \Delta t_{\text{lookback}}$$
   * Tham số cửa sổ lùi được cấu hình linh hoạt theo đặc thù vòng đời dữ liệu của từng nhóm bảng:
     * $\Delta t_{\text{lookback}} = 10\text{ phút}$: Áp dụng cho các bảng danh mục ít biến động (như `products`, `categories`, `stores`).
     * $\Delta t_{\text{lookback}} = 3\text{ ngày}$: Áp dụng cho các bảng giao dịch có chu kỳ cập nhật trạng thái kéo dài (như `orders`, `order_status_history`, `shipments`, `refunds`).
3. **Thực thi trích xuất song song có kiểm soát (Parallel JDBC Extraction)**:
   * Spark sử dụng kết nối JDBC qua lớp điều khiển `com.mysql.cj.jdbc.Driver`. Nhằm tối ưu hóa thời gian trích xuất mà không làm quá tải tài nguyên CPU/Connection Pool của MySQL, hàm `run_extract` sử dụng `concurrent.futures.ThreadPoolExecutor` với tham số `max_parallel_tables` (mặc định cấu hình 4–8 luồng song song).
4. **Đóng gói dữ liệu Parquet và tạo tệp Kê khai nguyên tử (`manifest.json`)**:
   * Dữ liệu đọc từ MySQL được Spark ghi vào vùng lưu trữ đệm Landing theo cấu trúc phân cấp:
     `s3a://lakehouse/landing/oltp/<table>/<batch_id>/part-*.parquet`
   * Toàn bộ tệp dữ liệu được nén theo thuật toán **Snappy** nhằm cân bằng tối ưu giữa tỷ lệ nén và tốc độ giải nén khi xử lý ở các tầng sau.
   * Ngay sau khi ghi xong các tệp Parquet, hàm `_write_manifest` tạo lập tệp kê khai nguyên tử `manifest.json` (tuân thủ cấu trúc `MANIFEST_VERSION = "1.0.0"`) ghi nhận toàn diện siêu dữ liệu mẻ nạp: mã phiên chạy (`run_id`), tổng số dòng bản ghi (`rows`), cờ dữ liệu rỗng (`empty`), phạm vi con trỏ quét được (`cursor_min`, `cursor_max`), danh sách tên tệp kèm mã băm kiểm tra toàn vẹn SHA-256, và mốc thời gian trích xuất UTC chính xác. Tệp kê khai này là bằng chứng duy nhất để các tác vụ tầng sau xác thực tính toàn vẹn trước khi nạp vào Bronze.

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.15: Giao diện MinIO Console hiển thị tệp dữ liệu Parquet và `manifest.json` tại tầng Landing]**
> * **Nội dung cần chụp**: Trình duyệt Web truy cập MinIO Storage Console tại `http://localhost:9001`:
>   * Chọn bucket `lakehouse`, điều hướng theo cây thư mục: `landing` $\rightarrow$ `oltp` $\rightarrow$ `orders` $\rightarrow$ `<batch_id>/`.
>   * Khung nhìn hiển thị danh sách các tệp dữ liệu dạng `part-00000-*.snappy.parquet` kèm tệp `manifest.json`.
>   * Mở xem chi tiết nội dung tệp `manifest.json` thể hiện các trường: `manifest_version: "1.0.0"`, `table: "orders"`, `run_id`, `rows`, `extract_started_at`, `extract_completed_at`.

---

### **4.4.2. Thu thập CDC bằng Debezium, Kafka và Flink**

Bên cạnh luồng trích xuất theo mẻ, hệ thống triển khai đường ống thu thập dữ liệu thay đổi theo thời gian thực (Change Data Capture - CDC) nhằm bắt giữ tức thời mọi biến động giao dịch từ MySQL, đưa vào nền tảng Lakehouse với độ trễ dưới 1 giây mà không tạo tải truy vấn `SELECT` lên cơ sở dữ liệu nguồn:

1. **Bắt sự kiện giao dịch qua Debezium MySQL Connector [13]**:
   * Dịch vụ Debezium Connect chạy phân tán trên container `debezium-connect` (cổng nội bộ 8083, cổng host 8086).
   * Connector kết nối trực tiếp đến MySQL bằng tài khoản chuyên biệt, liên tục đọc và giải mã luồng log nhị phân giao dịch của InnoDB (`binlog_format = ROW` và `binlog_row_image = FULL`).
   * Khi phát sinh bất kỳ thao tác cơ sở dữ liệu nào, Debezium tự động phát hiện và đóng gói thành một thông điệp sự kiện JSON mang cấu trúc chuẩn:
     * Trường `op`: Định danh loại thao tác gồm `c` (Create/Insert), `u` (Update), `d` (Delete), và `r` (Snapshot ban đầu).
     * Trường `before`: Chứa toàn bộ giá trị các cột của dòng dữ liệu trước khi thay đổi.
     * Trường `after`: Chứa toàn bộ giá trị các cột của dòng dữ liệu sau khi cập nhật.
     * Trường `source`: Chứa siêu dữ liệu tọa độ giao dịch trong binlog gồm tên tệp (`file`), vị trí (`pos`), mốc thời gian máy chủ (`ts_ms`), và định danh luồng giao dịch.

2. **Truyền dẫn thông điệp qua cụm Apache Kafka (KRaft Mode) [14]**:
   * Cụm Kafka vận hành theo cơ chế mới **KRaft** (Kafka Raft Metadata Mode), loại bỏ hoàn toàn sự phụ thuộc vào Apache ZooKeeper, giúp đơn giản hóa kiến trúc và tăng tốc độ đồng thuận cụm.
   * Sự kiện biến động của 27 bảng dữ liệu được Debezium tự động định tuyến vào các topic Kafka tương ứng theo cấu trúc: `cdc.ecommerce.<table>` (ví dụ: `cdc.ecommerce.orders`, `cdc.ecommerce.inventory_levels`, `cdc.ecommerce.payments`).
   * Mỗi topic được cấu hình chính sách lưu trữ (Retention Policy) và phân vùng (Partitioning) dựa trên khóa chính của bảng nghiệp vụ, đảm bảo thứ tự tuần tự tuyệt đối của các biến động trên cùng một bản ghi.

3. **Tiêu thụ luồng và cập nhật tầng Bronze Iceberg bằng Apache Flink [15]**:
   * Tác vụ luồng được thực thi bởi kịch bản `pipelines/src/jobs/cdc/mysql_cdc_to_bronze.py` trên cụm Apache Flink 1.19.
   * Flink khởi tạo `TableEnvironment`, kết nối vào Kafka với nhóm tiêu thụ `flink-oltp-cdc-bronze-v1` và lắng nghe toàn bộ các topic khớp với biểu thức chính quy: `cdc\.ecommerce\..*`.
   * **Cơ chế Checkpoint bảo toàn trạng thái**: Flink thiết lập chu kỳ kiểm tra trạng thái định kỳ $10.000\text{ ms}$ ($10\text{ giây}$) với trạng thái được lưu trữ an toàn trên MinIO S3 (`FLINK_CHECKPOINT_DIR=s3://lakehouse/checkpoints`). Cơ chế này bảo đảm ngữ nghĩa xử lý chính xác một lần (Exactly-Once Processing Semantics) ngay cả khi cụm gặp sự cố phần cứng.
   * **Ghi nhật ký kiểm toán bất biến (Immutable Audit Log)**: Dữ liệu CDC được Flink nạp nối tiếp (Append-only) vào bảng Apache Iceberg `lakehouse.bronze.oltp_cdc_events` thông qua Apache Polaris REST Catalog. Bảng này lưu giữ vĩnh viễn toàn bộ lịch sử biến động dữ liệu kèm tọa độ Kafka và Binlog, đóng vai trò nguồn chân lý kiểm toán cho phép tái hiện trạng thái dữ liệu tại bất kỳ thời điểm nào trong quá khứ (Time-Travel / Event Replay).

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.16: Bảng điều khiển Flink Dashboard giám sát Job CDC và Kafka Topic `cdc.ecommerce.*`]**
> * **Nội dung cần chụp**: Ảnh ghép hoặc 2 ảnh thành phần:
>   1. Giao diện Flink Web Dashboard tại `http://localhost:8085`: Hiển thị job streaming `oltp_cdc_to_bronze` đang ở trạng thái `RUNNING` màu xanh lá, thể hiện biểu đồ đồ thị luồng (Dataflow Graph) và các thông số Checkpoint định kỳ 10 giây thành công.
>   2. Cửa sổ Terminal chạy lệnh kiểm tra trạng thái của Debezium MySQL Connector:
>      ```bash
>      curl -s http://127.0.0.1:8086/connectors/ecommerce-mysql-cdc/status | jq
>      ```
>      hiển thị connector đang hoạt động với `state: "RUNNING"` và worker task đang ở trạng thái `RUNNING`.

---

### **4.4.3. Thu thập và xử lý Access Log**

Nhằm thu thập trọn vẹn luồng dữ liệu hành vi người dùng (Clickstream) phục vụ phân tích phễu chuyển đổi và theo dõi kỹ thuật, hệ thống triển khai đường ống xử lý luồng sự kiện truy cập thời gian thực kết nối từ Middleware FastAPI đến Apache Flink và Apache Iceberg:

1. **Phát tán sự kiện từ Middleware Backend**:
   * Middleware trên FastAPI bắt giữ mọi yêu cầu HTTP, bóc tách ngữ cảnh nghiệp vụ (`catalog_search`, `product_detail`, `cart_item_set`, `checkout_submit`), che giấu thông tin cá nhân PII (Email, Phone, Card, Token) và gửi bất đồng bộ qua `AIOKafkaProducer` vào topic `ecommerce.access-logs`.
   * Luồng đẩy log diễn ra trong tiến trình nền không khóa (Non-blocking I/O), đảm bảo không tạo thêm bất kỳ độ trễ nào cho khách hàng duyệt web.

2. **Xử lý luồng đa tầng bằng Apache Flink Multi-Sink Pipeline**:
   * Tác vụ luồng được triển khai trong kịch bản `pipelines/src/jobs/logs/kafka_to_lakehouse.py` kết hợp thư viện `pipelines/src/lakehouse/logs/streaming.py`.
   * Flink sử dụng toán tử ánh xạ `ParseAccessLog` (kế thừa `MapFunction`) để phân tích cú pháp chuỗi JSON, kiểm thực cấu trúc dữ liệu theo schema `ecommerce.access` v1.0.0. Các sự kiện sai định dạng hoặc bị lỗi sẽ bị loại bỏ an toàn kèm log cảnh báo (`Rejected malformed access event`) mà không làm sập luồng xử lý.
   * Flink tự động đăng ký và xác thực danh mục Apache Polaris REST Catalog (`register_polaris_catalog`), đồng thời kích hoạt chế độ **Merge-on-Read** và **Upsert Mode** trên các bảng Iceberg đích.

3. **Ghi đồng thời xuống 4 tầng Lakehouse thông qua Flink `StatementSet`**:
   * Thay vì phải chạy nhiều luồng đọc Kafka độc lập gây lãng phí băng thông mạng, Flink sử dụng cơ chế `StatementSet` để đọc một lần từ Kafka và phân tán ghi đồng thời (Multi-Sink Execution) xuống 4 bảng Apache Iceberg:
     1. **`lakehouse.landing.access_logs`**: Tiếp nhận và lưu trữ toàn bộ sự kiện thô nguyên bản kèm tọa độ Kafka partition và offset.
     2. **`lakehouse.bronze.web_events`**: Phân tách cấu trúc các cột trường định dạng mạnh, gán nhãn thời gian và thiết lập cơ chế phân vùng theo ngày sự kiện.
     3. **`lakehouse.silver.silver_logs`**: Lọc bỏ các yêu cầu kiểm tra sức khỏe hệ thống, khử trùng lặp và làm giàu thông tin phiên truy cập của khách hàng.
     4. **`lakehouse.gold.fact_web_events`**: Tổng hợp và tính toán các chỉ số thống kê sự kiện theo khung cửa sổ thời gian (Tumbling / Sliding Window) phục vụ trực tiếp cho Dashboard phân tích kỹ thuật và chuyển đổi hành vi.

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.17: Đồ thị luồng xử lý Flink Multi-Sink cho sự kiện Access Log]**
> * **Nội dung cần chụp**: Giao diện Flink Web Dashboard tại `http://localhost:8085`:
>   * Nhấp chọn job streaming `kafka_to_lakehouse_pure_streaming`.
>   * Cửa sổ hiển thị biểu đồ đồ thị luồng xử lý (Dataflow Graph): Từ một nguồn đầu vào duy nhất `Source: KafkaSource` rẽ nhánh song song thành 4 luồng ghi (Sinks) xuống 4 bảng Iceberg tương ứng (`landing.access_logs`, `bronze.web_events`, `silver.silver_logs`, `gold.fact_web_events`).
>   * Bảng thống kê bên dưới hiển thị số lượng bản ghi (Records Sent / Records Received) tăng đều đặn theo thời gian thực khi người dùng thao tác trên Storefront.

## **4.5. Xây dựng nền tảng Data Lakehouse**

### **4.5.1. Triển khai hệ thống lưu trữ MinIO, Iceberg và Polaris**

Nền tảng Data Lakehouse của D&K được thiết lập trên sự kết hợp giữa ba công nghệ cốt lõi: hệ thống lưu trữ đối tượng tương thích S3 **MinIO** [8], định dạng bảng mở **Apache Iceberg** [9], và hệ thống quản lý danh mục siêu dữ liệu tập trung **Apache Polaris REST Catalog** [10]:

1. **Phân vùng lưu trữ đối tượng trên MinIO S3 (Bucket Partitioning)**:
   * Toàn bộ tài nguyên hồ dữ liệu được tập trung trong bucket duy nhất mang tên `lakehouse` (`s3://lakehouse/`).
   * Cấu trúc thư mục logic được phân định rạch ròi theo chức năng:
     * `s3://lakehouse/warehouse/`: Khu vực lưu trữ dữ liệu bảng Apache Iceberg cho các phân tầng Bronze, Silver và Gold.
     * `s3://lakehouse/landing/`: Vùng lưu trữ tệp thô tạm thời (Parquet mẻ OLTP và JSON log).
     * `s3://lakehouse/state/`: Vùng lưu giữ trạng thái con trỏ Watermark trích xuất theo mẻ (`cursor/<table>.json`).
     * `s3://lakehouse/checkpoints/`: Vùng lưu giữ trạng thái điểm kiểm tra (Checkpoints) của các job luồng Apache Flink.
   * Dịch vụ `minio-init` tự động thực thi khi khởi động hệ thống: tự động tạo bucket, thiết lập chính sách lưu trữ (Lifecycle Policies) và tạo các tài khoản dịch vụ (Service Accounts) với quyền truy cập tối thiểu.

2. **Quản lý danh mục siêu dữ liệu tập trung qua Apache Polaris REST Catalog [10]**:
   * Apache Polaris vận hành như một dịch vụ quản lý danh mục (Catalog Server) độc lập theo chuẩn giao thức mở Iceberg REST Catalog Specification, sử dụng cơ sở dữ liệu PostgreSQL 16 làm kho lưu trữ metadata nội bộ.
   * Polaris quản lý thống nhất 6 không gian tên (Namespaces) phục vụ toàn bộ quy trình xử lý dữ liệu:
     * `lakehouse.landing`: Các bảng dữ liệu tiếp nhận sự kiện thô.
     * `lakehouse.bronze`: Các bảng thô lưu giữ nguyên trạng và lịch sử biến động dữ liệu.
     * `lakehouse.silver`: Các bảng sạch, đã chuẩn hóa kiểu dữ liệu, khử trùng lặp và mã hóa PII.
     * `lakehouse.gold`: Các bảng Chiều (Dimensions), Sự kiện (Facts) và Data Marts phân tích.
     * `lakehouse.quarantine`: Không gian cách ly dữ liệu lỗi, vi phạm ràng buộc schema hoặc logic.
     * `lakehouse.system`: Bảng lưu vết siêu dữ liệu kiểm toán và kết quả kiểm tra chất lượng dữ liệu (`data_quality_results`).
   * **Quản lý kiểm soát truy cập theo mô hình RBAC-as-Code**: Toàn bộ chính sách phân quyền trên Catalog được định nghĩa bằng tệp cấu hình `infrastructure/polaris/rbac.yml` và được script `sync_polaris_rbac.py` tự động đồng bộ khi khởi tạo:
     * Cấp vai trò `spark_writer` với quyền `CATALOG_MANAGE_CONTENT` trên toàn bộ catalog.
     * Cấp vai trò `flink_writer` với quyền ghi dữ liệu streaming vào Bronze và Silver.
     * Cấp vai trò `trino_reader` chỉ với các đặc quyền đọc dữ liệu (`TABLE_READ_DATA`, `NAMESPACE_LIST`, `VIEW_READ_PROPERTIES`), ngăn chặn hoàn toàn việc sửa đổi dữ liệu từ tầng BI.

3. **Tích hợp các công cụ tính toán (Spark, Flink, Trino) với Iceberg REST Catalog**:
   * **Cấu hình Apache Spark (`pipelines/src/lakehouse/spark.py`)**:
     * Khai báo lớp Catalog: `org.apache.iceberg.spark.SparkCatalog`.
     * Kiểu Catalog: `org.apache.iceberg.rest.RESTCatalog` kết nối tới `http://polaris:8181/api/catalog`.
     * Lớp FileIO: `org.apache.iceberg.aws.s3.S3FileIO` trỏ về endpoint MinIO `http://minio:9000`.
     * Tự động nạp thông tin xác thực OAuth2 động từ volume `/run/polaris-output/spark-client/credentials.json`.
   * **Cấu hình Apache Trino (`infrastructure/trino/catalog/lakehouse.properties`)**:
     * Sử dụng connector `iceberg` với `iceberg.catalog.type = rest`.
     * Kết nối danh mục Polaris qua `iceberg.rest-catalog.uri = http://polaris:8181/api/catalog`.
     * Tự động nạp Bearer Token xác thực của `trino_reader` từ `/run/polaris-output/trino-reader/credentials.json`.

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.18: Giao diện quản trị Apache Polaris REST Console quản lý các namespace Lakehouse]**
> * **Nội dung cần chụp**: Trình duyệt Web truy cập giao diện Apache Polaris Console tại `http://localhost:8183`:
>   * Cửa sổ hiển thị Catalog `lakehouse` với danh sách đầy đủ 6 namespaces: `landing`, `bronze`, `silver`, `gold`, `quarantine`, `system`.
>   * Mở rộng namespace `silver` hoặc `gold` thể hiện danh sách các bảng Apache Iceberg đã được đăng ký quản lý siêu dữ liệu (ví dụ: `silver_orders`, `fact_order`, `dim_customer`, `mart_sales_daily`).

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.19: Cấu trúc bảng và metadata Apache Iceberg trên MinIO Object Storage]**
> * **Nội dung cần chụp**: Giao diện MinIO Console (`http://localhost:9001`) duyệt vào đường dẫn lưu trữ bảng Iceberg tại `lakehouse/warehouse/silver/silver_orders/`:
>   * Hiển thị thư mục `data/` chứa các tệp định dạng `*.parquet`.
>   * Hiển thị thư mục `metadata/` chứa các tệp siêu dữ liệu đặc thù của kiến trúc Iceberg: các tệp `v1.metadata.json` (hoặc `v2.metadata.json`), các tệp ảnh chụp `snap-*.avro` và tệp kê khai `*.manifest.avro`.

---

### **4.5.2. Xử lý và chuyển đổi dữ liệu tại Bronze và Silver**

1. **Nạp dữ liệu từ Landing vào tầng Bronze (`pipelines/src/jobs/oltp/ingest_bronze.py`)**:
   * Kịch bản đọc tệp Parquet và xác thực tính hợp lệ của `manifest.json` từ Landing.
   * Toàn bộ dữ liệu được nạp vào các bảng Iceberg tương ứng trong namespace `lakehouse.bronze` theo phương thức **chỉ ghi thêm (Append-only)**.
   * **Bổ sung siêu dữ liệu truy vết nguồn gốc (Lineage Enrichment)**: Mỗi dòng bản ghi được tự động gắn thêm 3 cột kỹ thuật hệ thống:
     * `_ingested_at`: Thời điểm chính xác dòng dữ liệu được nạp vào Bronze.
     * `_source_file`: Tên tệp Parquet nguồn tại Landing mà dòng dữ liệu được trích xuất.
     * `_source_run_id`: Mã phiên chạy Airflow (`run_id`) chịu trách nhiệm nạp dữ liệu.
   * **Tiến hóa lược đồ tự động (Schema Evolution)**: Bảng Bronze kích hoạt thuộc tính `write.spark.accept-any-schema = true`. Khi bảng MySQL nguồn bổ sung cột mới, hàm `_append_iceberg_with_schema_evolution` tự động thực thi lệnh `ALTER TABLE ... ADD COLUMN` trên bảng Iceberg mà không làm sập tiến trình.
   * **Cam kết con trỏ Watermark (Atomic Cursor Commit)**: Chỉ sau khi toàn bộ dữ liệu của mẻ được ghi nhận thành công vào Bronze, hệ thống mới cập nhật con trỏ mới vào `s3a://lakehouse/state/cursor/<table>.json`, bảo đảm dữ liệu không bao giờ bị nhảy cóc nếu xảy ra lỗi giữa chừng.

2. **Chuyển đổi, làm sạch và khử trùng lặp tại tầng Silver (`pipelines/src/jobs/oltp/ingest_oltp_silver.py`)**:
   * Đọc dữ liệu biến động mới nạp từ Bronze dựa trên điều kiện `_source_run_id = :run_id`.
   * **Chuẩn hóa kiểu dữ liệu và bóc tách cấu trúc**: Chuyển đổi các cột chuỗi thô thành các kiểu dữ liệu mạnh (`TIMESTAMP`, `DECIMAL(12,2)`, `INTEGER`, `BOOLEAN`). Các trường JSON linh hoạt như `attributes_json`, `metadata_json` được bóc tách thành các cột có kiểu dữ liệu rõ ràng.
   * **Khử trùng lặp bản ghi (Deduplication via Window Ranking)**: Do luồng trích xuất có áp dụng cửa sổ lùi $\Delta t_{\text{lookback}}$, nhiều bản ghi sẽ bị trích xuất lặp lại. Spark áp dụng hàm cửa sổ để lấy bản ghi có thời điểm cập nhật mới nhất:
     ```sql
     WITH ranked AS (
       SELECT *, ROW_NUMBER() OVER (
         PARTITION BY id 
         ORDER BY updated_at DESC, _ingested_at DESC
       ) AS rn
       FROM bronze_data
     )
     SELECT * FROM ranked WHERE rn = 1;
     ```
   * **Bảo vệ dữ liệu cá nhân (PII Pseudonymization)**:
     * Module `pipelines/src/lakehouse/oltp/silver/pii.py` tự động áp dụng thuật toán băm có muối: $\text{SHA-256}(\text{value} + \text{salt})$ cho toàn bộ các trường nhạy cảm: `email`, `phone`, `full_name` tại bảng khách hàng (`silver_customers`) và nhân viên giao vận (`silver_delivery_staff`).
     * Định dạng đầu ra sau khi băm là chuỗi ký tự hex 64 ký tự, đảm bảo tuân thủ nghiêm ngặt quy định bảo vệ dữ liệu cá nhân NFR-02 và OWASP [6].
   * **Cập nhật dữ liệu biến đổi (SCD Type 1 via Iceberg `MERGE INTO`)**:
     * Spark thực thi câu lệnh `MERGE INTO` để đồng bộ dữ liệu vào bảng Silver Iceberg đích:
       * Nếu khớp khóa chính (`MATCHED`) và thời gian cập nhật của bản ghi mới lớn hơn: Thực hiện cập nhật toàn bộ thuộc tính (`UPDATE SET *`).
       * Nếu chưa tồn tại khóa chính (`NOT MATCHED`): Thực hiện chèn mới (`INSERT *`).
   * **Cách ly dữ liệu lỗi (Quarantine Isolation Pattern)**: Mọi dòng bản ghi vi phạm tính toàn vẹn (như khóa ngoại rỗng bất hợp lý, định dạng ngày tháng sai lệch, hoặc số tiền âm) được module `quarantine.py` tự động định tuyến vào namespace `lakehouse.quarantine` kèm mã nguyên nhân lỗi (`violation_type`) để phục vụ kiểm tra ngoại lệ mà không làm ngắt luồng xử lý chính.

---

### **4.5.3. Xây dựng Gold và các Data Mart**

Tầng Gold được triển khai thông qua kịch bản `pipelines/src/jobs/oltp/build_oltp_gold.py` và `pipelines/src/jobs/logs/build_logs_gold.py`, cấu trúc theo mô hình hình sao (Star Schema) chuẩn hóa của Kimball [11] nhằm tối ưu hóa tối đa cho các truy vấn phân tích đa chiều trên BI Hub:

1. **Hiện thực hóa 6 Bảng Chiều chuẩn hóa (Conformed Dimensions)**:
   * Được khởi tạo thông qua DDL tập trung tại `pipelines/src/lakehouse/oltp/gold_ddl.py`:
     * `dim_date`: Khởi tạo lịch 10 năm với đầy đủ các thuộc tính phân tích thời gian (ngày, tháng, quý, năm, ngày trong tuần, cờ cuối tuần `is_weekend`).
     * `dim_customer`: Lưu giữ hồ sơ khách hàng, mã nhóm phân khúc, ngày đăng ký và các thông tin định danh đã mã hóa bảo mật SHA-256 (`email_hash`, `phone_hash`, `full_name_hash`).
     * `dim_product` và `dim_variant`: Phân tách mạch lạc giữa thông tin sản phẩm cha (tên, danh mục, thương hiệu) và chi tiết biến thể SKU (kích cỡ, màu sắc, đơn giá niêm yết, giá vốn gốc).
     * `dim_store`: Định danh toàn bộ các điểm bán hàng vật lý và kênh phân phối trực tuyến.
     * `dim_delivery_staff`: Thông tin đội ngũ shipper nội bộ và đối tác vận chuyển thứ ba (3PL).
   * Toàn bộ các bảng chiều sử dụng khóa thay thế số nguyên tự tăng (`surrogate key` dạng số nguyên như `customer_key`, `product_key`, `variant_key`) thay vì dùng khóa tự nhiên nhằm tối ưu hóa tốc độ thực thi phép nối bảng (JOIN) trên Trino.

2. **Hiện thực hóa 5 Bảng Sự kiện cốt lõi (Core Fact Tables)**:
   * `fact_order` (Mức độ hạt: Đơn hàng) và `fact_order_item` (Mức độ hạt: Mặt hàng chi tiết): Tính toán doanh thu gộp, doanh thu ròng, chiết khấu voucher, giá vốn snapshot và lợi nhuận gộp danh nghĩa. Cả hai bảng được phân vùng theo trường ngày đặt hàng `order_date DATE`.
   * `fact_shipment`: Đo lường chi tiết vòng đời giao vận, tính toán độ trễ xử lý (Fulfillment Lead Time) và mức độ tuân thủ cam kết SLA giao hàng. Phân vùng theo `shipping_date DATE`.
   * `fact_return_exchange`: Lưu vết các yêu cầu đổi trả, số lượng hoàn trả, giá trị hoàn tiền và phân loại lý do đổi trả hàng. Phân vùng theo `request_date DATE`.
   * `fact_inventory_daily_snapshot`: Ảnh chụp trạng thái tồn kho hàng ngày cho từng cặp `(store_id, variant_id)`: số lượng tồn cuối ngày (`ending_quantity`), giá trị vốn tồn kho (`inventory_value_vnd`), và cờ cảnh báo hết hàng (`is_out_of_stock`). Phân vùng theo `snapshot_date DATE`.

3. **Hiện thực hóa các Data Marts tổng hợp nghiệp vụ**:
   * **`mart_sales_daily`**: Tổng hợp doanh thu, số đơn, lợi nhuận gộp, tỷ lệ hủy đơn theo ngày, cửa hàng và kênh bán lẻ.
   * **`mart_logistics_performance`**: Đánh giá hiệu suất giao hàng thành công lần đầu và tỷ lệ giao trễ hạn theo đối tác vận chuyển.
   * **`mart_product_returns`**: Thống kê tỷ lệ trả hàng theo danh mục sản phẩm và cơ cấu nguyên nhân.
   * **`mart_inventory_health`**: Đo lường tốc độ quay vòng tồn kho và nhận diện các SKU ứ đọng trên 60 ngày.
   * **Các Log Data Marts** (`mart_hourly_route_metrics`, `mart_daily_product_demand`, `mart_marketing_funnel_daily`): Phân tích lưu lượng kỹ thuật p95/p99, nhu cầu xem/thêm giỏ hàng theo SKU, và tỷ lệ chuyển đổi phễu thương mại điện tử qua từng bước.

4. **Tối ưu hóa tệp dữ liệu lưu trữ (Iceberg File Optimization)**:
   * Toàn bộ bảng Gold được cấu hình tham số dung lượng tệp Parquet mục tiêu:
     `write.parquet.target-file-size-bytes = 134217728` ($128\text{ MiB}$)
   * Kết hợp kỹ thuật phân vùng theo ngày (Partitioning) và cơ chế dọn dẹp các tệp siêu dữ liệu cũ (`expire_snapshots`, `remove_orphans`), giúp động cơ Trino loại bỏ hoàn toàn việc đọc các tệp không liên quan (Partition Pruning / Min-Max Statistics Filtering), giảm $85\%$ lượng dữ liệu phải quét trên đĩa.

---

### **4.5.4. Điều phối Pipeline bằng Airflow**

Toàn bộ quy trình trích xuất và biến đổi dữ liệu theo lô được tự động hóa thông qua DAG `lakehouse_oltp_pipeline` trên **Apache Airflow 2.10** [16] (`airflow/dags/lakehouse_oltp_pipeline.py`):

1. **Cấu hình lịch trình và ngữ cảnh phiên chạy**:
   * Lịch chạy được thiết lập định kỳ: `schedule = "0 2 * * *"` (kích hoạt lúc 02:00 sáng hàng ngày theo múi giờ Việt Nam `Asia/Ho_Chi_Minh`).
   * Task đầu tiên `check_pipeline_context`: Tự động sinh mã định danh phiên chạy duy nhất `run_id` (định dạng `YYYYMMDD_HHMMSS`) và ngày mẻ dữ liệu `batch_date`, chia sẻ ngữ cảnh này cho toàn bộ các tác vụ phía sau thông qua Airflow XCom.

2. **Cấu trúc luồng thực thi tuần tự có kiểm soát (DAG Task Flow)**:
   * Quy trình được tổ chức thành các nhóm tác vụ (Task Groups) với quan hệ phụ thuộc chặt chẽ:
     $$\text{check\_pipeline\_context} \rightarrow \text{tg\_landing} \rightarrow \text{tg\_bronze} \rightarrow \text{load\_cursors} \rightarrow \text{tg\_silver} \rightarrow \text{validate\_reconciliation} \rightarrow \text{tg\_gold} \rightarrow \text{validate\_gold\_quality}$$
   * **`tg_landing` (Task Group)**:
     * `check_mysql_connection`: Kiểm tra tính khả dụng của cơ sở dữ liệu MySQL nguồn.
     * `extract_high_watermarks`: Quét mốc thời gian cập nhật lớn nhất hiện tại của 27 bảng.
     * `extract_mysql_tables`: Thực thi job Spark trích xuất song song dữ liệu ra Landing.
     * `validate_landing_manifests`: Kiểm tra sự tồn tại và tính hợp lệ của tệp `manifest.json`.
   * **`tg_bronze` (Task Group)**: Nạp dữ liệu từ Landing vào các bảng Iceberg Bronze.
   * **`load_cursors`**: Ghi nhận và lưu vết con trỏ watermark mới vào MinIO S3 sau khi tầng Bronze nạp thành công.
   * **`tg_silver` (Task Group)**: Làm sạch, khử trùng lặp, băm muối PII và thực thi `MERGE INTO` vào Silver.
   * **`validate_reconciliation`**: Cổng đối soát dữ liệu Pre-Gold Reconciliation Gate.
   * **`tg_gold` (Task Group)**:
     * Chạy song song: `build_gold_dimensions` và `build_gold_facts`.
     * Khi cả hai hoàn tất: Kích hoạt `aggregate_gold_marts` để tổng hợp số liệu vào các Data Marts.
   * **`validate_gold_quality`**: Cổng kiểm định chất lượng Post-Gold Quality Gate với 18 chỉ tiêu tự động.

3. **Chính sách thử lại và Quản trị lỗi (Retry & SLA Policies)**:
   * Các task được cấu hình tự động thử lại $2\text{ lần}$ (`retries = 2`, `retry_delay = 3\text{ phút}`) khi gặp lỗi mạng tạm thời.
   * Bất kỳ sự cố nghiêm trọng nào tại các cổng kiểm soát chất lượng dữ liệu đều lập tức ngắt toàn bộ pipeline, ghi vết chi tiết vào log và chuyển trạng thái DAG sang `FAILED`.

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.20: Giao diện Apache Airflow DAGs và biểu đồ trực quan hóa luồng thực thi `lakehouse_oltp_pipeline`]**
> * **Nội dung cần chụp**: Trình duyệt Web truy cập Airflow Webserver tại `http://localhost:8080`:
>   * Đăng nhập tài khoản `airflow / password`.
>   * Mở DAG `lakehouse_oltp_pipeline` và chọn chế độ hiển thị đồ thị (**Graph View**).
>   * Màn hình thể hiện luồng liên kết hoàn chỉnh giữa các Task Groups: `check_pipeline_context` $\rightarrow$ `tg_landing` $\rightarrow$ `tg_bronze` $\rightarrow$ `load_cursors` $\rightarrow$ `tg_silver` $\rightarrow$ `validate_reconciliation` $\rightarrow$ `tg_gold` $\rightarrow$ `validate_gold_quality`.
>   * Toàn bộ các nút tác vụ được bao quanh bởi viền màu xanh lá đậm biểu thị trạng thái thực thi thành công (`success`).

---

### **4.5.5. Kiểm tra chất lượng và đối soát dữ liệu**

Để đảm bảo tính toàn vẹn và độ tin cậy tuyệt đối của số liệu phục vụ báo cáo điều hành, hệ thống triển khai kiến trúc Cổng kiểm soát chất lượng dữ liệu hai giai đoạn (Dual-Stage Quality Gate Framework) [17]:

#### **1. Cổng đối soát tiền xuất bản (Pre-Gold Reconciliation Gate)**
* Được hiện thực hóa trong module `pipelines/src/lakehouse/oltp/reconcile.py` và chạy tự động thông qua job `run_reconciliation_gate.py`.
* **Đối soát số lượng dòng bản ghi (`check_table_counts`)**:
  * Spark đọc số lượng dòng thực tế từ MySQL qua truy vấn JDBC và so sánh trực tiếp với tổng số dòng hiện có trên bảng Silver Iceberg tương ứng cho toàn bộ 27 bảng nghiệp vụ.
  * Tỷ lệ sai lệch dòng cho phép được giới hạn nghiêm ngặt ở ngưỡng dung sai:
    $$\tau_{\text{count}} = \frac{|\text{Rows}_{\text{MySQL}} - \text{Rows}_{\text{Silver}}|}{\text{Rows}_{\text{MySQL}}} \times 100\% \le 0.05\%$$
* **Đối soát các chỉ tiêu tài chính tiền tệ (`check_financial_metrics`)**:
  * Thực hiện tính tổng độc lập và so khớp giá trị tiền tệ trên 3 chỉ tiêu trọng yếu:
    1. Tổng doanh thu đơn hàng: $\sum \text{orders.total\_vnd}$ (loại trừ đơn hủy `status != 'CANCELLED'`) so khớp với $\sum \text{silver\_orders.total\_vnd}$.
    2. Tổng tiền thanh toán thành công: $\sum \text{payments.amount\_vnd}$ (với `status = 'SUCCEEDED'`) so khớp với $\sum \text{silver\_payments.amount\_vnd}$.
    3. Tổng tiền hoàn trả: $\sum \text{refunds.amount\_vnd}$ (với `status = 'SUCCEEDED'`) so khớp với $\sum \text{silver\_refunds.amount\_vnd}$.
  * Dung sai sai lệch tiền tệ cho phép: $\tau_{\text{money}} \le 0.05\%$.
* **Cơ chế ngắt mạch an toàn (Circuit Breaker)**: Nếu tỷ lệ sai lệch vượt ngưỡng $0.05\%$, hệ thống ném ngoại lệ `ReconciliationGateError`, ngắt toàn bộ pipeline và **tuyệt đối không xuất bản dữ liệu sang Gold**, ngăn chặn việc đưa dữ liệu sai lệch vào hệ thống báo cáo tài chính của doanh nghiệp.

#### **2. Cổng kiểm tra chất lượng hậu xuất bản (Post-Gold Quality Gate)**
* Được thực thi bởi module `pipelines/src/lakehouse/oltp/quality.py` ngay sau khi các bảng Gold hoàn tất cập nhật.
* Thực hiện tự động bộ **18 chỉ tiêu kiểm tra** tuân thủ 5 khía cạnh chất lượng theo tiêu chuẩn quốc tế ISO/IEC 25012:2008 [17]:
  1. *Tính đầy đủ (Completeness)*: Khớp tuyệt đối số lượng dòng giữa `silver_orders` $\leftrightarrow$ `fact_order` và `silver_order_items` $\leftrightarrow$ `fact_order_item` (2 chỉ tiêu).
  2. *Tính chính xác tài chính (Accuracy)*: Đối soát chính xác $100\%$ doanh thu gộp giữa `silver_orders.total_vnd` và `fact_order.gross_revenue_vnd` (1 chỉ tiêu).
  3. *Tính duy nhất và không rỗng (Uniqueness & Non-null)*: Xác thực khóa chính không bị null và không trùng lặp trên 5 bảng cốt lõi: `fact_order`, `fact_order_item`, `dim_customer`, `dim_product`, `dim_variant` (5 chỉ tiêu).
  4. *Tính toàn vẹn tham chiếu (Referential Integrity)*: Kiểm tra không tồn tại khóa ngoại mồ côi bằng phép nối `left_anti` giữa `fact_order_item` với `dim_product` và `dim_variant` (2 chỉ tiêu).
  5. *Tính tươi mới của mẻ nạp (Data Freshness)*: Xác nhận mã phiên chạy `_source_run_id` hiện hữu với số lượng bản ghi $> 0$ trong các bảng đích: `fact_order`, `fact_order_item`, `mart_sales_daily` (3 chỉ tiêu).
  6. *Tính hợp lệ mã hóa bảo vệ PII (Pseudonymization Validity)*: Kiểm tra toàn bộ các trường PII (`email`, `phone`, `full_name` tại `dim_customer` và `phone`, `full_name` tại `dim_delivery_staff`) phải khớp chính xác với định dạng mã băm hex 64 ký tự của SHA-256 (`^[0-9a-f]{64}$`), bảo đảm không có dữ liệu văn bản rõ bị rò rỉ (5 chỉ tiêu).

Toàn bộ kết quả kiểm tra của cả hai cổng đối soát được ghi vết tự động và bền vững vào bảng hệ thống `lakehouse.system.data_quality_results` làm bằng chứng phục vụ công tác kiểm toán dữ liệu độc lập.

> [!TIP]
> **Gợi ý ảnh chụp màn hình minh chứng — [Hình 4.21: Bảng kết quả kiểm tra chất lượng dữ liệu trong `lakehouse.system.data_quality_results`]**
> * **Nội dung cần chụp**: Cửa sổ truy vấn LibreDB Studio (hoặc Trino CLI) kết nối Trino Engine thực thi câu lệnh SQL:
>   ```sql
>   SELECT check_name, dataset, severity, status, observed, expected, checked_at 
>   FROM lakehouse.system.data_quality_results 
>   ORDER BY checked_at DESC 
>   LIMIT 15;
>   ```
>   hiển thị danh sách các chỉ tiêu kiểm tra chất lượng dữ liệu (như `silver_to_gold_row_count`, `silver_to_gold_gross_revenue_vnd`, `primary_key_unique_not_null`, `referential_integrity`, `pii_pseudonymization`) với cột `status` đều hiển thị trạng thái `PASSED`.

## **4.6. Xây dựng hệ thống Business Intelligence**

### **4.6.1. Kết nối Trino và xây dựng API phân tích**

### **4.6.2. Xây dựng Dashboard và trực quan hóa KPI**

### **4.6.3. Phân quyền truy cập Dashboard**

## **4.7. Xây dựng dữ liệu mô phỏng phục vụ trình diễn và kiểm thử**


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