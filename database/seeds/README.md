# Database Seed Assets

This directory contains deterministic seed scripts for master catalog initialization and multi-role demo scenarios.

## Scope and Boundary

- `seed_catalog.py`: Populates foundational master data:
  - 8 core fashion categories (`ao-nu`, `quan-nu`, `dam-nu`, `vay-nu`, `ao-khoac-nu`, `set-do-nu`, `phu-kien`, `do-mac-nha`).
  - Baseline product catalog, size/color variants, and initial `opening_on_hand` / `on_hand` inventory balances.
  - Default promotional welcome coupon (`WELCOME10`).
- `seed_demo_scenarios.py`: Populates realistic time-series business scenarios for live demonstrations and testing:
  - Demo staff accounts across all 7 business roles (`admin`, `sales_manager`, `store_manager`, `inventory_manager`, `operations_manager`, `marketing_manager`, `system_admin`).
  - Inbound production batches (`inbound_receipts`, `inbound_receipt_items`) with Moving Weighted Average inventory costing recalculation.
  - 27+ historical orders across online and POS channels over 14 days with snapshotted COGS (`order_items.cost_price_vnd`).
  - Boom COD orders (`failed_delivery`) with inventory ledger rollback (`return_boom`) and customer boom count increment.
  - 7-day customer returns with inspection verification and refund disbursement (`refunds`).
  - Active coupons, redemptions, and product reviews.
- **Large-Scale Historical Backfill:** For multi-month load tests and ML dataset generation, use the `generator/` package.
