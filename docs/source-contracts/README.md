# Source contracts

TLCN có hai nhóm source contract chính thức:

1. 16 bảng MySQL OLTP được phép extract;
2. structured web access log có grain một completed HTTP request.

## MySQL contract

Mỗi bảng phải có owner, grain, PK/business key, cursor, mutability, delete/inactive semantics, timezone, PII class, allowed columns và reconciliation rules.

`customer_credentials` bị loại hoàn toàn khỏi extraction.

## Access-log contract

Contract log phải chốt:

- `request_id` và deduplication rule;
- UTC event/emitted time;
- service, method, canonical route, status và latency;
- optional actor/product/search/filter metadata;
- schema/parser version;
- file rotation 15 phút, `gzip`, file checksum và line count;
- field cấm: password, token, cookie, authorization header, checkout body và raw customer PII;
- pseudonymization cho IP/actor reference trước trusted Silver;
- reconciliation từ closed source file tới Bronze, Silver và Gold interval.

Clickstream event, analytics session, Kafka và CDC streaming không thuộc TLCN. Chi tiết tại [`../project/lakehouse-plan.md`](../project/lakehouse-plan.md).
