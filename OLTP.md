Bạn là Senior Database Architect chuyên thiết kế hệ thống OLTP cho website
thương mại điện tử.

Hãy phân tích repository hiện tại và đề xuất kiến trúc cơ sở dữ liệu OLTP cho
website thời trang một thương hiệu.

Mục tiêu của thiết kế:

1. Bảo đảm tính chính xác và nhất quán cho các nghiệp vụ giao dịch.
2. Tối ưu cho các thao tác đọc, ghi có độ trễ thấp.
3. Xử lý an toàn nhiều người dùng đồng thời.
4. Dễ bảo trì và mở rộng khi nghiệp vụ thay đổi.
5. Thuận tiện để đồng bộ dữ liệu sang Data Warehouse hoặc Lakehouse phục vụ
   OLAP trong tương lai.
6. Không làm biến dạng mô hình OLTP chỉ để phục vụ báo cáo.

======================================================================
PHẠM VI CÔNG VIỆC
======================================================================

Đây chỉ là nhiệm vụ phân tích và đề xuất kiến trúc.

Không được:

- Sửa bất kỳ file nào trong repository.
- Viết code backend.
- Viết SQL hoặc DDL hoàn chỉnh.
- Tạo migration.
- Tạo entity, model hoặc repository.
- Tạo API.
- Cài đặt transaction.
- Chạy lệnh làm thay đổi dữ liệu.
- Đề xuất triển khai ngay khi chưa phân tích đầy đủ.
- Tự ý thêm microservice, Kafka, Redis, sharding hoặc công nghệ phức tạp.

Chỉ được:

- Đọc repository.
- Phân tích hệ thống hiện tại.
- Phát hiện vấn đề.
- Đề xuất kiến trúc logic.
- Đưa ra các phương án và trade-off.
- Mô tả cách triển khai ở mức kiến trúc, không viết code.

======================================================================
BƯỚC 1 — KHẢO SÁT REPOSITORY
======================================================================

Hãy đọc repository để xác định:

- Framework backend.
- DBMS đang hoặc dự kiến sử dụng.
- ORM hoặc database access layer.
- Cấu trúc domain hiện tại.
- Các model hoặc entity hiện có.
- Các migration hiện có.
- Các service, repository và API liên quan đến dữ liệu.
- Các luồng nghiệp vụ chính.
- Các thao tác đọc và ghi quan trọng.
- Các transaction hiện có nếu có.
- Các trạng thái nghiệp vụ.
- Cách lưu lịch sử thay đổi.
- Cách xử lý xóa dữ liệu.
- Cách xử lý lỗi, retry và request trùng.
- Các chức năng báo cáo hoặc phân tích hiện có.
- Khả năng tích hợp Data Warehouse hoặc Lakehouse trong tương lai.

Không chỉ đọc schema. Phải đọc cả business logic để hiểu cách dữ liệu được sử dụng.

Nếu repository chưa có đủ thông tin, hãy nêu rõ giả định thay vì tự khẳng định.

======================================================================
BƯỚC 2 — PHÂN TÍCH WORKLOAD OLTP
======================================================================

Phân tích các loại workload của hệ thống:

- Point lookup theo khóa.
- Tìm kiếm theo điều kiện.
- Danh sách có sắp xếp và phân trang.
- Ghi mới.
- Cập nhật trạng thái.
- Cập nhật số lượng.
- Giao dịch nhiều bước.
- Các thao tác có nhiều người dùng truy cập đồng thời.
- Các dữ liệu có nguy cơ contention cao.
- Các truy vấn có thể trở thành truy vấn OLAP.

Với mỗi nhóm nghiệp vụ, mô tả:

- Read pattern.
- Write pattern.
- Tần suất dự kiến.
- Số lượng bản ghi được truy cập.
- Yêu cầu về latency.
- Yêu cầu về consistency.
- Nguy cơ concurrency.
- Mức độ quan trọng của dữ liệu.
- Giá trị đối với OLAP trong tương lai.

Không được kết luận thiết kế tối ưu khi chưa dựa trên workload.

======================================================================
BƯỚC 3 — ĐỀ XUẤT KIẾN TRÚC TỔNG THỂ
======================================================================

Đề xuất kiến trúc dữ liệu ở mức logic, bao gồm:

1. OLTP database

- Là nguồn dữ liệu giao dịch chính thức.
- Tối ưu cho transaction ngắn và truy vấn độ trễ thấp.
- Sử dụng mô hình quan hệ được chuẩn hóa hợp lý.
- Ưu tiên row-oriented storage.
- Bảo vệ các business invariant quan trọng.
- Không chạy truy vấn phân tích nặng trực tiếp trên primary database.

