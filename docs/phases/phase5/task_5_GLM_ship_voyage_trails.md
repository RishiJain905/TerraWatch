# Phase 5 — Task 5: Ship Voyage Trails

## Context

Read `frontend/src/hooks/useShips.js` and `frontend/src/components/Globe/Globe.jsx` first.

## UI / UX baseline (Gotham — read before implementing)

Same discipline as **Task 4 (flight trails)** — maritime trails should align with **`--accent-sea`** (`#58C4DC` → RGB `[88, 196, 220]`), not a disconnected cyan unrelated to the ship legend.

- **Ship accent:** Trail stroke RGBA derived from `--accent-sea`; optionally reference `SHIP_TYPE_COLORS` in `frontend/src/utils/shipIcons.js` only if it stays visually consistent with the sidebar ship-type legend (do not pick a one-off color that clashes).
- **Constants:** Share `TRAIL_MAX_POINTS` with planes via `frontend/src/utils/constants.js` (single source of truth with Task 4).
- **Layer order:** Trail **below** ship `IconLayer` so the selected ship icon remains on top and wins picking.

## Goal

Same concept as flight path trails, but for ships. When a ship is selected, render a `LineLayer` showing its recent voyage path.

## Implementation

### Trail Storage

Mirror the implementation from `usePlanes.js` into `useShips.js`:

```javascript
const trailStore = useRef({})

const addShip = useCallback((ship) => {
  if (!trailStore.current[ship.id]) {
    trailStore.current[ship.id] = []
  }
  trailStore.current[ship.id].push({
    lon: ship.lon,
    lat: ship.lat,
    timestamp: Date.now(),
  })
  if (trailStore.current[ship.id].length > 20) {
    trailStore.current[ship.id].shift()
  }
  // ... existing upsert logic
}, [])
```

### Globe Rendering

In `Globe.jsx`, when `selectedShip` is set:

```javascript
const shipTrail = shipTrailsRef.current[selectedShip?.id] ?? []

if (shipTrail.length >= 2) {
  deckLayers.push(
    new PathLayer({
      id: 'ship-trail-layer',
      data: [{ path: shipTrail.map(p => [p.lon, p.lat]) }],
      getPath: d => d.path,
      getColor: [88, 196, 220, 180], // --accent-sea aligned
      getWidth: 2,
    })
  )
}
```

Use a different hue family than the plane trail (**air vs sea accents**) so simultaneous plane+ship selection (if ever allowed) remains legible.

### Trail Color

Prefer **`--accent-sea`-aligned RGBA** (see baseline). `SHIP_TYPE_COLORS` may be used for per-type tint **only** if it does not break the Gotham palette harmony.

## Files to Update

- `frontend/src/hooks/useShips.js` — add trail storage
- `frontend/src/components/Globe/Globe.jsx` — render ship trail when ship selected; stack below `ships-layer`
- `frontend/src/utils/constants.js` — `TRAIL_MAX_POINTS = 20` (shared with planes — coordinate with Task 4)

## Verification

- [ ] Ship trail renders when ship is selected
- [ ] Trail shows last 20 positions as a line
- [ ] Trail updates as new positions come in
- [ ] Trail disappears when ship is deselected
- [ ] Plane and ship trails can coexist (one of each) with visually distinct accent families
- [ ] Ship trail color matches the maritime accent language of the UI
