# Documentation

Tài liệu được tổ chức theo mục đích thay vì đặt rải rác ở repository root.

## Nguồn quyết định

Đọc theo thứ tự ưu tiên:

1. [`project/scope.md`](project/scope.md) — phạm vi và acceptance TLCN;
2. [`architecture/oltp-schema.md`](architecture/oltp-schema.md) — logical schema và transaction catalogue;
3. [`project/web-plan.md`](project/web-plan.md) — kế hoạch source website;
4. [`architecture/project-structure.md`](architecture/project-structure.md) — kiến trúc triển khai;
5. [`../skills/oltp-design/SKILL.md`](../skills/oltp-design/SKILL.md) — nguyên tắc thiết kế tham khảo.

Khi tài liệu xung đột, `project/scope.md` được ưu tiên.

## Danh mục

| Thư mục | Nội dung |
|---|---|
| [`project/`](project/) | Scope, roadmap và implementation plan |
| [`architecture/`](architecture/) | System boundary, project structure và OLTP schema |
| [`source-contracts/`](source-contracts/) | Contract cho nguồn MySQL được phép extract |
| [`data-dictionary/`](data-dictionary/) | Grain và định nghĩa trường dữ liệu |
| [`kpi/`](kpi/) | Công thức, cutoff và reconciliation của KPI |
| [`runbook/`](runbook/) | Setup, operation, recovery và teardown |
| [`thesis/`](thesis/) | Outline, hình vẽ, bảng thực nghiệm và demo script |

Tài liệu phải dùng đường dẫn tương đối, không chứa secret và không commit output được sinh tự động.
