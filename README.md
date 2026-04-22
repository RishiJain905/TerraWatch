# TerraWatch

> Real-time GEOINT platform — track planes, ships, and world events on a 3D globe

![Phase](https://img.shields.io/badge/Phase-5_Complete-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## What Problem Does TerraWatch Solve?

TerraWatch provides real-time situational awareness of global mobility — who is moving, where, and why. Built for:

- **Logistics** — monitor supply chain routes, port activity, and fleet positions in real time
- **Defense & security** — track air and maritime activity across regions of interest
- **Maritime safety** — monitor vessel traffic, collisions risk, and search and rescue operations
- **OSINT & research** — open-source intelligence on global movement patterns

Unlike expensive enterprise platforms, TerraWatch runs entirely in your browser using free APIs.

**Core Features:**
- Real-time aircraft tracking via ADS-B (OpenSky global + optional ADSB.lol regional augmentation)
- Real-time maritime vessel tracking via AIS (aisstream.io — global coverage)
- World event monitoring (GDELT) — V2 (live)
- Conflict zone visualization (GDELT violent events + conflict heatmap) — V2 (live)
- Solar terminator line, starfield background, atmospheric rim glow — V3 (live)
- Intelligence alerting — V4

**Recent Additions:**
- Plane route enrichment for selected aircraft via Aviationstack
- Map style switching, minimap, keyboard shortcuts, and fly-to/reset controls
- Plane and ship trail overlays, plus selected-plane route lines
- Relative timestamps, clipboard copy buttons, and safer empty-state handling
- Configurable stale-thresholds exposed through the backend API

---

## System Architecture

```mermaid
graph TB
    subgraph Client["Browser (React + deck.gl)"]
        Globe["3D Globe — Terminator + Starfield + Atmosphere<br/>Map style switcher + minimap + trails"]
        Hooks["useWebSocket<br/>usePlanes<br/>useShips<br/>useEvents<br/>useConflicts<br/>useStaleThresholds"]
        Panels["PlaneInfoPanel<br/>ShipInfoPanel<br/>EventInfoPanel<br/>ConflictInfoPanel"]
        Globe <--> Hooks
        Hooks <--> Panels
    end

    subgraph Backend["FastAPI Backend :8000"]
        WS["WebSocket Server /ws"]
        REST["REST API /api/*"]
        ROUTE["Plane route API /api/planes/{icao24}/route"]
        THRESHOLDS["Stale thresholds API /api/stale-thresholds"]
        Config["settings / env vars"]
        Schedulers["Background Schedulers"]
        Services["adsb_service<br/>adsblol_service<br/>aisstream_service<br/>gdelt_service<br/>aviationstack_service"]
        DB[(SQLite<br/>planes<br/>ships<br/>events<br/>conflicts)]
        Schedulers --> Services
        Services --> DB
        WS <--> Schedulers
        REST --> DB
        ROUTE --> Services
        THRESHOLDS --> Config
        Schedulers --> Config
        Services --> Config
    end

    Client -- "HTTP/REST + WebSocket" --> Backend
    Services -->|"OpenSky Network + adsb.lol"| ADSB["ADS-B APIs"]
    Services -->|"aisstream.io WebSocket"| AIS["AIS Stream"]
    Services -->|"GDELT Project"| GDELT["GDELT API"]
    Services -->|"Aviationstack"| AV["Route enrichment"]
```

## Data Flow — Planes (ADS-B)

```mermaid
flowchart LR
    A["OpenSky Network + adsb.lol API
opensky-network.org/api/states/all
api.adsb.lol/v2/point/{lat}/{lon}/{radius}"] --> B["adsb_service.fetch_planes()
AsyncIO + httpx + gzip"]
    B --> C["SQLite planes table
Upsert + stale cleanup (5 min)"]
    C --> D["WebSocket broadcast
plane_batch / plane:remove"]
    D --> E["usePlanes hook
Map-based state"]
    E --> F["deck.gl IconLayer
Directional plane icons
Color-coded by altitude"]
    F --> G["PlaneInfoPanel
Slide-in on click"]
    G --> H["GET /api/planes/{icao24}/route
Aviationstack route enrichment
Selected-plane route overlay"]
```

## Data Flow — Ships (AIS)

```mermaid
flowchart LR
    A1["aisstream.io
WebSocket stream
Real-time vessel positions"] --> B["aisstream_service
Parse + normalize + dedup by MMSI"]
    B --> C["SQLite ships table
Upsert + stale cleanup (10 min)"]
    C --> D["WebSocket broadcast
ship_batch / ship:remove"]
    D --> E["useShips hook
Map-based state"]
    E --> F["deck.gl IconLayer
Directional ship icons
Color-coded by type"]
    F --> G["ShipInfoPanel
Slide-in on click
Mutually exclusive w/ plane panel"]
```

---

## Current Status

| Phase | Name | Status | Key Deliverables |
|-------|------|--------|------------------|
| 1 | Foundation Setup | Complete | FastAPI backend, React + deck.gl frontend, Docker Compose, REST API + WebSocket pipeline |
| 2 | Live Aircraft Tracking | Complete | OpenSky integration + optional ADSB.lol regional augmentation, 30s refresh, directional icons, PlaneInfoPanel |
| 3 | Live Ship Tracking | Complete | aisstream.io WebSocket integration (global coverage), real-time streaming, type-colored icons, ShipInfoPanel |
| 4 | Events & Conflicts | Complete | GDELT world events, conflict heatmap, event/conflict filtering, ACLED integration |
| 5 | Visual Enhancements | Complete | Solar terminator raster, starfield, atmosphere, map style switcher, minimap, trails, keyboard shortcuts, copy UX, route enrichment |
| 6–7 | Alerting & Hardening | Planned | Zone alerting, production hardening |

### Phase 1 — Foundation Setup

- FastAPI backend with WebSocket support
- React + deck.gl frontend with 3D globe
- Docker Compose orchestration with healthchecks
- REST API and WebSocket data pipeline

### Phase 2 — Live Aircraft Tracking

- OpenSky Network integration with optional ADSB.lol regional augmentation
- Background scheduler (30s refresh)
- WebSocket broadcast to all connected clients
- Directional plane icons on globe, color-coded by altitude
- Click-to-inspect PlaneInfoPanel (callsign, altitude, speed, heading)
- OpenSky OAuth2 support for higher rate limits
- Comprehensive backend test suite

### Phase 3 — Live Ship Tracking

- aisstream.io WebSocket integration (global coverage, real-time streaming)
- Multi-source deduplication (digitraffic + aisstream)
- WebSocket broadcast for ship updates (batch + individual)
- Directional ship icons on globe, color-coded by type
- Click-to-inspect ShipInfoPanel (name, MMSI, heading, speed, destination)
- PlaneInfoPanel and ShipInfoPanel are mutually exclusive
- Comprehensive backend test suite

### Phase 4 — Events & Conflicts

- GDELT world event ingestion and persistence
- Conflict heatmap derived from violent event categories
- Event and conflict filtering on the globe
- Live WebSocket broadcast for event and conflict batches

### Phase 5 — Visual Enhancements

- Procedural solar terminator raster, starfield background, and polar caps
- Atmospheric rim glow that tracks globe radius and viewport changes
- Map style switcher, minimap, and globe navigation shortcuts
- Plane and ship trails, plus selected-plane route lines
- Relative timestamps, clipboard copy buttons, and null-safe panel fallbacks
- Stale-threshold endpoint and route enrichment for selected planes

---

## How to Run

### Option 1 — Docker (Recommended)

**Prerequisites:** Docker + Docker Compose v2 installed. Internet required for map tile loading.

```bash
# Clone the repository
git clone https://github.com/RishiJain905/TerraWatch.git
cd TerraWatch

# Copy the environment template and fill in your API keys
cp .env.example docker/.env
# Edit docker/.env — add your aisstream.io key (required for ship tracking)
# OpenSky credentials are optional but recommended for higher rate limits
# ADSB.lol is optional and now uses regional v2 point queries if configured
# See .env.example for all available variables

# Start both backend and frontend
cd docker
docker compose up --build

# Open in browser
open http://localhost:5173
```

> **Important:** Docker Compose v2 is required (`docker compose` with a space). The older `docker-compose` v1 (hyphen) is incompatible with Docker Engine 29+.

Docker will:
- Build the backend Docker image and start it on port **8000**
- Build the frontend Docker image and start it on port **5173**
- Proxy `/api` and `/ws` requests from frontend to backend automatically
- Run a healthcheck against `GET /health` before marking backend ready
- Pass environment variables from `docker/.env` to the backend container

**Required API keys:**
| Key | Where to get | Required? |
|-----|-------------|-----------|
| `AISSTREAM_API_KEY` | https://aisstream.io/ (free) | Yes — ships won't track without it |
| `OPENSKY_CLIENT_ID` + `SECRET` | https://opensky-network.org/ (free) | Optional — increases plane refresh rate limits |

**Verify it works:**
```bash
# Backend health
curl http://localhost:8000/health

# Backend API — plane count
curl http://localhost:8000/api/planes/count

# Backend API — ship count
curl http://localhost:8000/api/ships/count

# All planes
curl http://localhost:8000/api/planes

# All ships
curl http://localhost:8000/api/ships
```

### Option 2 — Local Development

**Prerequisites:** Python 3.12+, Node.js 22+, npm. Dedicated GPU recommended for 10,000+ planes.

#### Backend

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
or 
source .venv/Scripts/activate
# Install dependencies
pip install -r requirements.txt

# Start the API server (runs on port 8000)
python -m uvicorn app.main:app --reload --port 8000
```

#### Frontend (separate terminal)

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (runs on port 5173, proxies /api and /ws to localhost:8000)
npm run dev
```

Then open **http://localhost:5173** in your browser.

> **Note:** The frontend uses `VITE_API_URL` and `VITE_WS_URL` when set; the defaults point at `localhost:8000` for local development. The Vite proxy variables are only needed for Docker or custom host setups.

### Vite Proxy Configuration

The frontend's `vite.config.js` handles cross-origin in development:

```javascript
server: {
  proxy: {
    '/api': { target: 'http://localhost:8000', changeOrigin: true },
    '/ws':  { target: 'ws://localhost:8000', ws: true, changeOrigin: true },
  }
}
```

---

## Running Tests

```bash
cd backend
source .venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_ship_integration.py -v
python -m pytest tests/test_adsb_service.py -v
```

---

## Project Structure

```
TerraWatch/
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── main.py             # App entry, lifespan events, CORS, routers
│   │   ├── config.py           # Environment config (refresh + stale thresholds, route cache)
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── planes.py   # GET /api/planes, /api/planes/count, /api/planes/{icao24}
│   │   │   │   └── ships.py    # GET /api/ships, /api/ships/count, /api/ships/{mmsi}
│   │   │   ├── stale_thresholds.py # GET /api/stale-thresholds
│   │   │   └── websocket.py     # WebSocket /ws — broadcast_plane_batch/ship_batch
│   │   ├── core/
│   │   │   ├── database.py     # SQLite init, upsert/delete helpers, db_write_guard
│   │   │   └── models.py       # Pydantic models: Plane, Ship, Route, WSMessage
│   │   ├── services/
│   │   │   ├── adsb_service.py # OpenSky fetch + normalize
│   │   │   ├── adsblol_service.py # ADSB.lol v2 point fetch + normalize
│   │   │   ├── ais_service.py  # Digitraffic AIS fetch + merge by MMSI
│   │   │   └── aviationstack_service.py # Plane route enrichment + cache
│   │   └── tasks/
│   │       └── schedulers.py    # asyncio scheduler loops for planes + ships
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                    # React 18 application
│   ├── src/
│   │   ├── App.jsx             # Root — selectedPlane/selectedShip state, route loading, mutual exclusion
│   │   ├── components/
│   │   │   ├── Globe/
│   │   │   │   ├── Globe.jsx   # deck.gl GlobeView + terminator + trails + minimap + style switcher
│   │   │   │   ├── Globe.css   # Legend, info bar, atmosphere
│   │   │   │   ├── MapStyleSwitcher.jsx # Basemap style selector
│   │   │   │   ├── Minimap.jsx # Globe inset overview
│   │   │   │   ├── planeTrail.js # Plane trail helpers
│   │   │   │   ├── routeOverlay.js # Selected-plane route helpers
│   │   │   │   ├── shipTrail.js # Ship trail helpers
│   │   │   │   ├── planeTrail.test.js # Plane trail unit tests
│   │   │   │   └── routeOverlay.test.js # Route overlay unit tests
│   │   │   ├── PlaneInfoPanel/ # Slide-in panel for plane details + route actions
│   │   │   └── ShipInfoPanel/  # Slide-in panel for ship details + copy UX
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js # WS connection, heartbeat, reconnect
│   │   │   ├── usePlanes.js    # Plane state + WS plane_batch handling
│   │   │   ├── useShips.js     # Ship state + WS ship_batch handling
│   │   │   └── useStaleThresholds.js # Backend-driven cleanup thresholds
│   │   └── utils/
│   │       ├── constants.js    # Shared numeric limits
│   │       ├── formatters.js   # Display helpers, clipboard fallback, relative time
│   │       ├── planeIcons.js   # Directional SVG plane icons (cached atlas)
│   │       ├── polarCaps.js    # Polar cap overlay data
│   │       ├── shipIcons.js    # Directional SVG ship icons (type-colored)
│   │       ├── starfield.js    # Seeded SVG starfield generator
│   │       └── terminator.js   # Procedural night-side raster
│   ├── package.json
│   ├── vite.config.js          # Vite + React plugin + /api + /ws proxy
│   └── Dockerfile
│
├── docker/
│   └── docker-compose.yml       # Backend + Frontend services, healthchecks
│
├── docs/                       # Architecture docs + phase completion summaries
│   ├── ARCHITECTURE.md
│   ├── DATA_SOURCES.md
│   ├── API.md
│   └── docs/completedphases/
│       ├── phase2/
│       └── phase3/
│
└── README.md
```

---

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | React 18 + Vite | Fast HMR, ESBuild |
| Globe | deck.gl `GlobeView` | WebGL, renders 10,000+ points |
| Map Tile | MapLibre GL JS | Open-source map tiles |
| Backend | Python FastAPI | Async-native, auto OpenAPI docs |
| Database | SQLite | File-based, zero config |
| Real-time | FastAPI WebSockets | Native, no extra deps |
| HTTP Client | `httpx` (async) | Handles gzip decompression |
| Containers | Docker + Docker Compose | One-command startup |

---

## Development

### Agent Workflow

TerraWatch is built by a multi-agent system:

| Agent | Role | Model |
|-------|------|-------|
| **Coordinator** | Architecture, Docker, integration, PRs | MiniMax M2.7 |
| **Backend** | FastAPI routes, data services, schedulers, database | GLM 5.1 |
| **Frontend** | React, deck.gl layers, globe, info panels | GLM 5.1 |

Execution uses **Droid Missions** for structured multi-agent orchestration, or task-file-based dispatch for simpler phases.

### Version Roadmap

| Version | Phases | Features | Status |
|---------|--------|---------|--------|
| **V1** | 1–3 | Live planes + ships on globe | Complete |
| **V2** | 4 | GDELT world events + conflict heatmap | Complete |
| **V3** | 5 | Terminator raster + starfield + atmosphere + map controls + trails + route enrichment | Complete |
| **V4** | 6–7 | Zone alerting + production hardening | Planned |

---

## API Reference

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | API info + version |
| `GET` | `/health` | Health check → `{"status":"healthy"}` |
| `GET` | `/api/planes` | All active planes (stale removed) |
| `GET` | `/api/planes/count` | Plane count → `{"count": N}` |
| `GET` | `/api/planes/{icao24}` | Single plane or `null` |
| `GET` | `/api/planes/{icao24}/route` | Enriched route details for a selected plane |
| `GET` | `/api/ships` | All active ships (stale removed) |
| `GET` | `/api/ships/count` | Ship count → `{"count": N}` |
| `GET` | `/api/ships/{mmsi}` | Single ship or `null` |
| `GET` | `/api/stale-thresholds` | Current backend cleanup thresholds in seconds |

### WebSocket — `/ws`

Connect via `new WebSocket('ws://localhost:8000/ws')`.

**Server → Client messages:**

| Type | Action | Description |
|------|--------|-------------|
| `plane` | `upsert` / `remove` | Single plane update |
| `plane_batch` | `upsert` | All planes in one message |
| `ship` | `upsert` / `remove` | Single ship update |
| `ship_batch` | `upsert` | All ships in one message |
| `heartbeat` | — | Sent every 10s to keep connection alive |

Example ship_batch message:
```json
{
  "type": "ship_batch",
  "action": "upsert",
  "data": [{ "id": "219598000", "lat": 55.77, "lon": 20.85, "heading": 79, "speed": 0.1, "name": "NORD SUPERIOR", "destination": "NL AMS", "ship_type": "tanker", "timestamp": "..." }],
  "timestamp": "2026-04-11T05:00:00Z"
}
```

---

## Data Sources

| Source | Type | Coverage | Auth | Status |
|--------|------|----------|------|--------|
| [OpenSky Network](https://opensky-network.org/api/states/all) | Aircraft (ADS-B) | Global (~12,000+ aircraft) | OAuth2 (optional) | Live |
| [adsb.lol](https://api.adsb.lol/) | Aircraft (ADS-B) | Public regional v2 API, feeder-only full API | None for public API | Live |
| [Aviationstack](https://aviationstack.com/) | Aircraft routes / airport lookups | Selected flight enrichment | API key (optional) | Live |
| [aisstream.io](https://aisstream.io/) | Ships (AIS) | Global (real-time WebSocket) | API Key (free) | Live |
| [GDELT Project](https://www.gdeltproject.org/) | World Events | Global | None | Live |

**Note:** ADS-B and AIS are public broadcast technologies — aircraft and vessels actively transmit their positions. This is established and legal in most jurisdictions.

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — System design, data models, version plan
- [Data Sources](docs/DATA_SOURCES.md) — API details, response formats, field mappings
- [API Reference](docs/API.md) — Full REST + WebSocket API docs
- [Deployment Guide](docs/DEPLOYMENT.md) — Docker, production, environment variables

---

## License

MIT — see [LICENSE](LICENSE) for details.
