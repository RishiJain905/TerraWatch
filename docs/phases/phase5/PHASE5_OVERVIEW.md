# Phase 5 — Map & Data Refinements

## Goal

Polish the existing TerraWatch platform to production quality. No new data sources or major features — this phase is entirely about making what's already built feel like a premium GEOINT product.

---

## Context Files (Read First)

Before any implementation, read:
- `docs/ARCHITECTURE.md` — system architecture
- `frontend/src/components/Globe/Globe.jsx` — current globe implementation
- `frontend/src/components/Sidebar/Sidebar.jsx` — current sidebar
- `frontend/src/hooks/usePlanes.js` — plane state management
- `frontend/src/hooks/useShips.js` — ship state management
- `frontend/src/index.css` — **Gotham** design tokens (`--bg-*`, `--line*`, `--text-*`, `--accent-*`, `--mono`, `--sans`)
- `frontend/src/components/Globe/Globe.css` — globe HUD (stat strip, legend, basemap control, atmosphere)
- `frontend/src/components/Sidebar/Sidebar.css` — sidebar command-panel layout (layer rows, filters, toggles)
- `frontend/src/components/InfoPanel/infoPanel.css` — shared bracket-card chrome for plane/ship-style info panels

---

## UI / UX baseline (Gotham command panel)

Phase 5 polish must match the **Gotham GEOINT** UI shipped across the frontend: dark layered surfaces, `1px` borders using `var(--line)` / `var(--line-strong)`, corner bracket accents on HUD cards, `backdrop-filter: blur(12px)` on floating panels, **IBM Plex** via `--sans` / `--mono`, and accent colors (`--accent-air`, `--accent-sea`, etc.) for semantic emphasis — not ad-hoc grays or generic Material-style pills.

**Globe HUD:** New controls (minimap, reset view, etc.) should reuse the same visual grammar as `.globe-info`, `.globe-legend`, and **Task 2** `.map-style-switcher` (top-right basemap strip): `rgba(11, 14, 20, 0.92)` panels, `2px` border radius (square HUD geometry), mono micro-labels where appropriate.

**Sidebar:** Layer toggles, filters, and future freshness rows follow `.layer-item`, `.filter-panel`, and `.layer-toggle` patterns from `Sidebar.css`.

**Info panels:** Rows, labels, close control, and copy/link affordances should extend `infoPanel.css` rather than inventing parallel styles.

Respect **`prefers-reduced-motion`** (`index.css`) for any new motion.

---

## What This Phase Is

- Globe visual enhancements (terminator line, starfield, atmosphere glow)
- Map style switching (multiple tile providers)
- Navigation improvements (minimap, fly-to, reset view)
- Data trails (flight paths for selected plane/ship)
- Keyboard shortcuts
- Data quality improvements (stale thresholds, freshness indicators)
- UI polish (loading states, empty states, copy buttons, relative timestamps)

---

## What This Phase Is NOT

- New data sources or layers
- New backend services or schedulers
- Zone alerting (Phase 6)
- Production hardening / deployment (Phase 7)

---

## Task Breakdown

### Visual Enhancements

| # | Task | Description | Agent |
|---|------|-------------|-------|
| 1 | Terminator line + starfield + atmosphere | Day/night boundary great circle, star sphere background, atmospheric rim glow | GLM |
| 2 | Map style switcher | **Done** — Top-right **segmented basemap HUD** (four cells: SAT / VEC / LITE / NIGHT), `MAP_STYLES` tile URLs, `localStorage` persistence, night-lights overlay `TileLayer`; Gotham chrome matching sidebar toggles | GLM |
| 3 | Minimap/navigator inset | Small globe in corner showing current view position | GLM |

### Data Trails

| # | Task | Description | Agent |
|---|------|-------------|-------|
| 4 | Flight path trails | LineLayer trail for selected plane — last N positions | GLM |
| 5 | Ship voyage trails | LineLayer trail for selected ship — last N positions | GLM |

### Navigation UX

| # | Task | Description | Agent |
|---|------|-------------|-------|
| 6 | Fly-to + reset view | Smooth transition to clicked entity + reset/home button | GLM |
| 7 | Keyboard shortcuts | Arrow keys rotate, +/– zoom, Escape closes panel, R reset | MiniMax |

### Data Quality

| # | Task | Description | Agent |
|---|------|-------------|-------|
| 8 | Stale thresholds + freshness indicators | Env vars for stale times, per-layer "last updated" display | MiniMax |
| 9 | Null field graceful handling | Null checks in info panels, fallback values, no crashes | GLM |

### UI Polish

| # | Task | Description | Agent |
|---|------|-------------|-------|
| 10 | Loading skeletons | Initial load skeletons for globe and sidebar | GLM |
| 11 | Empty state messages | Friendly messages when filters return 0 results | GLM |
| 12 | External links + copy buttons | target="\_blank" on source URLs, clipboard copy on IDs | MiniMax |
| 13 | Relative timestamps + panel overflow | "2 hours ago" format, panel stays within viewport | GLM |

---

## File Structure

