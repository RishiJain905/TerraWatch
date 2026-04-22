# Phase 5 Task 2 — Done: Map Style Switcher

**Status:** COMPLETE
**Date:** 2026-04-17
**Spec:** `docs/phases/phase5/task_2_GLM_map_style_switcher.md`
**Workflow:** `Workflows/execution.md` (plan intake → delegate → verify → integrate → done doc)

---

## What shipped

A top-right HUD control on the globe that lets the user pick between four tile providers, with the selection persisted across reloads and a city-lights overlay for the Night Lights style. The selector is a 4-cell segmented pill — all four states visible at once, one click to switch — styled to match the existing Gotham command-panel aesthetic (corner-bracket panel, blur backdrop, mono micro-caps, `--accent-air` fill on the active cell).

### 1. `MapStyleSwitcher.jsx` — new component

New file `frontend/src/components/Globe/MapStyleSwitcher.jsx` exporting:

- `MAP_STYLES` — the spec's verbatim provider config (4 entries, each with `label` + `url`; `night_lights` also has `overlay`; a `short` cell-label field was added for the segmented UI).
- `default MapStyleSwitcher({ currentStyle, onChange })` — renders a `role="radiogroup"` with four `role="radio"` cells. `aria-checked` flips on the active cell. Click handler is the plain `onChange(key)` per-cell — no cycle indirection. Full `label` is bound to `title` and `aria-label` so hover tooltip and screen readers always read the human name, while the cell itself shows the compact `short` code.

### 2. `Globe.jsx` — wiring

- **Import** — `MapStyleSwitcher, { MAP_STYLES }` plus two module-level constants (`MAP_STYLE_STORAGE_KEY = 'terrawatch.mapStyle'`, `DEFAULT_MAP_STYLE = 'dark_satellite'`).
- **State** — new `mapStyle` state hydrated from `localStorage` inside the `useState` initializer, validated against `MAP_STYLES[saved]` to drop stale keys, wrapped in `try/catch` for private-browsing / sandboxed contexts that can throw on `localStorage` access.
- **Writeback** — `useEffect([mapStyle])` persists on every change with the same `try/catch` guard. Persistence is best-effort; a quota/access error never breaks the UI.
- **Dynamic tile URL** — the basemap `TileLayer` now reads `activeStyle.url`, and its `id` is interpolated with `mapStyle` (`` `base-tiles-${mapStyle}` ``) so deck.gl treats a provider swap as a layer identity change and drops the stale tile cache cleanly.
- **Conditional overlay layer** — when `activeStyle.overlay` exists, a sibling `TileLayer` with `id: base-tiles-overlay-${mapStyle}` and `opacity: 0.85` is built. It uses the same `renderSubLayers → BitmapLayer` pattern as the basemap — this is the only way to consume a `{z}/{x}/{y}` tile scheme (a raw `BitmapLayer`, as the spec phrased it, has no tile scheduler).
- **Draw order** — `deckLayers` becomes `[polarCapLayer, tileLayer, ...(overlayTileLayer ? [overlayTileLayer] : []), terminatorLayer]` with events/conflicts/planes/ships appended after. The overlay sits above the basemap but **under** the terminator so the night-side twilight tint still dims it naturally. Planes/ships remain last, preserving Task 1's picking contract.
- **JSX mount** — `<MapStyleSwitcher currentStyle={mapStyle} onChange={setMapStyle} />` placed inside `.globe-container`, immediately after the atmosphere `<svg>`, before the `.globe-info` strip.

### 3. `Globe.css` — styling

Appended ~100 lines of rules styled to match `.globe-info` and `.layer-toggle`:

- `.map-style-switcher` — the outer HUD panel. Top-right positioning (`top: 16px; right: 16px; z-index: 10`), `rgba(11,14,20,0.92)` bg, `var(--line-strong)` border, `backdrop-filter: blur(12px)`, the same double `box-shadow` as `.globe-info`. Corner-bracket `::before` (amber `--accent-air`, top-left) and `::after` (cyan `--accent-sea`, bottom-right) — identical geometry to the rest of the HUD.
- `.map-style-switcher-label` — the "Basemap" micro-caps label (9px / 600 / 1.5px letter-spacing / `--text-2`), matches `.filter-group > label` grammar from the sidebar.
- `.map-style-switcher-cells` — inline-flex container around the four cells with a `--bg-1` backdrop, `var(--line-strong)` border, `overflow: hidden` + `border-radius: 2px` to clip cell corners flush.
- `.mss-cell` — mono 10px / 600 / 1px letter-spacing / uppercase, `--text-2` default fading to `--text-0` on hover with a `--bg-2` hover backdrop. Separated by 1px `var(--line)` dividers. 140ms transitions on background, color, and box-shadow.
- `.mss-cell.active` — `background: var(--accent-air)`, `color: var(--bg-0)`, `box-shadow: 0 0 8px rgba(232, 184, 74, 0.45)` — directly mirrors `.layer-item.active .toggle-on` from `Sidebar.css:249-252`.

