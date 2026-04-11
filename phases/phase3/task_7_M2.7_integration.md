# Phase 3 — Task 7: M2.7 — Integration Test — Live Ship Data

## Context

Tasks 2-6 have ship data flowing end-to-end. This task verifies the full pipeline with integration tests, mirrors the Phase 2 integration test approach.

## Instructions

You are M2.7 (coordinator). Read these files first:
- `docs/ARCHITECTURE.md`
- `docs/phases/phase3/PHASE3_OVERVIEW.md`
- `docs/phases/phase3/P3-task2-done.md`
- `docs/phases/phase3/P3-task3-done.md`
- `docs/phases/phase3/P3-task5-done.md`
- `docs/phases/phase3/P3-task6-done.md`
- `backend/tests/test_integration.py` (Phase 2 integration test — use as template)

## Your Task

### 1. Create `backend/tests/test_ship_integration.py`

Mirror the Phase 2 integration test structure:

```python
# Tests to include:
# 1. test_ship_api_health — GET /api/ships returns 200
# 2. test_ship_count_endpoint — GET /api/ships/count returns {"count": N}
# 3. test_ship_fetch — ais_service.fetch_ships() returns non-empty list
# 4. test_ship_websocket — WS receives ship_batch message within 60s
# 5. test_ship_detail_endpoint — GET /api/ships/{mmsi} returns ship or 404
# 6. test_ship_schema — ships have required fields (id, lat, lon, name, ship_type)
```

### 2. Run existing Phase 2 integration tests

Verify Phase 2 plane functionality is NOT broken:
```bash
cd backend && python -m pytest tests/test_integration.py -v
```

### 3. Run Phase 3 ship tests

```bash
cd backend && python -m pytest tests/test_ship_integration.py -v
```

### 4. Manual browser verification

1. Start backend: `cd backend && python -m uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open http://localhost:5173
4. Verify:
   - Globe renders
   - Ships appear as directional icons on globe
   - Ships are color-coded by type
   - Clicking a ship opens the ShipInfoPanel
   - Plane layer still works (no regression)
   - WebSocket connected indicator shows live
   - Console has no errors

### 5. Create `docs/phases/phase3/PHASE3_COMPLETE.md`

Document:
- What was built
- Data flow (ship path)
- Test results (all tests passing)
- Files changed
- Any bugs found and fixed
- V1 status (planes + ships complete)

## Key Constraints

- All Phase 2 tests must still pass (no regression)
- All Phase 3 tests must pass
- Browser verification must confirm ships + planes work simultaneously
- Integration tests should be automated, not just manual

## Output Files

- `backend/tests/test_ship_integration.py` — create
- `docs/phases/phase3/PHASE3_COMPLETE.md` — create

## Verification

- `cd backend && python -m pytest tests/ -v` → all tests pass
- Browser: ships + planes visible simultaneously on globe
- Browser: ship panel opens on click
- No console errors
