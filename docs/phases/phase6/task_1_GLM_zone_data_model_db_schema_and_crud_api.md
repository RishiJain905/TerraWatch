# Phase 6 — Task 1: Zone Data Model, DB Schema, and CRUD API

## Context

Read first:
- `backend/app/core/models.py`
- `backend/app/core/database.py`
- `backend/app/api/routes/planes.py`
- `backend/app/api/routes/ships.py`
- `backend/app/main.py`
- `docs/ARCHITECTURE.md`

## Goal

Add first-class backend support for zones and alerts, then expose stable `/api/zones` CRUD routes with strict validation.

## Implementation

### Models (`backend/app/core/models.py`)

Add:
- `Zone` model
- `ZoneCreate` / `ZoneUpdate` request models
- `Alert` model

Recommended `Zone` fields:
- `id: str`
- `name: str`
- `polygon: list[list[float]]` (`[lon, lat]` points)
- `active: bool`
- `alert_on_entry: bool`
- `alert_on_exit: bool`
- `created_at`, `updated_at`

Recommended `Alert` fields:
- `id`, `zone_id`, `zone_name`
- `entity_type`, `entity_id`
- `alert_type`, `severity`
- `title`, `message`, `timestamp`
- `acked`, `acked_at`
- `dedup_key`

### Database (`backend/app/core/database.py`)

Add table creation in `init_db()`:
- `zones`
- `alerts`

`zones` table:
- `id TEXT PRIMARY KEY`
- `name TEXT NOT NULL`
- `polygon TEXT NOT NULL` (JSON array)
- `active INTEGER NOT NULL DEFAULT 1`
- `alert_on_entry INTEGER NOT NULL DEFAULT 1`
- `alert_on_exit INTEGER NOT NULL DEFAULT 1`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

`alerts` table:
- `id TEXT PRIMARY KEY`
- `zone_id TEXT NOT NULL`
- `zone_name TEXT NOT NULL`
- `entity_type TEXT NOT NULL`
- `entity_id TEXT NOT NULL`
- `alert_type TEXT NOT NULL`
- `severity TEXT NOT NULL`
- `title TEXT NOT NULL`
- `message TEXT NOT NULL`
- `timestamp TEXT NOT NULL`
- `acked INTEGER NOT NULL DEFAULT 0`
- `acked_at TEXT`
- `dedup_key TEXT NOT NULL`

Indexes:
- `idx_zones_active`
- `idx_alerts_timestamp`
- `idx_alerts_zone`
- `idx_alerts_entity`
- `idx_alerts_ack_state`
- `idx_alerts_dedup_key`

### Zone CRUD API (`backend/app/api/routes/zones.py`)

Create `backend/app/api/routes/zones.py` and register router in `app/main.py`.

Endpoints:
- `GET /api/zones`
- `POST /api/zones`
- `GET /api/zones/{zone_id}`
- `PATCH /api/zones/{zone_id}`
- `DELETE /api/zones/{zone_id}`

Validation rules:
- minimum polygon vertices: 3 unique points
- polygon coordinates must be valid lon/lat ranges
- close polygon server-side if not explicitly closed
- reject malformed JSON polygon payloads
- enforce non-empty `name`

Behavior:
- return `404` for missing zone IDs
- return `422` for invalid payloads
- hard delete is acceptable in Phase 6

### Helpers

Add DB helpers for:
- insert/update/list/get/delete zones
- insert/list/count/ack alerts (schema-ready helpers)

Keep function style aligned with existing plane/ship/event helper patterns.

## Files to Create/Update

- Update: `backend/app/core/models.py`
- Update: `backend/app/core/database.py`
- Create: `backend/app/api/routes/zones.py`
- Update: `backend/app/main.py`
- Update: `backend/tests/test_database_and_scheduler.py` (schema assertions)
- Create: `backend/tests/test_zone_routes.py`

## Verification

- [ ] `init_db()` creates `zones` and `alerts` tables
- [ ] required indexes exist
- [ ] create/list/get/patch/delete zone flow passes
- [ ] create response returns normalized polygon
- [ ] invalid polygons rejected with clear `422` errors
- [ ] zone and alert row round-trip works
- [ ] `python -m pytest backend/tests/test_database_and_scheduler.py -v` passes
- [ ] `python -m pytest backend/tests/test_zone_routes.py -v` passes
