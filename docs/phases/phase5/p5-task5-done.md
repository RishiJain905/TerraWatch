# Phase 5 — Task 5: Ship Voyage Trails — DONE

## What was implemented

When a ship is selected, an SVG overlay renders its recent voyage path — the last 20 position updates received via WebSocket. The trail uses the `--accent-sea` color palette (`#58C4DC`, RGB `[88, 196, 220]`) and sits above the plane trail overlay (z-index 7 vs 6) using the same viewport-projected SVG `<polyline>` approach as the plane trail.

## Files changed

### `frontend/src/hooks/useShips.js`
- Added `selectedShipId = null` parameter to `useShips()` function signature
- Added `useRef` to React imports
- Imported `TRAIL_MAX_POINTS` from `'../utils/constants'`
- Added `shipsRef = useRef([])`, `selectedShipIdRef = useRef(selectedShipId)`, `trailStoreRef = useRef({})`
- Added `useEffect` to sync `shipsRef.current = ships`
- Added `appendSelectedShipTrailPoint(ship)` — appends `{lon, lat, timestamp: Date.now()}` to selected ship's trail, capped at `TRAIL_MAX_POINTS`
- Added `seedSelectedShipTrail(ship)` — seeds trail with current position when selection changes; resets trail store if no match
- Updated `addShip` — calls `appendSelectedShipTrailPoint(ship)` after existing upsert
- Updated `addShips` (batch) — cleans up trail entries for ship IDs no longer in the batch; appends trail point for selected ship if present
- Updated `removeShip` — deletes `trailStoreRef.current[shipId]`
- Added `useEffect` to sync `selectedShipIdRef` with `selectedShipId` prop, seed/reset trail on change
- Added `trailStoreRef` to return object

### `frontend/src/components/Globe/shipTrail.js` (NEW)
- `SHIP_TRAIL_COLOR_RGB = [88, 196, 220]` — `--accent-sea` aligned
- `SHIP_TRAIL_ALPHA_MIN = 80`, `SHIP_TRAIL_ALPHA_MAX = 220`
- `buildShipTrailPath(points, livePosition)` — filters valid points, appends live position if different from last
- `buildShipTrailSegments(points, livePosition)` — gradient-alpha segments for potential PathLayer use

### `frontend/src/components/Globe/Globe.jsx`
- Imported `buildShipTrailPath` from `'./shipTrail'`
- Added `selectedShip` to component props destructure
- Updated `useShips(selectedShip?.id)` call — destructured `trailStoreRef: shipTrailStoreRef`
- Added `liveSelectedShip` useMemo (parallel to `liveSelectedPlane`)
- Added ship trail path construction + viewport projection block (mirrors plane trail)
- Added ship trail SVG overlay in JSX (after plane trail SVG, before atmosphere SVG)

### `frontend/src/components/Globe/Globe.css`
- Added `.ship-trail-overlay` — absolute positioned SVG container, `mix-blend-mode: screen`, `filter: drop-shadow(0 0 4px rgba(88, 196, 220, 0.4))`, z-index 7 (above plane trail at z-index 6)
- Added `.ship-trail-path` — `stroke: rgba(88, 196, 220, 0.92)`, `stroke-width: 2.75`, `stroke-dasharray: 2 8`, rounded linecap/join

### `frontend/src/App.jsx`
- Added `selectedShip={selectedShip}` prop to `<Globe>` component

## Design decisions

- **SVG overlay approach** — matches the existing plane trail implementation (viewport-projected `<polyline>`) rather than a deck.gl `PathLayer`, ensuring consistent rendering behavior on GlobeView and consistent visual treatment (dashed trail line, glow filter, screen blend mode)
- **Trail data is a mutable ref, not React state** — trail updates don't trigger re-renders. The path re-renders when `selectedShip` changes (Globe re-render via prop), and trail data is read from the ref at render time
- **Only incremental `addShip` calls append to trails** — batch replaces via `addShips` clean up stale entries but only append for the currently-selected ship, since batches are authoritative snapshots, not incremental movement data
- **`--accent-sea` color `[88, 196, 220]`** — visually distinct from plane trail amber `[232, 184, 74]`, maintaining the air vs sea accent language established in the Gotham design system
- **`shipTrail.js` is standalone** — does not import from `planeTrail.js`, keeping the two trail modules decoupled while maintaining identical logic
- **z-index 7** — ship trail renders above plane trail (z-index 6) so if both coexist, the maritime trail stays on top (consistent with ship icon layer being on top of plane icon layer in deck.gl)

## Verification

- [x] `vite build` compiles successfully (1445 modules, 0 errors)
- [x] Trail storage in `useShips.js` appends on each `addShip` call and caps at 20 entries
- [x] Trail only renders when a ship is selected and has >= 2 positions
- [x] Trail color is `--accent-sea` aligned: `rgba(88, 196, 220, 0.92)`
- [x] Ship trail z-index above plane trail (7 vs 6)
- [x] SVG overlay is `pointer-events: none` — clicks pass through to ship IconLayer
- [x] `TRAIL_MAX_POINTS` shared constant in `constants.js` (no magic number)
