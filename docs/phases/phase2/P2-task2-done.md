# Phase 2 — Task 2 Complete

Agent: GPT backend workflow
Completed: 2026-04-10
Branch: Rishi-Ghost

---

## Task Completion Status

| Step | Status | Notes |
|------|--------|-------|
| Review current model/database/service state | ✅ Done | Confirmed repo contract uses `Plane.id` and `timestamp` |
| Resolve data source conflict | ✅ Done | Implemented against OpenSky Network because ADSB Exchange VirtualRadar is deprecated/broken |
| Implement live aircraft fetch service | ✅ Done | `backend/app/services/adsb_service.py` now fetches and normalizes live OpenSky aircraft data |
| Add TDD coverage | ✅ Done | Added `backend/tests/test_adsb_service.py` with 6 async unit tests |
| Local verification | ✅ Done | Tests pass and live fetch returns real aircraft |
| Create completion summary | ✅ Done | This file |

---

## What Was Implemented

### ADS-B service implementation
Updated `backend/app/services/adsb_service.py` to:
- call `https://opensky-network.org/api/states/all`
- normalize OpenSky state vectors into the repo’s existing `Plane` contract
- preserve compatibility with current backend/frontend expectations:
  - `id`
  - `callsign`
  - `lat`
  - `lon`
  - `alt`
  - `heading`
  - `speed`
  - `squawk`
  - `timestamp`
- strip trailing spaces from callsigns
- convert altitude meters → feet
- convert speed m/s → knots
- skip aircraft without valid coordinates
- return `None` from `fetch_plane_details()` when a plane is not found

### Defensive parsing / external feed hardening
Added defensive handling so malformed upstream values do not break the whole fetch:
- safe float parsing for numeric OpenSky fields
- invalid timestamps fall back safely
- unexpected top-level JSON shape returns `[]`
- malformed state rows are skipped instead of crashing the batch

### Tests added
Created:
- `backend/tests/__init__.py`
- `backend/tests/test_adsb_service.py`

Coverage includes:
- successful normalization from OpenSky state vectors
- callsign trimming
- unit conversions
- default handling for missing optional values
- malformed numeric/timestamp handling
- request failure returning an empty list
- unexpected JSON shape returning an empty list
- detail lookup by normalized ICAO24/id

---

## Data Source Resolution

Task 2 spec text still referenced ADSB Exchange, but Task 1 documentation updated the source of truth:
- `docs/DATA_SOURCES.md`
- `docs/phases/phase2/P2-task1-done.md`

Those documents confirm:
- ADSB Exchange VirtualRadar is deprecated/broken
- OpenSky Network is the correct live API for Phase 2

Implementation therefore uses OpenSky Network while preserving the existing TerraWatch model contract.

---

## Repo Contract Decision

No model/schema rename was made in Task 2.

Current repo state already expects:
- `Plane.id` instead of `icao24`
- `timestamp` instead of `last_seen`

This is consistent with:
- backend model definitions
- SQLite schema
- current frontend plane hooks

So OpenSky `icao24` is mapped to `id`, and OpenSky timing values are mapped to `timestamp`.

---

## Verification Performed

### Unit tests
Command run:

`cd backend && ./.venv/bin/python -m unittest discover -s tests -v`

Result:
- 6 tests passed
- 0 failures

### Live fetch verification
Command run:

`cd backend && ./.venv/bin/python - <<'PY' ... PY`

Observed result:
- fetched 11k+ live aircraft from OpenSky
- sample normalized plane dict printed successfully
- `fetch_plane_details()` returned a matching plane id from live data

Sample live output shape:

```python
{
  'id': '39de4f',
  'lat': 48.7254,
  'lon': 2.364,
  'alt': 0,
  'heading': 250.31,
  'callsign': 'TVF32DR',
  'squawk': '',
  'speed': 0.0,
  'timestamp': '2026-04-10T19:11:59+00:00'
}
```

---

## Files Changed

Modified:
- `backend/app/services/adsb_service.py`

Created:
- `backend/tests/__init__.py`
- `backend/tests/test_adsb_service.py`
- `docs/phases/phase2/P2-task2-done.md`

---

## Handoff to Task 3

Task 2 is ready for Task 3.

Backend now provides:
- live normalized plane fetches from OpenSky
- plane detail lookup by id/ICAO24
- basic defensive parsing and test coverage

Next step for Task 3:
- schedule periodic fetches every 30 seconds
- upsert planes into SQLite
- broadcast plane updates over WebSocket
