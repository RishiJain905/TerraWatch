"""
AIS Service — fetches live ship data from AIS providers.
To be implemented in Phase 3.
"""
from typing import List


async def fetch_ships() -> List[dict]:
    """Fetch live ship positions. Returns empty list in Phase 1."""
    return []


async def fetch_ship_details(mmsi: str) -> dict:
    """Fetch details for a specific ship. Returns empty dict in Phase 1."""
    return {}
