# Phase 5 Task 8 — Stale Thresholds + Freshness Indicators: DONE

## What was shipped

Configurable stale data thresholds via environment variables and per-layer freshness indicators in the sidebar showing LIVE / relative age / STALE / NO DATA status.

## Files changed

| File | Action | Description |
|------|--------|-------------|
| `backend/app/config.py` | UPDATE | Added `STALE_PLANE_SECONDS`, `STALE_SHIP_SECONDS`, `STALE_EVENT_SECONDS`, `STALE_CONFLICT_SECONDS` env-driven settings |
| `backend/app/core/database.py` | UPDATE | Replaced hardcoded defaults with config-derived fallbacks in `delete_old_planes`, `delete_old_ships`, `delete_old_events` |
| `backend/app/tasks/schedulers.py` | UPDATE | Replaced hardcoded `PLANE_STALE_AGE_MINUTES=5` and `SHIP_STALE_AGE_MINUTES=10` with config-derived values |
| `backend/app/api/stale_thresholds.py` | NEW | GET `/api/stale-thresholds` endpoint exposing thresholds as JSON |
| `backend/app/main.py` | UPDATE | Registered `stale_thresholds_router` |
| `backend/tests/test_config_defaults.py` | UPDATE | Added tests for stale threshold defaults and env override |
| `backend/tests/test_integration.py` | UPDATE | Added test for `/api/stale-thresholds` endpoint |
| `frontend/src/hooks/useStaleThresholds.js` | NEW | Hook fetching `/api/stale-thresholds` with fallback defaults |
| `frontend/src/hooks/usePlanes.js` | UPDATE | Added `lastUpdated` state, set on data arrival, exposed in return |
| `frontend/src/hooks/useShips.js` | UPDATE | Added `lastUpdated` state, set on data arrival, exposed in return |
| `frontend/src/hooks/useEvents.js` | UPDATE | Added `lastUpdated` state, set on data arrival, exposed in return |
| `frontend/src/hooks/useConflicts.js` | UPDATE | Added `lastUpdated` state, set on data arrival, exposed in return |
| `frontend/src/components/Globe/Globe.jsx` | UPDATE | Destructures `lastUpdated` from hooks + `useStaleThresholds()`, adds freshness data to `filterHooksRef`, re-triggers sidebar on freshness changes |
| `frontend/src/components/Sidebar/Sidebar.jsx` | UPDATE | Added `FreshnessIndicator` component rendering per-layer freshness in sidebar; reads `lastUpdated`/`staleThreshold` from `filterHook` |
| `frontend/src/components/Sidebar/Sidebar.css` | UPDATE | Added `.layer-freshness`, `.freshness-dot` (live/age/stale/none), `.freshness-text` styles reusing `metaPulse` animation, `--accent-ok`/`--accent-warn` tokens, and `prefers-reduced-motion` support |
| `docs/ENVIRONMENT.md` | NEW | Documents all environment variables including new stale thresholds |

## Implementation details

### Backend — Configurable stale thresholds

- Four new `Settings` class attributes driven by env vars: `STALE_PLANE_SECONDS` (300), `STALE_SHIP_SECONDS` (600), `STALE_EVENT_SECONDS` (3600), `STALE_CONFLICT_SECONDS` (3600)
- `database.py`: `delete_old_planes`, `delete_old_ships`, `delete_old_events` now default to `None` and fall back to `settings.STALE_*_SECONDS` conversions — backward-compatible for explicit callers
- `schedulers.py`: Module-level `PLANE_STALE_AGE_MINUTES` and `SHIP_STALE_AGE_MINUTES` derived from `settings.STALE_*_SECONDS // 60`
- New `/api/stale-thresholds` endpoint returns `{"planes": 300, "ships": 600, "events": 3600, "conflicts": 3600}` for frontend consumption

### Frontend — Freshness indicators

- Each data hook (`usePlanes`, `useShips`, `useEvents`, `useConflicts`) now tracks `lastUpdated` (ms timestamp set via `Date.now()` on every data arrival — initial fetch, single upsert, and batch upsert)
- `useStaleThresholds` hook fetches thresholds from backend API, falls back to defaults on failure
- `FreshnessIndicator` component inside each sidebar layer item computes age and renders:
  - **LIVE** (age < 30s): Pulsing green dot + "LIVE" (`--accent-ok`, reuses `metaPulse` 2.4s timing)
  - **Relative age** (30s ≤ age < threshold): Static dim dot + "Xm ago" (`--text-2`, tabular-nums)
  - **STALE** (age ≥ threshold): Static amber dot + "STALE" (`--accent-warn`)
  - **NO DATA** (null timestamp): Static dim dot + "NO DATA" (`--text-3`)
- 10-second interval re-renders freshness text to keep relative ages accurate
- Freshness data flows through existing `filterHooksRef` getter rather than a separate prop — each layer's filter hook object now includes `lastUpdated` and `staleThreshold`
- CSS uses existing Gotham tokens; `prefers-reduced-motion: reduce` disables pulse animation

## Verification checklist

- [x] `STALE_PLANE_SECONDS`, `STALE_SHIP_SECONDS`, `STALE_EVENT_SECONDS`, `STALE_CONFLICT_SECONDS` env vars drive backend behavior
- [x] Defaults work when env vars are not set (300, 600, 3600, 3600)
- [x] `GET /api/stale-thresholds` returns correct JSON
- [x] Frontend hooks expose `lastUpdated` timestamps
- [x] Sidebar shows "LIVE" with pulsing green dot for active layers
- [x] Sidebar shows relative age ("Xm ago") for recently-updated layers
- [x] Sidebar shows "STALE" / "NO DATA" with amber emphasis for stale layers
- [x] Layer card layout doesn't double in height (freshness inline in `.layer-label-block`)
- [x] `prefers-reduced-motion` respected
- [x] 124 backend tests pass (3 new tests added)
- [x] Frontend build compiles successfully
- [x] `docs/ENVIRONMENT.md` documents all new env vars
