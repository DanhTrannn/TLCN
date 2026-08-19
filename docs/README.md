# Documentation

Tài liệu được tổ chức theo mục đích thay vì đặt rải rác ở repository root.

## Nguồn quyết định

Đọc theo thứ tự ưu tiên:

1. [`project/scope.md`](project/scope.md) — phạm vi và acceptance TLCN;
2. [`project/lakehouse-plan.md`](project/lakehouse-plan.md) — kế hoạch kiến trúc Lakehouse;
3. [`architecture/oltp-schema.md`](architecture/oltp-schema.md) — logical schema và transaction catalogue;
4. [`project/web-plan.md`](project/web-plan.md) — kế hoạch source website;
5. [`architecture/project-structure.md`](architecture/project-structure.md) — kiến trúc triển khai;
6. [`../skills/oltp-design/SKILL.md`](../skills/oltp-design/SKILL.md) — nguyên tắc thiết kế tham khảo.

Khi tài liệu xung đột, `project/scope.md` được ưu tiên.

## Tài liệu kiến trúc mở rộng

- [`architecture/lakehouse-v2-reduced.md`](architecture/lakehouse-v2-reduced.md) — đánh giá kiến trúc Iceberg–Polaris–Spark–Trino theo hướng Lakehouse 2.0 và các thành phần được hoãn.

## Danh mục

| Thư mục | Nội dung |
|---|---|
| [`project/`](project/) | Scope, roadmap và implementation plan |
| [`architecture/`](architecture/) | System boundary, project structure và OLTP schema |
| [`design-system/`](design-system/) | Tokens, typography và component specs cho Storefront UI |
| [`runbook/`](runbook/) | Setup, Polaris/Iceberg local, operation, recovery và teardown |

Tài liệu phải dùng đường dẫn tương đối, không chứa secret và không commit output được sinh tự động.
