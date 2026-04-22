# Phase 5 Task 1 — Done (Revamp): Terminator Line + Starfield + Atmospheric Glow

**Status:** COMPLETE (revamp)
**Date:** 2026-04-17
**Supersedes:** The previous completion of this task (reverted in commits `1e4d5b4` "Massive UI/UX bug fixes" and `d7fa622` "Update Globe component") — the original polygon-based terminator had antimeridian/winding/pole bugs, the atmosphere was a fixed CSS oval that misaligned under pan/zoom, and the starfield as a deck.gl ScatterplotLayer added WebGL cost for no visual gain. This revamp removes all three of those failure modes.

---

## Why the previous attempt was discarded

Looking at the archived commits (`6142f83` → `8ec4ff1`), the polygon terminator required five follow-up fixes for antimeridian crossings, winding order, and pole closure — and still produced a hard knife-edge boundary that didn't feel like a real planet. The atmosphere was a `::after` oval sized `52% × 88%` relative to the viewport, which only lined up with the globe at the default zoom. Starfield stars were billboarded ScatterplotLayer points at 20 Mm radius that got occluded by the globe itself at wide zooms.

This revamp replaces the whole approach:

| Piece | Previous (reverted) | Revamp |
|---|---|---|
| Terminator | `SolidPolygonLayer` with per-latitude crossing search + `wrapLongitude` | `BitmapLayer` with a procedurally-generated 720×360 twilight raster |
| Starfield | `ScatterplotLayer` at 20 Mm sphere radius | Inline SVG `background-image` on `.globe-container` |
| Atmosphere | `::after` fixed oval | Viewport-tracked `<svg>` overlay whose center + radius are computed from the live deck.gl viewport |

---

## What shipped

### 1. Terminator — procedural `BitmapLayer`

New util `frontend/src/utils/terminator.js` exports `buildTerminatorImage(date, { width=720, height=360 })` returning an `ImageData`. For each pixel it computes `sin(solar_elevation)` using the classic NOAA low-precision equations (δ declination, subsolar longitude, hour angle) and maps it to alpha via a smoothstep band:

- Solar elevation ≥ +2° → alpha 0 (day, fully transparent)
- +2° > elev > −12° → smoothstep ramp (civil + nautical twilight, ~70 km on real Earth)
- Solar elevation ≤ −12° → alpha 140 (astronomical night, `rgb(4, 8, 24)`)

