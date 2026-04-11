# Phase 3 Task 3 — DONE ✓

Agent: GPT 5.4
Date: 2026-04-11
Status: COMPLETE

---

## What was implemented

Implemented the full ship refresh pipeline for Phase 3:
- AIS ship fetch -> SQLite persistence -> stale cleanup -> WebSocket ship broadcasts -> scheduler startup integration

This mirrors the existing Phase 2 plane scheduler pattern while preserving the current backend contracts.

---

## Files changed

Modified:
- `backend/app/core/database.py`
- `backend/app/api/websocket.py`
- `backend/app/tasks/schedulers.py`
- `backend/tests/test_database_and_scheduler.py`

Created:
- `docs/completedphases/phase3/p3-task3-done.md`

---

## Database changes

Added ship persistence helpers to `backend/app/core/database.py`:
- `upsert_ship(db, ship, commit=True)`
- `upsert_ships(db, ships, commit=True)`
- `delete_old_ships(db, max_age_minutes=10, commit=True)`

Implementation details:
- Added ship column definitions and a batched ship upsert SQL statement
- Reused the same write-guard pattern as planes
- Ships are stored with the existing schema:
  - `id`, `lat`, `lon`, `heading`, `speed`, `name`, `destination`, `ship_type`, `timestamp`
- Stale ship cleanup removes rows older than 10 minutes and returns deleted ship IDs
- `init_db()` now also verifies ship table columns via `_ensure_table_columns(...)`

---

## WebSocket changes

Added ship-specific broadcast helpers to `backend/app/api/websocket.py`:
- `broadcast_ship_update(ship, action="upsert")`
- `broadcast_ship_batch(ships)`

Message formats implemented:

Single ship update/remove:
```json
{
  "type": "ship",
  "action": "upsert" | "remove",
  "data": {...},
  "timestamp": "..."
}
```

Batch ship upsert:
```json
{
  "type": "ship_batch",
  "action": "upsert",
  "data": [...],
  "timestamp": "..."
}
```

Behavior matches the plane broadcast pattern:
- one batch message for upserts
- individual remove messages for stale deletions
- dead WebSocket clients are removed via the existing shared broadcast machinery

---

## Scheduler changes

Updated `backend/app/tasks/schedulers.py` to include real ship scheduling.

Added constants:
- `SHIP_REFRESH_INTERVAL_SECONDS = settings.AIS_REFRESH_SECONDS`
- `SHIP_STALE_AGE_MINUTES = 10`

Added functions:
- `_broadcast_ship_messages(...)`
- `refresh_ships_once()`
- `ships_refresh_loop(interval_seconds=SHIP_REFRESH_INTERVAL_SECONDS)`

`refresh_ships_once()` behavior:
- fetches ships from `fetch_ships()`
- uses `open_db_connection()` for an isolated writer connection
- upserts current ship snapshot
- deletes stale ships older than 10 minutes
- commits on success
- rolls back on any failure
- broadcasts one `ship_batch` for upserts and one `ship/remove` per deleted ID

`ships_refresh_loop()` behavior:
- runs continuously
- logs transient failures
- does not crash the loop unless cancelled

`start_schedulers()` now starts both:
- plane fetch loop
- ship fetch loop

`stop_schedulers()` already handled tracked tasks generically, so it now shuts down both loops cleanly.

---

## Spec reconciliation notes

A few repo/spec mismatches were reconciled during implementation:

1. The live task file is:
   - `docs/completedphases/phase3/task_3_GPT_ship_scheduler_ws.md`
   not `task_3_GPT_ship_scheduler.md`

2. The spec referenced prior summaries under `docs/completedphases/...`, but the live completion artifacts are under `docs/completedphases/phase3/`.
   The live repo files were treated as the source of truth.

3. The spec mentioned `SHIP_REFRESH_INTERVAL_SECONDS`, but the live config already has:
   - `settings.AIS_REFRESH_SECONDS = 60`

   Implementation choice:
   - define `SHIP_REFRESH_INTERVAL_SECONDS` in the scheduler module from `settings.AIS_REFRESH_SECONDS`
   - preserve the existing app config convention instead of inventing a second competing config key

4. The plane scheduler architecture in the repo already had important safety fixes:
   - dedicated DB writer connection
   - rollback on failed write batches
   - batch WebSocket upserts plus individual removes

   The ship scheduler was intentionally built to mirror that proven pattern rather than introducing a new one.

---

## Tests added/updated

Extended `backend/tests/test_database_and_scheduler.py` with ship coverage for:

Database helpers:
- ship upsert helper inserts and updates rows
- stale ship cleanup removes old rows

Scheduler behavior:
- `refresh_ships_once()` persists ships, removes stale rows, and broadcasts ship updates/removes
- `refresh_ships_once()` rolls back on failed write batches
- `refresh_ships_once()` uses a dedicated DB connection instead of shared `get_db()`
- `ships_refresh_loop()` recovers after refresh failures
- `start_schedulers()` starts both plane and ship background tasks

WebSocket behavior:
- `broadcast_ship_update()` sends single ship payloads
- `broadcast_ship_update()` supports remove actions
- `broadcast_ship_batch()` sends one batch payload

---

## Verification

### Targeted scheduler/database test run
Command:
`cd backend && .venv/bin/python -m pytest tests/test_database_and_scheduler.py -v`

Result:
- 21 tests collected
- 21 passed

### Full backend regression run
Command:
`cd backend && .venv/bin/python -m pytest tests -v`

Result:
- 42 tests collected
- 42 passed

### Live backend smoke check
Started backend locally on port 8011 and verified:
- `/health` returned 200
- `/api/ships` returned live ship rows after scheduler startup
- `/api/metadata` showed non-zero `ships_count`

Observed sample results:
- `/api/ships` returned live ship objects
- `/api/metadata` reported `ships_count: 629` at the time of the API check

### Live WebSocket verification
Connected to `/ws` and confirmed:
- heartbeat messages arrived
- a `ship_batch` message arrived from the scheduler
- received ship batch count: `18247`

Important note from live verification:
- the default Python `websockets` client max message size was too small for the full ship batch and closed with code 1009
- reconnecting with `max_size=None` successfully received the full `ship_batch`
- this does not affect browser clients in the intended frontend path, but it is worth noting for Python-based test clients

---

## Outcome

Phase 3 Task 3 is complete:
- ship scheduler is real
- ship data is persisted
- stale ships are cleaned up
- ship updates are broadcast over WebSocket
- scheduler startup/shutdown now includes ships
