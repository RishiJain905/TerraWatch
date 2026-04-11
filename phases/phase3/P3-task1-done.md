# Phase 3 Task 1 — DONE ✓

**Agent:** M2.7 (Coordinator)
**Date:** 2026-04-11
**Status:** COMPLETE

---

## API Chosen: Digitraffic (Finland) — REST API

**Why Digitraffic:**
- Truly free, no API key required
- REST endpoint — simpler to implement than WebSocket alternatives
- Returns rich, well-structured data (GeoJSON positions + vessel metadata)
- Supports 60s refresh (cache-control: max-age=60)
- Already documented in DATA_SOURCES.md with verified response formats

**Rejected alternatives:**
| API | Reason Rejected |
|-----|-----------------|
| AISHub | Requires reciprocal AIS feed hardware — not immediately accessible |
| AISStream.io | Requires free API key signup; WebSocket adds complexity |
| MarineTraffic | Heavy JS rendering, not suitable for direct API access |
| VesselFinder/ORVRTS | Primarily paid aggregators, free tier insufficient |
| Norwegian Coastal Admin | Raw TCP stream requires special handling |

---

## Verified Endpoints

### 1. Vessel Positions (GeoJSON)
```
GET https://meri.digitraffic.fi/api/ais/v1/locations
Header: Accept-Encoding: gzip
```

Returns ~18,247 vessels in Finnish/Baltic Nordic waters (lat 54–66°N, lon 10–37°E).

### 2. Vessel Metadata
```
GET https://meri.digitraffic.fi/api/ais/v1/vessels
Header: Accept-Encoding: gzip
```

Returns ~18,268 vessel metadata records (names, destinations, ship types).

**Implementation note:** Fetch BOTH endpoints every 60s. Merge by MMSI.

---

## Response-to-Ship-Model Mapping

### From `/api/ais/v1/locations` (positions):
| API Field | Ship Model Field | Notes |
|-----------|-----------------|-------|
| `mmsi` | `id` | Primary key, integer → string |
| `geometry.coordinates[0]` | `lon` | GeoJSON order: [lon, lat] |
| `geometry.coordinates[1]` | `lat` | |
| `properties.cog` | `heading` | Course over ground, degrees |
| `properties.sog` | `speed` | Speed over ground, already in knots |
| `properties.timestampExternal` | `timestamp` | Epoch ms → ISO 8601 UTC string |

### From `/api/ais/v1/vessels` (metadata):
| API Field | Ship Model Field | Notes |
|-----------|-----------------|-------|
| `name` | `name` | Ship name string |
| `destination` | `destination` | Destination port string |
| `shipType` | `ship_type` | Numeric AIS code → mapped string (see below) |

---

## AIS shipType Code → String Mapping

Implement in `ais_service.py`:

```python
def _map_ship_type(code: int) -> str:
    """Map AIS shipType code to ship_type string."""
    mapping = {
        70: "cargo",      # Cargo vessels
        80: "tanker",     # Tanker vessels
        60: "passenger",  # Passenger vessels
        52: "tug",        # Tugboats
        31: "tug",        # Towing operations
        30: "fishing",    # Fishing vessels
        36: "sailing",   # Sailing vessels
        # Everything else → "other"
    }
    return mapping.get(code, "other")
```

Common codes seen in live data: 70 (9429 vessels), 80 (5208 vessels), 60 (658 vessels), 52 (499 vessels), 90 (560 vessels).

---

## Unit Conversions

| Field | API Unit | Ship Model Unit | Conversion |
|-------|----------|----------------|------------|
| `sog` | knots | knots | None needed — already in knots |
| `cog` | degrees | heading (degrees) | None needed |
| `timestampExternal` | epoch milliseconds | ISO 8601 string | `datetime.fromtimestamp(ts/1000, tz=UTC).isoformat()` |

No altitude conversion needed — AIS is 2D (no alt field).

---

## Verified Sample Response (live data, 2026-04-11)

### Position (`/api/ais/v1/locations`):
```json
{
  "type": "FeatureCollection",
  "dataUpdatedTime": "2026-04-11T01:44:52Z",
  "features": [
    {
      "mmsi": 219598000,
      "geometry": { "type": "Point", "coordinates": [20.85169, 55.770832] },
      "properties": {
        "mmsi": 219598000,
        "sog": 0.1,
        "cog": 346.5,
        "heading": 79,
        "navStat": 1,
        "timestampExternal": 1659212938646
      }
    }
  ]
}
```

### Metadata (`/api/ais/v1/vessels`):
```json
{
  "mmsi": 219598000,
  "name": "NORD SUPERIOR",
  "callSign": "OWPA2",
  "imo": 9692129,
  "destination": "NL AMS",
  "shipType": 80
}
```

### Merged Ship Object (what ais_service.py should return):
```python
{
    "id": "219598000",
    "lat": 55.770832,
    "lon": 20.85169,
    "heading": 79.0,
    "speed": 0.1,
    "name": "NORD SUPERIOR",
    "destination": "NL AMS",
    "ship_type": "tanker",
    "timestamp": "2022-07-30T22:48:58+00:00"  # from timestampExternal
}
```

---

## Notes for Task 2 Implementer (GPT)

1. **Two fetch calls required** per refresh cycle — `/locations` (positions) and `/vessels` (metadata). Merge on MMSI for full data.

2. **HTTP client must support gzip decompression.** In `httpx`:
   ```python
   async with httpx.AsyncClient() as client:
       resp = await client.get(url, headers={"Accept-Encoding": "gzip"})
   ```
   The API returns `cache-control: max-age=60` — polling every 60s is safe and respectful.

3. **`timestampExternal` is epoch milliseconds.** Convert to ISO 8601:
   ```python
   from datetime import datetime, timezone
   ts = props["timestampExternal"]
   timestamp = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()
   ```

4. **`mmsi` is an integer in responses** but the Ship model uses `id: str`. Convert: `str(mmsi)`.

5. **`geometry.coordinates` is [lon, lat] in GeoJSON order**, NOT [lat, lon].

6. **Coverage is Nordic/Baltic only.** Ships in other regions will not appear. This is a known limitation of Digitraffic for V1. Global AIS is a V2+ concern (see AISStream.io as upgrade path).

7. **Vessel metadata (`/vessels`) is separate from positions (`/locations`).** Some vessels may appear in one but not the other — handle missing fields gracefully with defaults.

8. **Rate limit:** cache-control says `max-age=60`. Do NOT poll more frequently than once per 60 seconds.

---

## Verification

✅ Live test confirmed: `curl --compressed https://meri.digitraffic.fi/api/ais/v1/locations` returns 18,247 vessels
✅ Live test confirmed: `curl --compressed https://meri.digitraffic.fi/api/ais/v1/vessels` returns 18,268 vessel metadata records
✅ gzip decompression required — confirmed working with `--compressed` flag
✅ Data structure verified: GeoJSON format, all required fields present
✅ Ship type codes verified: cargo=70, tanker=80, passenger=60, etc.
