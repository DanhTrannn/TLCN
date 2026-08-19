# D&K Storefront Application

The Storefront is a Next.js 15 application providing user interfaces for consumer shopping and store management.

## Technology Stack

- **Framework:** Next.js 15 (App Router, Standalone Output)
- **UI & State:** React 19, Tailwind CSS
- **Language:** TypeScript (strict mode)

---

## Route Structure

### Customer Routes

| Path | Access | Description |
|---|---|---|
| `/` | Public | Storefront homepage with editorial hero banners |
| `/products` | Public | Search, sort, and faceted category/price/stock catalog |
| `/products/[slug]` | Public | Product detail, variant selection, and approved reviews |
| `/cart` | Public / Customer | Active shopping cart item management |
| `/wishlist` | Customer | Saved wishlist items with presence indicators |
| `/checkout` | Customer | Atomic checkout with coupon validation and stock check |
| `/checkout/result/[orderNumber]` | Customer | Post-checkout receipt and payment confirmation |
| `/orders` | Customer | Order history listing with status badges |
| `/orders/[orderNumber]` | Customer | Detailed order status timeline and verified review submission |
| `/login`, `/register` | Public | Customer & Admin authentication screens |

### Admin Operations Routes

| Path | Access | Description |
|---|---|---|
| `/admin` | Admin | Operations dashboard with summary metrics |
| `/admin/products` | Admin | Product catalog management and soft-archive controls |
| `/admin/orders` | Admin | Order queue and fulfillment state transitions |
| `/admin/orders/[orderNumber]` | Admin | Order fulfillment inspection and detail view |
| `/admin/coupons` | Admin | Promotion code creation, usage limits, and archive controls |
| `/admin/reviews` | Admin | Post-publication review moderation (hide/restore with reason) |
| `/admin/customers` | Admin | Customer account status controls |

---

## Running the Application

### Docker Compose (Recommended)

From the repository root:

```bash
docker compose --profile core up -d --build storefront
```

Open `http://localhost:3000` in a browser.

### Local Development

Prerequisites: Node.js 22+ and npm.

```bash
cd apps/storefront
npm ci
npm run dev
```

### Environment Configuration

Configure build-time and runtime environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Target FastAPI backend URL |
| `NEXT_PUBLIC_CSRF_COOKIE_NAME` | `web_csrf` | CSRF cookie identifier |

---

## Verification and Build

Run TypeScript type checks and the production build:

```bash
npm --prefix apps/storefront run typecheck
npm --prefix apps/storefront run build
```
