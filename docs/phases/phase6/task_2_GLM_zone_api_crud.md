# Phase 6 — Task 2: Zone CRUD API

## Context

Read first:
- `backend/app/api/routes/planes.py`
- `backend/app/api/routes/ships.py`
- `backend/app/core/database.py`
- `backend/app/core/models.py`

## Goal

Implement REST CRUD for zones with strict validation and stable response contracts.

## Implementation

Create `backend/app/api/routes/zones.py` and register router in `app/main.py`.

Endpoints:
- `GET /api/zones`
- `POST /api/zones`
- `GET /api/zones/{zone_id}`
- `PATCH /api/zones/{zone_id}`
- `DELETE /api/zones/{zone_id}`

### Validation rules

- minimum polygon vertices: 3 unique points
- polygon coordinates must be valid lon/lat ranges
- close polygon server-side if not explicitly closed
- reject malformed JSON polygon payloads
- enforce non-empty `name`

### Behavior

- return `404` for missing zone IDs
- return `422` for invalid payloads
- soft-delete is not required in Phase 6 (hard delete acceptable)

## Files to Create/Update

- Create: `backend/app/api/routes/zones.py`
- Update: `backend/app/main.py`
- Update: `backend/app/core/models.py` (request/response models if needed)
- Update: `backend/app/core/database.py` (route helpers)
- Create: `backend/tests/test_zone_routes.py`

## Verification

- [ ] create zone succeeds and returns normalized polygon
- [ ] list endpoint includes created zone
- [ ] get endpoint returns exact zone
- [ ] patch endpoint updates name/flags/polygon
- [ ] delete endpoint removes zone
- [ ] invalid polygons rejected with clear error
- [ ] route tests pass
