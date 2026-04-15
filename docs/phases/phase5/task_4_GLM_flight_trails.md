# Phase 5 — Task 4: Flight Path Trails

## Context

Read `frontend/src/hooks/usePlanes.js` and `frontend/src/components/Globe/Globe.jsx` first.

## Goal

When a plane is selected, render a `LineLayer` showing its recent path — the last N position updates it has received. This gives a "where has this plane been" view.

## Implementation

### Trail Storage

In `usePlanes.js`, add trail storage:

```javascript
// Store last N positions per plane ID
const trailStore = useRef({})

const addPlane = useCallback((plane) => {
  // Add position to trail
  if (!trailStore.current[plane.id]) {
    trailStore.current[plane.id] = []
  }
  trailStore.current[plane.id].push({
    lon: plane.lon,
    lat: plane.lat,
    timestamp: Date.now(),
  })
  // Keep only last 20 positions
  if (trailStore.current[plane.id].length > 20) {
    trailStore.current[plane.id].shift()
  }
  // ... existing upsert logic
}, [])
```

Expose trail via `useTrail(planeId)` getter or `trailsRef`:

```javascript
const trailsRef = useRef({}) // { [planeId]: [{lon, lat}, ...] }
trailStoreRef.current = trailStore.current
```

### Globe Rendering

In `Globe.jsx`, when a `selectedPlane` is set:

```javascript
const planeTrail = trailRef.current[selectedPlane?.id] ?? []

// Add LineLayer to deckLayers
if (planeTrail.length >= 2) {
  deckLayers.push(
    new LineLayer({
      id: 'plane-trail-layer',
      data: [{ path: planeTrail.map(p => [p.lon, p.lat]) }],
      getSourcePosition: d => d.path[0],
      getTargetPosition: d => d.path[d.path.length - 1],
      getColor: [255, 100, 100, 150],
      getWidth: 2,
      pickable: false,
    })
  )
}
```

Or better — render as a `PathLayer` showing the full polyline:

```javascript
new PathLayer({
  id: 'plane-trail-layer',
  data: planeTrail.map((p, i, arr) => i < arr.length - 1 ? {
    path: [[arr[i].lon, arr[i].lat], [arr[i+1].lon, arr[i+1].lat]]
  } : null).filter(Boolean),
  getColor: [255, 100, 100, 150],
  getWidth: 2,
})
```

### Trail Color

Use the same red as the plane icon (or slightly transparent) to indicate "path taken."

### Performance

Only store trail for the **selected plane** — not all 10k planes. If no plane is selected, trail array is empty.

## Files to Update

- `frontend/src/hooks/usePlanes.js` — add trail storage and getter
- `frontend/src/components/Globe/Globe.jsx` — render plane trail LineLayer when plane selected
- `frontend/src/utils/constants.js` — `TRAIL_MAX_POINTS = 20`

## Verification

- [ ] Trail renders when plane is selected
- [ ] Trail shows last 20 positions as a line
- [ ] Trail updates as new positions come in via WebSocket
- [ ] Trail disappears when plane is deselected
- [ ] No performance impact when no plane selected
