# Phase 3 — Task 3: GPT 5.4 — Ship Scheduler + WebSocket Broadcast

## Context

Task 2 implemented `ais_service.py` with real AIS data fetching. This task wires it into the scheduler loop and WebSocket broadcast — mirroring the Phase 2 plane pattern.

## Instructions

You are GPT 5.4 (backend specialist). Read these files first:
- `docs/ARCHITECTURE.md`
- `docs/phases/phase3/PHASE3_OVERVIEW.md`
- `phases/phase3/P3-task1-done.md`
- `phases/phase3/P3-task2-done.md`
- `backend/app/tasks/schedulers.py` (existing — plane scheduler is there, ships is placeholder)
- `backend/app/api/websocket.py` (existing — plane broadcast is there)
- `backend/app/services/ais_service.py` (from Task 2)
- `backend/app/core/database.py` (upsert_ships, ships table)

## Your Task

### 1. Update `backend/app/tasks/schedulers.py`

Replace the placeholder `ships_refresh_loop()` with a real implementation:

```python
async def ships_refresh_loop(interval_seconds: int = 60):
    """Continuously refresh ship data every 60 seconds."""
    while True:
        try:
            ships = await fetch_ships()
            # upsert to DB
            # delete old ships
            # broadcast to WS clients
        except Exception:
            logger.exception("Ship refresh loop failed")
        await asyncio.sleep(interval_seconds)
```

Key requirements:
- Fetch every 60 seconds (configurable via `SHIP_REFRESH_INTERVAL_SECONDS`)
- Upsert ships to SQLite using async write guard
- Delete ships older than 10 minutes (stale threshold: `SHIP_STALE_AGE_MINUTES = 10`)
- Broadcast ship updates via WebSocket (individual removes + batch upserts)
- Do NOT crash on transient failures — log and continue

### 2. Update `backend/app/api/websocket.py`

Add ship-specific broadcast functions:

```python
async def broadcast_ship_update(ship: dict, *, action: str = "upsert"):
    """Broadcast a single ship payload."""
    ...

async def broadcast_ship_batch(ships: list[dict]):
    """Broadcast all ship upserts in a single WS message."""
    ...
```

Use the same pattern as plane broadcasts:
- `type: "ship"` / `type: "ship_batch"`
- `action: "upsert"` / `action: "remove"`
- Single batch message for all upserts (like plane_batch)

### 3. Database helpers (if not already in database.py)

Add if needed:
- `upsert_ship(db, ship, commit=False)` — single ship upsert
- `upsert_ships(db, ships, commit=False)` — batch upsert
- `delete_old_ships(db, max_age_minutes=10, commit=False)` — cleanup stale ships, return deleted IDs

Note: `ships` table already exists in schema. Verify the upsert SQL matches the Ship model fields.

### 4. Wire into `start_schedulers()` and `stop_schedulers()`

In `schedulers.py`:
- `start_schedulers()` should start BOTH plane AND ship loops
- `stop_schedulers()` should cancel BOTH
- Track ship scheduler task similarly to plane task

## Key Constraints

- 60-second refresh for ships (not 30s like planes — AIS updates less frequently)
- Use batch broadcast for efficiency (same fix as Phase 2 plane broadcast)
- Ship stale timeout: 10 minutes (longer than planes — ships move slower)
- Scheduler must survive API downtime — log errors, continue looping

## Output Files

- `backend/app/tasks/schedulers.py` — update placeholder with real ship scheduler
- `backend/app/api/websocket.py` — add ship broadcast functions
- `backend/app/core/database.py` — add ship upsert/delete helpers if needed

## Verification

- Start the backend: `cd backend && python -m uvicorn app.main:app --reload`
- Check logs for ship fetch attempts
- `curl http://localhost:8000/api/ships` should return ships after first fetch
- WebSocket should receive ship_batch messages every 60 seconds