```
frontend/src/
├── components/
│   ├── Globe/
│   │   ├── Globe.jsx         UPDATE — terminator, starfield, atmosphere, basemap state, fly-to, trails, minimap
│   │   ├── Globe.css         UPDATE — HUD chrome (info, legend, basemap switcher, atmosphere, minimap)
│   │   ├── Minimap.jsx       NEW — small globe navigator inset
│   │   └── MapStyleSwitcher.jsx  SHIPPED (Task 2) — segmented basemap control + MAP_STYLES
│   ├── Sidebar/
│   │   └── Sidebar.jsx       UPDATE — freshness indicators, empty states
│   └── InfoPanels/
│       ├── PlaneInfoPanel.jsx    UPDATE — copy button, relative time, null handling
│       ├── ShipInfoPanel.jsx     UPDATE — copy button, relative time, null handling
│       ├── EventInfoPanel.jsx   UPDATE — external link, copy button, relative time
│       └── ConflictInfoPanel.jsx UPDATE — external link, copy button, relative time
├── hooks/
│   ├── usePlanes.js          UPDATE — add trail positions, stale detection
│   └── useShips.js           UPDATE — add trail positions, stale detection
└── utils/
    ├── terminator.js         SHIPPED (Task 1) — twilight / solar helpers for terminator bitmap
    ├── starfield.js          SHIPPED (Task 1) — procedural starfield data URL
    └── formatters.js         UPDATE — add relativeTime(), add copyToClipboard()

backend/
├── app/config.py             UPDATE — add STALE_PLANE_SECONDS, STALE_SHIP_SECONDS, STALE_EVENT_SECONDS
└── docs/ENVIRONMENT.md      NEW — document new env vars
```

---

## Key Technical Details

### Terminator Line (Day/Night Boundary)

The terminator is the great circle separating day and night (solar position: declination, subsolar longitude, etc.). **Shipped implementation** (Task 1) uses a high-level approach documented in `docs/phases/phase5/P5-task1-done.md` and `frontend/src/utils/terminator.js` — defer to `Globe.jsx` rather than early sketch layers. Original polygon/sphere sketches in older docs are non-normative.

### Starfield

**Shipped:** procedural starfield behind the globe (see `frontend/src/utils/starfield.js` and `Globe.css`). Early `SphereLayer` sketches are non-normative.

### Atmospheric Glow

**Shipped:** viewport-tracked rim/haze aligned to the on-screen globe radius (see `Globe.jsx` + `Globe.css`). Early fixed-oval or extra-`PolygonLayer` sketches are non-normative.

### Map style switcher (Task 2 — shipped)

**UI:** Top-right **segmented basemap HUD** (four visible cells, Gotham styling aligned with `.layer-toggle` / globe HUD — not a stock HTML `<select>` or anonymous cycle button). Compact cell labels (`SAT`, `VEC`, `LITE`, `NIGHT`) with full names in tooltips / `aria-label`.

**Data:** `MAP_STYLES` in `MapStyleSwitcher.jsx` — four providers:
- **Dark Satellite**: `https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png`
- **Dark Vector**: `https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}.png`
- **Light**: `https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}.png`
- **Night Lights**: same Carto dark base plus **Stadia nightlights** overlay tiles (`https://tiles.stadiamaps.com/tiles/nightlights/{z}/{x}/{y}.png`) as a sibling `TileLayer` (tiled overlay, not a single full-globe `BitmapLayer`)

**State:** Selected style key persisted in `localStorage` (`terrawatch.mapStyle`). Main `Globe.jsx` `TileLayer` uses style-dependent `id` (`base-tiles-${mapStyle}`) so tile caches swap cleanly when the provider changes.

### Minimap

A second `GlobeView` in a small `<div>` absolutely positioned (typically **bottom-right**, clearing `.globe-info` and **not** overlapping the top-right basemap control). Shows a simplified view with a view-center indicator; **north-up** inset is the usual pattern. **Basemap tiles should match the active `MAP_STYLES` entry** (same URLs as the main globe). See `docs/phases/phase5/task_3_GLM_minimap.md`.

### Flight/Ship Trails

Store last 20 positions per entity in a `useRef` array. On entity selection, render as `LineLayer`. Append new position on each WebSocket update for the selected entity only.

### Fly-To

On entity click, animate `viewState` from current to entity's lat/lon using `deck.gl`'s `transitionInterpolator` or manual lerp over 60 frames.

### Freshness Indicators

Each hook tracks `lastUpdated` timestamp. Sidebar shows "Live" or "Xs ago" per layer. Backend exposes stale cleanup in SQLite but freshness is primarily a frontend display concern.

---

## Verification Checklist

- [ ] Terminator line accurately separates day/night on globe
- [ ] Starfield visible in space behind globe
- [ ] Atmospheric glow visible at globe edges
- [x] Map style switcher: all four basemap styles selectable; tiles update immediately; selection persists across reload; night lights requests both basemap and `nightlights` tiles (Task 2)
- [ ] Minimap shows current view position
- [ ] Clicking a plane smoothly flies to its position
- [ ] Flight trail renders for selected plane
- [ ] Ship voyage trail renders for selected ship
- [ ] Keyboard shortcuts work (Escape, R, arrows, +/-)
- [ ] Reset view button returns to initial view
- [ ] Per-layer freshness indicator shows "Live" or "Xs ago"
- [ ] Stale thresholds configurable via env vars
- [ ] Info panels handle null fields gracefully
- [ ] Loading skeletons show during initial data fetch
- [ ] Empty state messages appear when filters return 0 results
- [ ] External links open in new tab
- [ ] Copy button copies ID to clipboard
- [ ] Timestamps show relative time ("2 hours ago")
- [ ] Info panels don't overflow viewport
- [ ] All existing features still work (no regression)

---

## Constraints

- No new data sources
- No new WebSocket message types
- No changes to existing backend API contracts
- All visual enhancements are additive (toggle-able preferred)
- Keep performance in mind — 10k+ planes + trails must stay smooth
