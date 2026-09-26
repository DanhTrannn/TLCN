# Technical Design Specification: B2C Product Browsing & Purchasing Experience Revamp

- **Date:** 2026-09-26
- **Status:** Approved
- **Target Branch:** `dev`
- **Scope:** Complete UI/UX redesign and interactive upgrade for Customer Storefront Product Catalog (`/products`) and Product Detail Page (`/products/[slug]`).

---

## 1. Executive Summary & Goals

### 1.1 Problem Statement
The current D&K Fashion customer-facing product experience has significant friction points that reduce conversion rates (CRO) and fail to meet modern e-commerce fashion standards (e.g. Zara, Uniqlo, Mango, Coolmate):
1. **Catalog Browsing (`/products`)**:
   - Filter controls are rigid: Single-select dropdowns for Size and Color prevent filtering for multiple sizes (e.g. S and M) or multiple color shades simultaneously, even though the backend API already supports multi-value arrays.
   - Traditional form submission button ("Áp dụng bộ lọc") interrupts the browsing flow.
   - Product cards lack color swatch indicators, badges, rating summaries, and a Quick View modal, forcing customers to navigate back and forth to inspect variants.
2. **Product Detail Page (`/products/[slug]`)**:
   - Variant selection combines sizes and colors into a single cluttered button grid (`M · black`, `L · navy`, `XL · white`), making it confusing to compare availability and pricing across options.
   - There is no quantity selector stepper (`[-] 1 [+]`) before adding to cart.
   - On mobile devices, the "Thêm vào giỏ" button scrolls out of viewport when viewing product descriptions or reviews (missing Sticky Buy Bar).
   - Product information, care instructions, and shipping policies lack clear structured hierarchy (accordion).

### 1.2 Key Objectives
1. **Catalog (`/products`)**:
   - Interactive multi-select filter sidebar with pill/checkbox chips for Sizes and Colors.
   - Active Filter Chips bar at the top with single-click removal and "Xóa tất cả" reset.
   - Product card enhancements: Color dots previewing available shades, badges ("Sẵn hàng" / "Tạm hết hàng"), hover elevation, and a "Xem nhanh" (Quick View) action button.
   - Reusable `QuickViewModal` allowing customers to inspect photos, pick color/size, and add directly to the mini-cart drawer without navigating away.
2. **Product Detail Page (`/products/[slug]`)**:
   - Two-tier variant selection:
     - **Tier 1: Color Swatches**: Circular color circles with active rings and selected color name label.
     - **Tier 2: Size Pills**: Size pills (S, M, L, XL, 30, 32...) that dynamically reflect stock availability for the currently selected color, with out-of-stock sizes visually disabled/struck-through.
   - Quantity Stepper (`[-] [1] [+]`) bounded between 1 and `variant.stock_quantity`.
   - Mobile Sticky Buy Bar fixed at the bottom on smaller viewports when scrolling past the main buy panel.
   - Structured Product Information Accordion (Product Details & Fit, Materials & Care Guide, Shipping & 30-day Return Policy).
   - Retain full compatibility with existing `StoreAvailabilityBox`, `ProductReviews`, and `SizeGuideModal`.
3. **Icons & Design System**:
   - Add missing UI icons (`minus`, `filter`, `eye`) to `Icon.tsx`.
   - Maintain the Editorial Fashion Minimalist design language (`#f7f4ee` Paper, `#152722` Ink, `#a94728` Terracotta Accent, `#315b4f` Moss).

---

## 2. Architecture & Component Structure

```
apps/storefront/src/
├── components/
│   ├── ui/
│   │   └── Icon.tsx                 (Extended with minus, filter, eye)
│   ├── QuickViewModal.tsx           (New: Modal for quick inspect & add-to-cart)
│   ├── ProductCard.tsx              (Enhanced or inline modular card in Catalog)
│   ├── StoreAvailabilityBox.tsx     (Retained)
│   ├── ProductReviews.tsx           (Retained)
│   └── SizeGuideModal.tsx           (Retained)
├── app/
│   ├── products/
│   │   └── page.tsx                 (Revamped Catalog with interactive multi-select filters)
│   └── products/[slug]/
│       └── page.tsx                 (Revamped PDP with 2-tier swatches, stepper & sticky bar)
```

---

## 3. Detailed Specifications

### 3.1 Icon Extensions (`Icon.tsx`)
- Add `"minus"`: `<path d="M5 12h14" />`
- Add `"filter"`: `<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />`
- Add `"eye"`: `<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" /><circle cx="12" cy="12" r="3" />`