2. Hệ thống OLAP tương lai

- Là hệ thống dữ liệu dẫn xuất.
- Nhận dữ liệu từ OLTP thông qua batch extraction, CDC hoặc event stream.
- Có thể sử dụng column-oriented storage.
- Có thể xây dựng star schema, fact và dimension.
- Chấp nhận eventual consistency theo độ trễ đã định nghĩa.
- Có khả năng rebuild từ dữ liệu nguồn và lịch sử thay đổi.

3. Luồng dữ liệu đề xuất

Mô tả kiến trúc ở mức khái niệm:

Application
→ OLTP database
→ cơ chế ghi nhận thay đổi
→ vùng dữ liệu thô
→ xử lý và chuẩn hóa
→ mô hình phục vụ OLAP

Không cần đưa ra tên sản phẩm công nghệ cụ thể nếu repository chưa có yêu cầu.

Nếu đề xuất công nghệ, phải giải thích:

- Nó giải quyết vấn đề gì.
- Vì sao cần thiết.
- Có thể trì hoãn triển khai hay không.
- Chi phí vận hành.
- Phương án đơn giản hơn.

======================================================================
BƯỚC 4 — MÔ HÌNH DỮ LIỆU LOGIC
======================================================================

Không cần đưa ra tên bảng chi tiết.

Hãy xác định ở mức khái niệm:

- Các nhóm thực thể nghiệp vụ.
- Quan hệ giữa các nhóm thực thể.
- Cardinality.
- Aggregate boundary nếu phù hợp.
- Dữ liệu nào là master data.
- Dữ liệu nào là transaction data.
- Dữ liệu nào là current state.
- Dữ liệu nào là historical state.
- Dữ liệu nào là immutable event.
- Dữ liệu nào là derived data.
- Dữ liệu nào là snapshot tại thời điểm giao dịch.

Với mỗi nhóm dữ liệu, xác định grain:

- Một bản ghi đại diện cho điều gì.
- Khi nào bản ghi được tạo.
- Khi nào được phép thay đổi.
- Khi nào không được thay đổi.
- Có cần giữ lịch sử không.
- Có giá trị gì đối với OLAP.

Không thiết kế OLTP theo star schema.

Không dùng cấu trúc fact và dimension trực tiếp trong OLTP, trừ khi nó thực sự
phục vụ nghiệp vụ giao dịch.

======================================================================
BƯỚC 5 — BUSINESS INVARIANTS
======================================================================

Liệt kê các quy tắc nghiệp vụ bắt buộc phải luôn đúng.

Phân loại:

- Invariant trên một đối tượng.
- Invariant giữa nhiều đối tượng.
- Invariant về uniqueness.
- Invariant về số lượng.
- Invariant về tổng tiền.
- Invariant về trạng thái.
- Invariant về chuyển trạng thái.
- Invariant về quan hệ tham chiếu.
- Invariant về tài nguyên hữu hạn.
- Invariant cần đối soát.

Với mỗi invariant, xác định cơ chế bảo vệ phù hợp:

- Data type.
- NOT NULL.
- CHECK constraint.
- UNIQUE constraint.
- Foreign key.
- Atomic operation.
- Transaction.
- Locking.
- Optimistic concurrency.
- Serializable isolation.
- Application validation.

Không chỉ ghi chung chung rằng database hỗ trợ ACID.

======================================================================
BƯỚC 6 — PHÂN TÍCH ACID
======================================================================

Phân tích cụ thể:

1. Atomicity

- Những thay đổi nào phải commit hoặc rollback cùng nhau.
- Transaction boundary phù hợp.
- Trạng thái hệ thống khi lỗi xảy ra giữa quá trình.
- Các side effect nào nằm ngoài database.
- Cách tránh xử lý một phần.
- Cách xử lý khi client không biết transaction đã commit hay chưa.

2. Consistency

- Các invariant nào do database bảo vệ.
- Các invariant nào do application bảo vệ.
- Trường hợp nào cần kết hợp constraint và transaction.
- Dữ liệu nào có nguy cơ trở nên không nhất quán.

3. Isolation

- Các transaction nào có thể chạy đồng thời.
- Transaction nào truy cập cùng dữ liệu.
- Các race condition có thể xảy ra.
- Isolation level nào phù hợp với từng nhóm nghiệp vụ.

4. Durability

- Ý nghĩa của commit thành công.
- Vai trò của WAL hoặc transaction log.
- Backup và point-in-time recovery.
- Ảnh hưởng của replication đồng bộ hoặc bất đồng bộ.
- Nguy cơ mất recent writes khi failover.
- Phân biệt replication và backup.

