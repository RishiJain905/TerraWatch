# Phase 5 — Task 8: Stale Thresholds + Freshness Indicators

## Context

Read `backend/app/config.py` and `frontend/src/components/Sidebar/Sidebar.jsx` + `frontend/src/components/Sidebar/Sidebar.css` first.

## UI / UX baseline (Gotham — read before implementing)

Freshness indicators live in the **sidebar command panel**, not as random colored pills floating over the map.

- **Typography & color:** Reuse patterns from `.sidebar-header-meta`, `.meta-dot`, `.footer-pulse`, and `.ws-status` in `Sidebar.css` — mono / caps micro-labels (`9px`–`10px`, `letter-spacing`), **`--accent-ok`** for live, **`--accent-warn`** for stale / degraded, **`--text-2`** for idle copy.
- **Structure:** Prefer a **single row per layer** (or a compact sub-row inside `.layer-item`) so the layer list does not double in height — align with `.layer-label-block` / `.layer-count` hierarchy.
- **WebSocket status:** The globe already exposes Live / Reconnecting in `.globe-info .ws-status`. Freshness is **data-age per layer**, not duplicate socket text — differentiate copy (“Live feed” vs “Last update 2m ago”).
- **Motion:** Pulse animations already exist (`metaPulse`, `footerPulse`, `wsPulse`) — reuse timing/easing for consistency; respect global `prefers-reduced-motion`.

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
- **"Live"** with a pulsing dot (reuse `.meta-dot` / `.footer-pulse` visual language) if last update < threshold T1 (e.g. 30s)
- **"Xm ago"** mono tabular if recent but not “live”
- **"Stale"** or **"No data"** with `--accent-warn` emphasis if age exceeds configured stale seconds for that layer

## Backend API

No new endpoints needed — staleness is handled in SQLite queries. But ensure the frontend's WebSocket heartbeat connection status is also reflected (already in `Globe.jsx` `.ws-status`).

## Files to Update

- `backend/app/config.py` — add stale threshold env vars
- `backend/app/core/database.py` — use config values
- `backend/app/tasks/schedulers.py` — use config values for stale cleanup intervals (if applicable)
- `frontend/src/hooks/usePlanes.js` — track lastUpdated
- `frontend/src/hooks/useShips.js` — track lastUpdated
- `frontend/src/hooks/useEvents.js` — track lastUpdated
- `frontend/src/hooks/useConflicts.js` — track lastUpdated
- `frontend/src/components/Sidebar/Sidebar.jsx` — display freshness per layer
- `frontend/src/components/Sidebar/Sidebar.css` — any new sub-row styles (reuse existing variables; avoid introducing non-token oranges)
- `docs/ENVIRONMENT.md` — document new env vars

## Verification

- [ ] `STALE_PLANE_SECONDS`, `STALE_SHIP_SECONDS`, `STALE_EVENT_SECONDS`, `STALE_CONFLICT_SECONDS` env vars work
- [ ] Freshness indicator shows "Live" for active layers (Gotham pulse styling)
- [ ] Freshness indicator shows relative age after data received
- [ ] Defaults work if env vars not set
- [ ] Sidebar shows status for all 4 layers without breaking the existing layer-card layout
