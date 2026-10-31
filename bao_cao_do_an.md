CHƯƠNG 2. CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ SỬ DỤNG

2.1. Tổng quan về thương mại điện tử và bán hàng đa kênh

2.1.1. Mô hình thương mại điện tử và bán hàng đa kênh
Theo định nghĩa của OECD, thương mại điện tử (e-commerce) bao gồm các giao dịch mà đơn hàng được đặt hoặc tiếp nhận thông qua mạng máy tính bằng những phương thức được thiết kế riêng cho mục đích đó. Thanh toán và giao nhận không nhất thiết phải thực hiện trực tuyến [1]. Chẳng hạn, một đơn hàng đặt trên website và thanh toán khi nhận hàng vẫn thuộc phạm vi thương mại điện tử. Ngược lại, giao dịch trực tiếp tại quầy không trở thành giao dịch thương mại điện tử chỉ vì được ghi nhận bằng phần mềm. Do đó, khi mô tả một hệ thống bán lẻ, cần tách biệt kênh đặt hàng, phương thức thanh toán và hình thức giao nhận.

Dựa trên chủ thể tham gia, thương mại điện tử có thể diễn ra giữa doanh nghiệp, người tiêu dùng và cơ quan nhà nước. Trong hoạt động mua bán hàng hóa, ba mô hình phổ biến là B2B, B2C và C2C, với đặc điểm được khái quát ở bảng dưới đây [2].
Mô hình	Quan hệ giao dịch	Ví dụ minh họa
B2B (Business-to-Business)	Doanh nghiệp bán hàng hóa hoặc dịch vụ cho doanh nghiệp khác.	Nhà cung cấp bán nguyên liệu cho doanh nghiệp may mặc thông qua hệ thống đặt hàng điện tử.
B2C (Business-to-Consumer)	Doanh nghiệp bán hàng hóa hoặc dịch vụ cho người tiêu dùng.	Doanh nghiệp thời trang tiếp nhận đơn mua sản phẩm của khách hàng trên website.
C2C (Consumer-to-Consumer)	Các cá nhân giao dịch với nhau, có thể thông qua nền tảng trung gian.	Cá nhân bán lại sản phẩm cho cá nhân khác trên nền tảng giao dịch.


Trong thực tiễn bán lẻ, doanh nghiệp thường kết hợp website, ứng dụng di động và cửa hàng vật lý để tiếp cận khách hàng. Cách tổ chức này được gọi là bán hàng đa kênh (multichannel). Tuy nhiên, ở mô hình đa kênh, mỗi kênh vẫn có thể quản lý dữ liệu và quy trình riêng. Bởi vậy, việc đồng thời vận hành website và cửa hàng chưa đồng nghĩa với việc thông tin khách hàng, giỏ hàng và trạng thái đơn hàng đã được đồng bộ giữa các kênh [3].

Khác với multichannel, mô hình bán hàng hợp kênh (omnichannel) đặt trọng tâm vào sự liên thông giữa các điểm tiếp xúc và trải nghiệm nhất quán của khách hàng. Ví dụ, khách có thể đặt hàng trực tuyến và nhận sản phẩm tại cửa hàng nhờ sự phối hợp giữa kênh bán và địa điểm thực hiện đơn [3]. Theo Verhoef, Kannan và Inman, sự chuyển dịch sang omnichannel còn thể hiện ở cách doanh nghiệp quản lý hành trình khách hàng khi họ liên tục chuyển đổi giữa các kênh tìm kiếm và mua sắm [4]. Như vậy, multichannel chủ yếu phản ánh phạm vi hiện diện của doanh nghiệp, còn omnichannel nhấn mạnh khả năng kết nối dữ liệu và phối hợp nghiệp vụ giữa những kênh đó.

Để triển khai bán hàng trên nhiều kênh, hệ thống phải quản lý sản phẩm theo một danh mục thống nhất, đồng thời nhận diện được nguồn phát sinh giao dịch và địa điểm lưu trữ hàng hóa. Cùng một biến thể sản phẩm có thể được giới thiệu trên website và tại nhiều cửa hàng, nhưng lượng hàng sẵn có lại khác nhau giữa các địa điểm. Vì thế, số tồn tổng hợp của toàn hệ thống không thể thay thế dữ liệu tồn kho theo từng nơi khi xác định khả năng đáp ứng đơn hàng.

2.1.2. Quy trình quản lý bán hàng, đơn hàng và tồn kho
Hoạt động bán lẻ được hình thành từ ba nhóm nghiệp vụ gắn bó với nhau: quản lý bán hàng, quản lý đơn hàng và quản lý tồn kho. Quản lý bán hàng tập trung vào danh mục sản phẩm, điều kiện bán và thông tin giao dịch; quản lý đơn hàng theo dõi quá trình tiếp nhận, thực hiện và hoàn tất yêu cầu mua; còn quản lý tồn kho phản ánh số lượng hàng hóa cùng các biến động tại từng địa điểm. Mặc dù một giao dịch có thể đồng thời tạo ra đơn hàng, khoản thanh toán và biến động tồn kho, mỗi đối tượng vẫn có vòng đời và quy tắc xử lý riêng.

Quy trình bán hàng bắt đầu khi khách lựa chọn sản phẩm, số lượng, mức giá áp dụng và địa điểm nhận hoặc giao hàng. Với mặt hàng thời trang, hệ thống phải quản lý đến từng biến thể như kích cỡ và màu sắc, bởi số tồn của một mẫu sản phẩm không phản ánh chính xác lượng hàng còn lại ở mỗi biến thể. Trước khi xác nhận đơn, thông tin về giá bán, ưu đãi và khả năng đáp ứng cần được kiểm tra lại. Những giá trị đã được chấp thuận phải được lưu trong giao dịch để các thay đổi về sau của danh mục sản phẩm không làm sai lệch lịch sử đơn hàng.

Quản lý đơn hàng bao trùm toàn bộ quá trình từ tiếp nhận yêu cầu mua đến giao nhận và hỗ trợ sau bán. Theo IBM, quy trình này liên quan đến kiểm tra tồn kho, xác minh đơn, xác định nguồn hàng, tổ chức giao nhận và chăm sóc khách hàng [5]. Đối với đơn giao hàng thông thường, các bước chính gồm tiếp nhận, xác nhận, chuẩn bị hàng, bàn giao vận chuyển và ghi nhận kết quả giao. Bên cạnh quy trình hoàn tất, hệ thống còn phải hỗ trợ các tình huống phát sinh như thanh toán thất bại, hủy đơn, giao không thành công hoặc trả hàng, cùng điều kiện xử lý phù hợp cho từng trường hợp.

Trạng thái đơn hàng, thanh toán và giao nhận cần được quản lý độc lập vì chúng phản ánh những giai đoạn khác nhau của giao dịch. Đơn hàng đã xác nhận chưa chắc đã được thanh toán; tương tự, thanh toán thành công không có nghĩa sản phẩm đã đến tay khách hàng. Sự khác biệt này thể hiện rõ ở phương thức thanh toán khi nhận hàng (COD). Do đó, mỗi thay đổi trạng thái phải gắn với một sự kiện nghiệp vụ xác định, tuân thủ luồng xử lý được cho phép và lưu lại thời điểm, lý do đối với những trường hợp cần giải trình như hủy đơn hoặc giao thất bại.

Quản lý tồn kho phản ánh quá trình tiếp nhận, lưu trữ, luân chuyển và xuất hàng trong hệ thống phân phối. Theo IBM, một yêu cầu quan trọng là xác định được vị trí hàng hóa và số lượng có thể đáp ứng tại từng địa điểm [6]. Đối với bán lẻ thời trang, dữ liệu tồn kho nên gắn với từng cặp biến thể sản phẩm và địa điểm. Bên cạnh số dư hiện tại, hệ thống cần duy trì lịch sử nhập, xuất và điều chỉnh để có thể truy vết nguyên nhân hình thành số dư đó.

Đối với một biến thể sản phẩm tại một địa điểm lưu trữ trong khoảng thời gian xác định, số dư tồn kho được đối chiếu theo công thức:
\[
Q_{\text{cuối kỳ}} = Q_{\text{đầu kỳ}} + \sum_{i=1}^{n} \Delta Q_i
\]
Trong công thức trên, \(Q_{\text{đầu kỳ}}\) và \(Q_{\text{cuối kỳ}}\) lần lượt là số dư ở đầu và cuối kỳ; \(\Delta Q_i\) biểu thị biến động của nghiệp vụ thứ \(i\), mang giá trị dương khi nhập tăng và âm khi xuất giảm. Phép đối chiếu chỉ chính xác khi tất cả số liệu thuộc cùng biến thể, địa điểm, đơn vị tính và khoảng thời gian. Đây là quan hệ kế toán về số lượng, không thay thế hoạt động kiểm kê thực tế. Nếu lịch sử thiếu nghiệp vụ hoặc ghi nhận trùng, số dư tính lại sẽ có khả năng chênh lệch với số dư đang lưu.

