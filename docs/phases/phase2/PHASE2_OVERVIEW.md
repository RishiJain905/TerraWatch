# Phase 2 — Live Aircraft Tracking

## Phase Goal

Get real ADSB plane data flowing end-to-end: OpenSky Network API → FastAPI backend → WebSocket → deck.gl globe.

By end of Phase 2:
- Planes appear as directional icons on the globe with real callsigns
- Data refreshes every 30 seconds automatically
- Clicking a plane shows its details
- WebSocket pushes updates to all connected clients

---

## What This Phase Is NOT

This phase is planes only. Ships come in Phase 3. Events/conflict in Phase 4+.

---

## Context Files (Read First)

Before any task, read:
- `../../ARCHITECTURE.md` — project architecture
- `../../DATA_SOURCES.md` — ADS-B Exchange API details
- `PHASE2_OVERVIEW.md` — this file

---

## Tasks Overview

| # | Agent | Task | Description | Dependencies |
|---|-------|------|-------------|-------------|
| 1 | M2.7 | Phase 2 docs + API research | OVERVIEW, update DATA_SOURCES.md with ADS-B API details | None |
| 2 | GPT 5.4 | adsb_service.py implementation | Fetch from ADSB Exchange, parse to Plane model | Task 1 |
| 3 | GPT 5.4 | Plane scheduler + WS broadcast | Background task fetching every 30s, broadcast to WS clients | Task 2 |
| 4 | GPT 5.4 | Plane detail endpoint | GET /api/planes/{icao24} — fetch single plane history | Task 2 |
| 5 | GLM 5.1 | Globe layer — plane icons + direction | IconLayer or PathMarkerLayer, heading-based rotation | Task 1 |
| 6 | GLM 5.1 | Plane info panel on click | Sidebar popup or tooltip with callsign, altitude, speed | Task 5 |
| 7 | M2.7 | Integration test — live data | Verify planes appear on globe, WS updates work | Tasks 3, 5, 6 |

---

## Data Flow

```
ADSB Exchange API
    → adsb_service.fetch_planes() [every 30s]
    → SQLite planes table (upsert)
    → WebSocket broadcast (all connected clients)
    → usePlanes hook (frontend state)
    → IconLayer on globe
```

---

## Key Technical Decisions

### ADSB Exchange API
- Endpoint: `https://opensky-network.org/api/states/all`
- No API key required (anonymous access)
- Returns `states` array with 17-element arrays: `[icao24, callsign, origin_country, time_position, last_contact, lon, lat, baro_altitude, on_ground, velocity, heading, ...]`
- Parse `icao24` as hex string (lowercase), `callsign` as callsign (strip whitespace)

### Plane Icon Representation
- Use IconLayer with aircraft icon
- Rotate icon based on `Track` (heading in degrees)
- Color-code by altitude: low=green, medium=yellow, high=red
- Fall back to ScatterplotLayer if icon assets unavailable

### WebSocket Message Format
```json
{
  "type": "plane",
  "action": "upsert",  // or "remove"
  "data": {
    "id": "a1b2c3",
    "lat": 51.5,
    "lon": -0.1,
    "alt": 35000,
    "heading": 270,
    "callsign": "BAW123",
    "speed": 450,
    "squawk": "7200"
  },
  "timestamp": "2026-04-10T12:00:00Z"
}
```

### Database Schema (existing — verify)
```sql
CREATE TABLE planes (
    id TEXT PRIMARY KEY,
    callsign TEXT,
    lat REAL,
    lon REAL,
    alt INTEGER DEFAULT 0,
    heading REAL DEFAULT 0,
    speed REAL DEFAULT 0,
    squawk TEXT DEFAULT '',
    timestamp TEXT
);
```

---

## Success Criteria

- [ ] `curl https://opensky-network.org/api/states/all` returns plane data
- [ ] adsb_service correctly parses response to Plane dict
- [ ] /api/planes returns planes from database
- [ ] /ws broadcasts plane updates every 30 seconds
- [ ] Globe shows planes as directional icons
- [ ] Clicking a plane shows callsign, altitude, speed, heading
- [ ] Multiple browser tabs stay in sync via WebSocket
- [ ] No console errors in browser
