# Phase 1.5 — Task 2: AIS Friends Ship Service

**Agent:** GPT 5.4 (backend)
**Related overview:** `PHASE1_5_OVERVIEW.md`

---

## Objective

Create `ais_friends_service.py` to fetch live vessel data from AIS Friends and integrate it as a secondary ship source alongside Digitraffic.

---

## AIS Friends API

**Base URL:** `https://www.aisfriends.com/api/public/v1`

**Authentication:** Bearer token in header
```
Authorization: Bearer <token>
```

**Free registration:** https://www.aisfriends.com/

---

### Endpoint: Vessels in Bounding Box

`GET https://www.aisfriends.com/api/public/v1/vessels/bbox`

**Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| lat_min | float | Yes | Min latitude |
| lat_max | float | Yes | Max latitude |
| lon_min | float | Yes | Min longitude |
| lon_max | float | Yes | Max longitude |
| from | int | No | Max age of positions in minutes |
| format | string | No | `json` (default) |

**Limits:** 1 request/minute | Max 1,000 vessels per response

**Response format:**
```json
{
  "data": [
    {
      "mmsi": "219015000",
      "name": "NORDIC SOLAR",
      "ship_type": "cargo",
      "lat": 55.77,
      "lon": 10.05,
      "speed_over_ground": 10.2,
      "course_over_ground": 79.0,
      "true_heading": 82,
      "destination": "NL AMS",
      "draught": 8.5,
      "imo": "9457786",
      "call_sign": "LAQZ4",
      "flag": "NO",
      "length": 141,
      "width": 22,
      "timestamp": "2026-04-11T05:00:00Z"
    }
  ]
}
```

---

### Global Coverage Strategy

AIS Friends returns max 1,000 vessels per request. To cover the globe:

**Option A — Large bounding box:**
- Query the full world in one bbox: `lat_min=-90, lat_max=90, lon_min=-180, lon_max=180`
- AIS Friends may return all vessels in their database (~5,000+)

**Option B — Tile the globe (if Option A is too large):**
- Divide into 6-8 regional tiles
- Query each tile in sequence
- Merge results by MMSI

Implement Option A first. If AIS Friends rejects the bounding box as too large, fall back to tiling.

**Rate limit:** AIS Friends allows 1 request per minute. Set scheduler to 60s and ensure only one request is in flight at a time.

---

## Implementation

### File: `backend/app/services/ais_friends_service.py`

Create a new service file. Follow the pattern of the existing `ais_service.py`.

Required:

1. **`AisFriendsService` class** — async service that:
   - Fetches from `https://www.aisfriends.com/api/public/v1/vessels/bbox`
   - Uses `httpx` async client
   - Passes `Authorization: Bearer <token>` header
   - Returns a list of `Ship` objects (reuse the existing Pydantic model)

2. **`AisFriendsService.fetch_ships(bbox: dict = None) -> List[Ship]`**
   - If no bbox provided, use full world: `lat_min=-90, lat_max=90, lon_min=-180, lon_max=180`
   - Map each entry to a `Ship` object
   - Add `source: str = "ais_friends"` attribute if supported

3. **Error handling:**
   - Timeout: 30 seconds (higher than plane service since AIS Friends is more restrictive)
   - HTTP 429 (rate limit): wait and retry once
   - Other HTTP errors: log and return empty list
   - Parse errors: log and return empty list

4. **Config:**
   - `AIS_FRIENDS_API_KEY` — required, from environment
   - `AIS_FRIENDS_REFRESH_SECONDS` — default 60

---

## Config

### `backend/app/config.py`

Add:
```python
AIS_FRIENDS_API_KEY: str  # Required — no default
AIS_FRIENDS_REFRESH_SECONDS: int = 60
```

### `.env.example`

Add:
```
AIS_FRIENDS_API_KEY=your_token_here
```

---

## Testing

### `backend/tests/test_ais_friends_service.py`

Create tests:

1. **`test_fetch_ships_parses_response`** — mock httpx response matching AIS Friends format, verify Ship objects are created correctly
2. **`test_fetch_ships_handles_empty_response`** — verify graceful handling of empty `data` list
3. **`test_fetch_ships_handles_timeout`** — mock timeout, verify empty list returned
4. **`test_fetch_ships_handles_rate_limit`** — mock 429 response, verify retry and eventual success or empty list
5. **`test_fetch_ships_uses_correct_auth_header`** — verify Bearer token is passed

Use `pytest` and `pytest-asyncio`. Follow the testing patterns in `tests/test_ais_service.py`.

**Note:** Tests that require the API key should be integration tests and marked with `@pytest.mark.integration` or skipped if no API key is present.

---

## Completion Criteria

- `ais_friends_service.py` exists and exports `AisFriendsService`
- `fetch_ships()` returns a list of `Ship` objects
- Bearer token authentication is implemented
- Rate limit (429) is handled gracefully
- Config has `AIS_FRIENDS_API_KEY` and `AIS_FRIENDS_REFRESH_SECONDS`
- All 5 tests in `test_ais_friends_service.py` pass
- No existing tests are broken
