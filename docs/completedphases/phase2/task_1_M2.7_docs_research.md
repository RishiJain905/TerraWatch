# Task 1 — Phase 2 Docs + ADS-B API Research
**Agent:** MiniMax M2.7 (Coordinator)
**Dependencies:** None

## Goal

Create Phase 2 documentation and verify the ADSB Exchange API works as expected.

## Steps

### 1. Read Context Files
- `../../ARCHITECTURE.md`
- `../../DATA_SOURCES.md`
- `PHASE2_OVERVIEW.md` (in this folder — you just created it)

### 2. Update DATA_SOURCES.md with ADS-B API Details

Add detailed ADS-B Exchange API information to `../../DATA_SOURCES.md`:

```
## ADS-B Exchange API

**Endpoint:**
https://public-api.adsbexchange.com/VirtualRadar/AircraftList.json

**No API key required**

**Response format:** JSON with `acList` array.

Sample `acList` item:
{
  "Icao": "a1b2c3",       // hex ICAO24 address
  "Lat": 51.5,           // decimal degrees
  "Lon": -0.1,           // decimal degrees
  "Alt": 35000,          // feet MSL
  "Track": 270,          // degrees true heading
  "Speed": 450,          // knots ground speed
  "Call": "BAW123",      // callsign
  "Squawk": "7200",      // transponder code
  "Reg": "G-EUPU",       // registration (if available)
  "Type": "A320",        // aircraft type (if available)
  "From": "LHR",         // origin airport
  "To": "JFK"            // destination airport
}

**Rate limits:** One request per 30 seconds recommended.
```

Append this to DATA_SOURCES.md under the Aircraft Data section (replace placeholder).

### 3. Test the API

```bash
curl "https://public-api.adsbexchange.com/VirtualRadar/AircraftList.json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
ac = data.get('acList', [])
print(f'Total aircraft: {len(ac)}')
if ac:
    p = ac[0]
    print(f'Sample: Icao={p.get(\"Icao\")}, Lat={p.get(\"Lat\")}, Lon={p.get(\"Lon\")}, Alt={p.get(\"Alt\")}, Call={p.get(\"Call\")}')
"
```

Verify it returns data. Note the format and any quirks.

### 4. Create phase2 PHASE2_OVERVIEW.md

Make sure `docs/completedphases/phase2/PHASE2_OVERVIEW.md` is complete. It should include:
- Phase goal
- What's NOT in this phase
- Tasks table
- Data flow diagram
- Key technical decisions
- Success criteria

### 5. Verify DATABASE Schema

Check `backend/app/core/database.py` — ensure the `planes` table exists with the right schema. If the schema differs from what's needed for ADS-B data, note what changes are required for Task 2.

## Output

1. Updated `docs/DATA_SOURCES.md` with ADS-B Exchange API details
2. Verified `docs/completedphases/phase2/PHASE2_OVERVIEW.md` is complete
3. API test results (how many planes, sample data)
4. Any schema issues that need fixing before Task 2

## Handoff to Task 2 (GPT 5.4)

After completing, message GPT 5.4 that Task 1 is done and Task 2 (adsb_service.py) can start. Share:
- The ADS-B API endpoint and response format
- Any schema issues found
- The expected Plane model structure
