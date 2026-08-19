# E-Commerce Web Application Plan

This document outlines the architecture, domain design, and technical specifications of the source web application and API that generate operational data for the D&K E-Commerce Data Platform.

## 1. Application Goals

The source application serves as the system of record for e-commerce transactions and the origin of structured access logs. It provides a realistic, robust retail workflow for both consumer shopping and store management.

### 1.1. Core Capabilities
- **Customer:** Account registration, login, profile management, catalog browsing, faceted filtering, search, multi-item wishlist, and active shopping cart.
- **Checkout:** Atomic checkout flow with stock deduction, coupon validation, and simulated payment success.
- **Admin Operations:** Product catalog management, archive controls, inventory oversight, promotion lifecycle, customer accounts, and post-publication review moderation.
- **Data Engineering Integration:** Strict surrogate PKs, UTC `updated_at` timestamps for composite cursor extraction, and exclusion of authentication credentials from analytical access.

---

## 2. Architecture and Data Flow

The application follows a clean 3-tier architecture, strictly decoupled from the analytical data lakehouse components:

```text
Browser Client (Storefront & Admin)
         │ HTTP/JSON + CSRF
         ▼
Next.js 15 Storefront (Port 3000)
         │ HTTP/JSON
         ▼
FastAPI Backend (Port 8000)
        /                      \
Short Transactions         Structured Access Logs (stdout)
      /                          \
     ▼                            ▼
MySQL 8.4 (OLTP)              Fluent Bit
  (17 tables)             (15-min micro-batches)
     │                            │
     └─────────────┬──────────────┘
                   ▼
       MinIO S3 Landing Zone
```

### 2.1. Dependency Invariants
- The Storefront only communicates with the FastAPI Backend; it never accesses MySQL directly.
- The FastAPI Backend never interacts with Spark, Polaris, Trino, or Superset.
- The Data Lakehouse batch pipelines only read from MySQL with a dedicated read-only user and never write back to the OLTP database.

---

## 3. Domain Modules

### 3.1. Catalog and Search
- Categorized navigation with parent-child hierarchy.
- Bounded search (`LIKE` filters) and faceted filtering (category, size, color, price range, stock availability).
- Products and categories support soft-archive (`archived_at`, `archived_by_customer_id`, `archive_reason`). Archived products are terminal and hidden from storefront browsing while preserving historical order references.

### 3.2. Wishlist and Cart
- Customers maintain a multi-item wishlist with soft presence tracking (`is_present`, `first_added_at`, `last_added_at`, `removed_at`).
- Active shopping carts track item additions, updates, and logical removals. Adding items to a cart does not hold inventory.

### 3.3. Checkout and Orders
- Requires authentication and client-generated `Idempotency-Key` headers.
- Re-validates catalog pricing, coupon criteria, and inventory availability at checkout time.
- Valid checkouts atomically create a `paid` order, decrement inventory, insert payment (`succeeded`), and record order status history.
- Order State Machine:
  ```text
  paid ──(admin confirm)──▶ confirmed ──(admin complete)──▶ completed
  paid ──(cancel)─────────▶ cancelled (restores stock, full refund, releases coupon)
  ```

### 3.4. Product Reviews
- Customers can review items from `completed` orders only (verified purchase).
- **Immediate Publication:** Reviews default to `status = 'approved'` and display immediately.
- **Post-Publication Moderation:** Admins can moderate reviews (`approved` ↔ `rejected`) with a mandatory reason, hiding inappropriate content without introducing a blocking approval queue.

### 3.5. Promotions and Coupons
- Percentage or fixed-amount discount codes with minimum subtotal requirements, effective windows, and total/per-customer limits.
- Order snapshots capture coupon code, discount type, and discount amount at purchase.
- Expired campaigns can be archived without affecting past order redemption history.

---

## 4. Transaction Constraints

- **Atomicity:** All state mutations during checkout (order creation, order items, payment record, inventory decrement, coupon redemption) execute within a single transaction under `READ COMMITTED` isolation.
- **Idempotency:** Replay requests with the same idempotency key return the original result without duplicate charges or stock deductions.
- **Concurrency Control:** Inventory and coupon balances are locked with `SELECT ... FOR UPDATE` ordered by primary key to prevent deadlocks and overselling.
- **Monetary Precision:** All monetary amounts are stored as integer VND (no float rounding issues).

---

## 5. Structured Access Logging

Every completed HTTP request emits a standardized JSON log to stdout matching the [`ecommerce.access:1.0.0`](../contracts/ecommerce-access-v1.schema.json) contract:

- **Core Fields:** `request_id`, `timestamp`, `service`, `event.duration_ns`, `http.request_method`, `http.route`, `http.status_code`.
- **E-Commerce Context:** `actor.type`, `actor.key`, `ecommerce.action`, `ecommerce.product_key`, `ecommerce.search_query`.
- **Privacy Redaction:** Passwords, authorization tokens, session cookies, raw IP addresses, and customer PII are strictly excluded.
- **Rotation:** Fluent Bit buffers logs and flushes gzip-compressed micro-batches to MinIO every 15 minutes.

---

## 6. Synthetic Data Generation

The workspace includes a deterministic synthetic data generator (`generator` package):
- Generates 12 months of realistic transactions and 30 days of matching access logs based on Vietnamese retail behavior (campaign spikes, 0h sales, Tet seasonality, category weights).
- Guarantees 100% reproducibility and strict adherence to OLTP relational constraints.