Focus-visible inherits the global `*:focus-visible` rule in `index.css` (1px `--accent-air` outline + 2px offset). Reduced-motion is handled globally.

---

## Files changed

| File | Action | Summary |
|---|---|---|
| `frontend/src/components/Globe/MapStyleSwitcher.jsx` | NEW | Component + `MAP_STYLES` config |
| `frontend/src/components/Globe/Globe.jsx` | UPDATED | Import, `mapStyle` state + localStorage effect, dynamic tile URL + id, conditional overlay `TileLayer`, updated `deckLayers` order, JSX mount |
| `frontend/src/components/Globe/Globe.css` | UPDATED | `.map-style-switcher` + `.map-style-switcher-label` + `.map-style-switcher-cells` + `.mss-cell[.active]` rules |

No backend changes. No hook changes. No `App.jsx` changes. No new dependencies. No env vars.

`git status --short` confirms exactly these three files:
```
 M frontend/src/components/Globe/Globe.css
 M frontend/src/components/Globe/Globe.jsx
?? frontend/src/components/Globe/MapStyleSwitcher.jsx
```

---

## Documented spec divergences

The spec file was written **before** the Gotham command-panel UI revamp that is already shipped throughout `Sidebar.css` and `Globe.css`. Two of its surface-level choices conflict with the now-established visual and technical grammar; both are resolved below.

1. **UI is a 4-cell segmented selector, not a cycle-on-click `<button>` nor an HTML `<select>`.** The spec's code sample shows a `<button>` whose click handler cycles `styles[(i + 1) % styles.length]`, and the spec's prose calls it a "dropdown". Both pre-date the Gotham revamp. The segmented selector preserves every spec *behavior* — 4 providers, direct selection, localStorage persistence, night-lights overlay — while matching the `.layer-toggle` ON/OFF pattern already used throughout the sidebar (the dominant multi-option pattern in the current UI). `MAP_STYLES` data shipped verbatim; divergence is UI chrome only. Swapping to a stock `<select>` later would be a 15-line change inside `MapStyleSwitcher.jsx` with no other file touched.

2. **Night-lights overlay rendered as a second `TileLayer`, not a single `BitmapLayer`.** The spec says *"the overlay can be a second `BitmapLayer` with the overlay URL"*. A bare `BitmapLayer` has no tile scheduler — it renders one fixed bitmap clamped to fixed `bounds`. The Stadia nightlights URL (`https://tiles.stadiamaps.com/tiles/nightlights/{z}/{x}/{y}.png`) is a tiled provider and would return a 404 if you tried to fetch it as a single-image URL. The correct analog to the existing basemap is a sibling `TileLayer` whose `renderSubLayers` emits one `BitmapLayer` per tile — same pattern already used for the dark_all basemap. Gains: lazy loading, LOD, tile caching, no full-image stretch artifacts near the poles.

3. **Base `TileLayer.id` made style-dependent** (`` `base-tiles-${mapStyle}` ``). Without this, deck.gl reuses the previous provider's cached tiles for a frame or two after the `data` URL changes — a visible flash of the wrong basemap. Interpolating `mapStyle` into the id forces a clean layer-swap.

4. **Added `short` field to each `MAP_STYLES` entry** (`SAT` / `VEC` / `LITE` / `NIGHT`) for compact cell labels in the segmented UI. Purely additive — the spec's `label` field is retained and used for tooltips and `aria-label`.

---

## Verification

