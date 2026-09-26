# B2C Product Browsing & Purchasing Experience Revamp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the customer-facing catalog (`/products`) and product detail page (`/products/[slug]`) into a modern, high-converting Editorial Fashion shopping experience with multi-select filters, quick view modal, 2-tier color/size swatches, quantity stepper, and mobile sticky buy bar.

**Architecture:** Client-side React 19 Next.js App Router components with Tailwind CSS tokens (`paper`, `ink`, `accent`, `moss`, `sand`). Reusable `QuickViewModal` interacting with Mini-Cart Drawer (`useCartDrawer`), centralized color swatch mapping, and stateful multi-select facet filters synced to URL search parameters.

**Tech Stack:** Next.js 15, React 19, Tailwind CSS, TypeScript, FastAPI backend API.

**Spec:** [`docs/superpowers/specs/2026-09-26-product-ui-ux-enhancements-design.md`](file:///home/danhtran/TLCN/docs/superpowers/specs/2026-09-26-product-ui-ux-enhancements-design.md)

## Global Constraints

- Preserve all existing routes, API contracts, and database constraints.
- Retain existing integration with `StoreAvailabilityBox`, `ProductReviews`, `SizeGuideModal`, and `useCartDrawer()`.
- Use the established Editorial Fashion design language (`#f7f4ee` Paper, `#152722` Ink, `#a94728` Accent, `#315b4f` Moss).
- Typecheck (`npm --prefix apps/storefront run typecheck`) and Next.js build (`npm --prefix apps/storefront run build`) must pass with 0 errors.
- All backend tests (`pytest services/ecommerce-api/tests`) must pass with 0 regressions.

---

### Task 1: UI Icons Extension & Centralized Color Swatch Utility

**Files:**
- Modify: `apps/storefront/src/components/ui/Icon.tsx:1-90`
- Create: `apps/storefront/src/lib/colors.ts`
- Test: `apps/storefront/src/components/ui/Icon.tsx` (typecheck)

**Interfaces:**
- Produces:
  - `IconName`: adds `"minus" | "filter" | "eye"`
  - `getColorHex(colorCode: string): string`
  - `getColorLabel(colorCode: string): string`

- [ ] **Step 1: Add new icons to `Icon.tsx`**
  Add `"minus"`, `"filter"`, `"eye"` to `IconName` and `paths` map in `apps/storefront/src/components/ui/Icon.tsx`.

- [ ] **Step 2: Create `apps/storefront/src/lib/colors.ts`**
  Implement `getColorHex` and `getColorLabel` mapping Vietnamese and English color codes to visual hex codes and friendly labels.

- [ ] **Step 3: Run typecheck**
  Run: `npm --prefix apps/storefront run typecheck`
  Expected: PASS

- [ ] **Step 4: Commit**
  ```bash
  git add apps/storefront/src/components/ui/Icon.tsx apps/storefront/src/lib/colors.ts
  git commit -m "feat(storefront): add minus, filter, eye icons and color swatch utility"
  ```

---

### Task 2: Reusable Quick View Modal Component

**Files:**
- Create: `apps/storefront/src/components/QuickViewModal.tsx`
- Test: `npm --prefix apps/storefront run typecheck`

**Interfaces:**
- Consumes:
  - `getProduct(slug: string)` from `@/lib/api`
  - `useCartDrawer()` from `@/lib/cart-context`
  - `getColorHex`, `getColorLabel` from `@/lib/colors`
  - `formatVnd` from `@/lib/api`
- Produces:
  - `QuickViewModal({ slug, isOpen, onClose }: QuickViewModalProps): JSX.Element | null`

- [ ] **Step 1: Implement `QuickViewModal.tsx`**
  Build a responsive modal displaying:
  - Async product detail loading with skeleton state.
  - Image preview, category eyebrow, title, and formatted price.
  - Color swatches & size pills selection with stock checking.
  - Direct "Thêm vào giỏ" button using `addItemAndOpen`.
  - Link to full product detail page (`/products/${slug}`).

- [ ] **Step 2: Run typecheck**
  Run: `npm --prefix apps/storefront run typecheck`
  Expected: PASS

- [ ] **Step 3: Commit**
  ```bash
  git add apps/storefront/src/components/QuickViewModal.tsx
  git commit -m "feat(storefront): implement interactive QuickViewModal with cart drawer integration"
  ```

---

### Task 3: Catalog Listing Page Revamp (`/products/page.tsx`)

**Files:**
- Modify: `apps/storefront/src/app/products/page.tsx`
- Test: `npm --prefix apps/storefront run typecheck`

**Interfaces:**
- Consumes:
  - `getProducts`, `getCategories`, `getCatalogFacets`, `getWishlist`, `addWishlistProduct`, `removeWishlistProduct` from `@/lib/api`
  - `QuickViewModal` from `@/components/QuickViewModal`
  - `getColorHex`, `getColorLabel` from `@/lib/colors`
- Produces:
  - Interactive multi-select filter sidebar (sizes, colors, categories, price range, in-stock).
  - Active filter tags bar with single-click dismissal.
  - Enhanced product cards with hover Quick View button, color dots, and wishlist button.

- [ ] **Step 1: Update `AppliedFilters` and URL search parameters mapping**
  Support arrays `sizes: string[]` and `colors: string[]` in `filtersFromSearchParams` and `filtersToSearchParams`.

- [ ] **Step 2: Revamp Filter Sidebar & Active Filter Chips Bar**
  Implement multi-select pill checkboxes for sizes, circular color swatch buttons for colors, category buttons, and active filter dismissible chips.

- [ ] **Step 3: Enhance Product Card & integrate `QuickViewModal`**
  Add hover "Xem nhanh" button, available color dots, rating stars, and wire up `QuickViewModal` state.

- [ ] **Step 4: Run typecheck and Next.js build**
  Run: `npm --prefix apps/storefront run typecheck && npm --prefix apps/storefront run build`
  Expected: PASS

- [ ] **Step 5: Commit**
  ```bash
  git add apps/storefront/src/app/products/page.tsx
  git commit -m "feat(storefront): revamp product catalog with multi-select filters and quick view"
  ```

---

### Task 4: Product Detail Page Revamp (`/products/[slug]/page.tsx`)

**Files:**
- Modify: `apps/storefront/src/app/products/[slug]/page.tsx`
- Test: `npm --prefix apps/storefront run typecheck`

**Interfaces:**
- Consumes:
  - `getProduct` from `@/lib/api`
  - `useCartDrawer` from `@/lib/cart-context`
  - `getColorHex`, `getColorLabel` from `@/lib/colors`
  - `StoreAvailabilityBox`, `ProductReviews`, `SizeGuideModal`
- Produces:
  - 2-Tier variant selection: Color Swatches -> Size Pills (with stock-aware disabled states).
  - Quantity Stepper `[-] [quantity] [+]` bounded by stock.
  - Mobile Sticky Buy Bar fixed at bottom of viewport.
  - Structured Product Information Accordion.

- [ ] **Step 1: Refactor variant selection into 2-tier Color & Size controls**
  Extract distinct colors, render visual swatches with active rings, and map sizes for the active color with in-stock indicators.

- [ ] **Step 2: Add Quantity Stepper**
  Add state `quantity: number` (default 1) with increment/decrement buttons clamped to `[1, variant.stock_quantity]`.

- [ ] **Step 3: Implement Mobile Sticky Buy Bar**
  Add sticky bar rendered at bottom of screen on mobile viewports (`sm:hidden fixed bottom-0 left-0 right-0 z-40`) showing thumbnail, title, price, and "Thêm giỏ" button.

- [ ] **Step 4: Add Product Information Accordion**
  Organize description, materials & care, and shipping/returns policy into accordion sections.

- [ ] **Step 5: Run typecheck and Next.js build**
  Run: `npm --prefix apps/storefront run typecheck && npm --prefix apps/storefront run build`
  Expected: PASS

- [ ] **Step 6: Commit**
  ```bash
  git add apps/storefront/src/app/products/[slug]/page.tsx
  git commit -m "feat(storefront): revamp product detail page with 2-tier swatches, quantity stepper and sticky bar"
  ```

---

### Task 5: End-to-End Verification & Health Checks

**Files:**
- Full repository verification.

- [ ] **Step 1: Run Storefront Typecheck and Next.js Production Build**
  Run: `npm --prefix apps/storefront run typecheck && npm --prefix apps/storefront run build`
  Expected: 0 errors, all 27+ routes static/dynamically generated.

- [ ] **Step 2: Run Full Backend Pytest Suite**
  Run: `API_TRINO_URL="http://non-existent-trino:9999" uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests`
  Run: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests`
  Expected: 195/195 tests pass.

- [ ] **Step 3: Verify Docker Containers**
  Run: `docker compose ps`
  Expected: All containers Up and healthy.
