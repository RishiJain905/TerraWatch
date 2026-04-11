# Phase 1.5 — Data Source Enrichment

## Goal

Expand TerraWatch's live data coverage by adding secondary free API sources for both planes and ships, without removing existing sources. Implement smart deduplication to merge data from multiple providers into a single unified view.

---

## Motivation

- **Planes:** OpenSky has sparse coverage over Africa, Middle East, Canada, Russia, and ocean expanses. ADSB.lol aggregates data from a different volunteer feeder network, potentially filling gaps in some regions.
- **Ships:** Digitraffic covers only Nordic/Baltic seas (~1,000-2,000 ships). AIS Friends has global coverage through community AIS feeders (~5,000+ vessels), which would dramatically increase visible ship traffic.

---

## Scope

### What is in scope

1. **Add ADSB.lol as a second plane source**
   - Endpoint: `GET https://api.adsb.lol/aircraft/json` (no API key required)
   - Merge with existing OpenSky data
   - Deduplicate by `icao24` (hex ICAO code)

2. **Add AIS Friends as a second ship source**
   - Endpoint: `GET https://www.aisfriends.com/api/public/v1/vessels/bbox`
   - Requires free Bearer token (user registers at aisfriends.com)
   - Merge with existing Digitraffic data
   - Deduplicate by `mmsi`

3. **Deduplication strategy**
   - Per-source: filter stale entries before merge
   - Cross-source: prefer more recent `timestamp`, fall back to source priority
   - Unified DB schema that tracks source attribution

4. **Verification and testing**
   - Backend tests for deduplication logic
   - Integration tests confirming both sources feed into WebSocket
   - No regression in existing Phase 2/3 tests

### What is out of scope

- Removing OpenSky or Digitraffic (both remain active)
- Historical data (only live tracking)
- Changing frontend visualization logic (same IconLayer, same panels)
- Authentication flow for AIS Friends token (user provides it via env var)

---

## API Details

### ADSB.lol — Aircraft

**Endpoint:** `GET https://api.adsb.lol/aircraft/json`

**Response format (approximate):**
```json
{
  "ac": [
    {
      "hex": "76cccd",
      "flight": "SIA7371",
      "lat": 21.366613,
      "lng": 66.61321,
      "alt": 10021,
      "dir": 121,
      "speed": 966,
      "squawk": "3420",
      "icao24": "76cccd",
      "reg": "9V-SFM",
      "tail": "9V-SFM",
      "source": "adsblol"
    }
  ],
  "ctime": 1611366621,
  "ptime": 1611366621,
  "last_timestamp": 1611366621
}
```

**Refresh rate:** ~30s (match OpenSky cadence)

**Notes:**
- No API key required
- Hex is lowercase — normalize to uppercase for matching with OpenSky
- `flight` may be ICAO or IATA callsign — store as-is

---

### AIS Friends — Vessels

**Endpoint:** `GET https://www.aisfriends.com/api/public/v1/vessels/bbox`

**Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| lat_min | float | Yes | Min latitude of bounding box |
| lat_max | float | Yes | Max latitude of bounding box |
| lon_min | float | Yes | Min longitude |
| lon_max | float | Yes | Max longitude |
| from | int | No | Max age of positions in minutes |
| format | string | No | `json` (default) |

**Authentication:** Bearer token in header
```
Authorization: Bearer <token>
```

**Global coverage strategy:** Query in bounding box tiles to cover full globe, or query the full world in chunks. AIS Friends limits: 1 request/minute, max 1,000 vessels per response.

**Alternative endpoints if bbox is too limiting:**
- `GET /api/public/v1/vessels?mmsi=<mmsi>` — single vessel lookup
- `GET /api/public/v1/vessels/positions?from=<timestamp>` — recent positions

**Refresh rate:** AIS Friends allows 1 req/min — set scheduler to 60s matching Digitraffic

**Registration:** User gets free token at https://www.aisfriends.com/

---

## Deduplication Strategy

### Planes

1. Fetch from OpenSky (source A) and ADSB.lol (source B) in parallel
2. Normalize `icao24` to uppercase on both
3. Build a map keyed by `icao24`
4. If an `icao24` exists in both sources:
   - Use the entry with the more recent `timestamp` or `time_position`
   - If timestamps are equal or both missing, prefer OpenSky (source priority)
5. Mark each entry with its source(s) for debugging/attribution

