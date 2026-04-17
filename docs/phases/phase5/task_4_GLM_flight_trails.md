# Phase 5 — Task 4: Flight Path Trails

## Context

Read `frontend/src/hooks/usePlanes.js` and `frontend/src/components/Globe/Globe.jsx` first.

## UI / UX baseline (Gotham — read before implementing)

Trails are a **data ink** layer on the globe — they should read as part of the same GEOINT palette as the sidebar and HUD, not as a generic bright red debug line.

- **Aircraft accent:** Use colors aligned with **`--accent-air`** (`#E8B84A` → RGB `[232, 184, 74]`) for trail stroke / glow, possibly with alpha ~`180` for legibility over dark basemaps. Avoid default “pure red” unless it matches an existing intentional plane color system.
- **Typography / constants:** Shared magic numbers (e.g. max trail points) belong next to other app constants; `frontend/src/utils/constants.js` already exists — prefer extending it over scattering literals.
- **Layer order:** In `Globe.jsx`, trails must sit **above** basemap tiles but **below** plane `IconLayer` / ship `IconLayer` so selected vehicle icons remain the top pick target (same stacking discipline as events/conflicts vs icons today).
- **Performance:** Only maintain trail geometry for the **selected** plane (spec below); do not retain full history for the whole fleet.

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
      getColor: [232, 184, 74, 180], // --accent-air aligned
      getWidth: 2,
      pickable: false,
    })
  )
}
```

Or better — render as a `PathLayer` showing the full polyline (verify deck.gl v9 API for `PathLayer` import from `@deck.gl/layers`):

```javascript
new PathLayer({
  id: 'plane-trail-layer',
  data: [{ path: planeTrail.map(p => [p.lon, p.lat]) }],
  getPath: d => d.path,
  getColor: [232, 184, 74, 180],
  getWidth: 2,
})
```

### Trail Color

Use **`--accent-air`-aligned RGBA** (see baseline). If a single path must distinguish selected vs history, keep one accent family rather than introducing a new hue outside the design system.

### Performance

Only store trail for the **selected plane** — not all 10k planes. If no plane is selected, trail array is empty.

## Files to Update

- `frontend/src/hooks/usePlanes.js` — add trail storage and getter
- `frontend/src/components/Globe/Globe.jsx` — render plane trail layer when plane selected; respect deck layer ordering vs icons
- `frontend/src/utils/constants.js` — `TRAIL_MAX_POINTS = 20` (or re-use shared constant name agreed with Task 5)

## Verification

- [ ] Trail renders when plane is selected
- [ ] Trail shows last 20 positions as a line
- [ ] Trail updates as new positions come in via WebSocket
- [ ] Trail disappears when plane is deselected
- [ ] No performance impact when no plane selected
- [ ] Trail color reads as “air” accent, consistent with sidebar / HUD
