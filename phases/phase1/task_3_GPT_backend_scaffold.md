# Task 3 — FastAPI Backend Scaffold

**Agent:** GPT 5.4
**Phase:** 1
**Sequential Order:** 3 of 7
**Dependency:** Task 1 (directory structure and Docker base must exist)

---

## Task Overview

Set up the complete backend project scaffold so that `python -m uvicorn app.main:app --reload` works and starts on port 8000 with the app responding to basic routes.

---

## Steps

### 1. Verify Directory Structure

Before starting, verify these directories exist from Task 1:
- `backend/app/`
- `backend/app/api/routes/`
- `backend/app/core/`
- `backend/app/services/`
- `backend/app/tasks/`

### 2. Create `backend/app/__init__.py`

Empty file.

### 3. Create `backend/app/config.py`

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PYTHON_ENV: str = os.getenv("PYTHON_ENV", "development")
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Data refresh intervals (ms)
    ADSB_REFRESH_SECONDS: int = 30
    AIS_REFRESH_SECONDS: int = 60
    
    # Database
    DATABASE_URL: str = "sqlite:///./terrawatch.db"

settings = Settings()
```

### 4. Create `backend/app/core/__init__.py`

Empty file.

### 5. Create `backend/app/core/database.py`

```python
import aiosqlite
from app.config import settings

DATABASE_PATH = "./terrawatch.db"

async def get_db():
    """Dependency that provides a database connection."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db

async def init_db():
    """Initialize the database with required tables."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS planes (
                id TEXT PRIMARY KEY,
                lat REAL,
                lon REAL,
                alt INTEGER,
                heading REAL,
                callsign TEXT,
                squawk TEXT,
                speed REAL,
                timestamp TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ships (
                id TEXT PRIMARY KEY,
                lat REAL,
                lon REAL,
                heading REAL,
                speed REAL,
                name TEXT,
                destination TEXT,
                ship_type TEXT,
                timestamp TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                date TEXT,
                lat REAL,
                lon REAL,
                event_text TEXT,
                tone REAL,
                category TEXT,
                source_url TEXT
            )
        """)
        await db.commit()
```

### 6. Create `backend/app/core/models.py`

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PlaneBase(BaseModel):
    id: str
    lat: float
    lon: float
    alt: int = 0
    heading: float = 0
    callsign: Optional[str] = ""
    squawk: Optional[str] = ""
    speed: float = 0

class PlaneResponse(PlaneBase):
    timestamp: str

class ShipBase(BaseModel):
    id: str
    lat: float
    lon: float
    heading: float = 0
    speed: float = 0
    name: str = ""
    destination: str = ""
    ship_type: str = ""

class ShipResponse(ShipBase):
    timestamp: str

class EventBase(BaseModel):
    id: str
    lat: float
    lon: float
    event_text: str
    tone: float = 0
    category: str = ""
    source_url: str = ""

class EventResponse(EventBase):
    date: str

class MetadataResponse(BaseModel):
    status: str
    phase: int
    planes_count: int = 0
    ships_count: int = 0
    last_planes_update: Optional[str] = None
    last_ships_update: Optional[str] = None

class WSMessage(BaseModel):
    type: str  # "plane", "ship", "event", "heartbeat"
    data: dict
```

### 7. Create `backend/app/api/__init__.py`

Empty file.

### 8. Create `backend/app/api/routes/__init__.py`

Empty file.

### 9. Create `backend/app/api/routes/planes.py`

```python
from fastapi import APIRouter, Depends
import aiosqlite
from app.core.database import get_db
from app.core.models import PlaneResponse

router = APIRouter(prefix="/api/planes", tags=["planes"])

@router.get("", response_model=list[PlaneResponse])
async def get_planes(db: aiosqlite.Connection = Depends(get_db)):
    """Get all active planes from the database."""
    cursor = await db.execute("SELECT * FROM planes")
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]
```

### 10. Create `backend/app/api/routes/ships.py`

```python
from fastapi import APIRouter, Depends
import aiosqlite
from app.core.database import get_db
from app.core.models import ShipResponse

router = APIRouter(prefix="/api/ships", tags=["ships"])

@router.get("", response_model=list[ShipResponse])
async def get_ships(db: aiosqlite.Connection = Depends(get_db)):
    """Get all active ships from the database."""
    cursor = await db.execute("SELECT * FROM ships")
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]
```

### 11. Create `backend/app/api/routes/events.py`

```python
from fastapi import APIRouter, Depends
import aiosqlite
from app.core.database import get_db
from app.core.models import EventResponse

router = APIRouter(prefix="/api/events", tags=["events"])

@router.get("", response_model=list[EventResponse])
async def get_events(db: aiosqlite.Connection = Depends(get_db)):
    """Get all events from the database."""
    cursor = await db.execute("SELECT * FROM events")
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]
```

### 12. Create `backend/app/api/routes/metadata.py`

```python
from fastapi import APIRouter
from app.core.models import MetadataResponse

router = APIRouter(prefix="/api/metadata", tags=["metadata"])

@router.get("", response_model=MetadataResponse)
async def metadata():
    """Return system metadata and status."""
    return MetadataResponse(
        status="ok",
        phase=1,
        planes_count=0,
        ships_count=0
    )
```

### 13. Create `backend/app/api/websocket.py`

```python
from fastapi import APIRouter, WebSocket
import asyncio
import json
from datetime import datetime

router = APIRouter()

connected_clients: list[WebSocket] = []

async def broadcast(message: dict):
    """Broadcast a message to all connected WebSocket clients."""
    for client in connected_clients[:]:
        try:
            await client.send_json(message)
        except Exception:
            connected_clients.remove(client)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections and send periodic heartbeat."""
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        # Send initial heartbeat
        await websocket.send_json({
            "type": "heartbeat",
            "data": {"timestamp": datetime.utcnow().isoformat(), "status": "connected"}
        })
        
        # Keep connection alive with periodic heartbeats
        while True:
            await asyncio.sleep(10)
            await websocket.send_json({
                "type": "heartbeat", 
                "data": {"timestamp": datetime.utcnow().isoformat()}
            })
    except Exception:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
```

### 14. Update `backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db
from app.api.routes import planes, ships, events, metadata
from app.api import websocket

app = FastAPI(
    title="TerraWatch API",
    description="Real-time GEOINT platform API",
    version="0.1.0"
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(planes.router)
app.include_router(ships.router)
app.include_router(events.router)
app.include_router(metadata.router)
app.include_router(websocket.router)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/")
async def root():
    return {"message": "TerraWatch API", "docs": "/docs"}
```

---

## Verification

After completing your task, verify by running:
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then test:
- http://localhost:8000/ returns `{"message": "TerraWatch API", "docs": "/docs"}`
- http://localhost:8000/api/metadata returns `{"status": "ok", "phase": 1, ...}`
- WebSocket at ws://localhost:8000/ws connects and receives heartbeat messages

---

## Acceptance Criteria

1. `python -m uvicorn app.main:app --reload` starts without errors on port 8000
2. `/api/metadata` returns correct JSON with status "ok" and phase 1
3. `/api/planes` returns an empty array `[]`
4. `/api/ships` returns an empty array `[]`
5. WebSocket `/ws` accepts connections and sends heartbeat messages
6. CORS is configured to allow localhost:5173
7. All imports resolve correctly (no missing modules)

---

## Commit Message

```
Phase 1 Task 3: FastAPI backend scaffold
```
