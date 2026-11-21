---
name: Executive Emerald Pulse
colors:
  surface: '#10131a'
  surface-dim: '#10131a'
  surface-bright: '#363940'
  surface-container-lowest: '#0b0e14'
  surface-container-low: '#191c22'
  surface-container: '#1d2026'
  surface-container-high: '#272a31'
  surface-container-highest: '#32353c'
  on-surface: '#e1e2eb'
  on-surface-variant: '#bacac1'
  inverse-surface: '#e1e2eb'
  inverse-on-surface: '#2e3037'
  outline: '#85948c'
  outline-variant: '#3c4a43'
  surface-tint: '#2fe0aa'
  primary: '#44edb7'
  on-primary: '#003828'
  primary-container: '#00d09c'
  on-primary-container: '#00533c'
  inverse-primary: '#006c4f'
  secondary: '#45fec9'
  on-secondary: '#003829'
  secondary-container: '#00e1ae'
  on-secondary-container: '#005e47'
  tertiary: '#3ee7ff'
  on-tertiary: '#00363d'
  tertiary-container: '#00cae1'
  on-tertiary-container: '#00505a'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#59fdc5'
  primary-fixed-dim: '#2fe0aa'
  on-primary-fixed: '#002116'
  on-primary-fixed-variant: '#00513b'
  secondary-fixed: '#45fec9'
  secondary-fixed-dim: '#00e1ae'
  on-secondary-fixed: '#002117'
  on-secondary-fixed-variant: '#00513d'
  tertiary-fixed: '#9cf0ff'
  tertiary-fixed-dim: '#00daf3'
  on-tertiary-fixed: '#001f24'
  on-tertiary-fixed-variant: '#004f58'
  background: '#10131a'
  on-background: '#e1e2eb'
  surface-variant: '#32353c'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.03em
  display-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  metric-num-xl:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  metric-num-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-tablet: 1.5rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-2xl: 3rem
---

## Brand & Style
This design system governs an executive-grade wealth management and financial intelligence dashboard. Engineered for high-stakes decision-makers, portfolio managers, and modern investors, the interface balances ultra-dense financial data with pristine visual ergonomics.

The visual style is **Futuristic High-Contrast Dark-Mode Glassmorphism**:
- **Atmospheric Depth:** Deep slate and obsidian backgrounds establish a cinematic, low-fatigue workspace optimized for long trading sessions and late-night executive analysis.
- **Luminescent Accentuation:** Signature emerald, mint, and cyan accents cut through the obsidian backdrop, channeling energy directly toward performance deltas, real-time yield curves, and telemetry cues.
- **Precision Engineering:** Crisp structural lines, semi-translucent glass panels, and tabular numeric typography create an unmistakable atmosphere of institutional fidelity and algorithmic power.

## Colors
The palette is built around an emissive dark-canvas hierarchy paired with radiant performance indicators.

### Canvas & Surface Architecture
- **Obsidian Base (`#0B0E14`):** Canvas grounding layer, providing zero-distraction depth.
- **Deep Surface (`#121721`):** Structural panels, side navigation rails, and analytical docks.
- **Card Surface (`#18202F`):** Foreground cards, metric widgets, and floating modal interfaces.
- **Subtle Perimeter Border (`rgba(255, 255, 255, 0.08)`): Delimits bounding boxes with laser-etched precision without introducing visual noise.

### Dynamic Brand & Accent Colors
- **Emerald Green (`#00D09C`):** Primary brand anchor, dominant positive states, core call-to-actions, and growth trajectories.
- **Electric Mint (`#1DE9B6`):** Secondary accent for active tabs, secondary visual indicators, and hover glows.
- **Neon Cyan (`#00E5FF`):** Tertiary catalyst for predictive models, machine-learning signals, and interactive telemetry overlays.

