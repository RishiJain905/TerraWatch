# Task 2 — ADSB Service Implementation
**Agent:** GPT 5.4 (Backend)
**Dependencies:** Task 1 (M2.7 docs + research)

## Goal

Implement `backend/app/services/adsb_service.py` to fetch real plane data from ADSB Exchange API.

## Context

- Read `../../ARCHITECTURE.md`
- Read `../../DATA_SOURCES.md` (updated in Task 1)
- Read `backend/app/core/models.py` — Plane model definition
- Read `backend/app/core/database.py` — DB access pattern

## Steps

### 1. Review Existing Files

```bash
cat backend/app/core/models.py
cat backend/app/core/database.py
cat backend/app/services/adsb_service.py  # currently a stub
```

### 2. Update Plane Model (if needed)

Check if `backend/app/core/models.py` Plane model has all fields needed:
- icao24 (hex str, primary key)
- callsign (str)
- lat (float)
- lon (float)
- alt (int, feet)
- heading (float, degrees)
- speed (float, knots)
- squawk (str)
- last_seen (datetime)

If fields are missing, add them.

### 3. Implement adsb_service.py

Replace the stub with real implementation:

```python
"""
ADSB Service — fetches live plane data from ADSB Exchange.
"""
import httpx
from typing import List, Optional

ADSB_API = "https://public-api.adsbexchange.com/VirtualRadar/AircraftList.json"

async def fetch_planes() -> List[dict]:
    """
    Fetch live plane positions from ADSB Exchange.
    Returns list of Plane dicts.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(ADSB_API)
        response.raise_for_status()
        data = response.json()
    
    ac_list = data.get("acList", [])
    planes = []
    for ac in ac_list:
        # Skip planes without position
        lat = ac.get("Lat")
        lon = ac.get("Lon")
        if lat is None or lon is None:
            continue
        
        plane = {
            "icao24": ac.get("Icao", "").lower(),
            "callsign": ac.get("Call", "").strip() or None,
            "lat": lat,
            "lon": lon,
            "alt": ac.get("Alt", 0),
            "heading": ac.get("Track", 0) or 0,
            "speed": ac.get("Spd", 0) or 0,
            "squawk": ac.get("Squawk", ""),
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }
        planes.append(plane)
    
    return planes


async def fetch_plane_details(icao24: str) -> Optional[dict]:
    """
    Fetch details for a specific plane.
    For now, fetch all and filter — optimization can come later.
    """
    planes = await fetch_planes()
    for p in planes:
        if p["icao24"] == icao24.lower():
            return p
    return None
```

Make sure to add necessary imports (datetime, timezone, httpx).

### 4. Check httpx is in requirements.txt

If `httpx` is not in `backend/requirements.txt`, add it:
```
httpx>=0.25.0
```

### 5. Test Locally

```bash
cd backend
python3 -c "
import asyncio
from app.services.adsb_service import fetch_planes
async def test():
    planes = await fetch_planes()
    print(f'Fetched {len(planes)} planes')
    if planes:
        print(f'Sample: {planes[0]}')
asyncio.run(test())
"
```

Verify it prints plane data.

## Output

- `backend/app/services/adsb_service.py` — real ADSB fetching
- `backend/app/core/models.py` — updated if needed
- `backend/requirements.txt` — updated if httpx was added
- Test output showing fetched planes

## Handoff

After completing, message GPT 5.4 (Task 3) or wait for M2.7 coordination to confirm Task 3 can start.
