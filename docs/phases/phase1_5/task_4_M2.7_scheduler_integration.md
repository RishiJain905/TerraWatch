# Phase 1.5 — Task 4: Scheduler Integration & Verification

**Agent:** M2.7 (coordinator/integration)
**Related overview:** `PHASE1_5_OVERVIEW.md`

---

## Objective

Wire ADSB.lol and AIS Friends into the existing scheduler pipeline, update the WebSocket broadcast to emit the deduplicated (merged) datasets, and run the full verification suite to confirm Phase 1.5 works end-to-end without regressions.

---

## What Needs to Change

### 1. Scheduler (`backend/app/tasks/schedulers.py`)

The current scheduler fetches from one source per entity type. Update it to:

**Planes:**
```
1. Fetch OpenSky planes (async)
2. Fetch ADSB.lol planes (async, in parallel with step 1)
3. Run filter_stale_planes_open_sky() on OpenSky results
4. Run filter_stale_planes_adsblol() on ADSB.lol results
5. Run deduplicate_planes(open_sky_filtered, adsblol_filtered)
6. Upsert merged set to DB
7. WebSocket broadcast merged set
```

**Ships:**
```
1. Fetch Digitraffic ships (async)
2. Fetch AIS Friends ships (async, in parallel with step 1)
3. Run filter_stale_ships_digitraffic() on Digitraffic results
4. Run filter_stale_ships_ais_friends() on AIS Friends results
5. Run deduplicate_ships(digitraffic_filtered, ais_friends_filtered)
6. Upsert merged set to DB
7. WebSocket broadcast merged set
```

**Important:** Ensure the fetches in steps 1-2 run in parallel using `asyncio.gather` or similar. Do not serialize the API calls.

### 2. WebSocket Broadcast

The WebSocket currently sends `plane_batch` and `ship_batch` messages containing all active entities. After the merge:

- `plane_batch` should contain the **merged, deduplicated** plane set
- `ship_batch` should contain the **merged, deduplicated** ship set
- The message format stays the same (no frontend changes needed)

### 3. Config (`backend/app/config.py`)

Ensure these config values exist:
```python
# ADSB.lol
ADSBLOL_REFRESH_SECONDS: int = 30

# AIS Friends
AIS_FRIENDS_API_KEY: str        # Required — no default
AIS_FRIENDS_REFRESH_SECONDS: int = 60
```

### 4. Environment (`.env.example`)

Ensure these are documented:
```
# ADSB.lol (no API key needed)
ADSBLOL_REFRESH_SECONDS=30

# AIS Friends (free token at https://www.aisfriends.com/)
AIS_FRIENDS_API_KEY=your_token_here
AIS_FRIENDS_REFRESH_SECONDS=60
```

### 5. Docker Changes (`docker/docker-compose.yml`)

If the backend container uses `.env` or environment variables, ensure `AIS_FRIENDS_API_KEY` is passed in. If it's not currently in the compose file, add it as an environment variable reference (the actual value will be provided by the user at runtime).

### 6. Services `__init__.py`

If `backend/app/services/__init__.py` exports services, add:
```python
from .adsblol_service import AdsblolService
from .ais_friends_service import AisFriendsService
```

---

## Verification

Run the following checks in order. Fix any failures before claiming completion.

### A. Backend Unit Tests

```bash
cd backend
python -m pytest tests/ -v
```

**Must pass:**
- All existing Phase 2/3 tests (57/57 or however many exist)
- All new Phase 1.5 tests:
  - `test_adsblol_service.py` — 5 tests
  - `test_ais_friends_service.py` — 5 tests
  - `test_dedup.py` — 14 tests

### B. Backend Integration — Manual Smoke Test

Start the backend locally (with your AIS_FRIENDS_API_KEY in `.env`):

```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

In another terminal:
```bash
# Check plane count (should be >= OpenSky-only count)
curl http://localhost:8000/api/planes/count

# Check ship count (should be >= Digitraffic-only count)
curl http://localhost:8000/api/ships/count
```

Note: If ADSB.lol or AIS Friends APIs are slow/unavailable, the merge should still succeed using the working source only. No crash should occur.

### C. WebSocket Verification

```bash
# Connect to WebSocket and watch for plane_batch and ship_batch messages
wscat -c ws://localhost:8000/ws
```

You should see:
- `plane_batch` messages arriving every ~30s with merged plane data
- `ship_batch` messages arriving every ~60s with merged ship data

### D. Docker Build Test

```bash
cd docker
docker compose build
docker compose up -d
```

Verify:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/planes/count
curl http://localhost:8000/api/ships/count
```

Docker build must succeed and all endpoints must return valid responses.

---

## Completion Criteria

- Scheduler fetches from both sources in parallel for both planes and ships
- Deduplication runs before WebSocket broadcast
- WebSocket emits merged plane and ship sets
- `AIS_FRIENDS_API_KEY` is documented in `.env.example`
- Docker Compose passes build
- Backend health check passes in Docker
- All unit tests pass (existing + new Phase 1.5)
- Manual smoke test confirms more planes/ships than before Phase 1.5

---

## Blockers

If AIS Friends API key is not yet available, the AIS Friends portion of the scheduler should gracefully skip and fall back to Digitraffic-only. The ADSB.lol portion should work without any API key. Do not let missing config block ADSB.lol integration.
