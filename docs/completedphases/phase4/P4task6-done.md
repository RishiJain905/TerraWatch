# P4 Task 6 — GDELT Conflicts Layer Implementation (Complete)

**Status:** Done
**Branch:** Rishi-Ghost
**Date:** 2026-04-13
**Commits:** e3a16e4, ef5be2b, 90d1985, d0f04ed, acde0f0, 2c93fa1, fbc0c22, 81a70e8

---

## What Was Done

Replaced the non-functional ACLED-driven Conflicts heatmap layer with a GDELT-powered violent events filter, then fully removed all ACLED code from the codebase. Both the Events and Conflicts layers remain fully functional:

- **Events layer** — All GDELT events via ScatterplotLayer (unchanged)
- **Conflicts layer** — Only violent/aggressive GDELT events via HeatmapLayer (new data source)

---

## GDELT Verification (Live Test)

- Fetched 1049 events from live GDELT API
- 135 violent events across all 6 violent categories
- 14 distinct categories total, all events have coordinates
- Category mapping working correctly

---

## Changes Made

### Backend

| File | Change |
|------|--------|
| `backend/app/api/routes/conflicts.py` | Rewrote to query the `events` table filtered by violent categories |
| `backend/app/tasks/schedulers.py` | Added violent event broadcast; removed ACLED scheduler entirely |
| `backend/app/core/database.py` | Removed conflicts table, upsert_conflicts, delete_old_conflicts |
| `backend/app/core/models.py` | Removed Conflict and ConflictZone models |
| `backend/app/services/acled_service.py` | **Deleted** |

Violent GDELT categories filtered: `assault`, `fight`, `unconventional_mass_gvc`, `conventional_mass_gvc`, `force_range`, `rioting`

### Frontend

| File | Change |
|------|--------|
| `frontend/src/components/Globe/Globe.jsx` | Updated HeatmapLayer weight from `fatalities` to `Math.abs(tone) + 1` |
| `frontend/src/services/api.js` | Added `fetchConflicts()` function |

### Config

| File | Change |
|------|--------|
| `docker/docker-compose.yml` | Removed ACLED_EMAIL, ACLED_PASSWORD, ACLED_REFRESH_SECONDS |
| `.env.example` | Removed ACLED section |

### Tests

| File | Change |
|------|--------|
| `backend/tests/test_conflict_routes.py` | New file — 4 tests for violent category filtering |
| `backend/tests/test_database_and_scheduler.py` | Fixed 3 pre-existing failures; removed ACLED env var mocks |

### Docs

| File | Change |
|------|--------|
| `docs/DATA_SOURCES.md` | Removed ACLED section; updated refresh table and legal notes |
| `docs/ARCHITECTURE.md` | Removed ACLED from diagram, directory structure, and version plan |
| `README.md` | Updated all ACLED references to GDELT |

---

## Test Results

- **117 passed, 0 failed**

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

## ACLED Cleanup Summary

Fully removed — no ACLED references remain in any Python, config, or active doc files:
- acled_service.py deleted
- ACLED scheduler loop removed
- Conflict/ConflictZone models removed
- Conflicts DB table schema removed (conflicts route now queries events table)
- ACLED env vars removed from docker-compose and .env.example
- All docs updated to reference GDELT

---

## Spec Compliance

All requirements from `GDELT_Conflicts_Layer_Implementation.md` (Option A) implemented:
- [x] Frontend filters violent GDELT events into conflicts state
- [x] Both layers remain functional and independent
- [x] Heatmap renders with tone-based weights
- [x] No console errors
- [x] WebSocket updates propagate to both layers
- [x] ACLED code fully removed after GDELT confirmed working
