"""Background schedulers for periodic data refresh."""

import asyncio
import logging

from typing import Any, Callable

from app.api.websocket import (
    broadcast_conflict_batch,
    broadcast_event_batch,
    broadcast_plane_batch,
    broadcast_plane_update,
    broadcast_ship_batch,
    broadcast_ship_update,
)
from app.config import settings
from app.core.dedup import (
    deduplicate_planes,
    deduplicate_ships,
    filter_stale_ships_ais_friends,
    filter_stale_ships_digitraffic,
)
from app.core.database import (
    db_write_guard,
    delete_old_events,
    delete_old_planes,
    delete_old_ships,
    get_db,
    open_db_connection,
    upsert_events,
    upsert_planes,
    upsert_ships,
)

from app.services.ais_service import fetch_ships
from app.services.aisstream_service import AisstreamService
from app.services.adsb_service import fetch_planes
from app.services.adsblol_service import fetch_planes as fetch_adsblol_planes
from app.services.gdelt_service import fetch_events as fetch_gdelt_events

logger = logging.getLogger(__name__)

PLANE_REFRESH_INTERVAL_SECONDS = settings.ADSB_REFRESH_SECONDS
PLANE_STALE_AGE_MINUTES = settings.STALE_PLANE_SECONDS // 60
SHIP_REFRESH_INTERVAL_SECONDS = settings.AIS_REFRESH_SECONDS
SHIP_STALE_AGE_MINUTES = settings.STALE_SHIP_SECONDS // 60
AISSTREAM_BATCH_INTERVAL_SECONDS = settings.AISSTREAM_BATCH_INTERVAL_SECONDS

GDELT_REFRESH_SECONDS = settings.GDELT_REFRESH_SECONDS

# GDELT categories considered violent — used to populate the conflicts heatmap
VIOLENT_GDELT_CATEGORIES = [
    "assault", "fight", "unconventional_mass_gvc",
    "conventional_mass_gvc", "force_range", "rioting",
]

_scheduler_tasks: list[asyncio.Task] = []
_ship_state_lock: asyncio.Lock | None = None
_ship_state_lock_loop: asyncio.AbstractEventLoop | None = None
_latest_digitraffic_ships: dict[str, dict] = {}
_latest_aisstream_ships: dict[str, dict] = {}
_aisstream_service: AisstreamService | None = None


