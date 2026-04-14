# Phase 4.5 — Task 4: Wire Filtered Data to Globe Layers

**Agent:** GLM 5.1 (frontend)
**Related overview:** `PHASE4_5_OVERVIEW.md`
**Prerequisites:** Tasks 2 and 3 must be complete first

---

## Objective

Update `Globe.jsx` to receive filtered data from the hooks instead of raw data. The layer configurations remain the same — only the data source changes from raw to filtered.

---

## Changes Required

### 1. Update `Globe.jsx` Imports and Hook Usage

Change from:
```jsx
const { planes, addPlane, addPlanes, removePlane } = usePlanes()
const { ships, addShip, addShips, removeShip } = useShips()
```

To:
```jsx
const { filteredPlanes, planes, addPlane, addPlanes, removePlane } = usePlanes()
const { filteredShips, ships, addShip, addShips, removeShip } = useShips()
const { filteredEvents, events, addEvent, addEvents } = useEvents()
const { filteredConflicts, conflicts, addConflict, addConflicts } = useConflicts()
```

### 2. Pass Filtered Data to Layers

Change layer data props from raw to filtered:

**Plane layer:**
```jsx
// Before
data: planes

// After
data: filteredPlanes
```

**Ship layer:**
```jsx
// Before
data: ships

// After
data: filteredShips
```

**Events layer:**
```jsx
// Before
data: events

// After
data: filteredEvents
```

**Conflicts layer:**
```jsx
// Before
data: conflicts

// After
data: filteredConflicts
```

### 3. Keep Stats Display

The globe info bar shows raw counts for debugging. Keep these using raw data:
```jsx
<span>Planes: {planes.length}</span>
<span>Ships: {ships.length}</span>
<span>Events: {events.length}</span>
<span>Conflicts: {conflicts.length}</span>
```

This way users see both filtered count (on globe) and total count (in bar) — useful to know how many are being hidden by filters.

---

## What NOT to Change

- Layer configurations (`IconLayer`, `ScatterplotLayer`, `HeatmapLayer` settings) should remain exactly as they are
- The `layers` prop (which controls which layers are visible) still works independently
- WebSocket message handlers still update raw data — filtering happens on the derived `filtered*` data
- No changes to `getPosition`, `getIcon`, `getFillColor`, `getWeight`, or any other layer property

---

## Globe.jsx Prop Changes

`Globe.jsx` will need to receive the filtered data from hooks internally. Since hooks are called inside Globe, no prop drilling changes are needed for the filter data itself.

However, if `Globe.jsx` is called from `App.jsx`, the `layers` prop still comes from App state. No changes needed to the `layers` prop interface.

---

## Filter Count Display (Optional Enhancement)

Add a small indicator on each layer in the sidebar showing how many items are hidden by filters:

```
✈️ Aircraft (1,247 / 10,384)  [toggle]
```

This would require passing raw + filtered counts to the Sidebar. Consider adding `planeCount` and `filteredPlaneCount` to the filter hook return if desired.

---

## Acceptance Criteria

- [ ] Globe renders using filtered data (not raw data)
- [ ] Globe info bar still shows raw total counts
- [ ] All four layers receive their filtered data correctly
- [ ] No regression in layer rendering (icons still appear, colors correct)
- [ ] WebSocket updates still flow through to filtered data
- [ ] Filters apply immediately without page reload
- [ ] Layer toggle on/off still works independently of filters
- [ ] Commit message: `Phase 4.5 Task 4: Wire filtered data from hooks into Globe layers`
