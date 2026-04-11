# Task 5 Done — FastAPI App Completion + Additional Routes

## Summary

Completed the full Phase 1 Task 5 spec for the TerraWatch backend.

## Implemented

### 1. FastAPI app completion
Updated `backend/app/main.py` to:
- use FastAPI lifespan startup/shutdown
- initialize SQLite on startup with `init_db()`
- close SQLite cleanly on shutdown with `close_db()`
- include all routers
- expose `GET /`
- expose `GET /health`
- keep API docs available at `/docs`
- allow frontend CORS origins for local development

### 2. Database initialization and shutdown
Updated `backend/app/core/database.py` to:
- maintain a shared SQLite connection
- provide `get_db()` for route dependencies
- provide `init_db()`
- provide `close_db()`
- create the required tables:
  - `planes`
  - `ships`
  - `events`
- create the required indexes:
  - `idx_planes_timestamp`
  - `idx_ships_timestamp`
  - `idx_events_date`
  - `idx_events_location`

### 3. Core models
Replaced `backend/app/core/models.py` with the Task 5 model set:
- `Plane`
- `Ship`
- `WorldEvent`
- `ConflictZone`
- `Metadata`
- `WSMessage`

### 4. Service stubs
Created Phase 1 service placeholders in `backend/app/services/`:
- `__init__.py`
- `adsb_service.py`
- `ais_service.py`
- `gdelt_service.py`
- `acled_service.py`

These currently return empty values as required for Phase 1.

### 5. Task scheduler stubs
Created Phase 1 scheduler placeholders in `backend/app/tasks/`:
- `__init__.py`
- `schedulers.py`

These contain empty async refresh loops for future phases.

### 6. Metadata route completion
Updated `backend/app/api/routes/metadata.py` to:
- read counts from SQLite
- read latest timestamps/dates from SQLite
- return dynamic metadata for Phase 1

### 7. Route model alignment
Updated existing route files to use the new Task 5 models:
- `backend/app/api/routes/planes.py`
- `backend/app/api/routes/ships.py`
- `backend/app/api/routes/events.py`

### 8. WebSocket heartbeat confirmation
Updated `backend/app/api/websocket.py` to use the Task 5 `WSMessage` model and verified heartbeat behavior.

## Verification Performed

Ran backend verification with the project virtualenv and confirmed:

- `GET /` returns:
  `{"name":"TerraWatch API","version":"0.1.0","status":"running","docs":"/docs"}`
- `GET /health` returns:
  `{"status":"healthy"}`
- `GET /api/metadata` returns Phase 1 counts of zero on a fresh DB
- `GET /api/planes` returns `[]`
- `GET /api/ships` returns `[]`
- `GET /api/events` returns `[]`
- `GET /docs` responds with HTTP 200
- WebSocket `/ws` connects successfully
- WebSocket heartbeat interval was verified at 10.0 seconds between messages
- Uvicorn startup and shutdown completed cleanly
- Required SQLite indexes were present after initialization

## Files Modified

- `backend/app/main.py`
- `backend/app/core/database.py`
- `backend/app/core/models.py`
- `backend/app/api/routes/metadata.py`
- `backend/app/api/routes/planes.py`
- `backend/app/api/routes/ships.py`
- `backend/app/api/routes/events.py`
- `backend/app/api/websocket.py`

## Files Created

- `backend/app/services/__init__.py`
- `backend/app/services/adsb_service.py`
- `backend/app/services/ais_service.py`
- `backend/app/services/gdelt_service.py`
- `backend/app/services/acled_service.py`
- `backend/app/tasks/__init__.py`
- `backend/app/tasks/schedulers.py`
- `task5-done.md`

## Notes

This completes the Phase 1 backend shell for Task 5 only. The services and schedulers are intentionally stubbed and ready for later phases where live data ingestion is added.