def _normalize_ship_id(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _get_ship_state_lock() -> asyncio.Lock:
    global _ship_state_lock, _ship_state_lock_loop
    loop = asyncio.get_running_loop()
    if _ship_state_lock is None or _ship_state_lock_loop is not loop:
        _ship_state_lock = asyncio.Lock()
        _ship_state_lock_loop = loop
    return _ship_state_lock


def reset_ship_scheduler_state() -> None:
    """Reset in-memory ship snapshots. Useful for tests and shutdown cleanup."""
    global _latest_digitraffic_ships, _latest_aisstream_ships
    _latest_digitraffic_ships = {}
    _latest_aisstream_ships = {}


def _update_ship_snapshot(snapshot: dict[str, dict], ships: list[dict]) -> dict[str, dict]:
    updated_snapshot = {} if snapshot is None else dict(snapshot)
    for ship in ships:
        ship_id = _normalize_ship_id(ship.get("id"))
        if not ship_id:
            continue
        updated_ship = dict(ship)
        updated_ship["id"] = ship_id
        updated_snapshot[ship_id] = updated_ship
    return updated_snapshot


def _prune_ship_snapshot(
    snapshot: dict[str, dict],
    stale_filter: Callable[[list[dict]], list[dict]],
) -> dict[str, dict]:
    return _update_ship_snapshot({}, stale_filter(list(snapshot.values())))


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


async def _persist_and_broadcast_ships(ships: list[dict]) -> list[dict]:
    async with db_write_guard():
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


async def refresh_planes_once() -> list[dict]:
    """Fetch, persist, clean up, and broadcast a single plane snapshot."""
    open_sky_result, adsblol_result = await asyncio.gather(
        fetch_planes(
            client_id=settings.OPENSKY_CLIENT_ID or None,
            client_secret=settings.OPENSKY_CLIENT_SECRET or None,
        ),
        fetch_adsblol_planes(),
        return_exceptions=True,
    )
    if isinstance(open_sky_result, Exception):
        logger.warning("OpenSky plane refresh failed; continuing with ADSB.lol only: %s", open_sky_result)
        open_sky_planes = []
    else:
        open_sky_planes = open_sky_result

    if isinstance(adsblol_result, Exception):
        logger.warning("ADSB.lol plane refresh failed; continuing with OpenSky only: %s", adsblol_result)
        adsblol_planes = []
    else:
        adsblol_planes = adsblol_result

    planes = deduplicate_planes(open_sky_planes, adsblol_planes)

    async with db_write_guard():
        async with open_db_connection() as db:
            try:
                await upsert_planes(db, planes, commit=False)
                deleted_ids = await delete_old_planes(db, max_age_minutes=PLANE_STALE_AGE_MINUTES, commit=False)
                await db.commit()
            except Exception:
                await db.rollback()
                raise

    await _broadcast_plane_messages(planes, deleted_ids)
    logger.info("Plane refresh: %d planes from OpenSky, %d from ADSB.lol, %d merged, %d deleted",
                len(open_sky_planes), len(adsblol_planes), len(planes), len(deleted_ids))

    return planes


async def refresh_ships_once() -> list[dict]:
    """Refresh Digitraffic ships, merge with cached aisstream ships, then persist and broadcast."""
    global _latest_digitraffic_ships, _latest_aisstream_ships

    fetched_digitraffic_ships = await fetch_ships()

    async with _get_ship_state_lock():
        current_digitraffic = dict(_latest_digitraffic_ships)
        current_aisstream = dict(_latest_aisstream_ships)

        if fetched_digitraffic_ships or not current_digitraffic:
            proposed_digitraffic = _update_ship_snapshot({}, fetched_digitraffic_ships)
        else:
            logger.warning("Digitraffic ship refresh returned no ships; retaining previous snapshot")
            proposed_digitraffic = current_digitraffic

        proposed_digitraffic = _prune_ship_snapshot(
            proposed_digitraffic,
            filter_stale_ships_digitraffic,
        )
        proposed_aisstream = _prune_ship_snapshot(
            current_aisstream,
            filter_stale_ships_ais_friends,
        )
        merged_ships = deduplicate_ships(
            list(proposed_digitraffic.values()),
            list(proposed_aisstream.values()),
        )

    persisted_ships = await _persist_and_broadcast_ships(merged_ships)

    async with _get_ship_state_lock():
        _latest_digitraffic_ships = proposed_digitraffic
        _latest_aisstream_ships = _prune_ship_snapshot(
            _latest_aisstream_ships,
            filter_stale_ships_ais_friends,
        )

    return persisted_ships


async def ingest_aisstream_batch(ships: list[dict]) -> list[dict]:
    """Merge an incremental aisstream batch into the cached ship state and broadcast the result."""
    global _latest_digitraffic_ships, _latest_aisstream_ships

    async with _get_ship_state_lock():
        current_digitraffic = _prune_ship_snapshot(
            _latest_digitraffic_ships,
            filter_stale_ships_digitraffic,
        )
        proposed_aisstream = _prune_ship_snapshot(
            _latest_aisstream_ships,
            filter_stale_ships_ais_friends,
        )
        proposed_aisstream = _update_ship_snapshot(proposed_aisstream, ships)
        proposed_aisstream = _prune_ship_snapshot(
            proposed_aisstream,
            filter_stale_ships_ais_friends,
        )
        merged_ships = deduplicate_ships(
            list(current_digitraffic.values()),
            list(proposed_aisstream.values()),
        )

    persisted_ships = await _persist_and_broadcast_ships(merged_ships)

    async with _get_ship_state_lock():
        _latest_digitraffic_ships = _prune_ship_snapshot(
            _latest_digitraffic_ships,
            filter_stale_ships_digitraffic,
        )
        _latest_aisstream_ships = _prune_ship_snapshot(
            _latest_aisstream_ships,
            filter_stale_ships_ais_friends,
        )
        _latest_aisstream_ships = _update_ship_snapshot(_latest_aisstream_ships, ships)
        _latest_aisstream_ships = _prune_ship_snapshot(
            _latest_aisstream_ships,
            filter_stale_ships_ais_friends,
        )

    return persisted_ships


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
    """Continuously refresh Digitraffic ship data without dying on transient failures."""
    while True:
        try:
            await refresh_ships_once()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Ship refresh loop failed")

        await asyncio.sleep(interval_seconds)


async def aisstream_listener_loop(
    *,
    batch_interval_seconds: int = AISSTREAM_BATCH_INTERVAL_SECONDS,
    service: AisstreamService | None = None,
) -> None:
    """Continuously listen to aisstream and merge emitted batches with the latest Digitraffic snapshot."""
    global _aisstream_service

    active_service = service or _aisstream_service or AisstreamService()
    _aisstream_service = active_service

    if not active_service.api_key:
        logger.info("AISSTREAM_API_KEY missing; running Digitraffic-only ship scheduler")
        return

    try:
        while True:
            try:
                async for batch in active_service.listen(batch_interval=batch_interval_seconds):
                    try:
                        await ingest_aisstream_batch(batch)
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        logger.exception("Failed to persist or broadcast aisstream ship batch")
                return
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("aisstream listener loop failed")
                await active_service.close()
                if _aisstream_service is active_service:
                    _aisstream_service = None
                await asyncio.sleep(1)
                active_service = AisstreamService()
                _aisstream_service = active_service
                if not active_service.api_key:
                    logger.info("AISSTREAM_API_KEY missing; running Digitraffic-only ship scheduler")
                    return
    finally:
        await active_service.close()
        if _aisstream_service is active_service:
            _aisstream_service = None


async def gdelt_refresh_loop(interval_seconds: int = GDELT_REFRESH_SECONDS):
    """Continuously refresh GDELT events without dying on transient failures."""
    while True:
        try:
            await _gdelt_fetch_and_broadcast()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("GDELT refresh loop failed")

        await asyncio.sleep(interval_seconds)


async def _gdelt_fetch_and_broadcast():
    """Fetch GDELT events, persist to DB, and broadcast via WebSocket."""
    events = await fetch_gdelt_events()
    if not events:
        return

    async with db_write_guard():
        db = await get_db()
        try:
            await upsert_events(db, events, commit=False)
            await delete_old_events(db, max_age_days=30, commit=False)
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    await broadcast_event_batch(events)

    # Also broadcast violent events as conflicts for the heatmap layer
    violent_events = [e for e in events if e.get("category") in VIOLENT_GDELT_CATEGORIES]
    if violent_events:
        await broadcast_conflict_batch(violent_events)

    logger.info("GDELT refresh: persisted %d events (%d violent/conflicts)", len(events), len(violent_events))


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
    aisstream_batch_interval_seconds: int = AISSTREAM_BATCH_INTERVAL_SECONDS,
) -> list[asyncio.Task]:
    """Start any missing background scheduler tasks."""
    global _aisstream_service

    active_tasks = {task.get_name(): task for task in get_scheduler_tasks()}

    if "plane-fetch-loop" not in active_tasks:
        plane_task = asyncio.create_task(
            plane_fetch_loop(interval_seconds=interval_seconds),
            name="plane-fetch-loop",
        )
        _track_scheduler_task(plane_task)

    if "ship-fetch-loop" not in active_tasks:
        ship_task = asyncio.create_task(
            ships_refresh_loop(interval_seconds=ship_interval_seconds),
            name="ship-fetch-loop",
        )
        _track_scheduler_task(ship_task)

    if settings.AISSTREAM_API_KEY.strip():
        active_tasks = {task.get_name(): task for task in get_scheduler_tasks()}
        if "aisstream-listener-loop" not in active_tasks:
            _aisstream_service = AisstreamService()
            aisstream_task = asyncio.create_task(
                aisstream_listener_loop(
                    batch_interval_seconds=aisstream_batch_interval_seconds,
                    service=_aisstream_service,
                ),
                name="aisstream-listener-loop",
            )
            _track_scheduler_task(aisstream_task)
    else:
        logger.info("AISSTREAM_API_KEY missing; aisstream scheduler not started")

    # GDELT events scheduler — always starts (no API key required)
    active_tasks = {task.get_name(): task for task in get_scheduler_tasks()}
    if "gdelt-refresh-loop" not in active_tasks:
        gdelt_task = asyncio.create_task(
            gdelt_refresh_loop(),
            name="gdelt-refresh-loop",
        )
        _track_scheduler_task(gdelt_task)

    return get_scheduler_tasks()


async def stop_schedulers() -> None:
    """Cancel and await all active scheduler tasks."""
    global _aisstream_service

    active_tasks = get_scheduler_tasks()
    if active_tasks:
        for task in active_tasks:
            task.cancel()

        await asyncio.gather(*active_tasks, return_exceptions=True)

    _scheduler_tasks.clear()

    if _aisstream_service is not None:
        await _aisstream_service.close()
        _aisstream_service = None

    reset_ship_scheduler_state()
