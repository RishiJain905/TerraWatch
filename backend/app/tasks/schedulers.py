"""
Background schedulers for periodic data refresh.
To be implemented in later phases.
"""
import asyncio


async def planes_refresh_loop():
    """
    Periodically refreshes plane data from ADSB.
    Empty in Phase 1 — no data fetching yet.
    """
    while True:
        # Will be implemented in Phase 2
        await asyncio.sleep(30)


async def ships_refresh_loop():
    """
    Periodically refreshes ship data from AIS.
    Empty in Phase 1 — no data fetching yet.
    """
    while True:
        # Will be implemented in Phase 3
        await asyncio.sleep(60)


async def events_refresh_loop():
    """
    Periodically refreshes world events.
    Empty in Phase 1 — no data fetching yet.
    """
    while True:
        # Will be implemented in Phase 4
        await asyncio.sleep(3600)