======================================================================
BƯỚC 7 — TRANSACTION CATALOGUE
======================================================================

Không viết code transaction.

Hãy lập danh mục các transaction nghiệp vụ quan trọng.

Với mỗi transaction, mô tả:

- Tên nghiệp vụ.
- Trigger.
- Dữ liệu cần đọc.
- Dữ liệu cần ghi.
- Business invariant cần bảo vệ.
- Transaction bắt đầu và kết thúc ở đâu.
- Dữ liệu có contention hay không.
- Isolation level đề xuất.
- Concurrency control đề xuất.
- Hành vi khi transaction thất bại.
- Có cần retry không.
- Có cần idempotency không.
- Có side effect ngoài database không.
- Dữ liệu nào cần phát sinh cho OLAP.

Transaction phải được thiết kế ngắn.

Không đề xuất:

- Giữ transaction qua nhiều HTTP request.
- Chờ người dùng trong transaction.
- Gọi payment API trong khi giữ database lock.
- Gọi shipping API trong khi giữ lock.
- Gửi email trong transaction.
- Thực hiện truy vấn phân tích lớn trong transaction.

======================================================================
BƯỚC 8 — ISOLATION LEVELS
======================================================================

Không chọn một isolation level duy nhất cho toàn hệ thống nếu không cần thiết.

Với từng nhóm transaction, phân tích:

- Dirty read.
- Dirty write.
- Non-repeatable read.
- Read skew.
- Lost update.
- Write skew.
- Phantom.
- Duplicate execution.

Đánh giá các mức:

1. Read Committed

- Nghiệp vụ nào có thể dùng.
- Những anomaly nào vẫn có thể xảy ra.
- Có cần atomic update hoặc explicit locking bổ sung không.

2. Snapshot Isolation hoặc Repeatable Read

- Có cần consistent snapshot không.
- DBMS thực tế có tự phát hiện lost update không.
- Có nguy cơ write skew không.
- Có nguy cơ phantom không.
- Transaction dài ảnh hưởng MVCC như thế nào.

3. Serializable

- Nghiệp vụ nào thực sự cần.
- Invariant nào không thể bảo vệ bằng constraint hoặc atomic statement.
- Chi phí về throughput, abort, retry, lock và latency.
- Có nên áp dụng cục bộ thay vì toàn hệ thống không.

Không giả định các DBMS cung cấp guarantee giống nhau chỉ vì isolation level
cùng tên.

======================================================================
BƯỚC 9 — CONCURRENCY CONTROL
======================================================================

Với từng dữ liệu có contention, đề xuất một trong các chiến lược:

- Atomic database operation.
- Conditional update.
- Unique constraint.
- Pessimistic row-level locking.
- Optimistic locking bằng version.
- Compare-and-set.
- Automatic conflict detection.
- Serializable transaction.
- Thiết kế lại invariant.

Phân tích riêng:

1. Lost update

Xác định các luồng read-modify-write có thể làm ghi đè thay đổi của nhau.

Đề xuất cách ngăn chặn và giải thích trade-off.

2. Write skew

Xác định các trường hợp:

- Hai transaction cùng đọc một điều kiện.
- Cả hai cùng thấy điều kiện hợp lệ.
- Mỗi transaction ghi vào một đối tượng khác.
- Kết quả cuối cùng làm invariant bị vi phạm.

3. Phantom

Xác định các trường hợp transaction ra quyết định dựa trên:

- Sự tồn tại của một tập bản ghi.
- Số lượng bản ghi.
- Không có bản ghi thỏa điều kiện.
- Một khoảng giá trị.

Đánh giá nhu cầu về:

- Serializable isolation.
- Predicate locking.
- Index-range locking.
- Next-key locking.
- Unique constraint.
- Thiết kế lại mô hình.

4. Deadlock

Mô tả:

- Nghiệp vụ nào có nguy cơ deadlock.
- Thứ tự khóa đề xuất.
- Cách giữ transaction ngắn.
- Cơ chế retry phù hợp.
- Các metrics cần theo dõi.

======================================================================
BƯỚC 10 — STORAGE VÀ INDEX STRATEGY
======================================================================

Chỉ đề xuất ở mức chiến lược, không viết câu lệnh tạo index.

Phân tích:

- Row-oriented storage cho OLTP.
- Column-oriented storage cho OLAP.
- Point lookup.
- Range scan.
- Primary key locality.
- Sequential key và random key.
- Page split.
- Fragmentation.
- Hot page.
- Read amplification.
- Write amplification.
- WAL.
- Compaction nếu storage engine sử dụng LSM-tree.
- Tail latency.

