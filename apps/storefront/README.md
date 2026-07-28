# NÉT Studio Storefront

Next.js application cung cấp giao diện customer và admin cho hệ thống nguồn OLTP.

## Chức năng

- catalog, search, filter, sort và product detail;
- register/login, wishlist, cart và checkout;
- order history và order detail;
- admin dashboard, customer, catalog, inventory và order management.

## Chạy bằng Docker

Từ repository root:

```bash
docker compose --profile core up -d --build storefront
```

Mở `http://localhost:3000`.

## Chạy local

```bash
cd apps/storefront
npm install
npm run dev
```

Các biến public được cấu hình khi build:

- `NEXT_PUBLIC_API_BASE_URL`, mặc định `http://localhost:8000`;
- `NEXT_PUBLIC_CSRF_COOKIE_NAME`, mặc định `tlcn_csrf`.

## Kiểm tra

```bash
npm run typecheck
npm run build
```
