# Phase 1.5 — Data Source Enrichment

## Goal

Expand TerraWatch's live data coverage by adding secondary free API sources for both planes and ships, without removing existing sources. Implement smart deduplication to merge data from multiple providers into a single unified view while preserving the existing backend payload contracts.

---

## Motivation

- **Planes:** OpenSky has sparse coverage over Africa, the Middle East, Canada, Russia, and ocean expanses. ADSB.lol aggregates data from a different volunteer feeder network and can fill gaps in some regions.
- **Ships:** Digitraffic covers only Nordic/Baltic waters. aisstream.io adds a global WebSocket-based AIS feed, dramatically increasing visible ship traffic while keeping Digitraffic's richer regional metadata.

---

## Scope

### What is in scope

1. **Add ADSB.lol as a second plane source**
   - Endpoint: `GET https://api.adsb.lol/aircraft/json` (no API key required)
   - Merge with existing OpenSky data
   - Deduplicate by `icao24` / plane `id`

2. **Add aisstream.io as a second ship source**
   - Endpoint: `wss://stream.aisstream.io/v0/stream`
   - Requires free `AISSTREAM_API_KEY`
   - Maintain a persistent WebSocket listener
   - Merge streamed ship batches with the latest Digitraffic snapshot
   - Deduplicate by `mmsi` / ship `id`

3. **Deduplication strategy**
   - Per-source stale cleanup before merge
   - Cross-source: prefer the more recent `timestamp`
   - On timestamp ties, prefer Digitraffic
   - Merge safe missing metadata from the losing record into the winner

4. **Verification and testing**
   - Backend tests for ship deduplication and aisstream parsing/listener behavior
   - Scheduler tests confirming Digitraffic polling and aisstream batch merge behavior
   - No regression in existing backend contracts

### What is out of scope

- Removing OpenSky or Digitraffic (both remain active)
- Historical data (only live tracking)
- Changing frontend visualization logic
- Live validation without a real `AISSTREAM_API_KEY`

---

## API Summary

### ADSB.lol — Planes

- **Endpoint:** `GET https://api.adsb.lol/aircraft/json`
- **Auth:** None
- **Key field:** `hex` (normalize to plane `id`)
- **Refresh:** 30s

### aisstream.io — Ships

- **Endpoint:** `wss://stream.aisstream.io/v0/stream`
- **Auth:** `APIKey` field in the initial subscription payload
- **Key field:** `MMSI` / `UserID`
- **Transport:** Persistent WebSocket, not REST polling
- **Batching:** Buffer updates by MMSI and emit every 30 seconds

---

## Deduplication Strategy

### Planes

1. Fetch from OpenSky (source A) and ADSB.lol (source B) in parallel
2. Normalize `icao24` to uppercase on both
3. Build a map keyed by `icao24`
4. If an `icao24` exists in both sources:
   - Use the entry with the more recent `timestamp` or `time_position`
   - If timestamps are equal or missing, prefer OpenSky

### Ships

1. Poll Digitraffic to maintain the latest regional snapshot
2. Listen to aisstream continuously and accumulate the latest streamed ship record per MMSI
3. Merge both sources by ship `id`
4. If an `id` exists in both sources:
   - Use the record with the more recent `timestamp`
   - If timestamps are equal, prefer Digitraffic
   - Merge safe missing metadata (`name`, `destination`, `ship_type`, etc.) from the loser when useful

### Stale Entry Cleanup

- OpenSky: entries older than 5 minutes are stale
- ADSB.lol: entries without a recent update are stale
- Digitraffic: entries older than 10 minutes are stale
- aisstream: cached streamed entries older than 10 minutes are stale

Apply per-source cleanup before cross-source deduplication.

---

## Task Breakdown

| # | Agent | Task |
|---|-------|------|
| 1 | GPT | ADSB.lol service — fetch, normalize, model |
| 2 | GPT | aisstream service — websocket connect/listen/map/normalize |
| 3 | GPT | Ship deduplication rules in scheduler layer |
| 4 | M2.7 | Scheduler integration + tests + docs |

---

## File Structure (Changes)

```
backend/app/
├── services/
│   ├── adsb_service.py         (existing)
│   ├── ais_service.py          (existing Digitraffic)
│   ├── adsblol_service.py      (existing)
│   └── aisstream_service.py    NEW
├── tasks/
│   └── schedulers.py           UPDATE
└── config.py                   UPDATE

backend/tests/
├── test_database_and_scheduler.py  UPDATE
└── test_aisstream_service.py       NEW

.env.example                         UPDATE
```

---

## Verification Checklist

- [x] ADSB.lol service fetches and parses correctly
- [x] aisstream service connects and sends the required subscription payload
- [x] Wrapped aisstream `PositionReport` messages normalize to the existing `Ship` contract
- [x] Ship deduplication prefers newer timestamps and Digitraffic on ties
- [x] Scheduler merges Digitraffic snapshots with cached aisstream state
- [x] WebSocket broadcasts the merged ship set
- [x] Backend still runs without `AISSTREAM_API_KEY` (Digitraffic-only fallback)
- [x] All backend tests pass
