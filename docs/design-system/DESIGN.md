# D&K Design System

This document specifies the visual identity, design tokens, typography, and component guidelines for the D&K E-Commerce Storefront and Admin Console.

## Direction

- **Product:** Women's fashion e-commerce storefront with an integrated store operations console.
- **Style:** Warm editorial minimalism; product-first, refined typography, structured white cards, and calm earthen palettes.
- **Principles:** High-contrast accessibility (WCAG AA), solid surfaces, clear visual hierarchy, mobile-first navigation, and restrained micro-interactions.

---

## Design Tokens

The design tokens are defined in [`apps/storefront/tailwind.config.ts`](../../apps/storefront/tailwind.config.ts) and map directly to Tailwind utility classes.

| Role | Token | Hex Value | Usage |
|---|---|---:|---|
| **Canvas** | `paper` | `#F7F4EE` | Overall page background |
| **Surface** | `surface` | `#FFFDF9` | Product cards, navigation bars, modals, dialogs |
| **Muted Surface** | `sand` | `#ECE6DA` | Secondary containers, filters, chip backgrounds |
| **Primary Text** | `ink` | `#152722` | Headings, titles, and body typography |
| **Secondary Text** | `muted` | `#5D6965` | Supporting metadata, timestamps, helper copy |
| **Brand Action** | `accent` | `#A94728` | Primary CTAs, active links, checkout buttons |
| **Brand Support** | `moss` | `#315B4F` | Navigation accents, category chips, positive badges |
| **Border** | `line` | `#DCD8CF` | Structural dividers, input borders, card outlines |
| **Danger** | `danger` | `#A63F3B` | Destructive actions, stock warnings, validation errors |
| **Warning** | `warning` | `#8B5B16` | Pending state badges, inventory low-stock alerts |
| **Success** | `success` | `#2F684F` | Completed order status, payment verified badges |

---

## Typography

- **UI & Body:** System sans-serif stack (`Inter`, `ui-sans-serif`, `system-ui`, `-apple-system`, `sans-serif`), 16px base, minimum 1.5 line height.
- **Editorial Display:** Serif stack (`Iowan Old Style`, `Palatino Linotype`, `Book Antiqua`, `Georgia`, `serif`).
- **Storefront Usage:** Serif headings are reserved for hero banners, collection headers, and editorial storytelling.
- **Admin Console Usage:** The Admin workspace exclusively uses sans-serif typography for maximum legibility and information density.
- **Size Bounds:** Supporting text must not be smaller than 12px.

---

## Elevation and Shadows

| Token | Shadow Value | Intended Surface |
|---|---|---|
| `shadow-soft` | `0 16px 45px rgba(21, 39, 34, 0.08)` | Product cards, floating search bar |
| `shadow-lift` | `0 24px 65px rgba(21, 39, 34, 0.13)` | Modal dialogs, drawer menus |
| `shadow-admin` | `0 10px 30px rgba(21, 39, 34, 0.07)` | Admin data tables, summary cards |

---

## Component Guidelines

### Storefront Components
- **Product Cards:** Solid `surface` background, 1px `line` border, image aspect-ratio 3:4, and clear price formatting in integer VND (`đ`).
- **Interactive Controls:** Minimum touch target height of 44px, visible labels, and inline error states.
- **Buttons:** Pill-shaped (`rounded-full`) for primary storefront customer actions (e.g. "Thêm vào giỏ", "Thanh toán").
- **Navigation:** Fixed compact bottom bar on mobile (<640px) and a clean top header on desktop.

### Admin Operations Components
- **Data Tables:** Dense layout, monospace IDs, horizontally scrollable with sticky headers, and clear status badges.
- **Admin Buttons:** Rounded rectangle (`rounded-lg`) to maximize space and maintain visual distinction from storefront consumer actions.
- **Audit Metadata:** Displays timestamp (UTC/Local), actor identity, and operation reason for archive or moderation actions.

---

## Responsive Layouts

- **Mobile (<640px):** Single-column product grids, full-width drawers for filters, sticky bottom action bar on product detail pages.
- **Tablet (640px–1024px):** 2-to-3 column grids, collapsible sidebar navigation.
- **Desktop (>=1024px):** 4-column product grids, persistent left sidebar in the Admin workspace, sticky order summary sidebars in Checkout.

---

## Rules to Avoid

1. Never use translucent or glassmorphism cards over the `paper` background.
2. Avoid hardcoding raw hex values in React components; use Tailwind semantic tokens (`bg-surface`, `text-ink`, `border-line`).
3. Never use icon-only buttons without an accessible `aria-label`.
4. Avoid relying exclusively on color to convey state (always pair color badges with explicit text).
