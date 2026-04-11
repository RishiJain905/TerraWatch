# Phase 3 — Live Ship Tracking

## Phase Goal

Get real AIS ship data flowing end-to-end, parallel to the Phase 2 plane pipeline: AIS API → FastAPI backend → WebSocket → deck.gl globe.

By end of Phase 3:
- Ships appear on the globe with directional icons, color-coded by ship type
- Data refreshes every 60 seconds automatically
- Clicking a ship shows its details (name, destination, type, speed, heading)
- WebSocket pushes ship updates to all connected clients
- V1 is complete: planes + ships on a live globe

## What This Phase Is NOT

This phase is ships only. Events/conflict data comes in Phase 4. Zone alerting is Phase 6+.

## Context Files (Read First)

Before any task, read:
- `../../ARCHITECTURE.md` — project architecture
- `../../DATA_SOURCES.md` — AIS API details (updated in Task 1)
- `PHASE3_OVERVIEW.md` — this file

## Tasks Overview

| # | Agent | Task | Description | Dependencies |
|---|-------|------|-------------|-------------|
| 1 | M2.7 | Phase 3 docs + AIS API research | OVERVIEW, update DATA_SOURCES.md with verified AIS API details | None |
| 2 | GPT 5.4 | ais_service.py implementation | Fetch from chosen AIS provider, parse to Ship model | Task 1 |
| 3 | GPT 5.4 | Ship scheduler + WS broadcast | Background task fetching every 60s, broadcast to WS clients | Task 2 |
| 4 | GPT 5.4 | Ship detail endpoint | GET /api/ships/{mmsi} — fetch single ship details | Task 2 |
| 5 | GLM 5.1 | Globe layer — ship icons + direction | IconLayer with directional icons, color by ship type | Task 1 |
| 6 | GLM 5.1 | Ship info panel on click | Slide-in panel showing ship name, destination, type, speed, heading | Task 5 |
| 7 | M2.7 | Integration test — live ship data | Verify ships appear on globe, WS updates work, panel shows details | Tasks 3, 5, 6 |

## Data Flow

```
AIS API
  → ais_service.fetch_ships() [every 60s]
  → SQLite ships table (upsert)
  → WebSocket broadcast (all connected clients)
  → useShips hook (frontend state)
  → IconLayer on globe (replacing ScatterplotLayer)
```

## Key Technical Decisions

### AIS API Selection (Task 1)
- Must be free (no paid API key)
- Must return: MMSI, name, position (lat/lon), heading, speed, destination, ship_type
- Verified working before implementation begins
- Options: VesselFinder, AISHub, MarineTraffic free tier — Task 1 picks the winner

### Ship Icon Representation
- Use IconLayer with ship/boat icon (directional like plane icons)
- Rotate icon based on `heading` field
- Color-code by ship_type:
  - Cargo = blue (#4A90D9)
  - Tanker = orange (#F5A623)
  - Passenger = green (#7ED321)
  - Fishing = purple (#9013FE)
  - Other = gray (#999999)
- Fall back to ScatterplotLayer if icon assets unavailable

### WebSocket Message Format
```json
{
  "type": "ship",
  "action": "upsert",
  "data": {
    "id": "123456789",
    "lat": 34.5,
    "lon": -122.3,
    "heading": 180,
    "speed": 12.5,
    "name": "MSC Oscar",
    "destination": "Los Angeles",
    "ship_type": "cargo",
    "timestamp": "2026-04-11T12:00:00Z"
  },
  "timestamp": "2026-04-11T12:00:00Z"
}
```

Batch message format (preferred for efficiency):
```json
{
  "type": "ship_batch",
  "action": "upsert",
  "data": [...ships],
  "timestamp": "2026-04-11T12:00:00Z"
}
```

### Database Schema (already exists — verify)
```sql
CREATE TABLE ships (
    id TEXT PRIMARY KEY,
    lat REAL,
    lon REAL,
    heading REAL DEFAULT 0,
    speed REAL DEFAULT 0,
    name TEXT DEFAULT '',
    destination TEXT DEFAULT '',
    ship_type TEXT DEFAULT '',
    timestamp TEXT
);
```

## Success Criteria

- [ ] AIS API returns ship data (verified via curl or httpx test)
- [ ] ais_service correctly parses response to Ship dict
- [ ] /api/ships returns ships from database
- [ ] /ws broadcasts ship updates every 60 seconds
- [ ] Globe shows ships as directional icons
- [ ] Ships are color-coded by type
- [ ] Clicking a ship shows name, destination, type, speed, heading
- [ ] Multiple browser tabs stay in sync via WebSocket
- [ ] No console errors in browser
- [ ] All Phase 2 plane functionality still works (regression)
- [ ] V1 complete: planes + ships on globe

## Technical Debt / Cleanup (V1 Polish)

- [ ] Remove placeholder ship ScatterplotLayer in Globe.jsx (replaced by Task 5 IconLayer)
- [ ] Vite proxy env vars documented in .env.example if not already
- [ ] ships table index (`idx_ships_timestamp`) already created in Phase 2 — verify
- [ ] ships_refresh_loop() in schedulers.py was placeholder — now real implementation