Tùy loại nghiệp vụ, biến động tồn kho được ghi nhận theo những nguyên tắc khác nhau. Nhập hàng làm tăng số lượng tại địa điểm nhận; xuất bán làm giảm số lượng tại địa điểm đáp ứng đơn; còn điều chuyển nội bộ tạo ra một lần giảm ở nơi gửi và một lần tăng ở nơi nhận. Trong thời gian vận chuyển, hàng đã xuất khỏi kho nguồn chưa thể được xem là sẵn sàng bán tại kho đích. Vì vậy, hệ thống phải quy định rõ thời điểm ghi tăng, ghi giảm và chứng từ làm căn cứ cho từng bước, không chỉ dựa vào tên trạng thái của đơn hàng.

Trả hàng là một quy trình riêng, bao gồm tiếp nhận yêu cầu, nhận và kiểm tra sản phẩm, quyết định phương án xử lý, sau đó giải quyết các nghĩa vụ tài chính. Microsoft phân biệt rõ những giai đoạn này trong quy trình quản lý hàng trả [7]. Với hoạt động bán lẻ, chỉ những sản phẩm đạt điều kiện sau kiểm tra mới được nhập lại vào lượng tồn có thể bán. Hàng hư hỏng hoặc chưa được đánh giá cần có trạng thái riêng. Nghiệp vụ hoàn tiền và nhập kho cũng phải được ghi nhận tách biệt để hỗ trợ trả hàng hoặc hoàn tiền một phần.

Sự liên kết giữa bán hàng, thanh toán và tồn kho đòi hỏi dữ liệu giao dịch được cập nhật nhất quán. Khi đơn hàng được chấp nhận, các bản ghi liên quan phải tuân thủ cùng một tập quy tắc nghiệp vụ. Hệ thống cần ngăn tình trạng nhiều khách đồng thời mua vượt lượng hàng sẵn có, đồng thời nhận diện yêu cầu gửi lặp do mất kết nối để tránh tạo đơn hoặc trừ tồn hai lần. Khả năng đáp ứng những yêu cầu này cần được chứng minh qua thiết kế giao dịch và kiểm thử, thay vì chỉ suy ra từ công nghệ sử dụng.

Chính sách thực hiện đơn hàng quyết định thời điểm giữ chỗ, trừ tồn và giải phóng hàng. Chẳng hạn, hệ thống có thể giữ hàng khi xác nhận đơn và chỉ ghi giảm tồn vật lý lúc xuất kho; một phương án khác là cập nhật lượng có thể bán ngay khi chấp nhận giao dịch. Dù lựa chọn cách nào, các khái niệm tồn vật lý, lượng đã cam kết và lượng sẵn sàng bán phải được định nghĩa rõ và áp dụng nhất quán trong các trường hợp đặt, hủy, giao thất bại hoặc trả hàng.

2.1.3. Vai trò của phân tích dữ liệu trong hoạt động kinh doanh
Mỗi giao dịch tạo ra một tập dữ liệu phản ánh các sự kiện như đặt hàng, thanh toán hoặc nhập kho. Khi được chuẩn hóa và tổng hợp theo cùng quy tắc nghiệp vụ, dữ liệu này trở thành nguồn thông tin hỗ trợ quản trị. Business Intelligence (BI) bao gồm hoạt động thu thập, quản lý và phân tích dữ liệu nhằm phục vụ quyết định vận hành cũng như định hướng kinh doanh [8]. Nhờ BI, doanh nghiệp có thể theo dõi kết quả, nhận diện xu hướng và khoanh vùng vấn đề cần tìm hiểu; tuy nhiên, việc diễn giải và ra quyết định vẫn thuộc trách nhiệm của nhà quản lý.

Cùng một nguồn dữ liệu có thể phục vụ nhiều bộ phận với các mục tiêu khác nhau. Bộ phận kinh doanh theo dõi doanh thu theo kênh, cửa hàng và sản phẩm; bộ phận kho quan tâm đến số lượng hàng tại từng địa điểm; trong khi bộ phận vận hành cần phát hiện các đơn chờ xử lý hoặc giao thất bại. Khi doanh thu sụt giảm, việc phân tích theo thời gian, nhóm sản phẩm và điểm bán giúp thu hẹp phạm vi tìm nguyên nhân. Tuy vậy, các khác biệt quan sát được mới là dấu hiệu ban đầu; để kết luận cần đối chiếu thêm những yếu tố như giá bán, tồn kho và nhu cầu thị trường.

Phân tích còn giúp đối chiếu kết quả giữa các khâu của quy trình kinh doanh. Số lượng đơn hàng, giá trị thanh toán, số đơn đã giao và lượng hàng trả thường không trùng khớp tuyệt đối vì mỗi chỉ số phản ánh một giai đoạn khác nhau. Do đó, khi xây dựng báo cáo phải xác định rõ mốc thời gian và điều kiện ghi nhận của từng phép đo. Một hệ thống định nghĩa chỉ số thống nhất sẽ giúp các bộ phận sử dụng cùng cách hiểu và giải thích được chênh lệch giữa các báo cáo.

Bên cạnh tính chính xác, độ kịp thời của dữ liệu cũng ảnh hưởng trực tiếp đến giá trị sử dụng. Thông tin về đơn đang chờ hoặc tồn kho hiện tại phải đủ mới để phục vụ vận hành, trong khi dữ liệu tổng hợp theo ngày thường phù hợp hơn cho phân tích xu hướng. Quy trình xử lý theo lô có thể đáp ứng báo cáo lịch sử nhưng khó thay thế nguồn giao dịch khi cần kiểm tra lượng hàng sẵn sàng bán ngay lập tức. Vì vậy, độ mới, mức độ đầy đủ và trạng thái kiểm chứng cần được lựa chọn theo mục đích của từng quyết định.

2.1.4. Hệ thống chỉ số KPI trong thương mại điện tử
Trong quản trị thương mại điện tử, chỉ số đo lường (metric) phản ánh một đặc điểm của hoạt động kinh doanh, còn chỉ số hiệu suất trọng yếu (Key Performance Indicator – KPI) được lựa chọn để đánh giá mức độ đạt mục tiêu. Các phép đo như lượt truy cập hay số đơn hàng chỉ trở thành căn cứ đánh giá có ý nghĩa khi gắn với kỳ đo, đối tượng và mục tiêu cụ thể. Nếu thiếu giá trị cơ sở hoặc mức đích để so sánh, báo cáo mới mô tả được hiện trạng chứ chưa đủ cơ sở xác định hiệu quả thực hiện kế hoạch.

Để bảo đảm khả năng tái lập và so sánh, mỗi chỉ số cần có định nghĩa về ý nghĩa nghiệp vụ, công thức tính, đơn vị, mức chi tiết, khoảng thời gian, bộ lọc và nguồn dữ liệu. Đặc biệt, đối với chỉ số dạng tỷ lệ, tử số và mẫu số phải dựa trên cùng phạm vi quan sát. Ví dụ, tỷ lệ chuyển đổi theo phiên truy cập (session) khác với tỷ lệ theo người dùng; sự khác biệt này quyết định cách thu thập sự kiện, loại bỏ bản ghi trùng và diễn giải kết quả.
Nhóm chỉ số	Phép đo minh họa	Yêu cầu khi diễn giải
Kết quả bán hàng	Số đơn, doanh thu, giá trị đơn trung bình	Xác định kỳ và điều kiện lựa chọn giao dịch.
Hiệu quả hàng hóa	Giá vốn, lợi nhuận gộp, giá trị tồn	Phân biệt giá bán với giá vốn và phạm vi chi phí.
Vận hành	Thời gian xử lý, giao thất bại, trả hàng	Phân biệt đơn, shipment và yêu cầu trả hàng.
Hành vi khách hàng	Lượt xem, session, chuyển đổi	Xác định đơn vị đếm và cách gắn kết hành trình.
Chất lượng dữ liệu	Tính đầy đủ, độ mới, sai lệch	Có phạm vi dữ liệu và quy tắc kiểm tra tương ứng.


Giá trị đơn hàng trung bình (Average Order Value – AOV) cho biết doanh thu bình quân của mỗi đơn trong phạm vi phân tích. Theo cách tính cơ bản, AOV bằng tổng doanh thu của các đơn được xét chia cho số lượng đơn tương ứng trong cùng kỳ [9]:
\[
AOV = \frac{\text{Doanh thu của các đơn được xét}}{\text{Số đơn được xét}}
\]
Khi tính AOV, hệ thống cần quy định rõ việc có tính đơn bị hủy, hàng trả, khoản giảm giá, thuế và phí vận chuyển hay không. Tập đơn ở mẫu số phải thống nhất với tập giao dịch tạo ra doanh thu ở tử số. Trường hợp không có đơn hàng, AOV là giá trị không xác định; hiển thị dưới dạng thiếu dữ liệu sẽ chính xác hơn việc gán bằng 0.

So sánh KPI giữa các kỳ chỉ có ý nghĩa khi công thức và phạm vi đo được giữ nhất quán. Với hai tỷ lệ \(p_1\) và \(p_2\), mức chênh lệch tuyệt đối được thể hiện bằng \(p_2-p_1\) điểm phần trăm, trong khi mức thay đổi tương đối bằng \((p_2-p_1)/p_1\) khi \(p_1 \ne 0\). Hai cách tính phục vụ những mục đích diễn giải khác nhau. Khi tổng hợp tỷ lệ từ nhiều nhóm, cần cộng tử số và mẫu số tương ứng trước khi chia, thay vì lấy trung bình đơn giản các tỷ lệ có quy mô khác nhau.

