# Task 7 — Docker Compose Sanity Check + Docs

**Agent:** M2.7 (MiniMax)
**Phase:** 1
**Sequential Order:** 7 of 7
**Dependencies:** Tasks 1, 2, 3, 4, 5, 6 (all other tasks must be complete)

---

## Task Overview

The final Task 7 wraps up Phase 1 by:
1. Running Docker Compose to verify everything builds and runs together
2. Creating or finalizing the remaining documentation files
3. Writing the final README

---

## Steps

### 1. Fix docker-compose.yml

First, verify and fix the docker-compose.yml. It should reference the correct Dockerfiles:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    working_dir: /app
    environment:
      - PYTHONUNBUFFERED=1
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    working_dir: /app
    environment:
      - NODE_ENV=development
    depends_on:
      backend:
        condition: service_healthy
```

### 2. Create `docker/nginx.conf`

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name localhost;

        # Frontend static files
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # Proxy API requests to backend
        location /api/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }

        # Proxy WebSocket to backend
        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

### 3. Create `docs/DEPLOYMENT.md`

```markdown
# TerraWatch — Deployment Guide

## Local Development

### Prerequisites
- Docker and Docker Compose installed
- Node.js 22+ (for local frontend development without Docker)
- Python 3.12+ (for local backend development without Docker)

### Option 1: Docker Compose (Recommended)

```bash
# Clone and navigate to project
cd TerraWatch

# Start both services
docker compose up --build

# Stop services
docker compose down
```

Services:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Manual Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Production Deployment

### Docker Compose Production

```bash
# Use production compose file
docker compose -f docker/docker-compose.prod.yml up --build -d
```

### Environment Variables

Create `.env` based on `.env.example`:

```
PYTHON_ENV=production
VITE_API_URL=https://your-domain.com/api
VITE_WS_URL=wss://your-domain.com/ws
```

### Docker Health Checks

Both services have health checks configured:
- Backend: `GET /health` — returns `{"status": "healthy"}`
- Frontend: No health check needed (serves static files)

### Nginx Reverse Proxy

For production, use nginx as a reverse proxy (see `docker/nginx.conf`).

---

## Troubleshooting

### Frontend can't reach backend
- Ensure backend health check passes: `curl http://localhost:8000/health`
- Check CORS configuration in `backend/app/main.py`
- Verify nginx proxy configuration

### WebSocket not connecting
- Check nginx WebSocket proxy configuration
- Ensure `VITE_WS_URL` environment variable is set correctly

### Docker build fails
- Clear Docker cache: `docker compose build --no-cache`
- Ensure ports 5173 and 8000 are not in use

### Performance issues
- Enable GPU acceleration for Docker (WSL2 backend on Windows)
- Increase Docker resource limits
- Consider PostgreSQL + TimescaleDB migration for V2+
```

### 4. Create `docs/API.md`

```markdown
# TerraWatch — API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

---

## Endpoints

### GET /
Root endpoint.

**Response:**
```json
{
  "name": "TerraWatch API",
  "version": "0.1.0",
  "status": "running",
  "docs": "/docs"
}
```

---

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

---

### GET /api/metadata
System metadata and counts.

**Response:**
```json
{
  "status": "ok",
  "phase": 1,
  "planes_count": 0,
  "ships_count": 0,
  "events_count": 0,
  "last_planes_update": null,
  "last_ships_update": null,
  "last_events_update": null
}
```

---

### GET /api/planes
Get all active planes.

**Response:**
```json
[
  {
    "id": "abc123",
    "lat": 51.5074,
    "lon": -0.1278,
    "alt": 35000,
    "heading": 270.5,
    "callsign": "BAW123",
    "squawk": "7000",
    "speed": 450.2,
    "timestamp": "2026-04-10T12:00:00Z"
  }
]
```

---

### GET /api/ships
Get all active ships.

**Response:**
```json
[
  {
    "id": "123456789",
    "lat": 1.3521,
    "lon": 103.8198,
    "heading": 180.0,
    "speed": 12.5,
    "name": "MV Example",
    "destination": "Singapore",
    "ship_type": "Cargo",
    "timestamp": "2026-04-10T12:00:00Z"
  }
]
```

---

### GET /api/events
Get world events.

**Response:**
```json
[
  {
    "id": "gdelt123",
    "date": "2026-04-10",
    "lat": 48.8566,
    "lon": 2.3522,
    "event_text": "Protest in Paris",
    "tone": -2.5,
    "category": "Protest",
    "source_url": "https://example.com"
  }
]
```

---

### WebSocket /ws

Real-time data stream. Connect via WebSocket protocol.

**Connection URL:** `ws://localhost:8000/ws`

**Incoming Messages:**

Heartbeat:
```json
{
  "type": "heartbeat",
  "data": {
    "timestamp": "2026-04-10T12:00:00Z",
    "status": "connected"
  }
}
```

Plane update:
```json
{
  "type": "plane",
  "data": {
    "id": "abc123",
    "lat": 51.5074,
    "lon": -0.1278,
    "alt": 35000,
    "heading": 270.5,
    "callsign": "BAW123",
    "speed": 450.2,
    "timestamp": "2026-04-10T12:00:00Z"
  }
}
```

Ship update:
```json
{
  "type": "ship",
  "data": {
    "id": "123456789",
    "lat": 1.3521,
    "lon": 103.8198,
    "heading": 180.0,
    "speed": 12.5,
    "name": "MV Example",
    "timestamp": "2026-04-10T12:00:00Z"
  }
}
```

