# TerraWatch

> Live Geospatial Intelligence Platform — planes, ships, and world events on a 3D globe

![Phase](https://img.shields.io/badge/Phase-2-blue)
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

**Phase 1 of 7 — Foundation Setup (Complete ✓)**

Phase 1 established the project foundation:
- [x] FastAPI backend with WebSocket support
- [x] React + deck.gl frontend with 3D globe
- [x] Docker Compose orchestration
- [x] REST API and WebSocket data pipeline

**Phase 2 of 7 — Live Aircraft Tracking (In Progress)**

Phase 2 adds real ADSB plane data end-to-end:
- [ ] ADSB Exchange API integration
- [ ] Background scheduler (30s refresh)
- [ ] WebSocket broadcast to all clients
- [ ] Directional plane icons on globe
- [ ] Click-to-inspect plane info panel

See [docs/phases/phase2/](docs/phases/phase2/) for task breakdown.

**Next: Phase 3 — Ship Tracking**

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
│   └── docs/         # Documentation + phases
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