Báo cáo KPI cũng cần cho biết thời điểm cập nhật dữ liệu và những giới hạn của nguồn. Chẳng hạn, doanh thu tính theo ngày tạo đơn có thể khác doanh thu tính theo ngày thanh toán, dù cùng sử dụng dữ liệu giao dịch. Tương tự, các sự kiện chưa liên kết được với từng người dùng không đủ cơ sở để suy ra tỷ lệ chuyển đổi theo khách hàng. Việc thống nhất các quy ước trước khi xây dựng dashboard giúp hạn chế cách hiểu sai từ tên trường hoặc hình thức biểu đồ.

2.2. Kiến trúc và công nghệ phát triển hệ thống thương mại điện tử

2.2.1. Kiến trúc Web Client–Server và REST API (Next.js, React, FastAPI)
Kiến trúc Client–Server phân chia trách nhiệm giữa phía khách (client), nơi tiếp nhận thao tác và hiển thị thông tin, với phía máy chủ (server), nơi xử lý yêu cầu, áp dụng quy tắc nghiệp vụ và truy xuất dữ liệu. Nhờ sự phân tách này, các thao tác quan trọng có thể được kiểm soát tập trung ở máy chủ, thay vì phụ thuộc vào mã chạy trên trình duyệt. Chẳng hạn, giá trị thanh toán phải được xác định từ dữ liệu hợp lệ ở phía máy chủ, ngay cả khi giao diện đã hiển thị một mức giá. Để hai thành phần phối hợp ổn định, giao diện trao đổi dữ liệu cần quy định rõ cấu trúc đầu vào, đầu ra và thông báo lỗi.

REST (Representational State Transfer) là một phong cách kiến trúc cho hệ thống phân tán, được xác lập bởi những ràng buộc như Client–Server, stateless, khả năng lưu đệm và giao diện thống nhất [10]. Trong đó, stateless yêu cầu mỗi yêu cầu chứa đủ thông tin để máy chủ xử lý mà không phải dựa vào trạng thái hội thoại của những yêu cầu trước. Các tài nguyên được truy cập thông qua biểu diễn và thông điệp có ngữ nghĩa rõ ràng. Vì vậy, API sử dụng HTTP và trao đổi JSON chưa chắc đã đáp ứng đầy đủ các nguyên tắc của REST.

React xây dựng giao diện từ các thành phần (component) có thể tái sử dụng và kết hợp, chẳng hạn thẻ sản phẩm, bảng dữ liệu hay bộ chọn cửa hàng [11]. Trên nền React, Next.js cung cấp cơ chế định tuyến và hỗ trợ cả Server Component lẫn Client Component. Server Component phù hợp với những phần có thể xử lý hoặc kết xuất phía máy chủ, trong khi Client Component đáp ứng nhu cầu quản lý trạng thái và tương tác với API của trình duyệt. Chỉ thị use client đánh dấu ranh giới dành cho phần mã tương tác chứ không yêu cầu toàn bộ ứng dụng chạy trên client [12].

FastAPI là framework phát triển API bằng Python, hỗ trợ khai báo kiểu dữ liệu, xác thực cấu trúc đầu vào, dependency injection và tạo mô tả OpenAPI [13]. Những khả năng này giúp tổ chức mã nguồn rõ ràng, tách phần tiếp nhận yêu cầu khỏi xử lý nghiệp vụ và tái sử dụng các thành phần xác thực, phân quyền hoặc quản lý phiên cơ sở dữ liệu. Tuy nhiên, dữ liệu đáp ứng đúng kiểu chưa chắc hợp lệ về mặt nghiệp vụ: số lượng đặt mua vẫn phải được đối chiếu với tồn kho, còn quyền truy cập một đối tượng phải được kiểm tra theo người dùng hiện tại.

Trong hệ thống thương mại điện tử, React và Next.js có thể đảm nhiệm giao diện và tương tác người dùng, còn FastAPI cung cấp các dịch vụ xử lý nghiệp vụ. Các thành phần này giao tiếp qua API và có thể triển khai độc lập tùy nhu cầu. Việc thiết kế hợp đồng API ổn định giúp giảm sự phụ thuộc giữa các lớp, đồng thời hạn chế tác động của thay đổi trong triển khai đến ý nghĩa dữ liệu trao đổi.

2.2.2. Cơ sở dữ liệu giao dịch OLTP (MySQL, SQLAlchemy)
OLTP (Online Transaction Processing) là mô hình xử lý giao dịch trực tuyến, được tối ưu cho các thao tác đọc và ghi ngắn trên những bản ghi cụ thể. Trong thương mại điện tử, việc tạo đơn có thể kéo theo ghi nhận chi tiết sản phẩm, cập nhật tồn kho và thanh toán. Cơ sở dữ liệu giao dịch cần bảo toàn tính hợp lệ của các thay đổi này ngay cả khi nhiều yêu cầu diễn ra đồng thời. Đây là điểm khác với hệ thống phân tích, vốn thường đọc lượng lớn dữ liệu để tổng hợp theo thời gian hoặc nhiều chiều nghiệp vụ.

MySQL sử dụng bộ máy lưu trữ InnoDB để hỗ trợ giao dịch theo các thuộc tính ACID: nguyên tử (Atomicity), nhất quán (Consistency), cô lập (Isolation) và bền vững (Durability) [14]. Theo đó, các thao tác trong một giao dịch được xác nhận hoặc hủy bỏ như một đơn vị; các ràng buộc hợp lệ được duy trì; giao dịch đồng thời chịu sự kiểm soát về mức cô lập; và thay đổi đã xác nhận được bảo toàn theo cơ chế lưu trữ tương ứng. Dù vậy, ACID không tự giải quyết quy tắc kinh doanh, nên hệ thống vẫn phải thiết kế khóa, ràng buộc và phạm vi giao dịch phù hợp.

Trong cơ sở dữ liệu quan hệ, khóa chính định danh bản ghi, khóa ngoại biểu diễn liên kết, còn các ràng buộc duy nhất và kiểm tra giúp duy trì tính toàn vẹn. Việc tách bảng đơn hàng và chi tiết đơn hàng cho phép thể hiện quan hệ một–nhiều mà không phải lặp lại thông tin chung của đơn. Riêng các giá trị mang tính lịch sử, chẳng hạn giá bán hoặc giá vốn tại thời điểm mua, cần được lưu theo giao dịch để những thay đổi của danh mục về sau không làm sai lệch số liệu quá khứ.

SQLAlchemy cung cấp công cụ ánh xạ đối tượng–quan hệ (ORM) và xây dựng truy vấn SQL trong ứng dụng Python. Thành phần Session quản lý trạng thái đối tượng và phạm vi làm việc với cơ sở dữ liệu, bao gồm các thao tác flush, commit và rollback. Trong đó, flush chuyển thay đổi đang theo dõi xuống cơ sở dữ liệu nhưng chưa đồng nghĩa giao dịch đã được commit [15]. Vì thế, sử dụng ORM vẫn đòi hỏi hiểu về giao dịch, ràng buộc dữ liệu và các tình huống truy cập đồng thời.

Thiết kế cơ sở dữ liệu OLTP cần dung hòa yêu cầu chính xác với hiệu năng xử lý khi nhiều giao dịch cùng hoạt động. Mức cô lập quyết định cách giao dịch quan sát thay đổi của nhau, còn phạm vi khóa tác động đến khả năng thực thi đồng thời. Mặt khác, lược đồ và các ràng buộc tại cơ sở dữ liệu mới là nơi thực thi tính toàn vẹn, trong khi mô hình ORM chỉ biểu diễn chúng ở tầng ứng dụng. Bởi vậy, mọi thay đổi mô hình dữ liệu cần được quản lý và đối chiếu giữa hai tầng.

2.2.3. Xác thực, phân quyền và bảo mật hệ thống
Trong bảo mật ứng dụng, xác thực (authentication) xác định danh tính của chủ thể gửi yêu cầu, còn phân quyền (authorization) xác định những thao tác chủ thể đó được phép thực hiện. Đăng nhập thành công không có nghĩa người dùng được truy cập mọi đơn hàng hoặc cửa hàng. Hệ thống cần kiểm tra quyền tại phía máy chủ cho từng yêu cầu theo nguyên tắc đặc quyền tối thiểu; việc ẩn nút trên giao diện không thể thay thế cơ chế này [16]. Với mô hình nhiều điểm bán, quyền truy cập còn phải gắn với phạm vi cửa hàng được giao quản lý.

Phiên đăng nhập có thể được duy trì thông qua cookie chứa thông tin phiên hoặc token. Các thuộc tính HttpOnly, Secure và SameSite hỗ trợ những mục tiêu bảo vệ khác nhau: hạn chế truy cập từ script, chỉ truyền qua HTTPS và kiểm soát việc gửi cookie trong ngữ cảnh khác site. Tuy nhiên, các thuộc tính này không loại bỏ hoàn toàn nguy cơ CSRF khi trình duyệt tự động đính kèm cookie [17]. Cơ chế phiên còn phải quy định thời hạn hiệu lực, cách đăng xuất và xử lý thông tin xác thực hết hạn hoặc bị thu hồi.

