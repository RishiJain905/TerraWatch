# Phase 1.5 — Task 1: ADSB.lol Plane Service

**Agent:** GPT 5.4 (backend)
**Related overview:** `PHASE1_5_OVERVIEW.md`

---

## Objective

Create `adsblol_service.py` to fetch live aircraft data from ADSB.lol and integrate it as a secondary plane source alongside OpenSky.

---

## ADSB.lol API

**Endpoint:** `GET https://api.adsb.lol/aircraft/json`

No API key required.

**Response format:**
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
      "tail": "9V-SFM"
    }
  ],
  "ctime": 1611366621,
  "last_timestamp": 1611366621
}
```

**Notes:**
- `hex` / `icao24` — lowercase ICAO code. Normalize to uppercase to match OpenSky's `icao24`.
- `flight` — callsign (ICAO or IATA format). Store as-is.
- `alt` — altitude in feet
- `dir` — direction/heading in degrees
- `speed` — speed in knots
- `squawk` — transponder code

---

## Implementation

### File: `backend/app/services/adsblol_service.py`

Create a new service file. Follow the pattern of the existing `adsb_service.py`.

Required:

1. **`AdsblolService` class** — async service that:
   - Fetches from `https://api.adsb.lol/aircraft/json`
   - Uses `httpx` async client (same as `adsb_service.py`)
   - Handles gzip decompression if needed
   - Returns a list of `Plane` objects (reuse the existing Pydantic model from `core/models.py`)

2. **`normalize_hex(hex_str: str) -> str`** — convert hex to uppercase

3. **`AdsblolService.fetch_planes() -> List[Plane]`**
   - Fetch the JSON
   - Map each entry to a `Plane` object
   - Use sensible defaults for fields ADSB.lol doesn't provide that the `Plane` model requires
   - Add `source: str = "adsblol"` attribute if the model supports it

4. **Error handling:**
   - Timeout: 10 seconds
   - HTTP errors: log and return empty list
   - Parse errors: log and return empty list

5. **Refresh interval:** Use `ADSBLOL_REFRESH_SECONDS` from config (default 30s)

---

## Config

### `backend/app/config.py`

Add:
```python
ADSBLOL_REFRESH_SECONDS: int = 30
```

### `backend/app/services/__init__.py`

Export `AdsblolService` if the pattern exists in the codebase.

---

## Testing

### `backend/tests/test_adsblol_service.py`

Create tests:

1. **`test_fetch_planes_parses_response`** — mock httpx response matching ADSB.lol format, verify Plane objects are created correctly
2. **`test_hex_normalized_to_uppercase`** — verify `76cccd` becomes `76CCCD`
3. **`test_fetch_planes_handles_empty_response`** — verify graceful handling of empty `ac` list
4. **`test_fetch_planes_handles_timeout`** — mock timeout, verify empty list returned
5. **`test_fetch_planes_handles_http_error`** — mock non-200 response, verify empty list returned

Use `pytest` and `pytest-asyncio`. Follow the testing patterns in `tests/test_adsb_service.py`.

---

## Completion Criteria

- `adsblol_service.py` exists and exports `AdsblolService`
- `fetch_planes()` returns a list of `Plane` objects
- Hex codes are normalized to uppercase
- Config has `ADSBLOL_REFRESH_SECONDS`
- All 5 tests in `test_adsblol_service.py` pass
- No existing tests are broken
