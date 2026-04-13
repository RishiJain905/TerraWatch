# P4 Task 6 — GDELT Conflicts Layer Implementation (Complete)

**Status:** Done
**Branch:** Rishi-Ghost
**Date:** 2026-04-13
**Commits:** e3a16e4, ef5be2b, 90d1985, d0f04ed, acde0f0

---

## What Was Done

Replaced the empty ACLED-driven Conflicts heatmap layer with a GDELT-powered violent events filter. Both the Events and Conflicts layers remain fully functional:

- **Events layer** — All GDELT events via ScatterplotLayer (unchanged)
- **Conflicts layer** — Only violent/aggressive GDELT events via HeatmapLayer (new data source)

---

## Changes Made

### Backend

| File | Change |
|------|--------|
| `backend/app/api/routes/conflicts.py` | Rewrote to query the `events` table filtered by violent categories instead of the empty `conflicts` table |
| `backend/app/tasks/schedulers.py` | Added `VIOLENT_GDELT_CATEGORIES` constant; `_gdelt_fetch_and_broadcast()` now also broadcasts violent events as `conflict_batch` |

Violent GDELT categories filtered: `assault`, `fight`, `unconventional_mass_gvc`, `conventional_mass_gvc`, `force_range`, `rioting`

### Frontend

| File | Change |
|------|--------|
| `frontend/src/components/Globe/Globe.jsx` | Updated HeatmapLayer weight from `fatalities` to `Math.abs(tone) + 1`; updated comment |
| `frontend/src/services/api.js` | Added `fetchConflicts()` function |

### Tests

| File | Change |
|------|--------|
| `backend/tests/test_conflict_routes.py` | New file — 4 tests covering violent category filtering, count, empty state, and constant validation |

### Docs

| File | Change |
|------|--------|
| `docs/DATA_SOURCES.md` | Added TerraWatch integration note to ACLED section; updated refresh strategy table |

---

## Test Results

- **114 passed** (including 4 new conflict route tests)
- **3 pre-existing failures** in scheduler task count tests (unrelated to this task — ACLED env vars causing extra task)

---

## Data Flow

```
GDELT CSV → gdelt_service.fetch_events() → upsert_events() + broadcast_event_batch()
                                              ↓
                                    filter violent categories
                                              ↓
                                    broadcast_conflict_batch()
                                              ↓
                              Globe.jsx HeatmapLayer (tone-based weight)
```

---

## What Was NOT Changed

- Events layer (ScatterplotLayer) — untouched, shows all GDELT events
- ACLED scheduler code — kept in codebase for future activation
- Database schema — no migrations needed (queries `events` table)
- WebSocket protocol — same `conflict_batch` message type

---

## Spec Compliance

All requirements from `GDELT_Conflicts_Layer_Implementation.md` (Option A) implemented:
- [x] Frontend filters violent GDELT events into conflicts state
- [x] Both layers remain functional and independent
- [x] Heatmap renders with tone-based weights
- [x] No console errors
- [x] WebSocket updates propagate to both layers