Đối với mật khẩu, phương án phù hợp là sử dụng thuật toán băm chuyên dụng có salt riêng và chi phí tính toán đủ lớn, thay vì lưu văn bản thuần. OWASP khuyến nghị những cơ chế như Argon2id và phân biệt chúng với các hàm băm nhanh thông thường [18]. Mục đích là tăng chi phí tấn công dò mật khẩu nếu dữ liệu băm bị lộ. Tuy nhiên, biện pháp này phải đi kèm kiểm soát truy cập, bảo vệ cơ sở dữ liệu và quản lý bí mật kết nối.

JSON Web Token (JWT) là một định dạng biểu diễn các thông tin xác nhận (claim), có thể được bảo vệ bằng chữ ký, mã xác thực thông điệp hoặc mã hóa tùy cách triển khai. JWT có chữ ký giúp kiểm tra tính toàn vẹn nhưng không mặc nhiên bảo mật nội dung [19]. Khi sử dụng JWT để xác thực, máy chủ phải kiểm tra chữ ký cùng các điều kiện về thời hạn, bên phát hành, đối tượng nhận và thuật toán hợp lệ, thay vì tin tưởng dữ liệu chỉ sau khi giải mã.

Ngoài xác thực và phân quyền, bảo mật hệ thống còn đòi hỏi giới hạn dữ liệu nhạy cảm được thu thập, lưu trữ và chia sẻ giữa các thành phần. Access log cần tránh ghi mật khẩu, token, cookie hoặc thông tin cá nhân không cần thiết; OWASP cũng nhấn mạnh việc lựa chọn nội dung log theo mục đích sử dụng [20]. Các dịch vụ phục vụ báo cáo chỉ nên được cấp quyền đọc trong phạm vi cần thiết, thay vì sử dụng chung tài khoản có khả năng sửa dữ liệu hoặc quản trị catalog.

Các biện pháp bảo mật chỉ phát huy hiệu quả khi được áp dụng xuyên suốt quá trình xử lý yêu cầu. Phân quyền theo vai trò cần được kết hợp với phạm vi đối tượng, chẳng hạn quyền xem đơn hàng của một cửa hàng cụ thể. Tài khoản dịch vụ cũng phải được giới hạn theo nhiệm vụ đọc, ghi hoặc quản trị. Do đó, thiết kế bảo mật cần xem xét đồng thời truy cập, truyền dữ liệu, lưu trữ bí mật và ghi nhận sự kiện, thay vì chỉ tập trung vào chức năng đăng nhập.

2.3. Kiến trúc và công nghệ lưu trữ Data Lakehouse

2.3.1. Tổng quan về Data Lakehouse
Data Lakehouse là kiến trúc dữ liệu kết hợp tính linh hoạt của lưu trữ mở với các cơ chế quản lý bảng phục vụ phân tích. Theo Armbrust và cộng sự, kiến trúc này hướng đến việc hỗ trợ nhiều loại tác vụ phân tích trên nền tảng định dạng dữ liệu mở [21]. Điểm cốt lõi của Lakehouse không chỉ là lưu file trong object storage, mà còn là khả năng quản lý phiên bản bảng và duy trì cách truy cập nhất quán giữa các công cụ xử lý.

Nếu Data Lake ưu tiên lưu trữ linh hoạt nhiều dạng dữ liệu và Data Warehouse tập trung vào dữ liệu đã được tổ chức cho truy vấn, thì Lakehouse bổ sung khả năng quản lý bảng ngay trên nền lưu trữ mở. Nhờ đó, dữ liệu có thể phục vụ các hình thức phân tích khác nhau mà không nhất thiết phải chuyển toàn bộ sang một hệ quản trị riêng. Tuy nhiên, hiệu quả về hiệu năng và chi phí còn phụ thuộc khối lượng dữ liệu, hạ tầng và đặc điểm truy cập thực tế.

Về cấu trúc, Lakehouse gồm ba nhóm chức năng chính: lưu trữ file dữ liệu, quản lý bảng thông qua metadata và catalog, và thực thi các tác vụ tính toán. Việc tách biệt các chức năng tạo điều kiện để nhiều engine cùng khai thác dữ liệu, nhưng cũng đòi hỏi sự tương thích về định dạng, quyền truy cập và cơ chế ghi. Hai engine cùng đọc được một loại file chưa chắc có thể cập nhật an toàn cùng một bảng nếu chúng không tuân thủ chung quy tắc quản lý metadata và commit.

Trong môi trường có nhiều tác vụ đọc và ghi, engine phải xác định được tập file thuộc phiên bản bảng đã được commit. Apache Iceberg giải quyết vấn đề này thông qua metadata và snapshot, cho phép truy vấn dựa trên một trạng thái bảng nhất quán [22]. Tuy vậy, tính nhất quán ở một bảng không đồng nghĩa toàn bộ pipeline gồm nhiều bảng đều được cập nhật trong cùng một giao dịch nguyên tử.

Lakehouse hướng đến một nền tảng dữ liệu có thể dùng chung cho báo cáo, phân tích lịch sử và các tác vụ xử lý chuyên sâu. Để đạt được điều đó, dữ liệu từ nhiều nguồn vẫn cần được tiếp nhận, chuẩn hóa, kiểm tra và quản lý vòng đời. Khả năng tích hợp công cụ chỉ thực sự có giá trị khi đi kèm chính sách chất lượng dữ liệu, quản lý schema, phân quyền và truy vết nguồn gốc.

2.3.2. Kiến trúc dữ liệu Landing – Bronze – Silver – Gold
Kiến trúc Medallion phân chia dữ liệu thành các tầng theo mức độ xử lý và khả năng sử dụng. Bronze lưu dữ liệu mới tiếp nhận, Silver chuẩn hóa và kiểm tra dữ liệu, còn Gold cung cấp những tập dữ liệu đã tổ chức cho nhu cầu phân tích [23]. Đây là cách phân tầng về mặt logic, không bắt buộc mỗi tầng phải chạy trên một hệ thống riêng. Trong nhiều triển khai, vùng Landing được bổ sung trước Bronze để tiếp nhận file hoặc sự kiện gốc và ghi nhận thông tin của từng lần thu thập.
Lớp	Chức năng điển hình	Thông tin cần bảo toàn
Landing	Tiếp nhận file hoặc sự kiện đầu vào, ghi thông tin lần thu thập	Nguồn, thời điểm, phạm vi dữ liệu và khả năng đọc lại.
Bronze	Lưu lịch sử đã tiếp nhận với lineage	Dữ liệu đủ để truy vết; không nhầm lịch sử với trạng thái hiện tại.
Silver	Chuẩn hóa kiểu, xử lý trùng, kiểm tra hợp lệ và giảm PII	Khóa, quan hệ, quy tắc lựa chọn phiên bản và dữ liệu lỗi.
Gold	Xây dimension, fact và mart theo câu hỏi phân tích	Grain, công thức và nguồn gốc của các phép tổng hợp.


Ranh giới giữa Landing và Bronze được xác định theo cách hệ thống quản lý dữ liệu đầu vào. Landing thường giữ file gần với nguồn phát sinh, còn Bronze có thể bổ sung cấu trúc và metadata để hỗ trợ truy vết. Một số hệ thống gộp hai chức năng này, song vẫn phải làm rõ nội dung lưu trữ, quy ước dữ liệu và thời hạn giữ lại. Cũng cần phân biệt đường dẫn lưu trữ, schema và namespace của catalog, vì mỗi khái niệm đảm nhiệm một vai trò tổ chức khác nhau.

Dòng dữ liệu từ Bronze sang Silver không phải phép sao chép đơn giản, mà bao gồm chuẩn hóa kiểu dữ liệu, kiểm tra ràng buộc và xử lý bản ghi trùng. Chẳng hạn, với bản ghi thiếu khóa hoặc sai kiểu, pipeline cần ghi nhận nguyên nhân và hướng xử lý thay vì loại bỏ âm thầm. Khi một khóa có nhiều phiên bản, quy tắc lựa chọn phải dựa vào thời gian và đặc điểm của nguồn. Những bản ghi chưa đạt yêu cầu có thể được chuyển sang vùng cách ly (quarantine) để phục vụ kiểm tra và tái xử lý.

Phân tầng dữ liệu cũng hỗ trợ khôi phục và tính toán lại kết quả. Khi thay đổi công thức tổng hợp, hệ thống có thể tạo lại Gold từ dữ liệu chi tiết thích hợp; khi thay đổi quy tắc làm sạch, khả năng tái xử lý phụ thuộc vào việc dữ liệu đầu vào còn được lưu giữ hay không. Vì thế, giá trị của mô hình Medallion gắn với chính sách lưu trữ, thông tin dòng dõi dữ liệu (lineage) và cơ chế xử lý thực tế, chứ không chỉ ở việc đặt tên các tầng.

2.3.3. Lưu trữ và quản lý dữ liệu (MinIO, Apache Iceberg, Apache Polaris)
MinIO cung cấp dịch vụ lưu trữ đối tượng tương thích với giao diện S3 [24]. Dữ liệu được tổ chức dưới dạng bucket và object, trong đó mỗi object có thể chứa file đầu vào, file dữ liệu hoặc metadata. Key và prefix giúp sắp xếp các đối tượng theo khu vực sử dụng. Tuy nhiên, sự tồn tại của một file trong storage chỉ cho biết file đã được lưu; nó chưa đủ để xác định file đó thuộc phiên bản bảng hợp lệ hoặc đã được kiểm tra chất lượng.

