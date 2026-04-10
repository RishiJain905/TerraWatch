# Task 5 — FastAPI App Completion + Additional Routes

**Agent:** GPT 5.4
**Phase:** 1
**Sequential Order:** 5 of 7
**Dependencies:** Tasks 1 and 3 (directory structure and backend scaffold must exist)

---

## Task Overview

Complete the FastAPI backend setup by adding:
1. A clean `app/main.py` with all routers properly included
2. All core service files (empty stubs ready for data)
3. The database initialization with proper schema
4. Health check endpoint
5. Graceful startup/shutdown

---

## Steps

### 1. Finalize `backend/app/main.py`

Replace the existing `main.py` with a complete version:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import init_db, close_db
from app.api.routes import planes, ships, events, metadata
from app.api import websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="TerraWatch API",
    description="Real-time GEOINT platform — planes, ships, and world events on a globe",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(metadata.router)
app.include_router(planes.router)
app.include_router(ships.router)
app.include_router(events.router)
app.include_router(websocket.router)


@app.get("/")
async def root():
    return {
        "name": "TerraWatch API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### 2. Update `backend/app/core/database.py`

```python
import aiosqlite
from contextlib import asynccontextmanager

DATABASE_PATH = "./terrawatch.db"

_db_instance = None

async def get_db():
    """Get a database connection."""
    global _db_instance
    if _db_instance is None:
        _db_instance = await aiosqlite.connect(DATABASE_PATH)
        _db_instance.row_factory = aiosqlite.Row
    return _db_instance

async def close_db():
    """Close the database connection on shutdown."""
    global _db_instance
    if _db_instance:
        await _db_instance.close()
        _db_instance = None

async def init_db():
    """Initialize the database with required tables and indexes."""
    db = await get_db()
    
    # Planes table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS planes (
            id TEXT PRIMARY KEY,
            lat REAL,
            lon REAL,
            alt INTEGER DEFAULT 0,
            heading REAL DEFAULT 0,
            callsign TEXT DEFAULT '',
            squawk TEXT DEFAULT '',
            speed REAL DEFAULT 0,
            timestamp TEXT
        )
    """)
    
    # Ships table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS ships (
            id TEXT PRIMARY KEY,
            lat REAL,
            lon REAL,
            heading REAL DEFAULT 0,
            speed REAL DEFAULT 0,
            name TEXT DEFAULT '',
            destination TEXT DEFAULT '',
            ship_type TEXT DEFAULT '',
            timestamp TEXT
        )
    """)
    
    # Events table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            date TEXT,
            lat REAL,
            lon REAL,
            event_text TEXT,
            tone REAL DEFAULT 0,
            category TEXT DEFAULT '',
            source_url TEXT DEFAULT ''
        )
    """)
    
    # Indexes for performance
    await db.execute("CREATE INDEX IF NOT EXISTS idx_planes_timestamp ON planes(timestamp)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_ships_timestamp ON ships(timestamp)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON events(date)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_events_location ON events(lat, lon)")
    
    await db.commit()
```

### 3. Create `backend/app/core/models.py`

```python
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


class Plane(BaseModel):
    id: str
    lat: float
    lon: float
    alt: int = 0
    heading: float = 0
    callsign: str = ""
    squawk: str = ""
    speed: float = 0
    timestamp: Optional[str] = None


class Ship(BaseModel):
    id: str
    lat: float
    lon: float
    heading: float = 0
    speed: float = 0
    name: str = ""
    destination: str = ""
    ship_type: str = ""
    timestamp: Optional[str] = None


class WorldEvent(BaseModel):
    id: str
    date: str
    lat: float
    lon: float
    event_text: str
    tone: float = 0
    category: str = ""
    source_url: str = ""


class ConflictZone(BaseModel):
    id: str
    date: str
    lat: float
    lon: float
    event_type: str
    fatalities: int = 0
    region: str = ""
    country: str = ""


class Metadata(BaseModel):
    status: str
    phase: int = 1
    planes_count: int = 0
    ships_count: int = 0
    events_count: int = 0
    last_planes_update: Optional[str] = None
    last_ships_update: Optional[str] = None
    last_events_update: Optional[str] = None


class WSMessage(BaseModel):
    type: Literal["plane", "ship", "event", "heartbeat", "metadata"]
    data: dict
    timestamp: str = ""
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow().isoformat()
        super().__init__(**data)
```

### 4. Create Empty Service Stubs

Create `backend/app/services/__init__.py`:
```python
# Services will be implemented in later phases
```

Create `backend/app/services/adsb_service.py`:
```python
"""
ADSB Service — fetches live plane data from ADSB Exchange.
To be implemented in Phase 2.
"""
from typing import List

async def fetch_planes() -> List[dict]:
    """Fetch live plane positions. Returns empty list in Phase 1."""
    return []

async def fetch_plane_details(icao24: str) -> dict:
    """Fetch details for a specific plane. Returns empty dict in Phase 1."""
    return {}
```

Create `backend/app/services/ais_service.py`:
```python
"""
AIS Service — fetches live ship data from AIS providers.
To be implemented in Phase 3.
"""
from typing import List

async def fetch_ships() -> List[dict]:
    """Fetch live ship positions. Returns empty list in Phase 1."""
    return []

async def fetch_ship_details(mmsi: str) -> dict:
    """Fetch details for a specific ship. Returns empty dict in Phase 1."""
    return {}
```

Create `backend/app/services/gdelt_service.py`:
```python
"""
GDELT Service — fetches world events from GDELT Project.
To be implemented in Phase 4.
"""
from typing import List

async def fetch_events() -> List[dict]:
    """Fetch recent world events. Returns empty list in Phase 1."""
    return []
```

Create `backend/app/services/acled_service.py`:
```python
"""
ACLED Service — fetches conflict data.
To be implemented in Phase 4.
"""
from typing import List

async def fetch_conflicts() -> List[dict]:
    """Fetch conflict data. Returns empty list in Phase 1."""
    return []
```

### 5. Create `backend/app/tasks/__init__.py`

Empty file.

Create `backend/app/tasks/schedulers.py`:
```python
"""
Background schedulers for periodic data refresh.
To be implemented in later phases.
"""
import asyncio
from datetime import datetime


async def planes_refresh_loop():
    """
    Periodically refreshes plane data from ADSB.
    Empty in Phase 1 — no data fetching yet.
    """
    while True:
        # Will be implemented in Phase 2
        await asyncio.sleep(30)


async def ships_refresh_loop():
    """
    Periodically refreshes ship data from AIS.
    Empty in Phase 1 — no data fetching yet.
    """
    while True:
        # Will be implemented in Phase 3
        await asyncio.sleep(60)


async def events_refresh_loop():
    """
    Periodically refreshes world events.
    Empty in Phase 1 — no data fetching yet.
    """
    while True:
        # Will be implemented in Phase 4
        await asyncio.sleep(3600)
```

### 6. Update `backend/app/api/routes/metadata.py`

```python
from fastapi import APIRouter, Depends
import aiosqlite
from app.core.database import get_db
from app.core.models import Metadata

router = APIRouter(prefix="/api/metadata", tags=["metadata"])


@router.get("", response_model=Metadata)
async def metadata(db: aiosqlite.Connection = Depends(get_db)):
    """Return system metadata and counts."""
    # Get counts
    planes_cur = await db.execute("SELECT COUNT(*) as c FROM planes")
    ships_cur = await db.execute("SELECT COUNT(*) as c FROM ships")
    events_cur = await db.execute("SELECT COUNT(*) as c FROM events")
    
    planes_count = (await planes_cur.fetchone())[0]
    ships_count = (await ships_cur.fetchone())[0]
    events_count = (await events_cur.fetchone())[0]
    
    # Get last update times
    last_plane = await db.execute(
        "SELECT timestamp FROM planes ORDER BY timestamp DESC LIMIT 1"
    )
    last_ship = await db.execute(
        "SELECT timestamp FROM ships ORDER BY timestamp DESC LIMIT 1"
    )
    last_event = await db.execute(
        "SELECT date FROM events ORDER BY date DESC LIMIT 1"
    )
    
    last_plane_row = await last_plane.fetchone()
    last_ship_row = await last_ship.fetchone()
    last_event_row = await last_event.fetchone()
    
    return Metadata(
        status="ok",
        phase=1,
        planes_count=planes_count,
        ships_count=ships_count,
        events_count=events_count,
        last_planes_update=last_plane_row[0] if last_plane_row else None,
        last_ships_update=last_ship_row[0] if last_ship_row else None,
        last_events_update=last_event_row[0] if last_event_row else None,
    )
```

---

## Verification

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Test all endpoints:
- `GET /` → `{"name": "TerraWatch API", "version": "0.1.0", "status": "running", "docs": "/docs"}`
- `GET /health` → `{"status": "healthy"}`
- `GET /api/metadata` → Returns phase 1, counts of 0
- `GET /api/planes` → `[]`
- `GET /api/ships` → `[]`
- `GET /api/events` → `[]`
- WebSocket `/ws` → connects and sends heartbeats

---

## Acceptance Criteria

1. All 7 REST endpoints return correct responses
2. WebSocket sends heartbeat every 10 seconds
3. Database initializes with correct schema and indexes on startup
4. All imports resolve — no missing module errors
5. Graceful shutdown when uvicorn is stopped
6. API docs available at `/docs`

---

## Commit Message

```
Phase 1 Task 5: FastAPI app completion + service stubs
```
