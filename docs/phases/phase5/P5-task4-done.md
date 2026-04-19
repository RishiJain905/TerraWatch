# Phase 5 — Task 4: Flight Path Trails — DONE

## What was implemented

When a plane is selected, a `PathLayer` renders its recent path — the last 20 position updates received via WebSocket. The trail uses the `--accent-air` color palette and sits above basemap/terminator layers but below pickable icon layers.

## Files changed

### `frontend/src/utils/constants.js`
- Added `export const TRAIL_MAX_POINTS = 20` — shared constant used by `usePlanes.js` and available for Task 5 (ship trails).

### `frontend/src/hooks/usePlanes.js`
- Added `useRef` to React imports
- Imported `TRAIL_MAX_POINTS` from constants
- Created `trailStoreRef = useRef({})` — a mutable ref keyed by plane ID, each value is `[{lon, lat, timestamp}, …]`
- In `addPlane`: appends `{lon, lat, timestamp: Date.now()}` to the plane's trail array, capped at `TRAIL_MAX_POINTS` via `shift()`
- In `addPlanes` (batch replace): cleans up trails for plane IDs no longer in the batch — does NOT append to trails (batch is a full replace, not incremental)
- In `removePlane`: deletes the trail entry for the removed plane ID
- Exposed `trailStoreRef` in the hook's return object

### `frontend/src/components/Globe/Globe.jsx`
- Added `PathLayer` to `@deck.gl/layers` import
- Added `selectedPlane` prop to component destructuring
- Destructured `trailStoreRef` from the `usePlanes()` call
- Added trail layer rendering after terminator and before events/conflicts/icon layers:
  - Reads `trailStoreRef.current[selectedPlane?.id]` for trail data
  - Only renders if trail has ≥ 2 points
  - `PathLayer` with color `[232, 184, 74, 180]` (accent-air aligned), width 2, `pickable: false`
- Layer order: polarCaps → tiles → overlay → terminator → **plane trail** → events → conflicts → planes → ships

### `frontend/src/App.jsx`
- Added `selectedPlane={selectedPlane}` prop to the `<Globe>` component

## Design decisions

- **Trail data is a mutable ref, not React state** — trail updates don't trigger re-renders. The path re-renders when `selectedPlane` changes (which triggers a Globe re-render via the prop), and trail data is read from the ref at that point.
- **Only incremental `addPlane` calls append to trails** — batch replaces via `addPlanes` clean up stale entries but don't grow trails, since the batch is an authoritative snapshot, not incremental movement data.
- **No `trailStoreRef` prop threading through App.jsx** — `trailStoreRef` is obtained directly from the `usePlanes()` call inside Globe.jsx, so it doesn't need to be passed through App.jsx. Only `selectedPlane` needed to be added as a prop.

## Verification

- [x] `vite build` compiles successfully (1443 modules, no errors)
- [x] Trail storage in `usePlanes.js` appends on each `addPlane` call and caps at 20 entries
- [x] Trail only renders when a plane is selected and has ≥ 2 positions
- [x] Trail color is accent-air aligned: `[232, 184, 74, 180]`
- [x] Layer ordering: trail above basemap/terminator, below icon layers
- [x] `PathLayer` is `pickable: false` — clicks pass through to the plane IconLayer
- [x] `TRAIL_MAX_POINTS` is in `constants.js`, not a magic number
