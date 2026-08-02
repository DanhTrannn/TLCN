# D&K Design System

## Direction

- Product: women's fashion ecommerce with a separate operational admin workspace.
- Style: warm editorial minimalism; product-first, calm, refined, not marketplace-dense.
- Principles: accessible contrast, solid surfaces, clear hierarchy, mobile-first interactions, restrained motion.

## Tokens

| Role | Token | Value | Usage |
|---|---|---:|---|
| Canvas | `paper` | `#F7F4EE` | Page background |
| Surface | `surface` | `#FFFDF9` | Cards, menus, dialogs |
| Muted surface | `sand` | `#ECE6DA` | Secondary groups |
| Primary text | `ink` | `#152722` | Headings and body |
| Secondary text | `muted` | `#5D6965` | Supporting copy; WCAG AA on paper |
| Brand action | `accent` | `#A94728` | Primary CTA, links, focus |
| Brand support | `moss` | `#315B4F` | Navigation, positive status |
| Border | `line` | `#DCD8CF` | Structural dividers |
| Danger | `danger` | `#A63F3B` | Destructive action and errors |
| Warning | `warning` | `#8B5B16` | Pending states |
| Success | `success` | `#2F684F` | Completed states |

## Typography

- UI and body: system sans stack, 16px base, minimum 1.5 line-height.
- Editorial display: `Iowan Old Style`, `Palatino Linotype`, `Book Antiqua`, Georgia.
- Use serif only for storefront display headings; admin remains sans-serif.
- Supporting text must not be smaller than 12px.

## Components

- Customer cards: white solid surface, 1px line border, soft shadow on elevated content.
- Admin cards: tighter radius and density; labels and actions remain explicit.
- Controls: minimum 44px height, visible label, inline error/help text.
- Buttons: pill shape for primary journeys; rounded rectangle for dense admin actions.
- Icons: outline SVG only; no emoji or text glyphs as functional icons.
- Focus: 2px accent ring with page-colored offset; never remove focus indication.

## Responsive

- Storefront uses a compact fixed bottom navigation below 640px and a horizontal header above it.
- Admin uses horizontal navigation on small screens and a left workspace sidebar on large screens.
- Tables remain horizontally scrollable with sticky headers where practical.
- No content depends on hover; hover only enhances an already visible affordance.

## Motion

- Interaction transitions: 150–250ms.
- Use opacity, transform and color only; avoid layout animation.
- Respect `prefers-reduced-motion` and disable nonessential transitions.

## Avoid

- Translucent cards over the paper background.
- Raw hex colors inside page components.
- Gray-on-gray helper text below AA contrast.
- Icon-only controls without accessible names.
- Controls below 44×44px or feedback communicated only by color.
