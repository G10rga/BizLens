---
name: Caucasian Alpine Clarity
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#414844'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#717973'
  outline-variant: '#c1c8c2'
  surface-tint: '#3f6653'
  primary: '#012d1d'
  on-primary: '#ffffff'
  primary-container: '#1b4332'
  on-primary-container: '#86af99'
  inverse-primary: '#a5d0b9'
  secondary: '#006c49'
  on-secondary: '#ffffff'
  secondary-container: '#6cf8bb'
  on-secondary-container: '#00714d'
  tertiary: '#382100'
  on-tertiary: '#ffffff'
  tertiary-container: '#563400'
  on-tertiary-container: '#e79400'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#c1ecd4'
  primary-fixed-dim: '#a5d0b9'
  on-primary-fixed: '#002114'
  on-primary-fixed-variant: '#274e3d'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  display-lg:
    fontFamily: Noto Sans
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Noto Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Noto Sans
    fontSize: 26px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Noto Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Noto Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Noto Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Noto Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Noto Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-lg:
    fontFamily: Noto Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Noto Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Noto Sans
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.03em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-md: 1.5rem
  gutter-lg: 2rem
  margin: 1rem
  margin-md: 2rem
  margin-lg: 3rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system is engineered for Georgian small-business owners—corner bakeries, neighborhood pharmacies, busy cafes, and independent salons—who need crystal-clear foresight into their daily cash flow without accounting jargon. 

The personality balances grounded financial authority with welcoming, tactile clarity:
- **Atmosphere:** Calm, dependable, organized, and unhurried. It dissolves the daily anxiety of payroll, supplier invoices, and inventory runs.
- **Design Movement:** Modern Tactile Utility with soft elevations. It blends the crisp readability of contemporary fintech with physical, touchable affordances suited for counter-top tablets, busy POS lanes, and quick checks on a mobile phone during a market run.
- **Emotional Intent:** Reassurance and proactive confidence. Positive metrics feel earned and refreshing; warnings feel like timely, supportive nudges rather than alarms.

## Colors

The palette draws directly from deep Caucasian mountain pine and luminous herbal greens, grounded by warm architectural neutrals:

- **Primary (`#1B4332` / Deep Pine Slate):** Used for structural navigation, primary action buttons, key analytical chart markers, and foundational brand moments. Anchors the interface with dependable stability. A darker tonal variant (`#0F2922`) serves for high-contrast app headers and POS register bars.
- **Secondary (`#10B981` / Mint Emerald):** Signals cash surplus, completed transactions, growth trends, and positive future runway. An accessible companion shade (`#059669`) provides high-contrast text on bright backgrounds.
- **Tertiary (`#F59E0B` / Amber Gold):** Pinpoints cash dips, overdue supplier invoices, and pending inventory reconciliations before they turn critical.
- **Semantic Danger (`#EF4444` / Crimson Rose):** Reserved strictly for negative balances, cash dry-up alerts, and voided sales.
- **Surfaces & Canvas:** The base backdrop uses warm porcelain hues (`#F8FAFC` descending into `#F1F5F9`), preserving optic rest during extended daylight cashiering. Foreground cards are pure, unyielding white (`#FFFFFF`) with deep charcoal ink (`#0F172A`) for effortless legibility.

## Typography

Typography is anchored entirely by **Noto Sans** to ensure native, fluid parity between the Georgian script (Mkhedruli / მხედრული) and Latin typography without glyph mismatches or uneven vertical metric shifts.

- **Numerics & Currency:** All currency figures, point-of-sale breakdowns, and balance projections enforce tabular figures (`font-variant-numeric: tabular-nums`). The Georgian Lari symbol (`₾`) must share the font size and baseline of its accompanying value, padded with a non-breaking space (e.g., `1,250.00 ₾`).
- **Mkhedruli Flow:** Because Mkhedruli characters feature unique loops and descenders without distinct capitalized forms, headline weights lean into 600 (SemiBold) and 700 (Bold) to cleanly separate structural titles from running descriptive text.
- **Hierarchy:** High-volume cash figures use `display-lg` on desktop telemetry and scale down gracefully to `headline-lg-mobile` on single-column phone views to prevent line wrapping of large financial amounts.

## Layout & Spacing

The layout philosophy follows a responsive fluid grid with strict ergonomics for both fast thumb-driven phone navigation and split-screen register POS setups:

- **Mobile Viewports (<640px):** Single-column layout with `1rem` outer canvas margin (`margin`). Action targets maintain a minimum 48px vertical footprint for accurate one-handed tapping during live sales.
- **Tablet / Counter POS (640px - 1024px):** 8-column layout with `gutter-md` (1.5rem). Divides into an asymmetrical 5:3 split: left zone for dynamic catalog/forecasting streams; right sticky panel for current cart order, register calculations, or cash-reconciliation details.
- **Desktop Dashboard (>1024px):** 12-column layout with `margin-lg` (3rem) maximum padding and `gutter-lg` (2rem) column gaps. The sidebar navigation anchors to a fixed 260px left rail while cards stretch symmetrically across visual columns.
- **Rhythm:** Spacing follows strict multiples of 4px and 8px. Card interior paddings lock to `space-md` (1rem) for mobile cards and step up to `space-lg` (1.5rem) on desktop analytics panels.