Apache Iceberg là định dạng bảng mở, sử dụng metadata và snapshot để quản lý tập file tạo thành một bảng. Mỗi lần cập nhật hợp lệ hình thành trạng thái metadata mới; quá trình commit thay đổi tham chiếu đến trạng thái đó theo cơ chế nguyên tử và kiểm soát tương tranh lạc quan [22]. Nhờ vậy, người đọc có thể truy cập snapshot nhất quán và hệ thống có thể quản lý lịch sử phiên bản. Cần phân biệt Iceberg với Parquet: Parquet lưu nội dung của từng file, còn Iceberg quản lý cấu trúc và trạng thái của toàn bộ bảng.

Apache Polaris đảm nhiệm vai trò catalog cho các bảng Iceberg thông qua giao thức REST [25]. Catalog quản lý tên bảng và thông tin metadata cần thiết để các engine tìm và truy cập dữ liệu. Sau khi xác định được bảng, engine vẫn cần quyền đối với vùng storage để đọc hoặc ghi file. Như vậy, catalog, hệ thống lưu trữ đối tượng và engine tính toán là ba thành phần có trách nhiệm khác nhau nhưng phối hợp trong cùng kiến trúc.
Thành phần	Đối tượng chịu trách nhiệm chính	Không nên đồng nhất với
MinIO	Bucket, object và quyền truy cập vùng lưu trữ	Engine SQL hoặc mô hình dimension/fact.
Iceberg	Metadata bảng, snapshot và tập file dữ liệu	Một máy chủ cơ sở dữ liệu giao dịch độc lập.
Polaris	Catalog và quyền truy cập thông qua giao diện quản lý	Nơi thực thi Spark job hoặc truy vấn báo cáo.


Khi phân tách storage và catalog, chính sách truy cập phải được kiểm soát ở cả hai lớp. Một engine có quyền tra cứu bảng trên catalog vẫn có thể không đọc được dữ liệu nếu thiếu quyền đối với object; ngược lại, quyền truy cập trực tiếp bucket có thể nằm ngoài phạm vi giới hạn của dashboard. Vì vậy, cần quy định rõ quyền đọc, ghi và quản trị tại từng điểm truy cập để tránh bỏ sót các đường đi đến dữ liệu.

Các bảng Iceberg tích lũy file dữ liệu và snapshot theo thời gian, do đó cần được bảo trì định kỳ. Những tác vụ như gom file nhỏ, hết hạn snapshot và dọn file không còn tham chiếu phục vụ các mục tiêu khác nhau. Việc thực hiện phải tính đến chính sách lưu giữ và các công việc đang đọc dữ liệu. Nếu chỉ xóa object theo tuổi file mà bỏ qua metadata của bảng, hệ thống có thể làm mất dữ liệu vẫn còn được tham chiếu bởi những snapshot cần thiết.

2.3.4. Mô hình dữ liệu phân tích (Dimension, Fact, Data Mart)
Mô hình dữ liệu phân tích được thiết kế từ các câu hỏi quản trị và mức độ chi tiết cần đo lường. Trong đó, bảng fact chứa sự kiện hoặc chỉ tiêu định lượng, còn bảng dimension cung cấp ngữ cảnh như thời gian, sản phẩm, khách hàng và cửa hàng. Khái niệm grain xác định ý nghĩa của một dòng trong bảng fact. Theo Kimball, grain phải được xác lập trước khi lựa chọn khóa và phép đo, bởi đây là cơ sở bảo đảm các giá trị trong cùng bảng có mức chi tiết nhất quán [26].

Ví dụ, fact đơn hàng có thể lưu một dòng cho mỗi đơn, còn fact chi tiết bán hàng lưu một dòng cho mỗi sản phẩm trong đơn. Nếu nối hai bảng rồi cộng tổng giá trị đơn ở mọi dòng chi tiết, doanh thu có thể bị nhân lên nhiều lần. Vì vậy, phép tổng hợp phải phù hợp với grain: các chỉ tiêu ở cấp đơn được tính theo đơn, còn số lượng và giá trị chi tiết được tính theo từng dòng hàng. Khi kết hợp nhiều fact, cần đặc biệt chú ý quan hệ nối và mức chi tiết của kết quả.

Trong mô hình ngôi sao (star schema), bảng fact nằm ở trung tâm và liên kết đến các bảng dimension thông qua khóa. Cấu trúc này tạo thuận lợi cho việc phân tích cùng một phép đo theo nhiều thuộc tính chiều, với điều kiện các khóa và quan hệ nối được thiết kế phù hợp với grain của fact [27].

Khả năng cộng gộp là đặc điểm quan trọng của các phép đo trong mô hình chiều. Số lượng bán và thành tiền thường có thể cộng theo nhiều chiều; tồn kho có thể cộng giữa các địa điểm ở cùng một thời điểm nhưng không nên cộng liên tiếp qua các ngày; còn các tỷ lệ phải được tính lại từ tử số và mẫu số tương ứng. Những trường hợp này lần lượt liên quan đến các nhóm additive, semi-additive và non-additive [27]. Việc xác định đúng đặc tính cộng gộp giúp tránh sai lệch khi xây dựng chỉ số tổng hợp.

Data Mart là tập dữ liệu được tổ chức để phục vụ một nhóm nhu cầu phân tích tương đối cụ thể, chẳng hạn doanh thu bán hàng, giao vận hoặc tồn kho. Mart có thể xây dựng từ fact và dimension ở mức chi tiết phù hợp rồi lưu thành bảng hoặc cung cấp qua lớp truy vấn. Mức tổng hợp càng cao thì truy vấn càng thuận tiện, nhưng khả năng phân tích sâu vào từng giao dịch càng bị giới hạn. Chẳng hạn, dữ liệu đã tổng hợp theo ngày không đủ để khôi phục mọi biến động theo phút. Vì thế, grain của mart cần xuất phát từ yêu cầu báo cáo và nhu cầu truy vết.
Loại đối tượng — ví dụ minh họa	Grain	Ý nghĩa phân tích
Dimension ngày	Một ngày	Thuộc tính lịch để lọc và nhóm.
Dimension sản phẩm	Một sản phẩm hoặc một phiên bản theo chính sách lịch sử	Ngữ cảnh phân loại hàng hóa.
Fact đơn hàng	Một đơn	Các phép đo ở cấp đơn.
Fact chi tiết bán hàng	Một chi tiết giao dịch	Lượng hàng và giá trị chi tiết.
Fact snapshot tồn kho	Một mốc thời gian × mặt hàng × địa điểm	Số dư tại mốc chụp.
Mart bán hàng	Một tổ hợp kỳ và các chiều được lựa chọn	Kết quả tổng hợp phục vụ báo cáo.


Do thuộc tính của dimension có thể thay đổi, thiết kế cần quyết định cách lưu giữ lịch sử. Với Slowly Changing Dimension (SCD), Type 1 cập nhật đè lên giá trị cũ, còn Type 2 tạo thêm phiên bản để phản ánh sự thay đổi theo thời gian [28], [29]. Lựa chọn phụ thuộc vào việc báo cáo cần phân tích theo đặc điểm hiện tại hay đặc điểm của đối tượng ở thời điểm giao dịch. Tương tự, fact snapshot chỉ phản ánh những thời điểm thực sự được chụp và lưu, không thể tự phục dựng các mốc quá khứ còn thiếu.

2.4. Công nghệ thu thập và xử lý dữ liệu

2.4.1. Thu thập và xử lý dữ liệu theo lô (Apache Spark)
Xử lý theo lô (batch processing) thực hiện các tác vụ trên một tập dữ liệu đã xác định trong từng lần chạy. Phạm vi xử lý có thể giới hạn theo thời gian, tập file hoặc lượng dữ liệu thay đổi đến một mốc cụ thể. Mô hình này phù hợp với việc tổng hợp báo cáo định kỳ, xử lý dữ liệu lịch sử và đối soát giữa nguồn giao dịch với hệ thống phân tích. Hạn chế chính là kết quả chỉ phản ánh dữ liệu đã được tiếp nhận và xử lý thành công ở lần chạy gần nhất.

Apache Spark là nền tảng xử lý dữ liệu phân tán, trong đó Spark SQL và DataFrame hỗ trợ làm việc với dữ liệu có cấu trúc. DataFrame biểu diễn dữ liệu theo các cột có tên, còn những thao tác lọc, chọn, nối và tổng hợp được tổ chức thành kế hoạch thực thi để Spark tối ưu [30]. Tuy nhiên, hiệu quả xử lý phân tán phụ thuộc cả cách phân vùng và tổ chức file. Các phép nối hoặc nhóm có thể làm phát sinh chi phí trao đổi dữ liệu giữa các node, trong khi số lượng lớn file nhỏ gia tăng chi phí lập kế hoạch và đọc dữ liệu.

