# Phase 5 — Task 8: Stale Thresholds + Freshness Indicators

## Context

Read `backend/app/config.py` and `frontend/src/components/Sidebar/Sidebar.jsx` first.

## Goal

Make data staleness configurable via environment variables, and display per-layer freshness indicators in the UI.

## Backend — Configurable Stale Thresholds

Currently hardcoded in `backend/app/core/database.py`:

```python
# Currently something like:
STALE_PLANE_SECONDS = 300  # 5 minutes
STALE_SHIP_SECONDS = 600   # 10 minutes
```

Make these env-driven:

```python
# backend/app/config.py
import os

STALE_PLANE_SECONDS = int(os.getenv("STALE_PLANE_SECONDS", 300))
STALE_SHIP_SECONDS = int(os.getenv("STALE_SHIP_SECONDS", 600))
STALE_EVENT_SECONDS = int(os.getenv("STALE_EVENT_SECONDS", 3600))  # 1 hour default
STALE_CONFLICT_SECONDS = int(os.getenv("STALE_CONFLICT_SECONDS", 3600))
```

Then use these values in `database.py` instead of hardcoded numbers.

## Frontend — Freshness Indicators

Each hook tracks when data was last received. Display in the Sidebar:

```javascript
// In usePlanes.js
const [lastUpdated, setLastUpdated] = useState(null)

const addPlanes = useCallback((planes) => {
  // ... existing logic
  setLastUpdated(Date.now())
}, [])

// Expose lastUpdated
return { ..., lastUpdated }
```

In Sidebar layer items, show:
- "Live" with a pulsing green dot if last update < 30s ago
- "Xs ago" if last update was recent but < 5min
- "Stale" with a warning icon if last update > threshold

## Backend API

No new endpoints needed — staleness is handled in SQLite queries. But ensure the frontend's WebSocket heartbeat connection status is also reflected.

## Files to Update

- `backend/app/config.py` — add stale threshold env vars
- `backend/app/core/database.py` — use config values
- `backend/app/tasks/schedulers.py` — use config values for stale cleanup intervals
- `frontend/src/hooks/usePlanes.js` — track lastUpdated
- `frontend/src/hooks/useShips.js` — track lastUpdated
- `frontend/src/hooks/useEvents.js` — track lastUpdated
- `frontend/src/hooks/useConflicts.js` — track lastUpdated
- `frontend/src/components/Sidebar/Sidebar.jsx` — display freshness per layer
- `docs/ENVIRONMENT.md` — document new env vars

## Verification

- [ ] STALE_PLANE_SECONDS, STALE_SHIP_SECONDS, STALE_EVENT_SECONDS, STALE_CONFLICT_SECONDS env vars work
- [ ] Freshness indicator shows "Live" for active layers
- [ ] Freshness indicator shows "Xs ago" after data received
- [ ] Defaults work if env vars not set
- [ ] Sidebar shows status for all 4 layers
