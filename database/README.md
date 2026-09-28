# Database Migrations and Seed Data

This directory contains the database schema definitions, Alembic migrations (revisions `0001` through `0017`), and deterministic seed assets for MySQL 8.4 OLTP (27 tables).

## Directory Structure

| Directory | Content | Responsibility |
|---|---|---|
| `migrations/` | Alembic migration scripts | Version-controlled schema migrations for all 27 OLTP tables (`0001` - `0017`) |
| `seeds/` | Python catalog and scenario seed scripts | Master catalog seed data and multi-role demo scenarios |

---

## Migration History

| Revision | File | Summary |
|---|---|---|
| `0001` | `0001_initial_schema.py` | Initial OLTP schema (customers, credentials, catalog, inventory, carts, orders, payments, status history) |
| `0002` | `0002_admin_console.py` | Admin customer role and admin order transition source |
| `0003` | `0003_wishlist.py` | Customer wishlist items with soft presence tracking |
| `0004` | `0004_simplify_checkout_payment.py` | Simplification of checkout payment fields |
| `0005` | `0005_order_lifecycle_promotions_reviews.py` | Order lifecycle milestones, coupons, refunds, and verified product reviews |
| `0006` | `0006_rebrand_product_master.py` | Rebrand product master data to D&K |
| `0007` | `0007_standardize_product_image.py` | Standardize product image URLs |
| `0008` | `0008_archive_catalog_promotions.py` | Terminal archive metadata and audit constraints for products and coupons |
| `0009` | `0009_reviews_publish_immediately.py` | Immediate product review publication and post-moderation checks |
| `0010` | `0010_multi_city_stores_inventory.py` | Multi-city stores and store-level inventory (`cities`, `stores`, `store_inventory`) |
| `0011` | `0011_pos_order_channel.py` | POS order channel and physical store linkage (`channel`, `store_id`, `staff_id`) |
| `0012` | `0012_pos_search_index.py` | Fulltext & composite index optimizations for POS barcode and SKU search |
| `0013` | `0013_make_cart_id_nullable.py` | Make `cart_id` nullable on `orders` for POS counter orders |
| `0014` | `0014_logistics_returns_inbound_cogs.py` | Logistics and returns (`delivery_staff`, `shipments`, `return_requests`, `return_items`, `inventory_transactions`), boom COD handling, and variant `cost_price_vnd` |
| `0015` | `0015_inbound_production_and_refund_updated_at.py` | Workshop inbound production batches (`inbound_receipts`, `inbound_receipt_items`), MWA costing, and `refunds.updated_at` |
| `0016` | `0016_update_order_status_history_transition_sources.py` | Update `order_status_history.transition_source` check constraint (`customer`, `admin`, `system`, `pos`, `delivery`) |
| `0017` | `0017_allow_pending_payment_status.py` | Allow `pending` payment status for COD orders in `ck_payments_status` and failure code check constraint |

---

## Migration Workflows

### Apply Pending Migrations

```bash
uv run --package ecommerce-api alembic -c database/alembic.ini upgrade head
```

### Create a New Migration

```bash
uv run --package ecommerce-api alembic -c database/alembic.ini revision --autogenerate -m "describe_change"
```

---

## Seed Data

### 1. Master Catalog Seed
Populate the foundational product catalog without synthetic customer transactions:

```bash
uv run --package ecommerce-api python database/seeds/seed_catalog.py
```

### 2. Multi-Role Demo Scenarios Seed
Populate realistic demo records across all 7 business domains (staff accounts, inbound batches with MWA costing, delivered online & POS orders with snapshotted COGS, boom deliveries, returns/refunds, coupons, reviews):

```bash
uv run --package ecommerce-api python database/seeds/seed_demo_scenarios.py
```

---

## Analytical Extraction Boundary

The Lakehouse batch pipeline extracts from **26 allowed analytical tables** (out of 27 tables in MySQL). The table `customer_credentials` is strictly excluded from Data Engineering extraction to protect authentication credentials.

For full schema details, relational constraints, and transaction boundaries, refer to [`../docs/architecture/OLTP_SCHEMA.md`](../docs/architecture/OLTP_SCHEMA.md).