Quá trình trích xuất theo lô có thể đọc toàn bộ dữ liệu nguồn hoặc chỉ nạp phần thay đổi kể từ lần trước. Với phương án nạp tăng dần, watermark được sử dụng để xác định khoảng dữ liệu của mỗi lần chạy [31]. Nếu nhiều bản ghi có cùng giá trị thời gian, có thể kết hợp thêm một khóa định danh để xác định ranh giới ổn định. Cách tiếp cận này chỉ đáng tin cậy khi trường theo dõi thay đổi được cập nhật đúng và dữ liệu còn hiện diện ở nguồn; các bản ghi bị xóa vật lý không thể được phát hiện chỉ bằng cách lọc timestamp của những dòng còn lại.

Để tránh bỏ sót dữ liệu ở ranh giới nạp tăng dần, pipeline đôi khi cần đọc chồng một khoảng thời gian. Khi đó, dữ liệu ở Silver phải được nhận diện theo khóa và phiên bản để cập nhật đúng trạng thái, thay vì tạo bản ghi trùng. Bronze có thể lưu lịch sử các lần tiếp nhận, còn Silver duy trì dữ liệu đã chuẩn hóa cho phân tích. Để chạy lại an toàn, tác vụ cần có quy tắc ghi idempotent, định danh lần chạy và cơ chế quản lý tiến độ; chỉ cấu hình retry trên bộ điều phối là chưa đủ.

Spark SQL hỗ trợ đọc dữ liệu từ cơ sở dữ liệu quan hệ qua JDBC rồi đưa vào DataFrame để tiếp tục xử lý hoặc kết hợp với nguồn khác [32]. Tuy nhiên, số lượng kết nối song song và cách chia khoảng đọc phải phù hợp với khả năng đáp ứng của hệ thống nguồn. Tăng số tác vụ quá mức có thể gây tải ngược cho cơ sở dữ liệu giao dịch. Khi nguồn tiếp tục thay đổi trong lúc trích xuất, pipeline còn phải xác định mốc ảnh chụp hoặc mức nhất quán có thể chấp nhận để bảo đảm độ tin cậy của kết quả.

2.4.2. Thu thập dữ liệu thay đổi CDC + Access Log (Debezium, Kafka, Flink)
Change Data Capture (CDC) là kỹ thuật theo dõi những thay đổi trong dữ liệu nguồn và phát chúng đến các thành phần xử lý tiếp theo. Với MySQL, Debezium có thể khai thác binlog để ghi nhận thao tác thay đổi, thay vì chỉ dựa vào các trường thời gian cập nhật. Connector hỗ trợ chụp trạng thái ban đầu (snapshot), sau đó tiếp tục đọc và phát sự kiện phát sinh [33]. Tuy nhiên, snapshot khởi tạo chỉ phản ánh trạng thái tại một thời điểm, không tái hiện đầy đủ mọi thay đổi đã xảy ra trước khi bắt đầu thu thập.

Bên cạnh CDC, access log phản ánh hoạt động truy cập ứng dụng thông qua những thông tin như thời điểm, đường dẫn yêu cầu, mã phản hồi và thời gian xử lý. Một yêu cầu đọc có thể không làm thay đổi dữ liệu giao dịch, trong khi một nghiệp vụ ghi lại có thể tạo ra nhiều sự kiện CDC. Vì vậy, hai nguồn bổ sung cho nhau nhưng phục vụ những mục tiêu phân tích khác nhau. Nội dung access log cũng cần được kiểm soát nhằm tránh ghi nhận dữ liệu nhạy cảm không cần thiết [20].

Apache Kafka tổ chức luồng sự kiện thành các topic, mỗi topic có thể gồm nhiều partition. Producer ghi dữ liệu và consumer đọc theo offset; thứ tự sự kiện được bảo đảm trong từng partition chứ không có thứ tự chung cho toàn bộ hệ thống [34]. Bộ ba topic–partition–offset mô tả vị trí lưu thông của một sự kiện, trong khi khóa nghiệp vụ và định danh sự kiện phản ánh ý nghĩa của dữ liệu. Một đơn hàng có thể phát sinh nhiều sự kiện, và cùng một sự kiện được gửi lại ở offset mới vẫn cần cơ chế nhận diện trùng ở tầng xử lý.

Apache Flink hỗ trợ xử lý luồng có trạng thái và dùng checkpoint để lưu tiến độ cùng trạng thái phục vụ phục hồi khi xảy ra sự cố [35]. Mức bảo đảm xử lý phụ thuộc không chỉ vào checkpoint mà còn vào khả năng phát lại dữ liệu của nguồn và cơ chế ghi ở đích. Bởi vậy, cấu hình exactly-once trong Flink không mặc nhiên bảo đảm giao dịch nguyên tử xuyên suốt mọi hệ thống ngoài. Thiết kế cần xem xét đầy đủ quá trình phục hồi, xử lý trùng và thời điểm xác nhận dữ liệu ở đầu ra.
Nguồn	Dữ liệu thường ghi nhận	Ý nghĩa sử dụng
CDC	Thao tác thay đổi, khóa, dữ liệu trước/sau và vị trí nhật ký	Theo dõi biến đổi bản ghi và xây biểu diễn trạng thái phù hợp.
Access log	Yêu cầu HTTP, route, mã phản hồi, thời lượng và thời điểm	Quan sát tương tác và hành vi phục vụ của ứng dụng.


Trong hệ thống thu thập dữ liệu, thời điểm sự kiện xảy ra, thời điểm hệ thống nhận được và thời điểm ghi vào đích có thể không trùng nhau. Khi phân tích theo ngày, phải thống nhất trường thời gian và múi giờ; thứ tự tiếp nhận cũng chưa chắc phản ánh chính xác thứ tự phát sinh nghiệp vụ. Đối với dữ liệu đến muộn, pipeline có thể cập nhật lại kết quả, chờ trong một khoảng thời gian xác định hoặc ghi nhận điều chỉnh. Chính sách lựa chọn phụ thuộc yêu cầu về độ mới và tính chính xác của báo cáo.

Thiết kế thu thập cần tách rõ dữ liệu sự kiện lịch sử và biểu diễn trạng thái hiện tại. Một khóa nguồn có thể trải qua nhiều thao tác tạo, sửa, xóa; để dựng trạng thái đúng, hệ thống phải xử lý thứ tự và loại bỏ bản ghi trùng theo quy tắc thống nhất. Tương tự, số yêu cầu HTTP không thể trực tiếp xem là số người dùng hoặc số giao dịch duy nhất. Việc lưu file, ghi sự kiện lên Kafka và commit dữ liệu vào bảng là những mốc xử lý khác nhau, vì vậy phải được theo dõi riêng.

2.4.3. Điều phối Pipeline (Apache Airflow)
Pipeline dữ liệu thường gồm nhiều tác vụ có quan hệ phụ thuộc, chẳng hạn dữ liệu phải được chuẩn hóa ở Silver trước khi sử dụng để tổng hợp Gold. Bộ điều phối chịu trách nhiệm xác định lịch chạy, thứ tự, điều kiện thực hiện và kết quả của các tác vụ. Apache Airflow mô hình hóa quy trình dưới dạng đồ thị có hướng không chu trình (Directed Acyclic Graph – DAG) [36]. DAG quản lý luồng thực thi, còn việc biến đổi dữ liệu được thực hiện bởi tác vụ hoặc engine được gọi.

Trong Airflow, một task có thể chạy chương trình Python hoặc gửi công việc đến hệ xử lý bên ngoài. Sự phân chia này giúp tách lỗi điều phối khỏi lỗi phát sinh trong phép biến đổi dữ liệu. Chẳng hạn, một task có thể thất bại do không kết nối được với Spark, hoặc do công việc đã chạy nhưng phát hiện dữ liệu không hợp lệ. Quan hệ phụ thuộc giữa các task cần thể hiện rõ điều kiện đầu vào sẵn sàng và tiêu chí cho phép chuyển sang bước tiếp theo.

Airflow phân biệt khoảng dữ liệu mà một DAG run phụ trách với thời điểm thực tế công việc được chạy [36]. Vì vậy, khi chạy bù hoặc chạy lại một kỳ cũ, pipeline phải sử dụng đúng nhãn kỳ dữ liệu thay vì mặc định lấy ngày hiện tại. Thông tin về kỳ xử lý, định danh lần chạy và nguồn đầu vào cần được lưu để phục vụ đối soát và truy vết.

Cơ chế retry hỗ trợ phục hồi những lỗi tạm thời, nhưng chỉ an toàn khi tác vụ được thiết kế để chạy lại mà không nhân đôi kết quả. Ngược lại, nếu lỗi xuất phát từ dữ liệu vi phạm ràng buộc, việc lặp lại cùng đầu vào thường không giải quyết được vấn đề. Quy trình xử lý cần phân loại lỗi hạ tầng, lỗi cấu trúc và lỗi nghiệp vụ để lựa chọn giữa chạy lại, sửa nguồn hoặc cách ly dữ liệu. Thứ tự task trong DAG cũng không tạo thành một giao dịch chung cho mọi bảng đầu ra.

Khi một bước trong pipeline thất bại, dữ liệu do các bước trước đã commit có thể vẫn tồn tại. Để phục hồi chính xác, hệ thống phải biết phạm vi dữ liệu đã tiếp nhận, phiên bản đầu ra và kết quả kiểm tra ở từng bước. Khi đó mới có thể xác định tác vụ nào cần chạy lại và phần nào có thể tái sử dụng. Nói cách khác, cơ chế điều phối chạy lại và khả năng xử lý lặp của từng tác vụ phải được thiết kế phối hợp với nhau.

