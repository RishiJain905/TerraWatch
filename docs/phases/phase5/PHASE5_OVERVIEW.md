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
| 2 | Map style switcher | Tile provider dropdown: dark satellite, dark vector, light, night city lights | GLM |
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
| 7 | Keyboard shortcuts | Arrow keys rotate, +/– zoom, E escape close panel, R reset | MiniMax |

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
│   │   ├── Globe.jsx         UPDATE — add terminator, starfield, atmosphere, fly-to, trails
│   │   ├── Globe.css         UPDATE — atmosphere glow, minimap position
│   │   ├── Minimap.jsx       NEW — small globe navigator inset
│   │   └── MapStyleSwitcher.jsx  NEW — tile provider dropdown
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
    ├── terminator.js         NEW — solar position calculation for day/night line
    └── formatters.js         UPDATE — add relativeTime(), add copyToClipboard()

backend/
├── app/config.py             UPDATE — add STALE_PLANE_SECONDS, STALE_SHIP_SECONDS, STALE_EVENT_SECONDS
└── docs/ENVIRONMENT.md      NEW — document new env vars
```

---

## Key Technical Details

### Terminator Line (Day/Night Boundary)

The terminator is the great circle separating day and night. Calculate using solar position:
- Sun's declination based on day of year
- Solar right ascension from UTC time
- Convert to lat/lon points forming the terminator polygon
- Render as a `PolygonLayer` with night-side semi-transparent dark fill, day-side invisible

Reference: `suncalc` library or manual calculation via NOAA solar equations.

### Starfield

A large sphere (radius >> globe radius) with a star texture, rendered behind the globe. Use a `SphereLayer` with a procedural star image or white dots on black.

### Atmospheric Glow

Post-processing or a slightly larger transparent sphere with rim gradient shader. deck.gl's `GlobeView` can use custom shaders or an additional `PolygonLayer` with radial gradient fill at globe edges.

### Map Style Switcher

Tile provider presets:
- **Dark Satellite**: `https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png` (current)
- **Dark Vector**: `https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}.png`
- **Light**: `https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}.png`
- **Night Lights**: `https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png` with city lights overlay via separate WMS

### Minimap

A second `GlobeView` in a small `<div>` absolutely positioned in the corner. Shows a simplified view of the full globe with a "you are here" indicator (small rectangle or dot for current view center). Synchronize view rotation to main globe or show fixed north-up orientation.

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
- [ ] Map style switcher cycles through all 4 tile styles
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