### Ships

1. Fetch from Digitraffic (source A) and AIS Friends (source B) in parallel
2. Build a map keyed by `mmsi`
3. If an `mmsi` exists in both sources:
   - Use the entry with the more recent `timestamp` or `last_position`
   - If timestamps are equal, prefer Digitraffic (source priority — richer vessel metadata)
4. AIS Friends may return more fields (draught, gt, dwt) — merge attributes from both where missing

### Stale Entry Cleanup

- OpenSky: entries with `time_position` older than 5 minutes are stale
- ADSB.lol: entries without recent update are stale
- Digitraffic: entries older than 10 minutes are stale
- AIS Friends: entries older than 10 minutes are stale

Apply per-source cleanup **before** deduplication to avoid cross-source pollution.

---

## Implementation Plan

### Task 1 — Backend: ADSB.lol Service
- Create `adsblol_service.py` in `backend/app/services/`
- Implement `fetch_planes()` — parallel fetch with OpenSky
- Normalize response to `Plane` model
- Add `ADSBLOL_REFRESH_SECONDS` to config

### Task 2 — Backend: AIS Friends Service
- Create `ais_friends_service.py` in `backend/app/services/`
- Implement `fetch_ships()` — query bbox or global tiles
- Normalize response to `Ship` model
- Add `AIS_FRIENDS_API_KEY`, `AIS_FRIENDS_REFRESH_SECONDS` to config

### Task 3 — Backend: Deduplication Logic
- Create `dedup.py` in `backend/app/core/`
- `deduplicate_planes(open_sky_planes, adsblol_planes) -> List[Plane]`
- `deduplicate_ships(digitraffic_ships, ais_friends_ships) -> List[Ship]`
- Track `source` attribute on each entity

### Task 4 — Backend: Scheduler Updates
- Update `schedulers.py` to fetch from both sources
- Run deduplication step before WebSocket broadcast
- Maintain two separate DB tables or unified table with source tags

### Task 5 — Backend: Config & Env Vars
- Add to `.env.example`:
  ```
  AIS_FRIENDS_API_KEY=your_token_here
  ADSBLOL_REFRESH_SECONDS=30
  AIS_FRIENDS_REFRESH_SECONDS=60
  ```

### Task 6 — Backend: Tests
- Unit tests for `deduplicate_planes()` — cases: no overlap, full overlap, partial, stale entries
- Unit tests for `deduplicate_ships()` — same cases
- Integration test: verify WebSocket receives data from both sources
- **Existing Phase 2/3 tests must pass (no regression)**

### Task 7 — Documentation
- Update `DATA_SOURCES.md` with new sources
- Update `ARCHITECTURE.md` if data flow changes

---

## Verification Checklist

- [ ] `adsblol_service.py` fetches and parses ADSB.lol correctly
- [ ] `ais_friends_service.py` fetches and parses AIS Friends correctly (with token)
- [ ] Deduplication produces correct merged set for planes
- [ ] Deduplication produces correct merged set for ships
- [ ] Stale entries from both sources are filtered before merge
- [ ] WebSocket broadcasts combined plane set
- [ ] WebSocket broadcasts combined ship set
- [ ] Frontend receives more planes than before (verify Africa/Middle East coverage improves)
- [ ] Frontend receives more ships than before (verify global coverage)
- [ ] All Phase 2/3 tests still pass
- [ ] New deduplication unit tests pass

---

## File Structure (Changes)

```
backend/app/
├── services/
│   ├── adsb_service.py        # (existing)
│   ├── ais_service.py         # (existing)
│   ├── adsblol_service.py     # NEW
│   └── ais_friends_service.py # NEW
├── core/
│   ├── database.py            # (existing)
│   ├── models.py              # (existing)
│   └── dedup.py               # NEW
├── tasks/
│   └── schedulers.py          # UPDATE
└── config.py                  # UPDATE

.env.example                   # UPDATE
docs/
├── DATA_SOURCES.md            # UPDATE
└── phases/phase1_5/
    └── PHASE1_5_OVERVIEW.md  # this file
```

---

## Estimated Complexity

- **Backend:** Medium — two new services + deduplication logic
- **Frontend:** None — same visualization, just more data
- **Testing:** Medium — deduplication edge cases need coverage
- **Risk:** AIS Friends rate limit (1 req/min) must be respected in scheduler