2.4.4. Kiểm soát chất lượng dữ liệu và xử lý lỗi
Chất lượng dữ liệu phải được đánh giá trên cơ sở mục đích sử dụng, thay vì chỉ kiểm tra file có đọc được hay không. Các tiêu chí thường gặp gồm tính đầy đủ, duy nhất, hợp lệ về kiểu và giá trị, cùng tính nhất quán giữa những tập dữ liệu liên quan. Schelter và cộng sự đã đề xuất cách tự động hóa việc xác minh các ràng buộc chất lượng ở quy mô lớn [37]. Do dữ liệu đúng cấu trúc vẫn có thể sai về nghiệp vụ, các phép kiểm tra cần kết hợp mức bản ghi với mức tổng hợp.
Nhóm kiểm soát	Ví dụ minh họa	Ý nghĩa khi không đạt
Cấu trúc và kiểu	Cột bắt buộc, timestamp, trường tiền	Chưa thể biến đổi theo contract đã công bố.
Khóa và quan hệ	Trùng khóa ở trạng thái Silver, chi tiết thiếu đơn cha	Kết quả nối và tổng hợp có thể sai.
Nghiệp vụ	Số lượng, trạng thái và quy tắc giá trị	Bản ghi cần kiểm tra theo ý nghĩa giao dịch.
Đối soát	Tổng dòng hoặc tiền ở nguồn và đích	Có chênh lệch cần giải thích theo cùng phạm vi.
Thời gian và lineage	Kỳ xử lý, lần nạp Gold, run_id	Chưa đủ căn cứ xác định dữ liệu thuộc lần xử lý nào.


Các phép kiểm tra chất lượng có thể bố trí ngay sau tiếp nhận, sau bước chuẩn hóa hoặc trước khi công bố dữ liệu tổng hợp. Tại mỗi điểm, quality gate quy định tiêu chí chấp nhận kết quả và cách xử lý khi không đạt. Tùy mức độ ảnh hưởng, hệ thống có thể dừng pipeline, chuyển bản ghi vào vùng quarantine hoặc phát cảnh báo. Kết quả kiểm tra cần đi kèm thông tin về kỳ, nguồn và phiên bản dữ liệu để có thể đối chiếu và tái hiện.

Đối với phép đo có thể so sánh giữa nguồn và đích, tỷ lệ sai lệch tương đối được xác định theo công thức:
\[
V = \frac{|S-T|}{|S|} \times 100\%,\quad S \ne 0
\]
Ở đây, \(S\) và \(T\) lần lượt là giá trị tại nguồn và đích, được đo theo cùng định nghĩa và phạm vi. Khi \(S=0\), công thức không xác định và phải sử dụng một quy tắc đánh giá riêng; trường hợp cả hai giá trị đều bằng 0 cũng khác với trường hợp chỉ nguồn bằng 0. Ngưỡng sai lệch chấp nhận được cần dựa trên yêu cầu nghiệp vụ, độ chính xác của dữ liệu và mục tiêu kiểm tra, thay vì áp dụng máy móc một tỷ lệ cho mọi chỉ số.

Kết quả đối soát chỉ có ý nghĩa khi dữ liệu nguồn và đích phản ánh cùng phạm vi. Chẳng hạn, dữ liệu giao dịch đang thay đổi liên tục sẽ khác với ảnh chụp đã nạp; Bronze lưu lịch sử cũng không thể so trực tiếp số dòng với Silver chỉ lưu trạng thái hiện tại. Các phép nối một–nhiều còn có thể làm nhân giá trị tổng hợp nếu grain không được kiểm soát. Vì vậy, mỗi lần đối soát cần ghi rõ kỳ dữ liệu, bộ lọc, khóa và snapshot được sử dụng.

Cơ chế xử lý lỗi phải bảo đảm khả năng truy vết nhưng không làm gia tăng rủi ro lộ dữ liệu. Bản ghi bị loại cần được lưu cùng nguồn, thời điểm, lần xử lý và lý do để phục vụ kiểm tra hoặc tái xử lý. Vùng quarantine phải có phân quyền và chính sách lưu giữ tương ứng với mức nhạy cảm của dữ liệu. Nếu sử dụng kỹ thuật giả danh hóa (pseudonymization), cần lưu ý rằng việc thay thế định danh trực tiếp không đồng nghĩa dữ liệu đã hoàn toàn ẩn danh; dữ liệu gốc và thông tin có thể dùng để liên kết lại vẫn phải được bảo vệ.

2.5. Công nghệ phân tích và trực quan hóa dữ liệu

2.5.1. Truy vấn dữ liệu phân tích (Apache Trino)
Apache Trino là công cụ truy vấn SQL phân tán, sử dụng coordinator để tiếp nhận yêu cầu và lập kế hoạch, sau đó phân phối công việc cho các worker thực thi. Thông qua connector và catalog, Trino có thể truy cập nhiều nguồn dữ liệu bằng một giao diện SQL thống nhất [38]. Nhờ vậy, lớp ứng dụng không phải tự xử lý từng định dạng file. Tuy nhiên, Trino vẫn dựa vào các nguồn lưu trữ bên ngoài và không thay thế hệ quản trị giao dịch như MySQL.

Khi sử dụng Iceberg connector, Trino tra cứu metadata trong catalog để xác định phiên bản bảng và các file dữ liệu cần đọc. Khả năng truy vấn, cập nhật và quản lý bảng phụ thuộc tính năng connector, cấu hình hệ thống và quyền được cấp [39]. Vì thế, engine cần đồng thời có quyền truy cập thông tin bảng và vùng lưu trữ vật lý, không chỉ biết tên bảng trong catalog.

Truy vấn phục vụ BI thường kết hợp lọc dữ liệu, nối bảng fact với dimension và tổng hợp ở một mức chi tiết đầu ra xác định. Chỉ đọc các cột cần thiết, giới hạn kỳ phân tích và sử dụng mart phù hợp có thể làm giảm lượng dữ liệu phải xử lý. Tuy nhiên, hiệu quả tối ưu cần được kiểm chứng bằng kế hoạch thực thi thực tế. Quan trọng hơn, truy vấn chạy thành công về mặt kỹ thuật chưa bảo đảm công thức, bộ lọc và quan hệ nối đã phản ánh đúng câu hỏi nghiệp vụ.

Trong kiến trúc BI, dữ liệu phân tích có thể được truy cập trực tiếp qua công cụ SQL hoặc thông qua lớp dịch vụ cung cấp dữ liệu cho dashboard. Lớp dịch vụ giúp kiểm soát quyền, phạm vi truy vấn và định dạng kết quả trước khi hiển thị. Nếu hệ thống có cơ chế chuyển sang nguồn dự phòng khi xảy ra lỗi, cần bảo đảm các phép đo giữa hai nguồn có cùng định nghĩa và thông báo rõ nguồn dữ liệu đang được sử dụng.

Quyền truy cập dữ liệu tại engine và quyền của người dùng trên dashboard là hai lớp kiểm soát khác nhau. Một tài khoản dịch vụ dùng chung để truy vấn có thể có phạm vi truy cập rộng hơn người xem cuối. Do đó, nếu yêu cầu bảo vệ đến từng dòng hoặc đối tượng, hệ thống phải xác định nơi thực thi chính sách và kiểm tra mọi đường truy cập liên quan. Không thể mặc nhiên xem quyền được áp dụng trên giao diện cũng có hiệu lực với một kết nối SQL độc lập.

2.5.2. Trực quan hóa dữ liệu và thiết kế Dashboard (Apache ECharts)
Dashboard là công cụ trình bày những chỉ số và kết quả phân tích nhằm giúp người dùng theo dõi hoạt động và hỗ trợ quyết định. Thiết kế dashboard nên xuất phát từ câu hỏi quản trị và nhu cầu của từng vai trò. Người quản lý bán hàng quan tâm kết quả theo kỳ, kênh và nhóm sản phẩm; bộ phận vận hành cần theo dõi đơn đang xử lý; trong khi quản trị dữ liệu chú ý độ mới và chất lượng nguồn. Sự khác biệt này chi phối cách lựa chọn chỉ số, mức chi tiết, tần suất cập nhật và bố cục hiển thị.

Apache ECharts là thư viện hỗ trợ xây dựng biểu đồ tương tác trên nền Web. Mỗi biểu đồ được khởi tạo trong một vùng hiển thị có kích thước xác định, cùng cấu hình về dữ liệu, trục, chuỗi giá trị và tương tác. Khi kích thước vùng chứa thay đổi, ứng dụng cần cập nhật lại biểu đồ theo cơ chế thích hợp [40]. Việc khởi tạo, cập nhật và giải phóng tài nguyên cũng phải được quản lý để bảo đảm hiệu năng và khả năng hiển thị trên các thiết bị khác nhau.
Câu hỏi cần trả lời	Cách biểu diễn điển hình	Điều kiện sử dụng
Giá trị hiện tại là bao nhiêu?	Thẻ chỉ số	Kèm đơn vị, phạm vi và ý nghĩa của giá trị thiếu.
Kết quả thay đổi theo ngày ra sao?	Biểu đồ đường	Thứ tự thời gian đúng; ngày thiếu không tự thay bằng 0.
Nhóm nào đóng góp nhiều hơn?	Thanh ngang hoặc cột	Các nhóm và đơn vị so sánh tương ứng; thể hiện gốc 0 phù hợp.
Tỷ lệ hoặc sai lệch nào cần kiểm tra?	Thanh so sánh và bảng số liệu	Cùng đơn vị; có mẫu số và giới hạn diễn giải.
Bản ghi hoặc đối tượng nào cần xử lý?	Bảng có tìm kiếm/sắp xếp	Nêu rõ phạm vi lọc và dữ liệu được xuất.


