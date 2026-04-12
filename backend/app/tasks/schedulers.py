"""Background schedulers for periodic data refresh."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.api.websocket import (
    broadcast_plane_batch,
    broadcast_plane_update,
    broadcast_ship_batch,
    broadcast_ship_update,
)
from app.config import settings
from app.core.database import (
    db_write_guard,
    delete_old_planes,
    delete_old_ships,
    open_db_connection,
    upsert_planes,
    upsert_ships,
)
from app.services.ais_service import fetch_ships
from app.services.aisstream_service import AisstreamService
from app.services.adsb_service import fetch_planes

logger = logging.getLogger(__name__)

PLANE_REFRESH_INTERVAL_SECONDS = settings.ADSB_REFRESH_SECONDS
PLANE_STALE_AGE_MINUTES = 5
SHIP_REFRESH_INTERVAL_SECONDS = settings.AIS_REFRESH_SECONDS
SHIP_STALE_AGE_MINUTES = 10
AISSTREAM_BATCH_INTERVAL_SECONDS = settings.AISSTREAM_BATCH_INTERVAL_SECONDS

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


def _parse_ship_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    return None


def _ship_source_priority(source_name: str) -> int:
    return 2 if source_name == "digitraffic" else 1


def _ship_value_is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


def _merge_ship_metadata(preferred_ship: dict, other_ship: dict) -> dict:
    merged_ship = dict(preferred_ship)
    for field_name in ("name", "destination", "timestamp", "lat", "lon"):
        if _ship_value_is_missing(merged_ship.get(field_name)) and not _ship_value_is_missing(
            other_ship.get(field_name)
        ):
            merged_ship[field_name] = other_ship[field_name]

    preferred_ship_type = merged_ship.get("ship_type")
    other_ship_type = other_ship.get("ship_type")
    if (
        _ship_value_is_missing(preferred_ship_type)
        or str(preferred_ship_type).strip().lower() == "other"
    ) and not _ship_value_is_missing(other_ship_type) and str(other_ship_type).strip().lower() != "other":
        merged_ship["ship_type"] = other_ship_type

    for numeric_field in ("heading", "speed"):
        if merged_ship.get(numeric_field) is None and other_ship.get(numeric_field) is not None:
            merged_ship[numeric_field] = other_ship[numeric_field]

    return merged_ship


def _prefer_ship(
    existing_ship: dict,
    existing_source: str,
    candidate_ship: dict,
    candidate_source: str,
) -> tuple[dict, str]:
    existing_timestamp = _parse_ship_timestamp(existing_ship.get("timestamp"))
    candidate_timestamp = _parse_ship_timestamp(candidate_ship.get("timestamp"))

    if candidate_timestamp and not existing_timestamp:
        winner_ship, winner_source = candidate_ship, candidate_source
        loser_ship = existing_ship
    elif existing_timestamp and not candidate_timestamp:
        winner_ship, winner_source = existing_ship, existing_source
        loser_ship = candidate_ship
    elif candidate_timestamp and existing_timestamp:
        if candidate_timestamp > existing_timestamp:
            winner_ship, winner_source = candidate_ship, candidate_source
            loser_ship = existing_ship
        elif candidate_timestamp < existing_timestamp:
            winner_ship, winner_source = existing_ship, existing_source
            loser_ship = candidate_ship
        elif _ship_source_priority(candidate_source) > _ship_source_priority(existing_source):
            winner_ship, winner_source = candidate_ship, candidate_source
            loser_ship = existing_ship
        else:
            winner_ship, winner_source = existing_ship, existing_source
            loser_ship = candidate_ship
    elif _ship_source_priority(candidate_source) > _ship_source_priority(existing_source):
        winner_ship, winner_source = candidate_ship, candidate_source
        loser_ship = existing_ship
    else:
        winner_ship, winner_source = existing_ship, existing_source
        loser_ship = candidate_ship

    return _merge_ship_metadata(winner_ship, loser_ship), winner_source


def deduplicate_ships(digitraffic_ships: list[dict], aisstream_ships: list[dict]) -> list[dict]:
    """Merge ship snapshots by MMSI, preferring newer timestamps and Digitraffic on ties."""
    merged_by_id: dict[str, tuple[dict, str]] = {}

    for source_name, ships in (("digitraffic", digitraffic_ships), ("aisstream", aisstream_ships)):
        for ship in ships:
            ship_id = _normalize_ship_id(ship.get("id"))
            if not ship_id:
                continue

            candidate_ship = dict(ship)
            candidate_ship["id"] = ship_id

            existing_entry = merged_by_id.get(ship_id)
            if existing_entry is None:
                merged_by_id[ship_id] = (candidate_ship, source_name)
                continue

            existing_ship, existing_source = existing_entry
            merged_by_id[ship_id] = _prefer_ship(
                existing_ship,
                existing_source,
                candidate_ship,
                source_name,
            )

    return [ship for ship, _source_name in merged_by_id.values()]


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


def _prune_stale_ship_snapshot(snapshot: dict[str, dict]) -> dict[str, dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=SHIP_STALE_AGE_MINUTES)
    pruned_snapshot: dict[str, dict] = {}

    for ship_id, ship in snapshot.items():
        timestamp = _parse_ship_timestamp(ship.get("timestamp"))
        if timestamp is None or timestamp >= cutoff:
            pruned_snapshot[ship_id] = ship

    return pruned_snapshot


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
    """Refresh Digitraffic ships, merge with cached aisstream ships, then persist and broadcast."""
    global _latest_digitraffic_ships, _latest_aisstream_ships

    fetched_digitraffic_ships = await fetch_ships()

    async with _get_ship_state_lock():
        if fetched_digitraffic_ships or not _latest_digitraffic_ships:
            _latest_digitraffic_ships = _update_ship_snapshot({}, fetched_digitraffic_ships)
        else:
            logger.warning("Digitraffic ship refresh returned no ships; retaining previous snapshot")

        _latest_digitraffic_ships = _prune_stale_ship_snapshot(_latest_digitraffic_ships)
        _latest_aisstream_ships = _prune_stale_ship_snapshot(_latest_aisstream_ships)
        merged_ships = deduplicate_ships(
            list(_latest_digitraffic_ships.values()),
            list(_latest_aisstream_ships.values()),
        )
        return await _persist_and_broadcast_ships(merged_ships)


async def ingest_aisstream_batch(ships: list[dict]) -> list[dict]:
    """Merge an incremental aisstream batch into the cached ship state and broadcast the result."""
    global _latest_digitraffic_ships, _latest_aisstream_ships

    async with _get_ship_state_lock():
        _latest_digitraffic_ships = _prune_stale_ship_snapshot(_latest_digitraffic_ships)
        _latest_aisstream_ships = _prune_stale_ship_snapshot(_latest_aisstream_ships)
        _latest_aisstream_ships = _update_ship_snapshot(_latest_aisstream_ships, ships)
        merged_ships = deduplicate_ships(
            list(_latest_digitraffic_ships.values()),
            list(_latest_aisstream_ships.values()),
        )
        return await _persist_and_broadcast_ships(merged_ships)


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
        async for batch in active_service.listen(batch_interval=batch_interval_seconds):
            try:
                await ingest_aisstream_batch(batch)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Failed to persist or broadcast aisstream ship batch")
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("aisstream listener loop failed")
    finally:
        await active_service.close()
        if _aisstream_service is active_service:
            _aisstream_service = None


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
    aisstream_batch_interval_seconds: int = AISSTREAM_BATCH_INTERVAL_SECONDS,
) -> list[asyncio.Task]:
    """Start background scheduler tasks once."""
    global _aisstream_service

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

    if settings.AISSTREAM_API_KEY.strip():
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
