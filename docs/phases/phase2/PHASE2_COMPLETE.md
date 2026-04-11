# Phase 2 — Live Aircraft Tracking: COMPLETE

**Completed:** 2026-04-10
**Branch:** Rishi-Ghost

## What Was Built

Phase 2 added live ADS-B aircraft tracking end-to-end:

- **ADS-B Data Source:** OpenSky Network API (replaced originally planned ADSB Exchange)
  - Free, no API key, anonymous access
  - ~8,000–12,000 aircraft globally
  - 17-element state vectors with unit conversions (meters→feet, m/s→knots)

- **Backend Pipeline (Tasks 1-4):**
  - `adsb_service.py` — Fetches from OpenSky Network, normalizes to Plane dicts
  - `schedulers.py` — Background scheduler fetching every 30 seconds
  - `database.py` — SQLite with upsert/delete, stale plane cleanup (5 min)
  - `planes.py` — REST routes: GET /api/planes, /api/planes/count, /api/planes/{icao24}
  - `websocket.py` — /ws endpoint with heartbeat (10s), broadcast to all clients

- **Frontend Pipeline (Tasks 5-6):**
  - `Globe.jsx` — deck.gl GlobeView with TileLayer basemap + IconLayer for planes
  - `planeIcons.js` — SVG-based directional aircraft icons, color-coded by altitude (3 pre-cached variants)
  - `usePlanes.js` — React state hook accumulating planes from WebSocket upserts
  - `useWebSocket.js` — Auto-reconnecting WebSocket hook
  - `PlaneInfoPanel.jsx` — Slide-in panel with glassmorphism styling showing plane details

- **Integration Test (Task 7):**
  - 7 automated integration tests (health, routes, WebSocket, ADS-B service)
  - End-to-end browser verification via Playwright

## Data Flow

```
OpenSky Network API
  → adsb_service.fetch_planes() [every 30s]
  → SQLite planes table (upsert)
  → WebSocket broadcast (all connected clients)
  → usePlanes hook (frontend state)
  → IconLayer on deck.gl globe
```

## Key Technical Decisions

1. **OpenSky Network** over ADSB Exchange — ADSB Exchange VirtualRadar endpoint was dead; OpenSky is free, reliable, no key required
2. **`id` field** as primary key (not `icao24` per original spec) — reconciled during implementation
3. **`timestamp` field** (not `last_seen`) — reconciled during implementation
4. **deck.gl v9** — `{ _GlobeView as GlobeView }` from `@deck.gl/core` (not public `GlobeView` export)
5. **SVG-based plane icons** — no external icon assets needed, 3 altitude-band variants pre-cached at module load
6. **Hybrid plane feed (REST + WebSocket)** — frontend fetches `GET /api/planes` on mount to seed initial state, then receives live updates via batch WebSocket messages

## Bugs Found & Fixed During Integration

1. **Vite proxy target** — made configurable via `VITE_PROXY_TARGET` / `VITE_WS_PROXY_TARGET` env vars (defaults to localhost for local dev, Docker compose sets `backend:8000`)
2. **Frontend starts with 0 planes** — Fixed: usePlanes hook now fetches `GET /api/planes` on mount, populating the plane map before WS messages arrive
3. **8400 individual WS messages per cycle** — Fixed: added `broadcast_plane_batch()` to send all plane upserts in a single WS message (`plane_batch` type), reducing message volume by ~99.9%
4. **TileLayer "GeoJSON does not have type"** — Fixed: added `renderSubLayers` callback with `BitmapLayer` to properly handle raster PNG tiles instead of default GeoJSON parsing

## Test Results

- **7/7 integration tests passing** (backend/tests/test_integration.py)
- **Backend verified:** 8,000+ planes from OpenSky, REST routes working, WS broadcasting
- **Frontend verified:** Globe renders, WebSocket connects, plane icons appear, legend visible
- **All prior task tests still passing** (test_adsb_service.py, test_plane_routes.py, test_database_and_scheduler.py)

## Files Changed in Phase 2

### Backend
- `app/services/adsb_service.py` — OpenSky Network integration
- `app/tasks/schedulers.py` — 30s plane refresh loop
- `app/api/websocket.py` — WebSocket endpoint with heartbeat
- `app/api/routes/planes.py` — Plane REST routes
- `app/core/models.py` — Plane, WSMessage models
- `app/core/database.py` — SQLite schema, upsert, cleanup, migration
- `app/main.py` — FastAPI app with lifespan, CORS, routers
- `tests/test_adsb_service.py` — 6 ADS-B service tests
- `tests/test_plane_routes.py` — 3 plane route tests
- `tests/test_database_and_scheduler.py` — Database and scheduler tests
- `tests/test_integration.py` — 7 integration tests

### Frontend
- `src/components/Globe/Globe.jsx` — deck.gl globe with TileLayer + IconLayer
- `src/components/Globe/Globe.css` — Globe styling, info bar, legend
- `src/components/PlaneInfoPanel/PlaneInfoPanel.jsx` — Plane detail panel
- `src/components/PlaneInfoPanel/PlaneInfoPanel.css` — Glassmorphism styling
- `src/hooks/usePlanes.js` — Plane state management
- `src/hooks/useWebSocket.js` — WebSocket connection management
- `src/hooks/useShips.js` — Ship hook (placeholder)
- `src/hooks/useEvents.js` — Events hook (placeholder)
- `src/utils/planeIcons.js` — SVG-based plane icon generator with 3 cached altitude-band variants
- `src/App.jsx` — Main app with layer toggles, entity click handling
- `vite.config.js` — Dev proxy config (env-configurable for local dev and Docker)

### Documentation
- `docs/DATA_SOURCES.md` — Updated with OpenSky Network details
- `docs/phases/phase2/PHASE2_OVERVIEW.md` — Phase 2 overview
- `docs/phases/phase2/task_*.md` — Task specs for all 7 tasks
- `docs/phases/phase2/P2-task{1-7}-done.md` — Completion summaries
