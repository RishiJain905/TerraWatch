# Phase 3 — Task 7 Complete: M2.7 Integration Test

**Agent:** M2.7 (Coordinator)
**Date:** 2026-04-11
**Status:** COMPLETE ✓

---

## What Was Implemented

Created the Phase 3 integration test suite (`test_ship_integration.py`) and the Phase 3 completion summary (`PHASE3_COMPLETE.md`). All tests pass, Phase 2 plane functionality is unaffected (no regression).

---

## Files Created

| File | Description |
|------|-------------|
| `backend/tests/test_ship_integration.py` | Phase 3 integration test suite — 10 tests |
| `docs/phases/phase3/PHASE3_COMPLETE.md` | Phase 3 completion summary document |

---

## Tests Added — 10 Total

All tests in `backend/tests/test_ship_integration.py`:

| Test | Description | Status |
|------|-------------|--------|
| `test_health_endpoint_returns_healthy` | `GET /health` → 200 `{"status":"healthy"}` | ✓ |
| `test_root_endpoint_returns_api_info` | `GET /` → name/version/status | ✓ |
| `test_ship_api_health` | `GET /api/ships` → 200 + list | ✓ |
| `test_ship_count_endpoint` | `GET /api/ships/count` → `{"count": N}` | ✓ |
| `test_ship_detail_endpoint_found` | `GET /api/ships/{mmsi}` → ship dict when found | ✓ |
| `test_ship_detail_endpoint_not_found` | `GET /api/ships/{mmsi}` → null when missing | ✓ |
| `test_websocket_accepts_connection_and_receives_heartbeat` | WS connect → immediate heartbeat | ✓ |
| `test_ais_service_fetch_ships_returns_dicts` | Mock Digitraffic → correct ship contract | ✓ |
| `test_ais_service_fetch_ships_empty_on_error` | HTTP error → `[]` | ✓ |
| `test_ship_schema_required_fields` | Insert → REST → all required fields present | ✓ |

---

## Verification Results

### Full backend test suite
```bash
cd backend && .venv/bin/python -m pytest tests/ -v
# → 57 passed in 1.74s
```

### Phase 2 regression
```bash
cd backend && .venv/bin/python -m pytest tests/test_integration.py -v
# → 7 passed (0 failures)
```

### Phase 3 ship tests
```bash
cd backend && .venv/bin/python -m pytest tests/test_ship_integration.py -v
# → 10 passed
```

---

## Key Implementation Notes

### Test pattern mirrors Phase 2
- `IntegrationTestBase` provides isolated temp DB per test
- `FakeAsyncClient` mocks `httpx.AsyncClient` responses
- WebSocket test uses `starlette.testclient.TestClient` with `websocket_connect`

### Bug fixed during test creation
- `upsert_ship()` takes its own write guard internally — tests must use `open_db_connection()` context manager (isolated writer) rather than wrapping in another guard
- Error mock must use `httpx.HTTPError`, not bare `Exception`, to match the `except (httpx.HTTPError, ValueError)` catch block in `fetch_ships()`

### WebSocket test uses heartbeat verification
The `ship_batch` message arrives every 60 seconds from the AIS scheduler. The test verifies the WS connection itself is working by checking for the immediate heartbeat, avoiding a 60+ second test wait. The Phase 3 scheduler broadcasts are verified to work via the broader test suite.

---

## V1 Status

**TerraWatch V1 is complete.** Phase 3 adds ships to the globe on top of the Phase 2 plane foundation:

- Ships: live Digitraffic AIS data (Nordic/Baltic), IconLayer, color by type, click for details
- Planes: live OpenSky Network data, directional icons, click for details
- Both layers share the WebSocket live update pipeline
- All 57 tests passing, 0 failures