Với mỗi nhóm index đề xuất, nêu:

- Query pattern mục tiêu.
- Cột lọc ở mức khái niệm.
- Cột JOIN.
- Điều kiện sort.
- Điều kiện range.
- Selectivity.
- Thứ tự cột trong composite index.
- Write cost.
- Storage cost.
- Locking impact.
- Khả năng trùng lặp với index khác.

Không đề xuất tạo index cho mọi thuộc tính.

Không kết luận index tối ưu nếu chưa có workload và execution plan.

======================================================================
BƯỚC 11 — THIẾT KẾ THUẬN TIỆN CHO OLAP
======================================================================

Thiết kế OLTP phải bảo tồn đủ dữ liệu để xây OLAP chính xác về sau.

Phân tích các nhóm dữ liệu:

1. Current state

- Trạng thái mới nhất phục vụ website.
- Có thể được cập nhật theo nghiệp vụ.

2. Historical state

- Lịch sử trạng thái.
- Thời điểm thay đổi.
- Trạng thái trước và sau.
- Tác nhân thay đổi.
- Lý do thay đổi.
- Nguồn thay đổi.

3. Transaction snapshot

Xác định những thuộc tính cần được giữ tại thời điểm giao dịch, ví dụ theo
khái niệm:

- Giá thực tế.
- Mức giảm giá.
- Thuế và phí.
- Thông tin giao nhận đã xác nhận.
- Thuộc tính sản phẩm hoặc phân loại tại thời điểm giao dịch.
- Kết quả tính toán cuối cùng.

Không luôn JOIN về master data hiện tại nếu điều đó làm sai lịch sử.

4. Event time

Phân biệt:

- Thời điểm sự kiện nghiệp vụ xảy ra.
- Thời điểm bản ghi được tạo.
- Thời điểm bản ghi được cập nhật.
- Thời điểm hệ thống nhận dữ liệu.
- Thời điểm dữ liệu được nạp vào OLAP.

5. Delete semantics

Phân biệt:

- Vô hiệu hóa.
- Hủy nghiệp vụ.
- Ẩn khỏi giao diện.
- Soft delete.
- Hard delete.
- Anonymization.

Mô tả cách delete hoặc anonymization được truyền sang OLAP.

======================================================================
BƯỚC 12 — CDC READINESS
======================================================================

Đánh giá kiến trúc OLTP có thuận tiện cho CDC hay không.

Kiểm tra:

- Định danh có ổn định không.
- Business key có rõ ràng không.
- Có thể nhận diện update và delete không.
- Có đủ timestamp không.
- Có thể thực hiện initial snapshot không.
- Có thể tiếp tục incremental capture sau snapshot không.
- Có nguy cơ bỏ sót nhiều thay đổi giữa hai lần extraction không.
- Có thể deduplicate không.
- Có thể replay không.
- Có thể xác định thứ tự thay đổi khi cần không.
- Schema evolution có làm hỏng downstream không.
- Có logic thay đổi dữ liệu ẩn mà CDC không nhìn thấy không.

Không được dựa duy nhất vào updated_at nếu một bản ghi có thể thay đổi nhiều lần.

======================================================================
BƯỚC 13 — KHẢ NĂNG SUY RA FACT VÀ DIMENSION
======================================================================

Không xây star schema trong OLTP.

Chỉ mô tả cách dữ liệu OLTP có thể chuyển thành:

- Transaction facts.
- Event facts.
- Periodic snapshot facts.
- Accumulating snapshot facts.
- Dimensions.
- Slowly Changing Dimensions.

Với từng nhóm dữ liệu phân tích, xác định:

- Grain.
- Event time.
- Measures.
- Dimensions liên quan.
- Business key.
- Snapshot attributes.
- Cách xử lý thay đổi.
- Cách xử lý xóa.
- Cách xử lý dữ liệu đến muộn.
- Cách deduplicate.
- Có thể rebuild từ nguồn hay không.

======================================================================
BƯỚC 14 — KHÔNG OVERENGINEER
======================================================================

Không tự động đề xuất:

- Microservices.
- Distributed transactions.
- Two-phase commit.
- Event sourcing toàn hệ thống.
- CQRS toàn hệ thống.
- Kafka.
- Redis.
- Elasticsearch.
- Read replica.
- Partitioning.
- Sharding.
- Multi-region writes.

Chỉ đề xuất khi có vấn đề thực tế cần giải quyết.