### 3.2 Color Mapping & Utility
Create a centralized color mapper utility `getColorHex(colorCode: string): string` mapping canonical color names to visual hex codes for swatches:
- `black` -> `#111827`
- `white` -> `#ffffff` (with subtle border `#e5e7eb`)
- `navy` -> `#1e3a8a`
- `blue` -> `#3b82f6`
- `beige` -> `#d4b996`
- `gray` -> `#6b7280`
- `brown` -> `#78350f`
- `red` -> `#dc2626`
- `green` -> `#15803d`
- fallback -> `#9ca3af`

### 3.3 Catalog Listing Page (`/products/page.tsx`)
1. **Interactive Multi-Select Filters**:
   - Sizes: Checkbox chips (e.g. `[ ] S`, `[x] M`, `[x] L`). Clicking toggles the size in the query params.
   - Colors: Circular color swatches with active checkmark or border ring.
   - Category: Pill buttons or clean list.
   - Price range: Minimum & maximum number inputs with debounce or clear presets.
   - "Chỉ sản phẩm còn hàng": Toggle switch.
   - Sort: Dropdown (`newest`, `price_asc`, `price_desc`).
2. **Active Filter Bar**:
   - Shows active filters as dismissible tags (e.g. `Màu: Đen ×`, `Size: M ×`).
   - "Xóa tất cả" button to reset in one click.
3. **Product Card**:
   - 4:5 aspect ratio image with smooth hover zoom (`scale-[1.03]`).
   - Quick View button overlay ("Xem nhanh" with eye icon).
   - Wishlist heart button.
   - Color dots showing available color variants.
   - Price formatted with `formatVnd`.
   - In-stock badge ("Sẵn hàng" / "Tạm hết hàng").
4. **Quick View Modal (`QuickViewModal.tsx`)**:
   - Receives `productSlug: string | null`, `isOpen: boolean`, `onClose: () => void`.
   - Fetches product detail asynchronously with `getProduct(slug)`.
   - Allows picking Color and Size.
   - Direct "Thêm vào giỏ hàng" calling `addItemAndOpen(variantId, 1)` from `useCartDrawer()`.
   - Link to full product detail page ("Xem chi tiết đầy đủ →").

### 3.4 Product Detail Page (`/products/[slug]/page.tsx`)
1. **2-Tier Variant Selection**:
   - Extract unique colors: `Array.from(new Set(product.variants.map(v => v.color_code)))`.
   - When a color is selected, filter available sizes:
     - Sizes with `in_stock: true` for that color are clickable.
     - Sizes with `in_stock: false` or not existing for that color are disabled with a visual slash/grayed out.
   - Selected variant resolves to `product.variants.find(v => v.color_code === selectedColor && v.size_code === selectedSize)`.
   - Fallback if only 1 variant exists (auto-select).
2. **Quantity Stepper**:
   - `[-] [ quantity ] [+]`
   - Decrement disabled when `quantity <= 1`.
   - Increment disabled when `quantity >= (variant?.stock_quantity ?? 1)`.
   - Passes selected quantity to `addItemAndOpen(variant.public_id, quantity)`.
3. **Mobile Sticky Buy Bar**:
   - Uses intersection observer or scroll listener on the primary buy button.
   - Appears fixed at viewport bottom on mobile (`sm:hidden fixed bottom-0 left-0 right-0 z-40 bg-surface/95 backdrop-blur border-t border-line p-3 shadow-lg`).
   - Displays small thumbnail, product name, price, and compact "Thêm giỏ" button.
4. **Product Information Accordion**:
   - Tab 1: **Mô tả & Phom dáng**: Full description, silhouette, fit notes.
   - Tab 2: **Chất liệu & Bảo quản**: Fabric composition, washing/ironing guidelines.
   - Tab 3: **Chính sách & Cam kết**: Freeship over 500.000đ, 30-day returns, store pickup.

---

## 4. Verification & Testing Plan

1. **Static Analysis & Compilation**:
   - `npm --prefix apps/storefront run typecheck` (0 errors).
   - `npm --prefix apps/storefront run build` (all Next.js routes compile).
2. **Functionality Verification**:
   - Catalog filtering with multiple sizes and colors.
   - Active filter tags removal and "Đặt lại" reset.
   - Quick View Modal opening, picking variant, and adding to cart drawer.
   - PDP 2-tier variant selection: selecting Color updates Size availability.
   - Quantity stepper increment/decrement within stock bounds.
   - Mobile responsive layout and Sticky Buy Bar on narrow screens.
3. **Zero Regression**:
   - Full backend test suite passes: `uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests`.
