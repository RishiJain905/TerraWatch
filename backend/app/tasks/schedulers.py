"""Background schedulers for periodic data refresh."""

import asyncio
import logging

from app.api.websocket import (
    broadcast_plane_batch,
    broadcast_plane_update,
    broadcast_ship_batch,
    broadcast_ship_update,
)
from app.config import settings
from app.core.database import (
    delete_old_planes,
    delete_old_ships,
    open_db_connection,
    upsert_planes,
    upsert_ships,
)
from app.services.adsb_service import fetch_planes
from app.services.ais_service import fetch_ships

logger = logging.getLogger(__name__)

PLANE_REFRESH_INTERVAL_SECONDS = settings.ADSB_REFRESH_SECONDS
PLANE_STALE_AGE_MINUTES = 5
SHIP_REFRESH_INTERVAL_SECONDS = settings.AIS_REFRESH_SECONDS
SHIP_STALE_AGE_MINUTES = 10

_scheduler_tasks: list[asyncio.Task] = []


async def _broadcast_plane_messages(planes: list[dict], deleted_ids: list[str]) -> None:
    coroutines = []

    if planes:
        coroutines.append(broadcast_plane_batch(planes))

    coroutines.extend(
        broadcast_plane_update({"id": plane_id}, action="remove") for plane_id in deleted_ids
    )

    if not coroutines:
        return

    results = await asyncio.gather(*coroutines, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            logger.warning("Plane broadcast failed: %s", result)


async def _broadcast_ship_messages(ships: list[dict], deleted_ids: list[str]) -> None:
    coroutines = []

    if ships:
        coroutines.append(broadcast_ship_batch(ships))

    coroutines.extend(
        broadcast_ship_update({"id": ship_id}, action="remove") for ship_id in deleted_ids
    )

    if not coroutines:
        return

    results = await asyncio.gather(*coroutines, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            logger.warning("Ship broadcast failed: %s", result)


async def refresh_planes_once() -> list[dict]:
    """Fetch, persist, clean up, and broadcast a single plane snapshot."""
    planes = await fetch_planes()

    async with open_db_connection() as db:
        try:
            await upsert_planes(db, planes, commit=False)
            deleted_ids = await delete_old_planes(db, max_age_minutes=PLANE_STALE_AGE_MINUTES, commit=False)
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    await _broadcast_plane_messages(planes, deleted_ids)

    return planes


async def refresh_ships_once() -> list[dict]:
    """Fetch, persist, clean up, and broadcast a single ship snapshot."""
    ships = await fetch_ships()

    async with open_db_connection() as db:
        try:
            await upsert_ships(db, ships, commit=False)
            deleted_ids = await delete_old_ships(db, max_age_minutes=SHIP_STALE_AGE_MINUTES, commit=False)
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    await _broadcast_ship_messages(ships, deleted_ids)

    return ships


async def plane_fetch_loop(interval_seconds: int = PLANE_REFRESH_INTERVAL_SECONDS):
    """Continuously refresh plane data without dying on transient failures."""
    while True:
        try:
            await refresh_planes_once()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Plane refresh loop failed")

        await asyncio.sleep(interval_seconds)


async def ships_refresh_loop(interval_seconds: int = SHIP_REFRESH_INTERVAL_SECONDS):
    """Continuously refresh ship data without dying on transient failures."""
    while True:
        try:
            await refresh_ships_once()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Ship refresh loop failed")

        await asyncio.sleep(interval_seconds)


async def events_refresh_loop():
    """Placeholder event scheduler for later phases."""
    while True:
        await asyncio.sleep(3600)


def _track_scheduler_task(task: asyncio.Task) -> None:
    _scheduler_tasks.append(task)

    def _discard(completed_task: asyncio.Task) -> None:
        if completed_task in _scheduler_tasks:
            _scheduler_tasks.remove(completed_task)

    task.add_done_callback(_discard)


def get_scheduler_tasks() -> list[asyncio.Task]:
    """Return currently active scheduler tasks."""
    return [task for task in _scheduler_tasks if not task.done()]


async def start_schedulers(
    *,
    interval_seconds: int = PLANE_REFRESH_INTERVAL_SECONDS,
    ship_interval_seconds: int = SHIP_REFRESH_INTERVAL_SECONDS,
) -> list[asyncio.Task]:
    """Start background scheduler tasks once."""
    active_tasks = get_scheduler_tasks()
    if active_tasks:
        return active_tasks

    plane_task = asyncio.create_task(
        plane_fetch_loop(interval_seconds=interval_seconds),
        name="plane-fetch-loop",
    )
    ship_task = asyncio.create_task(
        ships_refresh_loop(interval_seconds=ship_interval_seconds),
        name="ship-fetch-loop",
    )
    _track_scheduler_task(plane_task)
    _track_scheduler_task(ship_task)
    return [plane_task, ship_task]


async def stop_schedulers() -> None:
    """Cancel and await all active scheduler tasks."""
    active_tasks = get_scheduler_tasks()
    if not active_tasks:
        _scheduler_tasks.clear()
        return

    for task in active_tasks:
        task.cancel()

    await asyncio.gather(*active_tasks, return_exceptions=True)
    _scheduler_tasks.clear()
