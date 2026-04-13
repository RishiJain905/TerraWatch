# Phase 4.5 — Task 2: Add Filter State to Hooks

**Agent:** GLM 5.1 (frontend)
**Related overview:** `PHASE4_5_OVERVIEW.md`
**Prerequisites:** Task 1 (research) must be complete first

---

## Objective

Add filter state and filtered data output to each hook: `usePlanes`, `useShips`, `useEvents`, `useConflicts`. Each hook should expose both the raw data and the filtered data, plus filter update functions.

---

## Filter State Pattern

Each hook follows this pattern:

```javascript
import { useState, useCallback, useMemo } from 'react'

const DEFAULT_FILTERS = { /* ... */ }

export function usePlanes() {
  const [planes, setPlanes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState(DEFAULT_FILTERS)

  // ... existing fetch logic ...

  // NEW: Filtered planes derived from raw + filters
  const filteredPlanes = useMemo(() => {
    return planes.filter(plane => {
      // altitude
      if (plane.alt < filters.altitudeMin) return false
      if (plane.alt > filters.altitudeMax) return false
      // callsign
      if (filters.callsign && !(plane.callsign || '').toLowerCase().includes(filters.callsign.toLowerCase())) return false
      // speed
      const speed = plane.gs || plane.speed || 0
      if (speed < filters.speedMin) return false
      return true
    })
  }, [planes, filters])

  // NEW: Filter update helper
  const updateFilter = useCallback((key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }, [])

  return {
    planes,         // raw data
    filteredPlanes,  // NEW: filtered data for Globe
    loading, error,
    filters,         // NEW: current filter state
    updateFilter,    // NEW: update a single filter
    fetchPlanes, addPlane, addPlanes, removePlane
  }
}
```

---

## Implementation Per Hook

### 1. `usePlanes.js` — Add Plane Filters

**File:** `frontend/src/hooks/usePlanes.js`

**Default filters:**
```javascript
const DEFAULT_FILTERS = {
  altitudeMin: 0,
  altitudeMax: 50000,
  callsign: '',
  speedMin: 0,
}
```

**Filter logic:**
- `altitudeMin / altitudeMax`: Filter by `plane.alt` (feet). Skip if alt is null/undefined.
- `callsign`: Case-insensitive partial match on `plane.callsign`. Empty string = no filter.
- `speedMin`: Filter by `plane.gs || plane.speed || 0` (knots). Skip if null.

**Return:** Add `filteredPlanes`, `filters`, `updateFilter` to return object.

---

### 2. `useShips.js` — Add Ship Filters

**File:** `frontend/src/hooks/useShips.js`

**Default filters:**
```javascript
const DEFAULT_FILTERS = {
  types: ['cargo', 'tanker', 'passenger', 'fishing', 'other'], // all enabled
  speedMin: 0,
}
```

**Filter logic:**
- `types`: Array of enabled types. Filter by `ship.ship_type`. Empty array = show none.
- `speedMin`: Filter by `ship.sog || ship.speed || 0` (knots). Skip if null.

**Return:** Add `filteredShips`, `filters`, `updateFilter` to return object.

---

### 3. `useEvents.js` — Add Event Filters

**File:** `frontend/src/hooks/useEvents.js`

**Default filters:**
```javascript
const DEFAULT_FILTERS = {
  categories: ['diplomacy', 'statement', 'assault', 'fight', 'mass_gvc', 'force', 'rioting', 'protest'], // all
  toneMin: -10,
  toneMax: 10,
  dateRange: 'all', // '24h', '48h', '7d', 'all'
}
```

**Filter logic:**
- `categories`: Array of enabled categories. Filter by `event.category`. Empty = show none.
- `toneMin / toneMax`: Filter by `event.tone || 0`. Range check.
- `dateRange`: Compute cutoff date from current time. Compare against `event.date` or `event.timestamp`. `'all'` = no filter.

**Date parsing:** Events use GDELT date format. Parse carefully — see `gdelt_service.py` for the date parsing logic already in the backend.

**Return:** Add `filteredEvents`, `filters`, `updateFilter` to return object.

---

### 4. `useConflicts.js` — Add Conflict Filters

**File:** `frontend/src/hooks/useConflicts.js`

**Default filters:**
```javascript
const DEFAULT_FILTERS = {
  intensityMin: 0,
  dateRange: 'all',
}
```

**Filter logic:**
- `intensityMin`: Filter by `Math.abs(conflict.tone || 0) + 1 >= intensityMin`. The weight in the heatmap is `Math.abs(tone) + 1`.
- `dateRange`: Same date logic as events.

**Note:** If `useConflicts.js` doesn't exist yet, create it following the `useEvents.js` pattern but with the conflict-specific filters and data fetching from `/api/conflicts`.

**Return:** Add `filteredConflicts`, `filters`, `updateFilter` to return object.

---

## Important Notes

1. **DO NOT modify the raw data** — `planes`, `ships`, `events`, `conflicts` always contain all data. Only `filteredPlanes`, `filteredShips`, etc. are filtered.

2. **Always return both** — Globe.jsx uses filtered data; the raw data is available if needed for other panels.

3. **Memoize filtering** — use `useMemo` so filtering only runs when data or filters change, not on every render.

4. **WebSocket updates should preserve filter state** — when `addPlane`/`addShip` etc. update the raw data, filters remain unchanged.

5. **Date range filter must handle GDELT date format** — GDELT uses both `YYYYMMDD` and `YYYYMM` formats. See `gdelt_service.py` `_parse_date()` for the parsing logic.

---

## Acceptance Criteria

- [ ] `usePlanes.js` exports `filteredPlanes`, `filters`, `updateFilter`
- [ ] `useShips.js` exports `filteredShips`, `filters`, `updateFilter`
- [ ] `useEvents.js` exports `filteredEvents`, `filters`, `updateFilter`
- [ ] `useConflicts.js` exports `filteredConflicts`, `filters`, `updateFilter`
- [ ] Filters are applied correctly — test each filter independently
- [ ] Raw data is never modified by filters
- [ ] No performance issues with 10k+ planes
- [ ] All filters work with null/missing field values (graceful handling)
- [ ] Commit message: `Phase 4.5 Task 2: Add filter state and filtered data to hooks`
