# Phase 3 — Task 1: M2.7 — AIS API Research & Docs

## Context

Phase 2 is complete. Ships layer needs real AIS data. The current `ais_service.py` returns an empty list — a stub. This task finds the right free AIS API, verifies it works, and documents it in `docs/DATA_SOURCES.md`.

## Instructions

You are M2.7 (coordinator). Read these files first:
- `docs/ARCHITECTURE.md`
- `docs/DATA_SOURCES.md`
- `docs/phases/phase3/PHASE3_OVERVIEW.md`

## Your Task

1. **Research free AIS APIs.** Options listed in DATA_SOURCES.md:
   - VesselFinder.com (free tier)
   - AISHub.net (free with registration)
   - MarineTraffic (free tier with rate limits)

2. **Pick the best one based on:**
   - No API key required OR free tier immediately accessible
   - Returns: MMSI, name, position (lat/lon), heading, speed, destination, ship_type
   - Reasonable rate limits (60s refresh = ~1 req/min is easy)
   - Actually tested and confirmed working (not just documentation)

3. **Verify the API works.** Use `curl` or `httpx` in Python to confirm it returns data. Document the exact endpoint, parameters, and response format.

4. **Update `docs/DATA_SOURCES.md`** with the chosen AIS API:
   - Remove outdated/incorrect info
   - Add verified endpoint, auth requirements (or lack thereof)
   - Document response fields and unit conversions
   - Note rate limits
   - Verify: Test the API with a live request. If it doesn't work, try the next option until one succeeds.

5. **Create completion summary** at `docs/completedphases/phase3/P3-task1-done.md`:
   - Which API was chosen and why
   - Verified endpoint + parameters
   - Sample response snippet (clean, truncated)
   - Response fields that map to Ship model
   - Any unit conversions needed

## Constraints

- Free only — no paid API keys
- Must return enough fields to populate the Ship model (id, lat, lon, heading, speed, name, destination, ship_type, timestamp)
- Must be testable immediately

## Output Files to Modify

- `docs/DATA_SOURCES.md` (update maritime section)
- `docs/completedphases/phase3/P3-task1-done.md` (create — completion summary)

## Verification

Run a live test against the chosen API endpoint and confirm it returns valid ship data. Document the result.