Loại biểu đồ cần phù hợp với cấu trúc và ý nghĩa của dữ liệu. Biểu đồ cơ cấu chỉ nên dùng khi các nhóm tạo thành những phần của cùng một tổng thể và không chồng lặp; biểu đồ phễu đòi hỏi các bước có cùng đơn vị quan sát và mối liên hệ rõ ràng. Với những phép đo có đơn vị khác nhau, nên tách biểu đồ hoặc kèm bảng số liệu gốc để tránh tạo ra so sánh trực quan dễ gây hiểu lầm. Mục tiêu của trực quan hóa là làm rõ thông tin, không chỉ tạo ra hình thức bắt mắt.

Một dashboard thường có cấu trúc từ tổng quan đến phân tích chi tiết: chỉ số chính, xu hướng theo thời gian, so sánh giữa các nhóm và danh sách bản ghi cần xử lý. Cách vận hành bộ lọc phải nhất quán; bộ lọc toàn trang cần tác động đến những thành phần liên quan, còn tìm kiếm trong một bảng chỉ nên ảnh hưởng đến phạm vi cục bộ. Giao diện cũng cần phân biệt thời điểm tải trang, thời điểm cập nhật nguồn và thời điểm sự kiện xảy ra. Các trạng thái không có dữ liệu, đang tải hoặc lỗi phải được hiển thị rõ, thay vì mặc định chuyển thành giá trị 0.

Khả năng tiếp cận là một yêu cầu quan trọng của thiết kế dashboard. Bên cạnh nhãn và đơn vị rõ ràng, màu sắc không nên là dấu hiệu duy nhất để phân biệt nhóm hoặc trạng thái. ECharts hỗ trợ thành phần ARIA và mô tả biểu đồ cho công nghệ hỗ trợ đọc màn hình [41]; bảng số liệu đi kèm cũng giúp người dùng tiếp cận các giá trị chính xác. Các thao tác tìm kiếm, lọc, sắp xếp và xuất dữ liệu phải thống nhất về phạm vi, đồng thời cần được kiểm thử trên những thiết bị và công nghệ hỗ trợ phù hợp.
Tài liệu tham khảo
[1] OECD (2025), The 2025 OECD definition of e-commerce and guidelines for interpretation, OECD Publishing, mục 4.1–4.2 và Bảng 4.1. Ấn phẩm chính thức. DOI: 10.1787/2254f1de-en.

[2] OECD (2019), Unpacking E-commerce: Business Models, Trends and Policies, chương “Understanding E-Commerce”, phần “What is e-commerce?”. Nội dung trên OECD.

[3] IBM Think, What is omnichannel customer experience?, phần “Omnichannel strategy and multichannel strategy”. Tài liệu trực tuyến, truy cập ngày 28/10/2026.

[4] Verhoef, P. C., Kannan, P. K. và Inman, J. J. (2015), “From Multi-Channel Retailing to Omni-Channel Retailing: Introduction to the Special Issue on Multi-Channel Retailing”, Journal of Retailing, 91(2), tr. 174–181. DOI: 10.1016/j.jretai.2015.02.005. Thông tin và tóm tắt công trình tại University of Groningen.

[5] IBM Think, What is order management?, phần “How does order management work?” và “What are the basic steps of the order management process?”. Tài liệu trực tuyến, truy cập ngày 28/10/2026.

[6] IBM Think, What is inventory management?, phần “What is inventory management?” và “How does inventory management work?”. Tài liệu trực tuyến, truy cập ngày 28/10/2026.

[7] Microsoft Learn, Sales returns, phần “Return order process” và “Physical return order process”, Dynamics 365 Supply Chain Management. Tài liệu chính thức, truy cập ngày 28/10/2026.

[8] IBM Think, What is business intelligence (BI)? Tài liệu trực tuyến, truy cập ngày 28/10/2026.

[9] Shopify, Average Order Value: Formula and 7 Ways, phần định nghĩa và công thức AOV. Tài liệu trực tuyến, truy cập ngày 28/10/2026.

[10] Fielding, R. T. (2000), Architectural Styles and the Design of Network-based Software Architectures, chương 5, “Representational State Transfer (REST)”, University of California, Irvine. Luận án trên website tác giả.

[11] React Documentation, Your First Component. Tài liệu chính thức, truy cập ngày 28/10/2026.

[12] Next.js Documentation, Server and Client Components. Tài liệu chính thức, truy cập ngày 28/10/2026.

[13] FastAPI Documentation, Features. Tài liệu chính thức, truy cập ngày 28/10/2026.

[14] MySQL 8.4 Reference Manual, InnoDB and the ACID Model. Tài liệu chính thức, truy cập ngày 28/10/2026.

[15] SQLAlchemy 2.0 Documentation, Session Basics. Tài liệu chính thức, truy cập ngày 28/10/2026.

[16] OWASP Cheat Sheet Series, Authorization Cheat Sheet. Tài liệu chính thức, truy cập ngày 28/10/2026.

[17] OWASP Cheat Sheet Series, Session Management Cheat Sheet. Tài liệu chính thức, truy cập ngày 28/10/2026.

[18] OWASP Cheat Sheet Series, Password Storage Cheat Sheet. Tài liệu chính thức, truy cập ngày 28/10/2026.

[19] Jones, M., Bradley, J. và Sakimura, N. (2015), JSON Web Token (JWT), RFC 7519. Tiêu chuẩn IETF.

[20] OWASP Cheat Sheet Series, Logging Cheat Sheet. Tài liệu chính thức, truy cập ngày 28/10/2026.

[21] Armbrust, M., Ghodsi, A., Xin, R. và Zaharia, M. (2021), “Lakehouse: A New Generation of Open Platforms that Unify Data Warehousing and Advanced Analytics”, CIDR 2021. Bài báo.

[22] Apache Iceberg Documentation 1.10.0, Reliability. Tài liệu chính thức, truy cập ngày 28/10/2026.

[23] Databricks Documentation, What is the medallion lakehouse architecture? Tài liệu chính thức, truy cập ngày 28/10/2026.

[24] MinIO, kho mã nguồn chính thức và README của dự án. MinIO trên GitHub, truy cập ngày 28/10/2026.

[25] Apache Polaris, kho mã nguồn chính thức và phần giới thiệu catalog Iceberg REST. Apache Polaris trên GitHub, truy cập ngày 28/10/2026.

[26] Kimball, R. (2008), “Fact Tables”, Kimball Group. Bài viết của tác giả.

[27] Kimball Group, Dimensional Modeling Techniques, nhóm kỹ thuật fact, dimension và khả năng cộng gộp. Tài liệu của Kimball Group, truy cập ngày 28/10/2026.

[28] Kimball Group, Type 1: Overwrite. Kỹ thuật chiều thay đổi chậm, truy cập ngày 28/10/2026.

[29] Kimball Group, Type 2: Add New Row. Kỹ thuật chiều thay đổi chậm, truy cập ngày 28/10/2026.

[30] Apache Spark Documentation 3.5.7, Spark SQL, DataFrames and Datasets Guide. Tài liệu chính thức, truy cập ngày 28/10/2026. Nguồn được dùng cho khái niệm Spark SQL/DataFrame trong nhánh 3.5.

[31] Microsoft Learn, Incrementally load data from a source data store to a destination data store, phần “Delta data loading from database by using a watermark”. Tài liệu chính thức, truy cập ngày 28/10/2026.

[32] Apache Spark Documentation 3.5.7, JDBC To Other Databases. Tài liệu chính thức, truy cập ngày 28/10/2026.

[33] Debezium Documentation 3.0, Debezium connector for MySQL. Tài liệu chính thức, truy cập ngày 28/10/2026.

[34] Apache Kafka Documentation 3.8, Introduction. Tài liệu chính thức, truy cập ngày 28/10/2026.

[35] Apache Flink Documentation 1.19, Checkpointing. Tài liệu chính thức, truy cập ngày 28/10/2026.

[36] Apache Airflow Documentation 2.10.5, DAGs. Tài liệu chính thức, truy cập ngày 28/10/2026.

[37] Schelter, S. và cộng sự (2018), “Automating Large-Scale Data Quality Verification”, Proceedings of the VLDB Endowment, 11(12), tr. 1781–1794. DOI: 10.14778/3229863.3229867. Bài báo.

[38] Trino Documentation, Trino concepts. Tài liệu chính thức, truy cập ngày 28/10/2026.

[39] Trino Documentation, Iceberg connector. Tài liệu chính thức, truy cập ngày 28/10/2026.

[40] Apache ECharts Handbook, Chart Container and Size. Tài liệu chính thức, truy cập ngày 28/10/2026.

[41] Apache ECharts Handbook, Web Accessibility. Tài liệu chính thức, truy cập ngày 28/10/2026.