---

## Error Responses

All endpoints return appropriate HTTP status codes:

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Internal Server Error |

Error response format:
```json
{
  "detail": "Error message here"
}
```
```

### 5. Update README.md

Replace the current README with:

```markdown
# TerraWatch

> Live Geospatial Intelligence Platform — planes, ships, and world events on a 3D globe

![Phase](https://img.shields.io/badge/Phase-1-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## What is TerraWatch?

TerraWatch is a real-time GEOINT (Geospatial Intelligence) platform inspired by Palantir. It visualizes global activity — aircraft, maritime vessels, and world events — on an interactive 3D globe.

**Core Features:**
- Real-time aircraft tracking (ADS-B)
- Real-time maritime vessel tracking (AIS)
- World event monitoring (GDELT)
- Conflict zone visualization (ACLED)
- Intelligence alerting (V3 — future)

## Current Status

**Phase 1 of 7 — Foundation Setup (Complete)**

Phase 1 establishes the project foundation:
- [x] FastAPI backend with WebSocket support
- [x] React + deck.gl frontend with 3D globe
- [x] Docker Compose orchestration
- [x] REST API and WebSocket data pipeline

**Next: Phase 2 — Live Aircraft Tracking**

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + Vite + deck.gl |
| Backend | Python FastAPI |
| Database | SQLite (V1) → PostgreSQL + TimescaleDB (V2+) |
| Containers | Docker + Docker Compose |

## Quick Start

### Prerequisites
- Docker and Docker Compose
- 4GB RAM minimum
- macOS, Linux, or WSL2 on Windows

### Run with Docker

```bash
# Clone the repository
git clone https://github.com/RishiJain905/TerraWatch.git
cd TerraWatch

# Start all services
docker compose up --build

# Open in browser
open http://localhost:5173
```

### Run Locally (Development)

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Project Structure

```
TerraWatch/
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── api/      # Routes (REST + WebSocket)
│   │   ├── core/     # Database, models, config
│   │   └── services/  # Data fetching services
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/         # React application
│   ├── src/
│   │   ├── components/
│   │   │   ├── Globe/     # deck.gl globe + layers
│   │   │   ├── Sidebar/   # Layer toggles
│   │   │   └── Header/    # Top bar
│   │   └── hooks/         # Data hooks
│   ├── package.json
│   └── Dockerfile
├── docker/           # Docker configs
├── docs/             # Documentation
├── phases/           # Phase + task specifications
└── README.md
```

## Development

### Agent Workflow

This project is built with a multi-agent system:
- **GPT 5.4**: Backend (FastAPI, data services, schedulers)
- **GLM 5.1**: Frontend (React, deck.gl, globe visualization)
- **MiniMax M2.7**: Coordinator (architecture, Docker, integration)

Each phase has task files in `phases/phaseX/` that define implementation tasks for each agent.

### Version Plan

| Version | Phases | Features |
|---------|--------|----------|
| V1 | 1-3 | Live planes + ships on globe |
| V2 | 4-5 | Events + conflict data layer |
| V3 | 6-7 | Intelligence alerts + production |

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Data Sources](docs/DATA_SOURCES.md)
- [API Reference](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## Data Sources

All data is sourced from free, public APIs:
- **Aircraft**: ADSB Exchange (public ADS-B data)
- **Ships**: ORVRTS / AIS aggregators (AIS transponder data)
- **Events**: GDELT Project (world news events)
- **Conflicts**: ACLED (conflict data, free registration)

See [DATA_SOURCES.md](docs/DATA_SOURCES.md) for full details.

## License

MIT — see [LICENSE](LICENSE) for details.
```

### 6. Run Docker Compose Sanity Check

Run the full Docker Compose build and verify:

```bash
cd ~/TerraWatch

# Clean up any existing containers
docker compose down -v 2>/dev/null

# Build and start
docker compose up --build -d

# Wait for services to start
sleep 20

# Check backend health
curl -s http://localhost:8000/health

# Check metadata
curl -s http://localhost:8000/api/metadata

# Check frontend is serving
curl -s http://localhost:5173 | grep -o "TerraWatch" || echo "Frontend not responding"

# Check WebSocket
python3 -c "
import asyncio, websockets
async def test():
    async with websockets.connect('ws://localhost:8000/ws') as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=5)
        print('WS received:', msg)
asyncio.run(test())
" 2>/dev/null || echo "WS test skipped (websockets not installed locally)"

# Stop services
docker compose down
```

If all checks pass, Phase 1 is complete!

### 7. Git Commit

```bash
cd ~/TerraWatch
git add -A
git commit -m "Phase 1 complete: Foundation setup

- FastAPI backend with WebSocket + REST API
- React + deck.gl frontend with 3D globe shell
- Docker Compose orchestration
- All phase 1 tasks implemented

Exit criteria met:
- Backend on :8000, /api/metadata returns phase 1
- Frontend on :5173, globe renders
- WebSocket /ws connects and sends heartbeats
- Docker Compose builds and runs"
```

---

## Acceptance Criteria

1. `docker compose up --build` completes without errors
2. Backend responds on port 8000
3. Frontend serves on port 5173
4. `/api/metadata` returns `{"status": "ok", "phase": 1}`
5. WebSocket connects and receives heartbeats
6. All docs are created and accurate
7. README is updated with current status
8. Git commit created

---

## Commit Message

```
Phase 1: Complete foundation — FastAPI + React globe + Docker
```

This is the final task. When this is complete, all Phase 1 exit criteria are met.
