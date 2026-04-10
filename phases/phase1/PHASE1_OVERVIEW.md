# Phase 1 — Foundation Setup

## Phase Goal

Get the TerraWatch monorepo to a state where:
- Backend runs locally (`python -m uvicorn app.main:app`)
- Frontend runs locally (`npm run dev`)
- They communicate via WebSocket and REST
- `docker compose up` runs both services together
- The globe canvas is visible in the browser

---

## What This Phase Is NOT

This is NOT building any features. No real data yet. No layers. Just the empty shell that proves the architecture works end-to-end.

---

## Tasks Overview

| # | Agent | Task | Dependencies |
|---|-------|------|-------------|
| 1 | M2.7 | Directory structure + Docker base | None |
| 2 | M2.7 | Docker Compose orchestration | Task 1 |
| 3 | GLM 5.1 | React + Vite frontend scaffold | Task 1 |
| 4 | GPT 5.4 | FastAPI backend scaffold | Task 1 |
| 5 | GLM 5.1 | Basic React globe shell | Task 3 |
| 6 | GPT 5.4 | FastAPI app + dummy data routes | Task 4 |
| 7 | M2.7 | Frontend API service + WS hook | Tasks 3, 6 |
| 8 | M2.7 | Docker sanity check + docs | Tasks 2, 5, 7 |

---

## Tasks Summary

| # | Agent | Task File | Description |
|---|-------|-----------|-------------|
| 1 | M2.7 | `task_1_M2.7_directory_docker.md` | Directory structure + Docker base files |
| 2 | GLM 5.1 | `task_2_GLM_frontend_scaffold.md` | React + Vite frontend scaffold |
| 3 | GPT 5.4 | `task_3_GPT_backend_scaffold.md` | FastAPI backend scaffold |
| 4 | GLM 5.1 | `task_4_GLM_globe_shell.md` | Basic deck.gl globe shell |
| 5 | GPT 5.4 | `task_5_GPT_api_completion.md` | FastAPI app completion + service stubs |
| 6 | M2.7 | `task_6_M2.7_api_service_ws.md` | Frontend API service + WebSocket integration |
| 7 | M2.7 | `task_7_M2.7_docker_sanity.md` | Docker Compose sanity check + docs |

---

## Context Files (Always Read First)

Before starting any task, read these for full context:
- `../docs/ARCHITECTURE.md` — full project architecture
- `../docs/DATA_SOURCES.md` — data source documentation  
- `PHASE1_OVERVIEW.md` — this file
- Your specific task file (see table above)
