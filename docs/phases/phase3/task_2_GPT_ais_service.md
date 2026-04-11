# Phase 3 — Task 2: GPT 5.4 — AIS Service Implementation

## Context

Task 1 has verified a free AIS API and documented it in `docs/DATA_SOURCES.md`. The `ais_service.py` is currently a stub returning `[]`. This task implements the real AIS data fetching and parsing.

## Instructions

You are GPT 5.4 (backend specialist). Read these files first:
- `docs/ARCHITECTURE.md`
- `docs/DATA_SOURCES.md`
- `docs/phases/phase3/PHASE3_OVERVIEW.md`
- `docs/completedphases/phase3/P3-task1-done.md` (the completion summary from Task 1)
- `backend/app/core/models.py` (Ship model definition)
- `backend/app/services/adsb_service.py` (reference implementation pattern)

## Your Task

Implement `backend/app/services/ais_service.py` to:

1. **Fetch from the AIS API verified in Task 1**
   - Use `httpx.AsyncClient` (same pattern as adsb_service.py)
   - Handle HTTP errors gracefully — return `[]` on failure
   - Use appropriate timeout (30 seconds)

2. **Parse response to Ship dicts**
   - Map API response fields to Ship model fields:
     - `id` → MMSI (string)
     - `lat` → latitude
     - `lon` → longitude
     - `heading` → course/heading in degrees
     - `speed` → speed in knots
     - `name` → ship name
     - `destination` → destination port
     - `ship_type` → cargo/tanker/passenger/fishing/other
     - `timestamp` → ISO timestamp
   - Normalize nulls and whitespace

3. **Handle unit conversions if needed**
   - Speed: m/s → knots (multiply by 1.94384) if API returns m/s
   - Coordinates: ensure decimal degrees, handle negative for W/S

4. **Implement `fetch_ships()` — returns `List[dict]`**
   - Async function
   - Returns list of ship dicts matching Ship model contract
   - Empty list on any error (no exceptions propagated)

5. **Implement `fetch_ship_details(mmsi: str)` — returns `dict | None`**
   - Fetch all ships, filter by MMSI
   - Return single ship dict or None

6. **Include proper docstrings and type hints**

## Key Constraints

- **Free API only** — no paid keys
- **Return empty list on failure** — do not crash the scheduler
- **Ship model contract** must be respected:
  ```python
  class Ship(BaseModel):
      id: str          # MMSI
      lat: float
      lon: float
      heading: float = 0
      speed: float = 0
      name: str = ""
      destination: str = ""
      ship_type: str = ""
      timestamp: Optional[str] = None
  ```

## Output Files

- `backend/app/services/ais_service.py` — replace stub with real implementation
- `backend/tests/test_ais_service.py` — create unit tests (at least 3 test cases)

## Verification

- Run: `cd backend && python -m pytest tests/test_ais_service.py -v`
- Service should return non-empty list when API is available
- All tests pass
