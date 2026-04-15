# Phase 5 — Task 5: Ship Voyage Trails

## Context

Read `frontend/src/hooks/useShips.js` and `frontend/src/components/Globe/Globe.jsx` first.

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
      getColor: [100, 200, 255, 150], // cyan for ships
      getWidth: 2,
    })
  )
}
```

Use a different color than the plane trail (cyan/blue vs red) so they're visually distinct.

### Trail Color

Use `SHIP_TYPE_COLORS` from `shipIcons.js` — or a fixed blue/cyan since voyage trails are maritime-themed.

## Files to Update

- `frontend/src/hooks/useShips.js` — add trail storage
- `frontend/src/components/Globe/Globe.jsx` — render ship trail LineLayer when ship selected
- `frontend/src/utils/constants.js` — `TRAIL_MAX_POINTS = 20` (shared with planes)

## Verification

- [ ] Ship trail renders when ship is selected
- [ ] Trail shows last 20 positions as a line
- [ ] Trail updates as new positions come in
- [ ] Trail disappears when ship is deselected
- [ ] Plane and ship trails can coexist (one of each)