`Globe.jsx` paints the ImageData into an HTMLCanvasElement (deck.gl v9's BitmapLayer accepts canvases but not raw `ImageData`), memoizes it on a `now` tick state, and refreshes the tick every 60 seconds via `setInterval`. The layer is added to `deckLayers` directly after the basemap tile layer, so night tints the tiles. Bounds are clamped to `[-180, -85.0511, 180, 85.0511]` to match the Web Mercator tile coverage.

Why this beats the polygon approach:
- Pixels are independent → antimeridian/pole/winding bugs are impossible by construction
- Smooth twilight band reads as atmospheric scattering, not a knife edge
- Single canvas upload per minute is cheaper than a per-frame polygon geometry refresh
- Trivially unit-testable (see Verification below)

### 2. Starfield — seeded SVG background

New util `frontend/src/utils/starfield.js` exports `getStarfieldDataUrl()`. On first call it generates a 1920×1080 SVG with 400 circles at mulberry32-seeded positions (seed = 42), with three size bands (0.4–0.9, 0.9–1.6, 1.6–2.5 px), three color variants (white 70% / blue-white 20% / warm 10%), and variable fill-opacity (0.35–0.90). The resulting `url("data:image/svg+xml,...")` is memoized and attached to `.globe-container` via a `--starfield-bg` CSS custom property, consumed by a new `.globe-container::before` rule.

Because it's a DOM background layer behind the canvas, it cannot be occluded by the globe, doesn't trigger any WebGL work, and requires zero recomputation on resize, pan, or zoom.

### 3. Atmosphere — viewport-tracked SVG overlay

An inline `<svg>` is rendered next to the DeckGL canvas with two `radialGradient`s in `userSpaceOnUse` coordinates: an outer soft blue haze (`rgba(90,140,220,0.10)` at ~70% radius → transparent) and a tight fresnel rim (`rgba(140,180,255,0.22)` at the globe's on-screen radius, fading to transparent over ~12% of that radius). `mix-blend-mode: screen` lets the glow add light rather than veil it.

The overlay's center and radius come from a new `atmosphere` state in `Globe.jsx`. On every view-state change (and on `onLoad`, `onResize`, and window resize), an `updateAtmosphere` callback reads the live deck.gl viewport via `deckRef.current.deck.getViewports()[0]`, projects two lon/lat points 90° apart in angular distance on the sphere, and measures the resulting screen-space distance — which equals the visible globe radius in pixels. This means the rim glow precisely follows the globe as the user zooms or pans, fixing the main complaint about the reverted CSS oval.

---

## Files changed

| File | Action |
|---|---|
| `frontend/src/utils/terminator.js` | NEW — `buildTerminatorImage(date)` + `isNightSide(lon, lat, date)` |
| `frontend/src/utils/starfield.js` | NEW — `getStarfieldDataUrl()` with mulberry32-seeded 400-star SVG |
| `frontend/src/components/Globe/Globe.jsx` | UPDATED — imports, terminator canvas memo + minute timer, atmosphere state + `updateAtmosphere`, prepend terminator BitmapLayer, `--starfield-bg` style var, atmosphere SVG overlay |
| `frontend/src/components/Globe/Globe.css` | UPDATED — `overflow: hidden` on container, `::before` starfield rule, `.atmosphere-overlay` rule |
| `frontend/scripts/test-terminator.mjs` | NEW — node regression harness covering solar solstices + starfield |

No backend changes. No changes to other React components, hooks, or existing data layers. All existing pickability/filter behavior is untouched.

---

## Documented spec divergences

- **Terminator rendered as `BitmapLayer` raster, not `PolygonLayer`.** Eliminates the antimeridian/pole/winding bugs that killed the previous attempt and yields a smoother twilight band that matches real-Earth atmospheric scattering.
- **Terminator placed above the basemap tile layer**, not below. Night tints the basemap tiles (correct visual); below-the-tiles would be invisible since the carto dark basemap is opaque.
- **Starfield as SVG background**, not `SphereLayer`/`ScatterplotLayer`. `SphereLayer` doesn't exist in deck.gl v9; a scatter-based sphere added WebGL cost without better visuals. Background SVG has zero runtime cost and is guaranteed-visible.
- **Atmosphere as viewport-tracked SVG**, not `PolygonLayer` or CSS oval. Tracks the actual globe-radius-in-pixels via `viewport.project`, so it stays aligned during pan/zoom — the key flaw in the reverted implementation.

---

## Verification

- [x] `npm run build` succeeds with zero errors. 1439 modules transformed, 3.19s. (The `chunk size > 500 kB` warning is pre-existing and unrelated — deck.gl is large.)
- [x] Docker stack `docker compose up -d --build` boots both containers; backend `/health` returns `{"status":"healthy"}`, frontend on Vite dev server `http://localhost:5173/` returns HTTP 200.
- [x] Terminator math regression harness `frontend/scripts/test-terminator.mjs` — **15/15 passing**:
  - Subsolar point at summer solstice (lon 0, lat 23) has alpha 0 (day)
  - Antipode has alpha 140 (night)
  - North pole has midnight sun (alpha 0) on June solstice
  - South pole has polar night (alpha 140) on June solstice
  - Winter solstice inverts both poles correctly
  - `isNightSide()` convenience wrapper agrees with the raster
  - Global alpha is bounded in [0, 140] — no NaN/out-of-range pixels
  - Starfield contains exactly 400 `<circle>` elements, is a valid SVG data URL, and returns an identical string on repeated calls (memoization works)
- [x] No existing layer was removed, reordered, or had its picking behavior changed. `deckLayers` still ends with `planes → ships` on top so icon clicks win over scatter underneath.
- [x] No changes to `App.jsx`, `Sidebar/*`, `hooks/*`, or the backend.

### Visual verification note

Full in-browser visual confirmation (stars behind globe, twilight band crossing Europe at the current UTC, rim glow tracking a 0.5→3.0 zoom) requires a browser with hardware-accelerated WebGL. Cursor's embedded preview browser reports `Cannot read properties of undefined (reading 'maxTextureDimension2D')` from luma.gl on this machine — this is a pre-existing environmental issue (the embedded webview fails the same way for any deck.gl component, with or without the terminator layer), not a regression. The production `vite build` succeeds cleanly, the Docker stack serves on `http://localhost:5173/`, and the new utilities pass their full unit-level regression; final pixel-level visual verification should be done by opening that URL in a real browser (Chrome, Edge, Firefox).

---

## Rollback

Each of the three pieces is independent and file-scoped. To revert any one without affecting the others:

- Terminator: delete `frontend/src/utils/terminator.js`, remove its import and `terminatorLayer` push in `Globe.jsx`, drop the `now`/`terminatorImage` hooks.
- Starfield: delete `frontend/src/utils/starfield.js`, remove its import + the `--starfield-bg` style on `.globe-container`, delete the `.globe-container::before` CSS rule.
- Atmosphere: remove the `atmosphere` state, `updateAtmosphere`, the `<svg className="atmosphere-overlay">` JSX block, and the `.atmosphere-overlay` CSS rule.