Mỗi công nghệ hoặc kỹ thuật bổ sung phải nêu:

- Vấn đề đang giải quyết.
- Bằng chứng từ repository hoặc workload.
- Lợi ích.
- Chi phí.
- Rủi ro.
- Phương án đơn giản hơn.
- Thời điểm thích hợp để áp dụng.

======================================================================
ĐỊNH DẠNG KẾT QUẢ
======================================================================

Chỉ trả về một tài liệu kiến trúc dạng Markdown trong phần trả lời.

Không tạo file nếu chưa được yêu cầu.

Tài liệu phải gồm các phần:

# 1. Executive Summary

Tóm tắt kiến trúc được đề xuất và các quyết định quan trọng nhất.

# 2. Repository Assessment

- Công nghệ hiện tại.
- Mô hình dữ liệu hiện tại.
- Điểm tốt.
- Điểm chưa tốt.
- Các rủi ro chính.

# 3. Assumptions

Phân biệt rõ thông tin đọc được từ repository và các giả định.

# 4. OLTP Workload Analysis

Mô tả read pattern, write pattern, latency, contention và consistency.

# 5. Proposed Logical Architecture

Mô tả kiến trúc OLTP và hướng kết nối OLAP trong tương lai.

# 6. Conceptual Data Model

Chỉ mô tả nhóm thực thể, quan hệ, grain và loại dữ liệu.
Không cần tên bảng cụ thể.

# 7. Business Invariants

Lập danh sách invariant và cơ chế bảo vệ đề xuất.

# 8. Transaction Catalogue

Với từng nghiệp vụ chính, mô tả transaction boundary, isolation,
concurrency control, retry và idempotency.

# 9. Concurrency Analysis

Phân tích lost update, write skew, phantom, deadlock và duplicate execution.

# 10. Isolation Decision Matrix

Với từng nhóm transaction:

- Isolation đề xuất.
- Guarantee cần thiết.
- Anomaly còn có thể xảy ra.
- Biện pháp bổ sung.
- Trade-off.

# 11. Storage and Index Strategy

Đề xuất chiến lược storage và index ở mức kiến trúc.

# 12. OLAP Readiness

Phân tích history, snapshot, event time, CDC, fact và dimension derivation.

# 13. Failure and Recovery Considerations

Phân tích abort, retry, unknown commit, durability, backup và recovery.

# 14. Architecture Alternatives

Đưa ra tối thiểu hai phương án nếu có nhiều lựa chọn hợp lý.

Với mỗi phương án:

- Ưu điểm.
- Nhược điểm.
- Độ phức tạp.
- Khi nào nên chọn.

# 15. Recommended Architecture

Chọn một phương án phù hợp nhất với repository hiện tại và giải thích lý do.

# 16. Phased Roadmap

Chia thành:

- Giai đoạn cần làm ngay.
- Giai đoạn chuẩn bị cho OLAP.
- Giai đoạn chỉ thực hiện khi workload tăng.
- Những thứ chưa nên triển khai.

# 17. Open Questions

Liệt kê những thông tin còn thiếu cần xác nhận trước khi triển khai code.

======================================================================
QUY TẮC KẾT LUẬN
======================================================================

Kết luận phải trả lời rõ:

1. Kiến trúc OLTP đề xuất là gì?
2. Vì sao kiến trúc này phù hợp với workload hiện tại?
3. Các invariant quan trọng được bảo vệ thế nào?
4. Transaction nào có nguy cơ lost update?
5. Transaction nào có nguy cơ write skew hoặc phantom?
6. Isolation level nào được đề xuất cho từng loại nghiệp vụ?
7. Cách xử lý idempotency và unknown commit là gì?
8. Dữ liệu lịch sử nào phải được giữ lại?
9. OLTP cần chuẩn bị gì để CDC hoạt động chính xác?
10. Dữ liệu có đủ grain và timestamp để xây fact và dimension không?
11. Truy vấn OLAP sẽ được tách khỏi OLTP thế nào?
12. Những kỹ thuật nào chưa nên triển khai vì có nguy cơ overengineering?
13. Bước tiếp theo cần thực hiện trước khi bắt đầu viết code là gì?

Nguyên tắc ưu tiên cuối cùng:

Correctness trước Performance.
Business Invariants trước Schema.
Transaction Safety trước Throughput.
Performance phải dựa trên Workload.
OLTP và OLAP phải được tách theo workload.
OLTP phải bảo tồn đủ lịch sử để OLAP phân tích chính xác.
Simplicity trước Distributed Complexity.
Không viết code trong nhiệm vụ này.