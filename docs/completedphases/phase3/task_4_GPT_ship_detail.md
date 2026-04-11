# Phase 3 — Task 4: GPT 5.4 — Ship Detail Endpoint

## Context

Tasks 2 and 3 have ship data flowing into the database and WebSocket. This task adds the REST endpoint for fetching a single ship's details by MMSI.

## Instructions

You are GPT 5.4 (backend specialist). Read these files first:
- `docs/ARCHITECTURE.md`
- `docs/docs/completedphases/phase3/PHASE3_OVERVIEW.md`
- `docs/docs/completedphases/phase3/P3-task1-done.md`
- `docs/docs/completedphases/phase3/P3-task2-done.md`
- `backend/app/api/routes/ships.py` (existing stub routes)
- `backend/app/core/models.py` (Ship model)
- `backend/app/services/ais_service.py` (fetch_ship_details function)

## Your Task

Update `backend/app/api/routes/ships.py`:

### 1. GET /api/ships/{mmsi}

```python
@router.get("/{mmsi}", response_model=Ship | None)
async def get_ship(mmsi: str):
    """Get details for a specific ship by MMSI."""
    ...
```

- Fetch ship by `id` (MMSI) from the database
- Return `Ship` model or `None` if not found
- Return HTTP 200 with ship data, or HTTP 404 if not found

### 2. Existing GET /api/ships

The existing endpoint already returns all ships. Verify it works correctly with the new ship data from Task 2/3.

### 3. Add ship count endpoint

```python
@router.get("/count", response_model=dict)
async def get_ship_count():
    """Return total active ship count."""
    ...
```

## Key Constraints

- MMSI is the ship's unique identifier (stored as `id` in the database)
- Return `None` (not an exception) for ships not found
- Use the `Ship` Pydantic model as the response_model

## Output Files

- `backend/app/api/routes/ships.py` — update with real implementation

## Verification

- `curl http://localhost:8000/api/ships/count` should return `{"count": N}`
- `curl http://localhost:8000/api/ships/<valid_mmsi>` should return ship data
- `curl http://localhost:8000/api/ships/invalid_mmsi` should return 404 or null
