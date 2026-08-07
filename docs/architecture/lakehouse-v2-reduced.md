# Đánh giá Lakehouse 2.0 cho kiến trúc TLCN

## 1. Trạng thái tài liệu

Tài liệu này tham khảo bài viết [Lakehouse 2.0: Khi căn nhà trên hồ bị tháo thành những mảnh Lego](https://www.phamduytung.com/blog/2026-07-24-lakehouse-v2/) để đánh giá kiến trúc TLCN sau quyết định ngày 2026-08-07.

Tài liệu quyết định hiện hành:

1. [`../project/scope.md`](../project/scope.md) — phạm vi và acceptance;
2. [`../project/lakehouse-plan.md`](../project/lakehouse-plan.md) — kế hoạch kiến trúc Lakehouse chi tiết;
3. [`project-structure.md`](project-structure.md) — component boundary và cấu trúc repository.

Bản đánh giá cũ từng đề xuất `Delta + Spark + MinIO` và hoãn catalog/query engine riêng đã không còn khớp quyết định mới. Kiến trúc hiện tại chuyển sang `Iceberg + Polaris + Spark + Trino` và thêm structured access log làm nguồn TLCN.

## 2. Tư tưởng Lakehouse 2.0 liên quan

“Lakehouse 2.0” trong bài viết là hướng kiến trúc, không phải một phiên bản phần mềm chính thức. Các ý phù hợp với đồ án:

- open table format làm nền dữ liệu dùng chung;
- catalog tách khỏi compute engine;
- nhiều engine có vai trò chuyên biệt trên cùng table layer;
- storage cần hiểu snapshot, manifest, compaction và retention;
- batch và streaming có thể hội tụ nhưng không bắt buộc cùng triển khai;
- governance và semantic contract không tự xuất hiện chỉ vì dùng open format.

Lakehouse 2.0 không yêu cầu bỏ Bronze–Silver–Gold và cũng không yêu cầu thêm mọi công nghệ phổ biến.

## 3. Đối chiếu kiến trúc đã chốt

| Ý tưởng | Áp dụng trong TLCN | Giới hạn |
|---|---|---|
| Open table format | Apache Iceberg cho Bronze/Silver/Gold | Chỉ một format, không dùng Delta/Hudi song song |
| Open catalog | Apache Polaris | Quyền tối thiểu, chưa làm governance đa tenant |
| Composable compute | Spark ghi/transform, Trino đọc/query | Không cho nhiều writer engine |
| Object storage | MinIO Landing và Iceberg warehouse | Local Docker Compose, chưa cross-cloud |
| Batch/stream convergence | OLTP batch và log micro-batch 15 phút | Không Kafka/Flink/realtime SLA |
| Table-aware maintenance | File/snapshot/manifest metrics và compaction | Chạy theo threshold, không chạy mù |
| Data product/semantic | Gold facts, marts, KPI/ML contracts | Chưa xây semantic layer cấp doanh nghiệp |
| BI access | Superset → Trino → Polaris/Iceberg | Không query primary OLTP |

## 4. Vì sao Iceberg–Polaris–Trino có ý nghĩa

### Iceberg

Iceberg biến tập file trên MinIO thành bảng có snapshot, schema/partition evolution và atomic metadata commit. Giá trị luận văn nằm ở việc chứng minh replay, snapshot lineage, merge, compaction và query consistency, không chỉ ở việc ghi Parquet.

### Polaris

Polaris tách table catalog khỏi Spark và Trino. Cả hai engine phải phân giải cùng catalog/namespace/table thay vì mỗi engine giữ metastore riêng.

Phạm vi TLCN chỉ cần:

- một catalog `tlcn`;
- namespaces `bronze`, `silver`, `gold`, `quarantine`, `system`;
- Spark principal có quyền ghi cần thiết;
- Trino principal chỉ đọc trusted tables;
- audit/backup cấu hình catalog ở mức demo.

Không cần triển khai federation, multi-cloud, multi-tenant policy hoặc enterprise data sharing.

### Spark và Trino

Tách engine có mục đích rõ:

- Spark tối ưu cho batch ingestion, merge, DQ, aggregate và maintenance;
- Trino cung cấp SQL serving cho Superset;
- integration test phải chứng minh Trino nhìn đúng Iceberg snapshot Spark vừa publish;
- Spark là writer duy nhất để giảm compatibility/concurrency risk.

## 5. Medallion vẫn được giữ

### Landing

Landing giữ immutable OLTP extract và rotated `jsonl.gz` access-log files. Landing chưa phải trusted table và chưa tính KPI.

### Bronze

Bronze Iceberg append raw representation và ingestion metadata. Bronze giữ đủ thông tin để replay Silver mà không đọc lại nguồn.

### Silver

Silver chịu trách nhiệm parse, cast, deduplicate, merge, pseudonymize, enrich có kiểm soát và semantic quarantine.

### Gold

Gold chứa dimensions, facts, marts, web-performance aggregates và ML datasets có grain/KPI contract rõ.

### Quarantine/System

Quarantine là nhánh lỗi, không phải Medallion layer thứ tư. `system` giữ manifest, cursor, DQ, reconciliation, maintenance và publication audit.

## 6. Access log trong TLCN

DOCX bổ sung access log nhưng hoãn clickstream event. Vì vậy cần phân biệt:

- access log grain là một completed HTTP request;
- log phục vụ request volume, status/error, latency, route, search/filter request và product-request analysis;
- business revenue/order/cart vẫn lấy OLTP làm nguồn chính thức;
- DAU/MAU chỉ tính bằng authenticated actor key đã pseudonymize;
- không dùng IP làm customer identity;
- không khẳng định click funnel chi tiết nếu chưa có canonical event/action contract;
- event frontend/mobile, session analytics, Kafka và Flink để KLTN.

## 7. Đánh giá độ phức tạp

Kiến trúc mới nặng hơn phương án `Delta + Spark` vì thêm Polaris, Trino và một source contract cho log. Nó vẫn phù hợp đồ án hai người nếu giới hạn chặt:

1. chỉ một table format;
2. chỉ Spark được ghi;
3. Trino chỉ đọc;
4. một catalog và ít namespace;
5. batch/micro-batch, không streaming;
6. một dashboard chính;
7. log schema nhỏ, không clickstream;
8. compatibility PoC hoàn thành trước khi xây toàn bộ pipeline.

Nếu PoC không chứng minh được Spark–Polaris–Trino compatibility trong thời gian quy định, phải dừng và ghi nhận blocker thay vì thêm metastore hoặc format thứ hai một cách tùy tiện.

## 8. PoC bắt buộc

Trước khi triển khai full Medallion, PoC phải chứng minh:

1. Spark tạo Iceberg namespace/table qua Polaris;
2. Spark append và merge sample data;
3. Trino đọc đúng schema, row count và snapshot mới;
4. schema evolution được cả hai engine hỗ trợ ở mức dùng trong TLCN;
5. MinIO credential và endpoint hoạt động đúng từ hai engine;
6. Superset query được một Gold sample qua Trino;
7. restart container không làm mất catalog metadata;
8. một commit conflict/failure không tạo trusted partial result.

Không đạt PoC thì chưa được bắt đầu toàn bộ Silver/Gold implementation.

## 9. Maintenance thay cho Z-order mặc định

Sơ đồ Word nhắc partitioning và Z-order. Với Iceberg, plan chốt cách diễn đạt trung lập theo table format:

- partition evolution;
- sort order theo query pattern;
- rewrite data files;
- rewrite manifests;
- expire snapshots;
- remove orphan files sau safety window.

Compaction được trigger khi metric vượt threshold theo table class. Row count, checksum và KPI phải không đổi trước/sau maintenance.

## 10. Các phần hoãn

- frontend/mobile clickstream;
- Kafka/Flink và streaming SLA;
- GeoIP external enrichment;
- multiple writer engines;
- cross-cloud/federated catalog;
- credential vending nâng cao;
- enterprise semantic layer;
- realtime Gold marts;
- online feature store/inference;
- MLflow;
- recommendation engine.

## 11. Quyết định chốt

| ID | Quyết định |
|---|---|
| LH-01 | MySQL OLTP và structured access log là hai nguồn TLCN |
| LH-02 | Log rotate/nén theo micro-batch 15 phút; clickstream để sau |
| LH-03 | MinIO giữ Landing và Iceberg warehouse |
| LH-04 | Iceberg là table format duy nhất |
| LH-05 | Polaris là catalog chung |
| LH-06 | Spark là writer/transform engine duy nhất |
| LH-07 | Trino là read/query layer cho Superset |
| LH-08 | Bronze–Silver–Gold vẫn là logical trust boundaries |
| LH-09 | Gold publication phải qua DQ/reconciliation gate |
| LH-10 | Maintenance chạy theo metric/threshold và bảo toàn logical result |
| LH-11 | ML mua lại chỉ dùng OLTP-derived Gold trong TLCN |
| LH-12 | Kafka/Flink/event clickstream nằm ngoài TLCN |

## 12. Nguồn tham khảo

- Phạm Duy Tùng, [Lakehouse 2.0: Khi căn nhà trên hồ bị tháo thành những mảnh Lego](https://www.phamduytung.com/blog/2026-07-24-lakehouse-v2/).
- Apache Iceberg, [REST Catalog API Specification](https://iceberg.apache.org/rest-catalog-spec/).