### Executive Status Tiers
- **Critical / Friction (`#FF5252` Coral Crimson):** Downward performance, margin risk thresholds, drawdowns, and critical system alerts.
- **Warning / Notice (`#FFB74D` Amber):** Volatility alerts, pending order execution, and threshold saturation warnings.
- **Positive / Yield (`#00D09C` Emerald):** Upward momentum, portfolio gain, and validated transactions.
- **Live / Operational (`#00E676` Vivid Spring):** Real-time broker connectivity, streaming socket health, and market open states.

## Typography
The typographical hierarchy merges the humanistic, assertive architecture of **Plus Jakarta Sans** for titles with the industrial, micro-legible clarity of **Inter** for dense transactional tables, data rows, and analytical metrics.

### Quantitative Formatting
All numeric data presentation must enforce OpenType tabular figures (`font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1, "cv05" 1;`). This eliminates horizontal jitter during real-time tick streaming and ensures rigorous columnar alignment across balance sheets, order books, and P&L charts.

### Hierarchy & Legibility Rules
- **Display & Headline Levels:** Leverage Plus Jakarta Sans with negative letter tracking to produce a confident, authoritative executive presence.
- **Labels & Micro-data:** Small labels (`label-sm`, `label-md`) utilize Inter SemiBold with positive letter spacing to maintain visual distinction when set in uppercase above dense numerical readouts.
- **Text Contrast:** Primary headlines use pure `#FFFFFF` (100%), regular body text uses `rgba(255, 255, 255, 0.72)`, and tertiary captions utilize `rgba(255, 255, 255, 0.45)`.

## Layout & Spacing
The layout follows a responsive 12-column fluid grid system engineered to support multi-pane market watchlists, candlestick canvases, and executive KPI summaries simultaneously.

### Grid Anatomy
- **Desktop (≥ 1280px):** 12-column grid, `gutter-desktop` (1.5rem / 24px), `margin-desktop` (2rem / 32px). Maximum container width clamps at 1720px for ultrawide consistency.
- **Tablet (768px – 1279px):** 8-column layout, `gutter` (1rem / 16px), `margin-tablet` (1.5rem / 24px). Analytical sidebars collapse into slide-out glass drawers.
- **Mobile (< 768px):** 4-column layout, `gutter` (1rem / 16px), `margin` (1rem / 16px). Secondary modules reflow into horizontally swipeable cards or collapsible accordions.

### Spacing Cadence
A rigid 4px/8px micro-grid underpins all component interiors:
- `space-xs` (4px) and `space-sm` (8px) govern tight pairings between labels and tabular values.
- `space-md` (16px) establishes standard card internal padding for dense widgets.
- `space-lg` (24px) separates card clusters, metric blocks, and primary tab bars.
- `space-xl` (32px) and `space-2xl` (48px) isolate distinct analytical domains.

## Elevation & Depth
Elevation in this system eschews muddy, heavy drop shadows in favor of translucent layering, surface tonal steps, and luminescent back-glows.

### Structural Stratification
1. **Base Layer (Canvas - `#0B0E14`):** The non-interactive background.
2. **Intermediate Panels (`#121721`):** Flat contextual panels, toolbars, and dock frames, bordered by `1px solid rgba(255, 255, 255, 0.05)`.
3. **Elevated Glass Cards (`#18202F` with 88% opacity):** Backed by `backdrop-filter: blur(16px)` and circumscribed by `1px solid rgba(255, 255, 255, 0.08)`.
4. **Popovers, Dropdowns & Drawers (`#1E273A` with 95% opacity):** Backed by `backdrop-filter: blur(24px)` and framed with `1px solid rgba(255, 255, 255, 0.12)`. Supported by an ambient shadow: `0 16px 40px -8px rgba(0, 0, 0, 0.6)`.

### Chromatic Glows
Interactive, focal, and positive delta elements utilize directional emissive lighting:
- **Active Card Glow:** A targeted soft box-shadow `0 0 24px -4px rgba(0, 208, 156, 0.15)` highlights selected investment vehicles or key performance milestones.
- **Primary CTA Pulse:** `0 4px 20px 0 rgba(0, 208, 156, 0.35)` conveys immediate urgency and affordance.
- **Critical Breaches:** Elevated elements under stress utilize `0 0 20px -2px rgba(255, 82, 82, 0.25)`.

