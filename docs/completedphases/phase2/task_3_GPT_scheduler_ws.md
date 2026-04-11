# Task 3 — Plane Scheduler + WebSocket Broadcast
**Agent:** GPT 5.4 (Backend)
**Dependencies:** Task 2 (adsb_service.py complete)

## Goal

Set up the background scheduler to fetch planes every 30 seconds and broadcast updates via WebSocket.

## Context

- Read `backend/app/main.py` — FastAPI app structure
- Read `backend/app/api/websocket.py` — existing WS code
- Read `backend/app/tasks/schedulers.py` — existing scheduler stub
- Read `backend/app/core/database.py` — DB operations

## Steps

### 1. Review Existing Code

```bash
cat backend/app/api/websocket.py
cat backend/app/tasks/schedulers.py  # if exists
cat backend/app/core/database.py
```

### 2. Implement Database Upsert for Planes

In `backend/app/core/database.py`, add an `upsert_plane` function:

```python
async def upsert_plane(db: aiosqlite.Connection, plane: dict):
    """Insert or update a plane in the database."""
    await db.execute("""
        INSERT INTO planes (icao24, callsign, lat, lon, alt, heading, speed, squawk, last_seen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(icao24) DO UPDATE SET
            callsign = excluded.callsign,
            lat = excluded.lat,
            lon = excluded.lon,
            alt = excluded.alt,
            heading = excluded.heading,
            speed = excluded.speed,
            squawk = excluded.squawk,
            last_seen = excluded.last_seen
    """, (
        plane["icao24"],
        plane.get("callsign"),
        plane["lat"],
        plane["lon"],
        plane.get("alt", 0),
        plane.get("heading", 0),
        plane.get("speed", 0),
        plane.get("squawk"),
        plane.get("last_seen"),
    ))
    await db.commit()
```

Also add `delete_old_planes()` — remove planes not seen in 5 minutes:
```python
async def delete_old_planes(db: aiosqlite.Connection, max_age_minutes: int = 5):
    await db.execute(
        "DELETE FROM planes WHERE last_seen < datetime('now', '-' || ? || ' minutes')",
        (max_age_minutes,)
    )
    await db.commit()
```

### 3. Update init_db() Schema

Ensure `init_db()` creates the planes table if it doesn't exist:

```python
CREATE TABLE IF NOT EXISTS planes (
    icao24 TEXT PRIMARY KEY,
    callsign TEXT,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    alt INTEGER DEFAULT 0,
    heading REAL DEFAULT 0,
    speed REAL DEFAULT 0,
    squawk TEXT,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Also clean up stale planes on startup:
```python
await delete_old_planes(db)
```

### 4. Implement the Plane Scheduler

Create or update `backend/app/tasks/schedulers.py`:

```python
"""
Background schedulers for TerraWatch.
"""
import asyncio
from datetime import datetime, timezone

from app.core.database import get_db, upsert_plane, delete_old_planes
from app.services.adsb_service import fetch_planes

# Track active WebSocket connections
_active_connections: set = []

def register_connection(websocket):
    _active_connections.add(websocket)

def unregister_connection(websocket):
    _active_connections.discard(websocket)

async def broadcast_plane_update(planes: list, action: str = "upsert"):
    """Broadcast plane data to all connected WebSocket clients."""
    if not _active_connections:
        return
    
    message = {
        "type": "plane",
        "action": action,
        "data": planes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    dead = set()
    for ws in _active_connections:
        try:
            await ws.send_json(message)
        except Exception:
            dead.add(ws)
    
    # Clean up dead connections
    _active_connections.difference_update(dead)


async def plane_fetch_loop():
    """
    Background task: fetch planes from ADSB, store in DB, broadcast to WS.
    Runs every 30 seconds.
    """
    while True:
        try:
            planes = await fetch_planes()
            
            async with get_db() as db:
                # Upsert all planes
                for plane in planes:
                    await upsert_plane(db, plane)
                
                # Clean up old planes
                await delete_old_planes(db, max_age_minutes=5)
            
            # Broadcast to WebSocket clients
            await broadcast_plane_update(planes, action="upsert")
            
            print(f"[scheduler] Fetched {len(planes)} planes at {datetime.now(timezone.utc).isoformat()}")
            
        except Exception as e:
            print(f"[scheduler] Error fetching planes: {e}")
        
        await asyncio.sleep(30)


async def start_schedulers():
    """Start all background tasks."""
    asyncio.create_task(plane_fetch_loop())
```

### 5. Wire Scheduler into FastAPI Lifespan

Update `backend/app/main.py`:

```python
from app.tasks.schedulers import start_schedulers, register_connection, unregister_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await start_schedulers()  # Add this
    yield
    # Shutdown
    await close_db()
```

### 6. Update WebSocket Endpoint

Update `backend/app/api/websocket.py` to use register/unregister:

```python
from app.tasks.schedulers import register_connection, unregister_connection

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    register_connection(websocket)
    try:
        while True:
            # Keep connection alive — data comes via broadcast
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        unregister_connection(websocket)
```

### 7. Test the Full Pipeline

```bash
cd backend
python3 -c "
import asyncio
from app.services.adsb_service import fetch_planes
from app.core.database import get_db, upsert_plane, delete_old_planes

async def test():
    planes = await fetch_planes()
    print(f'Fetched {len(planes)} planes')
    
    async with get_db() as db:
        for p in planes[:5]:
            await upsert_plane(db, p)
        print('Upserted 5 planes')
        
    async with get_db() as db:
        await delete_old_planes(db)
        print('Cleanup done')

asyncio.run(test())
"
```

## Output

- `backend/app/core/database.py` — upsert_plane + delete_old_planes
- `backend/app/tasks/schedulers.py` — plane_fetch_loop + broadcast
- `backend/app/main.py` — scheduler wired to lifespan
- `backend/app/api/websocket.py` — connection tracking

## Handoff

After completing, notify M2.7 that backend is ready for integration testing (Task 7).