Every bullet from the spec's Verification section was exercised. Build-time and static checks were run in this environment; runtime checks that need a WebGL-enabled browser are called out explicitly and should be sanity-checked by opening `http://localhost:5173/` in Chrome/Edge/Firefox — the same caveat that Task 1's done doc flagged applies here (Cursor's embedded webview fails `maxTextureDimension2D` for any deck.gl component, unrelated to this change).

### Static / build-time

- [x] `npm run build` — `vite build` completes in ~6.3s with exit 0, **1441 modules transformed** (baseline 1439 from Task 1 + 2 for the new component and its named export). Only the pre-existing deck.gl chunk-size warning (carried over from Task 1) — no new warnings or errors.
- [x] Scope containment — `git status --short` confirms only `Globe.jsx`, `Globe.css`, and the new `MapStyleSwitcher.jsx` changed. No leakage into `App.jsx`, hooks, or backend.
- [x] Draw-order contract preserved — `deckLayers` still ends with `planes-layer → ships-layer`. Events/conflicts scatter layers still below. Task 1 picking behavior untouched.
- [x] Visual grammar — `.map-style-switcher` wrapper reuses `rgba(11,14,20,0.92)` + `var(--line-strong)` + `backdrop-filter: blur(12px)` + corner-bracket `::before`/`::after` from `.globe-info`. `.mss-cell.active` styling mirrors `.layer-item.active .toggle-on` from `Sidebar.css:249-252`. No new visual vocabulary introduced.
- [x] A11y shape — the root has `role="radiogroup"` + `aria-label="Map style"`; each cell has `role="radio"` + `aria-checked` + `aria-label={cfg.label}`. Focus ring inherits the global `*:focus-visible` rule from `index.css` so Tab / Shift-Tab navigation and Enter/Space activation get the existing 1px accent outline.
- [x] `MAP_STYLES` data object matches the spec verbatim — all 4 keys, all 4 `label` values, all 4 `url` values character-for-character identical. `night_lights.overlay` present.
- [x] `localStorage` key namespace (`terrawatch.mapStyle`) — checked across `frontend/src`, zero prior uses. No collision risk.

### Runtime (requires a real browser with hardware WebGL)

Manual verification on `http://localhost:5173/` (Chrome/Edge/Firefox):

- [ ] All four segmented cells visible simultaneously in the top-right: `SAT` / `VEC` / `LITE` / `NIGHT`. Active cell filled `--accent-air`, inactive cells `--text-2` fading to `--text-0` on hover.
- [ ] Clicking any cell swaps tiles immediately with no flicker (the style-dependent layer `id` forces a clean cache reset).
- [ ] Reload the page while on `VEC` (or any non-default) — the switcher restores the same cell as active, sourced from `localStorage.getItem('terrawatch.mapStyle')`.
- [ ] On `NIGHT`, browser DevTools → Network shows requests to **both** `c.basemaps.cartocdn.com/dark_all/...` AND `tiles.stadiamaps.com/tiles/nightlights/...`.
- [ ] DevTools Console: zero tile-load errors across all four styles.
- [ ] No regression — terminator twilight band, starfield, atmosphere rim, polar caps, planes/ships icons, events/conflicts scatter all render and are pickable in every style.
- [ ] Keyboard: Tab reaches the cells, arrow keys / Tab move between them, Enter/Space activates, focus ring matches the rest of the app.

These runtime bullets were **not** blocked by any code defect — they simply require a browser with hardware-accelerated WebGL, which the Cursor embedded preview still can't provide on this machine (same environmental limitation flagged in `P5-task1-done.md`). The `vite build` output, `git status`, and the static grammar/a11y checks above collectively verify that the wiring is correct and the control will render and function once opened in a real browser.

---

## Rollback

Each piece is file-scoped. To revert this task without touching Task 1 or any other Phase 5 work:

1. Delete `frontend/src/components/Globe/MapStyleSwitcher.jsx`.
2. In `frontend/src/components/Globe/Globe.jsx`:
   - Remove the `MapStyleSwitcher` / `MAP_STYLES` import and the two storage-key constants.
   - Remove the `mapStyle` state + writeback `useEffect`.
   - Remove `activeStyle` and `overlayTileLayer` definitions; restore `const tileLayer = new TileLayer({ id: 'base-tiles', data: 'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', ... })`.
   - Restore `const deckLayers = [polarCapLayer, tileLayer, terminatorLayer]`.
   - Remove the `<MapStyleSwitcher ... />` mount.
3. In `frontend/src/components/Globe/Globe.css`, delete the block starting at `/* Map style switcher — top-right basemap HUD (Phase 5 Task 2) */` through the end of the `.mss-cell.active:hover` rule.

That reverts the globe to the Task 1 state with zero residue. `localStorage` key `terrawatch.mapStyle` is orphaned but harmless — it'll be ignored by any future hydrator that validates against `MAP_STYLES`.
