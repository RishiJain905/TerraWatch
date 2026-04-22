# Phase 5 Task 3 — Minimap / Navigator Inset: DONE

## What was shipped

A small globe inset (minimap) in the bottom-right corner of the viewport that shows the user's current view position on the full Earth — a standard GEOINT navigation aid.

## Files changed

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/components/Globe/Minimap.jsx` | NEW | Self-contained minimap component rendering a second `DeckGL` + `GlobeView` instance |
| `frontend/src/components/Globe/Globe.jsx` | UPDATE | Import `<Minimap>` and render it with `viewState`, `basemapUrl`, and `overlayUrl` props |
| `frontend/src/components/Globe/Globe.css` | UPDATE | Add `.minimap-container` styles (bottom-right positioning, Gotham HUD chrome) |

## Implementation details

### Minimap.jsx

- Second `DeckGL` instance with `GlobeView({ id: 'minimap-globe' })`
- Always north-up: `bearing: 0`, `pitch: 0`, `zoom: 1` — only `longitude` and `latitude` are synced from the parent's `viewState`
- Read-only: `controller={false}` prevents pan/zoom interaction
- `pointer-events: none` on the container div so it never steals input from the main globe
- **Basemap sync:** Uses the same `TileLayer` + `BitmapLayer` pattern as the main globe, driven by `basemapUrl` prop (sourced from the active `MAP_STYLES` entry)
- **Night-lights overlay:** Conditionally renders a second `TileLayer` when `overlayUrl` is provided (opacity 0.85), matching the main globe's night-lights behavior
- **Indicator dot:** `ScatterplotLayer` at the current view center with `getFillColor: [232, 184, 74, 255]` (matches `--accent-air`) and `getRadius: 50000` meters
- `minimapViewState` is memoized with `useMemo` on `[viewState.longitude, viewState.latitude]` to avoid unnecessary re-renders

### Globe.jsx integration

- Added `import Minimap from './Minimap'` (line 17)
- Rendered `<Minimap viewState={viewState} basemapUrl={activeStyle.url} overlayUrl={activeStyle.overlay} />` after `<MapStyleSwitcher>` (inside `.globe-container`)
- `activeStyle` is the existing computed variable: `MAP_STYLES[mapStyle] ?? MAP_STYLES[DEFAULT_MAP_STYLE]`

### Globe.css styling

- `.minimap-container`: `position: absolute; bottom: 72px; right: 16px; width: 148px; height: 148px`
- Gotham HUD chrome matching `.globe-info`, `.globe-legend`, `.map-style-switcher`: `rgba(11, 14, 20, 0.92)` background, `border: 1px solid var(--line-strong)`, `border-radius: 2px`, `backdrop-filter: blur(12px)`, matching `box-shadow`
- `pointer-events: none; z-index: 90` — below legend (100) and above the deck canvas
- Corner bracket `::before` / `::after` accents: `accent-air` top-left, `accent-sea` bottom-right (matching pattern from other HUD elements)

## Verification checklist

- [x] Minimap visible in bottom-right corner, clears `.globe-info` (72px bottom offset) and does not cover `.globe-legend`
- [x] Shows full globe with the current basemap style (including night-lights overlay when active)
- [x] Indicator shows current view center with `--accent-air` color
- [x] Minimap is north-up regardless of main globe bearing (`bearing: 0`, `pitch: 0`)
- [x] Minimap does not intercept pointer events (`pointer-events: none` + `controller={false}`)
- [x] Panel chrome (border, blur, shadow, corner brackets) matches other globe HUD elements
- [x] Build compiles successfully (vite build — no errors)
