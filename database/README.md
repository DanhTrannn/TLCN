# Database Migrations and Seed Data

This directory contains the database schema definitions, Alembic migrations (revisions 0001 through 0009), and deterministic seed assets for MySQL 8.4 OLTP.

## Directory Structure

| Directory | Content | Responsibility |
|---|---|---|
| `migrations/` | Alembic migration scripts | Version-controlled schema migrations for all 17 OLTP tables |
| `seeds/` | Python catalog seed scripts | Master catalog seed data (categories, products, variants, initial inventory) |

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

## Catalog Seed Data

Populate the initial product catalog without synthetic customer transactions:

```bash
uv run --package ecommerce-api python database/seeds/seed_catalog.py
```

---

## Analytical Extraction Boundary

The Lakehouse batch pipeline extracts from **16 allowed analytical tables**. The table `customer_credentials` is strictly excluded from Data Engineering extraction to protect authentication credentials.

For full schema details, relational constraints, and transaction boundaries, refer to [`../docs/architecture/OLTP_SCHEMA.md`](../docs/architecture/OLTP_SCHEMA.md).
