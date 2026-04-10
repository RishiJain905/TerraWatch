"""
ADSB Service — fetches live plane data from ADSB Exchange.
To be implemented in Phase 2.
"""
from typing import List


async def fetch_planes() -> List[dict]:
    """Fetch live plane positions. Returns empty list in Phase 1."""
    return []


async def fetch_plane_details(icao24: str) -> dict:
    """Fetch details for a specific plane. Returns empty dict in Phase 1."""
    return {}
