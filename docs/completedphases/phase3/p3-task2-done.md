# Phase 3 Task 2 — DONE ✓

Agent: GPT 5.4
Date: 2026-04-11
Status: COMPLETE

---

## What was implemented

Implemented a real Digitraffic-backed AIS service in `backend/app/services/ais_service.py` and added unit tests in `backend/tests/test_ais_service.py`.

### Service implementation
- Replaced the Phase 1 stub in `fetch_ships()` with a real async implementation
- Uses `httpx.AsyncClient` with:
  - 30 second timeout
  - `Accept-Encoding: gzip`
  - `User-Agent: TerraWatch/0.1`
- Fetches both Digitraffic endpoints per refresh:
  - `https://meri.digitraffic.fi/api/ais/v1/locations`
  - `https://meri.digitraffic.fi/api/ais/v1/vessels`
- Merges position data and metadata by MMSI
- Normalizes each record through the existing `Ship` Pydantic model
- Returns `[]` on HTTP failure, JSON parsing failure, or invalid top-level payload shapes
- Implements `fetch_ship_details(mmsi: str) -> dict | None`

### Parsing and normalization behavior
- `id` = MMSI converted to string
- `lat`/`lon` parsed from GeoJSON coordinates in `[lon, lat]` order
- `heading` prefers `properties.heading`, falls back to `properties.cog`, then `0.0`
- `speed` uses `properties.sog` directly (already knots)
- `name` and `destination` are trimmed and null-safe
- `timestamp` prefers `timestampExternal` converted from epoch ms to ISO 8601 UTC
- If `timestampExternal` is missing/invalid, falls back to `dataUpdatedTime`, then `utc_now_iso()`

### Ship type mapping decision
To keep the backend contract aligned with the Phase 3 UI expectations, ship types are normalized into the stable categories:
- `cargo`
- `tanker`
- `passenger`
- `fishing`
- `other`

Mapping used:
- 70–79 → `cargo`
- 80–89 → `tanker`
- 60–69 → `passenger`
- 30 → `fishing`
- everything else → `other`

This intentionally collapses upstream codes like tug/sailing into `other` so later frontend color mapping stays simple and consistent with the spec.

---

## Spec reconciliation notes

A few spec/docs mismatches were reconciled during implementation:

1. Task 2 references `docs/docs/completedphases/phase3/P3-task1-done.md`, but the live completion summary is actually at:
   - `docs/completedphases/phase3/P3-task1-done.md`

2. The heading source was slightly inconsistent across the docs:
   - `DATA_SOURCES.md` emphasized `cog`
   - `P3-task1-done.md` sample merged object used `heading`

   Implementation choice:
   - use `heading` when present
   - otherwise fall back to `cog`

   This is the safest option for directional ship icon rendering.

3. Task 1 examples mention richer values like `tug` and `sailing`, but Phase 3 visualization wants a smaller stable category set.
   Implementation follows the Phase 3 contract and normalizes extra categories into `other`.

4. The old stub `fetch_ship_details()` returned `{}`. The task spec requires `dict | None`, so it now returns `None` for blank or missing MMSI values.

---

## Tests added

Created `backend/tests/test_ais_service.py` with coverage for:

1. Happy-path Digitraffic normalization and MMSI merge
2. Heading fallback to `cog` and safe defaults for malformed optional fields
3. Request failure returns empty list
4. Unexpected JSON shape returns empty list
5. `fetch_ship_details()` normalized MMSI lookup and miss handling

---

## Verification

### Targeted test run
Command:
`cd backend && .venv/bin/python -m pytest tests/test_ais_service.py -v`

Result:
- 5 tests collected
- 5 passed

### Live API smoke check
Command run:
`cd backend && .venv/bin/python - <<'PY' ... fetch_ships()/fetch_ship_details() ... PY`

Observed result:
- `fetched=18247`
- sample normalized ship object returned successfully
- `detail_found=True`
- `detail_id_matches=True`

Live sample:
```python
{
    'id': '219598000',
    'lat': 55.770832,
    'lon': 20.85169,
    'heading': 79.0,
    'speed': 0.1,
    'name': 'NORD SUPERIOR',
    'destination': 'NL AMS',
    'ship_type': 'tanker',
    'timestamp': '2022-07-30T20:28:58.646000+00:00'
}
```

---

## Output files

Modified:
- `backend/app/services/ais_service.py`

Created:
- `backend/tests/test_ais_service.py`
- `docs/completedphases/phase3/p3-task2-done.md`

---

## Notes / known limitation

Digitraffic coverage is Nordic/Baltic only, so ship positions are not global. That is an accepted V1 limitation documented in Task 1 and `DATA_SOURCES.md`.
