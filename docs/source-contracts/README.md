# Source contracts

TLCN chỉ có source contract cho 16 bảng MySQL OLTP được phép extract. Mỗi contract phải có owner, grain, PK/business key, cursor, mutability, delete/inactive semantics, timezone, PII class, allowed columns và reconciliation rules.

`customer_credentials` bị loại hoàn toàn khỏi extraction.
