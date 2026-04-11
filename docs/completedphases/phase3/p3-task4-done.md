# Phase 3 Task 4 — DONE ✓

Agent: GPT 5.3 Codex
Date: 2026-04-11
Status: COMPLETE

---

## What was implemented

Implemented the Phase 3 ship detail API endpoints in `backend/app/api/routes/ships.py` and added route-level regression tests in `backend/tests/test_ship_routes.py`.

### Route implementation
Added the missing ship REST endpoints under `/api/ships`:

- `GET /api/ships`
  - verified the existing collection endpoint still returns ship rows from the `ships` table
- `GET /api/ships/count`
  - returns `{ "count": N }`
- `GET /api/ships/{mmsi}`
  - fetches a single ship by MMSI using the database `id` column
  - strips surrounding whitespace from the path param before lookup
  - returns the matching `Ship` payload when present
  - returns `null` when the ship is missing

### Response contract preserved
The route continues to use the existing `Ship` Pydantic model as the API contract.

The detail endpoint reads directly from SQLite instead of refetching from the upstream AIS provider. This matches the existing backend architecture for collection routes and keeps the endpoint aligned with the persisted Phase 3 ship pipeline:

AIS API -> scheduler -> SQLite -> REST/WebSocket

---

## Files changed

Modified:
- `backend/app/api/routes/ships.py`

Created:
- `backend/tests/test_ship_routes.py`
- `docs/completedphases/phase3/p3-task4-done.md`

---

## Spec reconciliation notes

A few repo/spec mismatches were reconciled during implementation:

1. The prompt referenced `Architecture.md`, `Data_source.md`, and `Phase3_overview.md`, but the live repo files are:
   - `docs/ARCHITECTURE.md`
   - `docs/DATA_SOURCES.md`
   - `docs/completedphases/phase3/PHASE3_OVERVIEW.md`

2. The task spec referenced prior completion summaries under `docs/docs/completedphases/phase3/...`, but the live repo artifacts are under `docs/completedphases/phase3/`.
   The live repo files were treated as the source of truth.

3. The task text had an internal contradiction for missing ships:
   - one section said return `Ship | None`
   - another line said return HTTP 404 if not found
   - the constraints explicitly said `Return None (not an exception) for ships not found`

   Implementation choice:
   - return HTTP 200 with JSON `null` for missing ships

   Why:
   - this matches the explicit constraint in the task
   - this matches the existing plane endpoint pattern in `backend/app/api/routes/planes.py`
   - it preserves the current repo contract instead of introducing a new inconsistent missing-resource behavior

4. The task instructions mentioned `fetch_ship_details` in `ais_service.py`, but for the API route itself the database is the correct source of truth because Tasks 2 and 3 already persist normalized ship data into SQLite. The endpoint therefore queries the `ships` table directly.

---

## Tests added

Created `backend/tests/test_ship_routes.py` with coverage for:

1. `GET /api/ships` returns all active ships from the database
2. `GET /api/ships/count` returns the correct ship count
3. `GET /api/ships/{mmsi}` returns the matching ship by MMSI
4. `GET /api/ships/{mmsi}` strips surrounding whitespace in the path param before lookup
5. `GET /api/ships/{missing_mmsi}` returns `null` for a miss

Testing style mirrors the existing plane route tests:
- `unittest.IsolatedAsyncioTestCase`
- temp SQLite DB per test
- `httpx.ASGITransport(app=app)` for real FastAPI route coverage

---

## Verification

### Targeted ship route tests
Command:
`cd backend && .venv/bin/python -m pytest tests/test_ship_routes.py -v`

Result:
- 5 tests collected
- 5 passed

### Route regression tests
Command:
`cd backend && .venv/bin/python -m pytest tests/test_plane_routes.py tests/test_ship_routes.py tests/test_integration.py -v`

Result:
- 15 tests collected
- 15 passed

### Full backend regression run
Command:
`cd backend && .venv/bin/python -m pytest tests -v`

Result:
- 47 tests collected
- 47 passed

---

## Outcome

Phase 3 Task 4 is complete:
- ship collection route remains working
- ship count endpoint exists
- ship detail endpoint exists
- missing-ship behavior is implemented as `200 + null` to match the repo contract
- route-level regression coverage has been added
