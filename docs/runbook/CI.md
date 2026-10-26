# CI và kiểm tra mã nguồn

Workflow [`ci.yml`](../../.github/workflows/ci.yml) dùng GitHub Actions để kiểm tra cấu hình, cú pháp và khả năng build của đồ án.

## Sự kiện kích hoạt

- Push vào `dev`, `main` hoặc `master`.
- Pull request.
- Chạy thủ công bằng `workflow_dispatch`.

Workflow bỏ qua thay đổi chỉ nằm trong `docs/**`, `**.md`, `.gitignore` và `LICENSE`.

## Các job

### Repository validation

- Nạp cấu hình dev từ `.env.example` rồi kiểm tra Docker Compose với bốn profile: `core`, `batch`, `streaming`, `lakehouse-tools`.
- Biên dịch Python trong `airflow/dags/` để phát hiện lỗi cú pháp.
- Chạy Ruff trên mã nguồn Python.

Compose vẫn yêu cầu đầy đủ credential của từng service account. Job dùng `--env-file .env.example` vì `.env` không được lưu trong Git.

### Storefront

- Cài dependency bằng `npm ci`.
- Chạy lint và TypeScript typecheck.
- Build Next.js.

## Lệnh chạy cục bộ

Từ thư mục gốc của repo:

```bash
docker compose --env-file .env.example --profile core --profile batch --profile streaming --profile lakehouse-tools config --quiet
uv lock --check
python3 -m compileall -q airflow/dags/
uvx ruff check .

npm --prefix apps/storefront ci
npm --prefix apps/storefront run lint
make typecheck
npm --prefix apps/storefront run build
```