## Elevation & Depth

Visual hierarchy is constructed through **tonal layering paired with diffused botanical-tinted ambient shadows**, avoiding harsh gray borders:

- **Base Layer (Level 0):** The app canvas rests on `#F8FAFC`. It is flat, quiet, and matte.
- **Card Surfaces (Level 1):** Foreground cards and modules are pure `#FFFFFF`, separated from the floor by a hairline outline (`1px solid #E2E8F0`) and an ambient shadow tinted with deep pine: `0 2px 8px -2px rgba(15, 41, 34, 0.05), 0 1px 3px 0 rgba(15, 41, 34, 0.03)`.
- **Interactive Elevated Panels (Level 2):** POS cart receipts, date-range forecast selectors, and floating category pills hover with a higher lift: `0 10px 25px -5px rgba(15, 41, 34, 0.08), 0 4px 6px -2px rgba(15, 41, 34, 0.03)`.
- **Modals & Flyouts (Level 3):** Cash drawer settlement sheets and critical forecasting runout warnings use `0 20px 30px -10px rgba(15, 23, 42, 0.16)` backed by a warm porcelain semi-opaque backdrop blur (`rgba(15, 23, 42, 0.4)` with `backdrop-filter: blur(4px)`).

## Shapes

The design system implements a **Rounded (Level 2)** shape standard:

- **Base Radius (0.5rem / 8px):** Applied to buttons, inputs, segmented controls, item catalog tiles, and table rows. Conveys accessibility and modern durability without feeling juvenile.
- **Large Radius (`rounded-lg`, 1rem / 16px):** Applied to primary metric containers, cash-flow summary cards, and quick-action POS grids.
- **Extra Large Radius (`rounded-xl`, 1.5rem / 24px):** Reserved for slide-over modals, bottom navigation drawers on mobile devices, and system alert banners.
- **Pill Utility:** Status tags, currency badges, and quick-filter category chips make isolated use of full-radius pills (`rounded-full`) to contrast against rectangular data cards.

## Components

### Buttons
- **Primary:** Background `#1B4332`, text `#FFFFFF`, radius 8px, padding `0.75rem 1.25rem`. On hover/tap, smoothly shifts to `#0F2922`. Subtle downward transform (`scale(0.98)`) provides tactile feedback on touchscreens.
- **Secondary / Action:** White background with a `1.5px` border in `#1B4332`, text `#1B4332`. Ideal for "Print Receipt" or "Export Daily Summary".
- **Positive Accent (POS Complete):** Background `#10B981`, text `#FFFFFF`. Used selectively for final payment processing and sale completion.

### Cash Flow Health Chips & Badges
- **Positive / Inflow:** Background `#ECFDF5`, text `#059669`, border `1px solid #A7F3D0`. Displays leading directional icons (`↑` or `+`) alongside currency figures.
- **Pending / Warning:** Background `#FFFBEB`, text `#B45309`, border `1px solid #FDE68A`.
- **Negative / Outflow:** Background `#FEF2F2`, text `#DC2626`, border `1px solid #FECACA`.

### Input Fields & Numeric Keypads
- Text and number inputs feature `#FFFFFF` backgrounds, `1px` border in `#CBD5E1`, and deep charcoal text (`#0F172A`). Focus state illuminates a `2px` ring in `#10B981` without offset.
- Currency fields lock a bold Georgian Lari sign (`₾`) inside an inset left adornment box with a soft porcelain background (`#F1F5F9`).
- Mobile/Tablet POS custom numpad keys use 8px rounded `#FFFFFF` tiles with high tactile contrast and generous 56px touch heights.

### Metric & Forecasting Cards
- Structured with an interior padding of `space-md` (mobile) or `space-lg` (desktop).
- Header row contains the label in `label-md` uppercase muted slate (`#64748B`), paired with an optional time-window selector.
- Center displays the primary cash balance or projected balance in `headline-lg` (`tabular-nums`), followed by an inline indicator showing percentage change relative to the preceding week.

### POS Quick-Tap Item Tiles
- Designed for bakery and cafe item selections: 1:1 or 4:3 aspect ratio cards with 8px radius, white background, `1px solid #E2E8F0`, displaying the product name in `label-lg` and price prominently in `label-md` green (`#059669`). Active touch produces an instant `#ECFDF5` background highlight.

### Lists & Transaction Rows
- Compact tabular rows alternating with hairline divider borders (`#F1F5F9`). 
- Left-aligned timestamp, customer, or supplier title; right-aligned monetary values with strict decimal alignment using tabular numbers. Outflows render with a subtle minus sign (`-`), while POS cash takings render in bold `#059669`.