## Shapes
A roundedness level of `2` provides a sophisticated balance: modern, ergonomic curves that retain architectural sharpness without degenerating into playful pill geometry.

### Radius System
- **Base Components (`0.5rem` / 8px):** Applied to buttons, input fields, dropdown trigger targets, data table cells, and status badges.
- **Card Surfaces (`rounded-lg` - `1rem` / 16px):** Metric panels, chart containers, asset allocation modules, and modal bodies.
- **Nested Groups & Micro-elements:** Internal pill chips or nested indicators scale down to `0.25rem` (4px) or full circular radii (`9999px`) exclusively for live-status pulsing dots and user avatar frames.

## Components

### Buttons
- **Primary Action (Emerald Glow):** Background `#00D09C`, text `#0B0E14` (Inter Bold), rounded 8px. Hover shifts background to `#1DE9B6` with an emissive aura (`box-shadow: 0 0 20px rgba(0, 208, 156, 0.4)`). Active state applies a subtle `scale(0.98)` transform.
- **Secondary (Obsidian Translucent):** Background `rgba(255, 255, 255, 0.04)`, border `1px solid rgba(255, 255, 255, 0.12)`, text `#FFFFFF`. Hover triggers `background: rgba(255, 255, 255, 0.08)` and border illumination via `rgba(0, 229, 255, 0.4)`.
- **Tertiary / Ghost:** No border or background. Text `rgba(255, 255, 255, 0.72)`. Hover transitions text color to `#1DE9B6`.

### Cards & Analytical Widgets
- Multi-layered containers with `#18202F` background, 16px radius, and `1px solid rgba(255, 255, 255, 0.08)`.
- Cards feature an optional subtle top-edge gradient highlight (`linear-gradient(90deg, rgba(0, 208, 156, 0.3) 0%, rgba(0, 229, 255, 0) 50%)`) to create optical depth on high-priority executive tiles.

### Status Chips & Delta Badges
- Pill or 6px-radius capsules with translucent fills:
  - **Positive Gain:** Background `rgba(0, 208, 156, 0.12)`, border `1px solid rgba(0, 208, 156, 0.28)`, text `#00D09C`. Includes an upward trend caret (`▲`).
  - **Loss / Deficit:** Background `rgba(255, 82, 82, 0.12)`, border `1px solid rgba(255, 82, 82, 0.28)`, text `#FF5252`. Includes a downward trend caret (`▼`).
  - **Live Streaming Badge:** Embedded 6px circular dot with a continuous ping animation in `#00E676`, flanked by tabular tracking text.

### Data Tables & Transaction Logs
- Stripeless, low-friction architecture. Row borders defined by `1px solid rgba(255, 255, 255, 0.04)`.
- Row hover triggers an instantaneous tonal wash: `rgba(255, 255, 255, 0.02)`.
- Column alignments adhere to financial standards: text left-aligned, status chips centered, financial sums and metrics right-aligned with fixed tabular spacing.

### Input Fields & Controls
- **Inputs:** Height 44px, background `rgba(18, 23, 33, 0.8)`, border `1px solid rgba(255, 255, 255, 0.12)`, rounded 8px. Font is Inter 14px. On focus: border shifts to `#00D09C`, backed by a focused shadow ring `0 0 0 3px rgba(0, 208, 156, 0.15)`.
- **Checkboxes & Radios:** Compact 18px frames. Checked states feature solid `#00D09C` fill with a high-contrast dark `#0B0E14` checkmark.
- **Segmented Range Selectors (1D, 1W, 1M, 1Y, ALL):** Pill or 8px enclosure with dark sunken background (`#121721`). The active interval snaps via a glassmorphic `#18202F` tile with active text highlighted in `#00E5FF`.

### Chart Tooltip Overlays
- Floating dark glass panels (`rgba(11, 14, 20, 0.94)`, backdrop blur 12px) with crisp neon hairline left-borders reflecting the focused data series (`#00D09C` or `#00E5FF`). Values display in tabular figures.