# TerraWatch — Architecture

## Overview

TerraWatch is a real-time Geospatial Intelligence (GEOINT) platform that visualizes global activity — aircraft, maritime vessels, and world events — on an interactive 3D globe.

**Core Inspiration:** Palantir Technologies — data fusion, real-time intelligence, decision support.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                     │
│  React + deck.gl (WebGL Globe) ←── WebSocket/REST ──→      │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │  ADSB    │  │   AIS    │  │  GDELT   │                    │
│  │ Service  │  │ Service  │  │ Service  │                    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                    │
│       └────────────┴──────────────┘                           │
│                          ↕                                   │
│              Background Schedulers (asyncio)                  │
│                          ↕                                   │
│              WebSocket Server + REST API                     │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                       SQLite (V1)                            │
│   planes | ships | events | zones | alerts                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | React 18 + Vite | Fast dev server, JSX, massive ecosystem |
| **Globe/Map** | deck.gl + Mapbox GL JS | WebGL-accelerated layers, millions of points |
| **Backend** | Python FastAPI | Async-native, WebSockets built-in, auto-docs |
| **Database** | SQLite (V1), PostgreSQL + TimescaleDB (V2+) | Zero cost to start, rock-solid |
| **Real-time** | FastAPI WebSockets | Native, no extra infrastructure |
| **Containers** | Docker + Docker Compose | One-command deploy |

---

## Directory Structure

```
terrawatch/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry
│   │   ├── config.py               # Environment config
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── planes.py       # /api/planes
│   │   │   │   ├── ships.py        # /api/ships
│   │   │   │   ├── events.py       # /api/events
│   │   │   │   └── metadata.py     # /api/metadata
│   │   │   └── websocket.py        # /ws — live data stream
│   │   ├── core/
│   │   │   ├── database.py         # SQLite connection
│   │   │   └── models.py           # Pydantic models
│   │   ├── services/
│   │   │   ├── adsb_service.py     # Plane data fetching
│   │   │   ├── ais_service.py       # Ship data fetching
│   │   │   ├── gdelt_service.py     # World events
│   │   └── tasks/
│   │       └── schedulers.py        # Background refresh jobs
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── Globe/              # deck.gl globe + layers
│   │   │   ├── Sidebar/            # Layer toggles
│   │   │   ├── Header/             # Top bar
│   │   │   └── common/             # Shared UI components
│   │   ├── hooks/                  # useWebSocket, usePlanes, etc.
│   │   ├── services/               # API client
│   │   └── utils/                  # formatters, constants
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
│
├── docker/
│   ├── docker-compose.yml
│   └── nginx.conf
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATA_SOURCES.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── docs/completedphases/
│       └── phase1/
│           └── (task MD files)
│
├── scripts/
├── .env.example
├── .gitignore
└── README.md
```

---

## Data Models

### Plane
- `id`: str (hex ICAO address)
- `lat`: float
- `lon`: float
- `alt`: int (feet)
- `heading`: float (degrees)
- `callsign`: str
- `squawk`: str
- `speed`: float (knots)
- `timestamp`: datetime

### Ship
- `id`: str (MMSI)
- `lat`: float
- `lon`: float
- `heading`: float
- `speed`: float (knots)
- `name`: str
- `destination`: str
- `ship_type`: str
- `timestamp`: datetime

### Event (GDELT — covers both world events and conflicts)
- `id`: str
- `date`: date
- `lat`: float
- `lon`: float
- `event_text`: str
- `tone`: float
- `category`: str
- `source_url`: str

Conflict events are GDELT entries with violent/aggressive categories (assault, fight, rioting, mass violence, force), displayed on the conflict heatmap.

### Zone (User-defined)
- `id`: str (uuid)
- `name`: str
- `polygon`: list[lat, lon]
- `alert_on_entry`: bool
- `alert_on_exit`: bool
- `alert_types`: list[str]
- `active`: bool

---

## Version Plan

### V1 — Live Globe (Phases 1-3)
- Phase 1: Empty shell — backend + frontend run, Docker works
- Phase 2: Live plane positions on globe
- Phase 3: Ships layer added, V1 polished and shippable

### V2 — Intelligence Layer (Phases 4-5)
- Phase 4: GDELT world events + conflict heatmap (GDELT violent events)
- Phase 5: Performance optimization, UX polish

### V3 — Decision Support (Phases 6-7)
- Phase 6: Zone alerting, event correlation
- Phase 7: Production hardening, deployment

---

## Agent Responsibilities

| Agent | Responsibilities |
|-------|-----------------|
| **GPT 5.4** | Backend — FastAPI app, data services, schedulers, database models, API routes |
| **GLM 5.1** | Frontend — React app, deck.gl globe, all UI components, hooks, visualization layers |
| **MiniMax M2.7** | Coordinator — Architecture, Docker setup, WebSocket wiring, API integration, docs |

---

## Filtering Architecture

Filters are **frontend-only** — all data comes through existing endpoints and WebSocket channels, with filtering applied in the React hooks before data reaches the Globe.

### Filter Pattern

Each data hook (`usePlanes`, `useShips`, `useEvents`, `useConflicts`) maintains:
- **Raw data** — all records received from the backend, never mutated
- **Filter state** — user-configured filter values (altitude range, categories, etc.)
- **Filtered data** — derived via `useMemo`, raw data with filters applied
- **Update function** — `updateFilter(key, value)` to update a single filter

```
usePlanes() ──► filterPlanes() ──► Globe (IconLayer)
useShips() ───► filterShips() ────► Globe (IconLayer)
useEvents() ──► filterEvents() ────► Globe (ScatterplotLayer)
useConflicts() ─► filterConflicts() ──► Globe (HeatmapLayer)
```

### Filtered Data Exposure

Globe.jsx uses filtered data for rendering. Raw data counts are shown in the globe info bar so users can see how many items are hidden by filters.

### Filter UI

Filter controls live in collapsible panels in the Sidebar, one per layer. Filters update in real-time — no "Apply" button. State persists across WebSocket reconnects.
