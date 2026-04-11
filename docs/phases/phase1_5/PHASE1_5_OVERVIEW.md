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
- Changing frontend visualization logic
- Authentication flow for AIS Friends token (user provides via env var)

---

## API Summary

### ADSB.lol — Planes

- **Endpoint:** `GET https://api.adsb.lol/aircraft/json`
- **Auth:** None
- **Key field:** `hex` (lowercase, normalize to uppercase for matching)
- **Refresh:** 30s

### AIS Friends — Ships

- **Endpoint:** `GET https://www.aisfriends.com/api/public/v1/vessels/bbox`
- **Auth:** Bearer token (free registration at aisfriends.com)
- **Key field:** `mmsi`
- **Limits:** 1 req/min, max 1,000 vessels per response
- **Refresh:** 60s (respect rate limit)

---

## Deduplication Strategy

### Planes

1. Fetch from OpenSky (source A) and ADSB.lol (source B) in parallel
2. Normalize `icao24` to uppercase on both
3. Build a map keyed by `icao24`
4. If an `icao24` exists in both sources:
   - Use the entry with the more recent `timestamp` or `time_position`
   - If timestamps are equal/missing, prefer OpenSky (source priority)
5. Mark each entry with its source(s) for debugging/attribution

### Ships

1. Fetch from Digitraffic (source A) and AIS Friends (source B) in parallel
2. Build a map keyed by `mmsi`
3. If an `mmsi` exists in both sources:
   - Use the entry with the more recent `timestamp`
   - If timestamps are equal, prefer Digitraffic (richer vessel metadata)
4. Merge attributes from both where missing

### Stale Entry Cleanup

- OpenSky: entries with `time_position` older than 5 minutes are stale
- ADSB.lol: entries without recent update are stale
- Digitraffic: entries older than 10 minutes are stale
- AIS Friends: entries older than 10 minutes are stale

Apply per-source cleanup **before** deduplication.

---

## Task Breakdown

| # | Agent | Task |
|---|-------|------|
| 1 | GPT | ADSB.lol service — fetch, normalize, model |
| 2 | GPT | AIS Friends service — fetch, normalize, model |
| 3 | GPT | Deduplication logic — planes and ships |
| 4 | M2.7 | Scheduler updates + integration + tests |

---

## File Structure (Changes)

```
backend/app/
├── services/
│   ├── adsb_service.py         (existing)
│   ├── ais_service.py          (existing)
│   ├── adsblol_service.py      NEW
│   └── ais_friends_service.py  NEW
├── core/
│   ├── database.py             (existing)
│   ├── models.py               (existing)
│   └── dedup.py                NEW
├── tasks/
│   └── schedulers.py           UPDATE
└── config.py                   UPDATE

.env.example                     UPDATE
```

---

## Verification Checklist

- [ ] ADSB.lol service fetches and parses correctly
- [ ] AIS Friends service fetches and parses correctly (with token)
- [ ] Plane deduplication — no overlap pollution, stale entries filtered
- [ ] Ship deduplication — no overlap pollution, stale entries filtered
- [ ] WebSocket broadcasts combined plane set
- [ ] WebSocket broadcasts combined ship set
- [ ] Frontend receives more planes than before
- [ ] Frontend receives more ships than before
- [ ] All Phase 2/3 tests still pass
- [ ] New deduplication unit tests pass
