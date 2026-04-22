# Phase 5 - Task 14 Done: Aviationstack Route Lines

## Summary
Implemented selection-only flight route enrichment using Aviationstack, exposed through a new backend route endpoint with caching and stable status mapping, and rendered as two dotted globe legs for the selected plane only. Route metadata is now shown in `PlaneInfoPanel`, with calm fallback states when route resolution is unavailable.

## Changes Made

### Backend
- `backend/app/core/models.py`
  - Added `PlaneRouteAirport` and `PlaneRoute` response models.
- `backend/app/config.py`
  - Added `AVIATIONSTACK_ACCESS_KEY`, `AVIATIONSTACK_BASE_URL` (default `https://api.aviationstack.com/v1`), `AVIATIONSTACK_ROUTE_CACHE_TTL_SECONDS`, and `AVIATIONSTACK_AIRPORT_CACHE_TTL_SECONDS`.
- `backend/app/api/routes/planes.py`
  - Added `GET /api/planes/{icao24}/route` (`response_model=PlaneRoute`).
  - Returns `404` when the plane is missing.
  - Uses normalized backend statuses instead of provider-specific errors.
- `backend/app/services/aviationstack_service.py` (new)
  - Implemented best-effort route resolution via Aviationstack flights + airport lookups.
  - Added in-memory TTL caches for route results and airport metadata.
  - Added matching priorities (ICAO24 match, then callsign, then position tie-break).
  - Normalizes outcomes into `ok`, `not_found`, `rate_limited`, `error`.
- `backend/tests/test_aviationstack_service.py` (new)
  - Added service tests for success, not-found, rate-limited, missing-key error, matching priority, direct-coordinate fallback, and cache reuse.
- `backend/tests/test_plane_routes.py`
  - Added API tests for `/route` behavior (404 missing plane, missing-key fallback payload, successful service passthrough).
- `backend/tests/test_config_defaults.py`
  - Added assertions for Aviationstack config defaults.

### Frontend
- `frontend/src/App.jsx`
  - Added separate `selectedPlaneRoute` and `selectedPlaneRouteStatus` state.
  - Added fetch-on-select behavior for `/api/planes/{id}/route`.
  - Added stale-response protection (AbortController + request sequence guard).
  - Clears route state on deselect.
- `frontend/src/components/Globe/routeOverlay.js` (new)
  - Added pure helper to build two selected-plane route legs.
- `frontend/src/components/Globe/routeOverlay.test.js` (new)
  - Added unit tests for route leg helper behavior.
- `frontend/src/components/Globe/Globe.jsx`
  - Added selected-plane route overlay rendering using projected SVG legs.
  - Route overlay renders only when route status is `ok` and airport coordinates exist.
- `frontend/src/components/Globe/Globe.css`
  - Added route overlay styles in the air accent family, with origin/destination differentiated by opacity + dash pattern.
- `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.jsx`
  - Added route rows: Airline, Flight IATA/ICAO, Departure, Arrival, Route status.
  - Added `Loading route...` UI state and explicit fallback formatting.
- `frontend/package.json`
  - Expanded test script to include `routeOverlay.test.js`.

### Docs / Env
- `.env.example`
  - Added Aviationstack environment variables and cache TTL settings.
- `docs/DATA_SOURCES.md`
  - Added Aviationstack route-enrichment data source section.
  - Updated source availability statement to reflect key requirement for this feature.

## Verification
- [x] `python -m pytest tests/test_config_defaults.py tests/test_plane_routes.py tests/test_aviationstack_service.py` (from `backend/`)
  - Result: 16 passed.
- [x] `npm test` (from `frontend/`)
  - Result: 7 tests passed.
- [x] `npm run build` (from `frontend/`)
  - Result: build passed.
  - Note: existing Vite chunk-size warning remains.

## Notes
- Route enrichment remains selection-only; no fleet-wide polling or prefetching was added.
- Missing `AVIATIONSTACK_ACCESS_KEY` returns a stable payload with `status="error"`, matching calm-fallback UI behavior.
- Overlay ordering follows the current SVG-overlay strategy; styling keeps aircraft icon readability with low-noise dotted lines.
