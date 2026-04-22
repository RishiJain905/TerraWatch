import asyncio
import os
from math import ceil
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

from app.config import settings

_backend_root = Path(__file__).resolve().parents[2]
_project_root = _backend_root.parent if _backend_root.name == "backend" else _backend_root
DATABASE_PATH = os.getenv("TERRAWATCH_DB_PATH", str(_project_root / "terrawatch.db"))

_db_instance: aiosqlite.Connection | None = None
_db_write_lock: asyncio.Lock | None = None
_db_write_lock_loop: asyncio.AbstractEventLoop | None = None

_PLANE_COLUMN_DEFINITIONS = {
    "id": "TEXT PRIMARY KEY",
    "lat": "REAL",
    "lon": "REAL",
    "alt": "INTEGER DEFAULT 0",
    "heading": "REAL DEFAULT 0",
    "callsign": "TEXT DEFAULT ''",
    "squawk": "TEXT DEFAULT ''",
    "speed": "REAL DEFAULT 0",
    "timestamp": "TEXT",
}

_PLANE_UPSERT_SQL = """
    INSERT INTO planes (id, lat, lon, alt, heading, callsign, squawk, speed, timestamp)
    VALUES (:id, :lat, :lon, :alt, :heading, :callsign, :squawk, :speed, :timestamp)
    ON CONFLICT(id) DO UPDATE SET
        lat = excluded.lat,
        lon = excluded.lon,
        alt = excluded.alt,
        heading = excluded.heading,
        callsign = excluded.callsign,
        squawk = excluded.squawk,
        speed = excluded.speed,
        timestamp = excluded.timestamp
"""

_SHIP_COLUMN_DEFINITIONS = {
    "id": "TEXT PRIMARY KEY",
    "lat": "REAL",
    "lon": "REAL",
    "heading": "REAL DEFAULT 0",
    "speed": "REAL DEFAULT 0",
    "name": "TEXT DEFAULT ''",
    "destination": "TEXT DEFAULT ''",
    "ship_type": "TEXT DEFAULT ''",
    "timestamp": "TEXT",
}

_SHIP_UPSERT_SQL = """
    INSERT INTO ships (id, lat, lon, heading, speed, name, destination, ship_type, timestamp)
    VALUES (:id, :lat, :lon, :heading, :speed, :name, :destination, :ship_type, :timestamp)
    ON CONFLICT(id) DO UPDATE SET
        lat = excluded.lat,
        lon = excluded.lon,
        heading = excluded.heading,
        speed = excluded.speed,
        name = excluded.name,
        destination = excluded.destination,
        ship_type = excluded.ship_type,
        timestamp = excluded.timestamp
"""

_EVENT_COLUMN_DEFINITIONS = {
    "id": "TEXT PRIMARY KEY",
    "date": "TEXT",
    "lat": "REAL",
    "lon": "REAL",
    "event_text": "TEXT",
    "tone": "REAL DEFAULT 0",
    "category": "TEXT DEFAULT ''",
    "source_url": "TEXT DEFAULT ''",
}

_EVENT_UPSERT_SQL = """
    INSERT INTO events (id, date, lat, lon, event_text, tone, category, source_url)
    VALUES (:id, :date, :lat, :lon, :event_text, :tone, :category, :source_url)
    ON CONFLICT(id) DO UPDATE SET
        date = excluded.date,
        lat = excluded.lat,
        lon = excluded.lon,
        event_text = excluded.event_text,
        tone = excluded.tone,
        category = excluded.category,
        source_url = excluded.source_url
"""


def _minutes_from_seconds(seconds: int) -> int:
    return max(1, ceil(seconds / 60))


def _days_from_seconds(seconds: int) -> int:
    return max(1, ceil(seconds / 86400))



async def _connect_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    return db


@asynccontextmanager
async def open_db_connection() -> AsyncIterator[aiosqlite.Connection]:
    """Open a dedicated database connection for isolated work."""
    db = await _connect_db()
    try:
        yield db
    finally:
        await db.close()


async def get_db() -> aiosqlite.Connection:
    """Get a shared database connection."""
    global _db_instance
    if _db_instance is None:
        _db_instance = await _connect_db()
    return _db_instance


def _get_db_write_lock() -> asyncio.Lock:
    global _db_write_lock, _db_write_lock_loop
    loop = asyncio.get_running_loop()
    if _db_write_lock is None or _db_write_lock_loop is not loop:
        _db_write_lock = asyncio.Lock()
        _db_write_lock_loop = loop
    return _db_write_lock


@asynccontextmanager
async def db_write_guard():
    """Serialize write batches on the shared database connection."""
    async with _get_db_write_lock():
        yield


async def close_db() -> None:
    """Close the database connection on shutdown."""
    global _db_instance
    if _db_instance is not None:
        await _db_instance.close()
        _db_instance = None


async def _get_table_columns(db: aiosqlite.Connection, table_name: str) -> set[str]:
    async with db.execute(f"PRAGMA table_info({table_name})") as cursor:
        rows = await cursor.fetchall()
    return {row[1] for row in rows}


async def _migrate_planes_table_if_needed(db: aiosqlite.Connection) -> None:
    columns = await _get_table_columns(db, "planes")
    if not columns:
        return

    if "id" in columns and "timestamp" in columns:
        return

    if "icao24" not in columns and "last_seen" not in columns:
        return

    id_source = "id" if "id" in columns else "icao24"
    timestamp_source = "timestamp" if "timestamp" in columns else "last_seen"

    def select_expr(column: str, default_sql: str) -> str:
        return column if column in columns else default_sql

    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS planes_contract_migration (
            id TEXT PRIMARY KEY,
            lat REAL,
            lon REAL,
            alt INTEGER DEFAULT 0,
            heading REAL DEFAULT 0,
            callsign TEXT DEFAULT '',
            squawk TEXT DEFAULT '',
            speed REAL DEFAULT 0,
            timestamp TEXT
        )
        """
    )
    await db.execute(
        f"""
        INSERT OR REPLACE INTO planes_contract_migration
            (id, lat, lon, alt, heading, callsign, squawk, speed, timestamp)
        SELECT
            {id_source},
            {select_expr('lat', 'NULL')},
            {select_expr('lon', 'NULL')},
            {select_expr('alt', '0')},
            {select_expr('heading', '0')},
            {select_expr('callsign', "''")},
            {select_expr('squawk', "''")},
            {select_expr('speed', '0')},
            {timestamp_source}
        FROM planes
        """
    )
    await db.execute("DROP TABLE planes")
    await db.execute("ALTER TABLE planes_contract_migration RENAME TO planes")


async def _ensure_table_columns(
    db: aiosqlite.Connection,
    table_name: str,
    column_definitions: dict[str, str],
    *,
    skip_columns: set[str] | None = None,
) -> None:
    skip_columns = skip_columns or set()
    existing_columns = await _get_table_columns(db, table_name)

    for column_name, definition in column_definitions.items():
        if column_name in existing_columns or column_name in skip_columns:
            continue
        await db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


async def init_db() -> None:
    """Initialize the database with required tables and indexes."""
    db = await get_db()

    async with db_write_guard():
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS planes (
                id TEXT PRIMARY KEY,
                lat REAL,
                lon REAL,
                alt INTEGER DEFAULT 0,
                heading REAL DEFAULT 0,
                callsign TEXT DEFAULT '',
                squawk TEXT DEFAULT '',
                speed REAL DEFAULT 0,
                timestamp TEXT
            )
            """
        )
        await _migrate_planes_table_if_needed(db)
        await _ensure_table_columns(db, "planes", _PLANE_COLUMN_DEFINITIONS, skip_columns={"id"})

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS ships (
                id TEXT PRIMARY KEY,
                lat REAL,
                lon REAL,
                heading REAL DEFAULT 0,
                speed REAL DEFAULT 0,
                name TEXT DEFAULT '',
                destination TEXT DEFAULT '',
                ship_type TEXT DEFAULT '',
                timestamp TEXT
            )
            """
        )
        await _ensure_table_columns(db, "ships", _SHIP_COLUMN_DEFINITIONS, skip_columns={"id"})

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                date TEXT,
                lat REAL,
                lon REAL,
                event_text TEXT,
                tone REAL DEFAULT 0,
                category TEXT DEFAULT '',
                source_url TEXT DEFAULT ''
            )
            """
        )
        await _ensure_table_columns(db, "events", _EVENT_COLUMN_DEFINITIONS, skip_columns={"id"})

        await db.execute("CREATE INDEX IF NOT EXISTS idx_planes_timestamp ON planes(timestamp)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_ships_timestamp ON ships(timestamp)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON events(date)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_events_location ON events(lat, lon)")

        await delete_old_planes(db, commit=False)
        await db.commit()


async def upsert_plane(
    db: aiosqlite.Connection,
    plane: dict,
    *,
    commit: bool = True,
) -> None:
    """Insert or update a single plane row using the repo contract."""
    await upsert_planes(db, [plane], commit=commit)


async def upsert_planes(
    db: aiosqlite.Connection,
    planes: list[dict],
    *,
    commit: bool = True,
) -> None:
    """Insert or update plane rows using a single batched statement."""
    if commit:
        async with db_write_guard():
            await upsert_planes(db, planes, commit=False)
            await db.commit()
        return

    if not planes:
        return

    normalized_planes = []
    for plane in planes:
        normalized_planes.append(
            {
                "id": plane["id"],
                "lat": plane.get("lat"),
                "lon": plane.get("lon"),
                "alt": plane.get("alt", 0),
                "heading": plane.get("heading", 0),
                "callsign": plane.get("callsign", ""),
                "squawk": plane.get("squawk", ""),
                "speed": plane.get("speed", 0),
                "timestamp": plane.get("timestamp"),
            }
        )

    await db.executemany(_PLANE_UPSERT_SQL, normalized_planes)


async def delete_old_planes(
    db: aiosqlite.Connection,
    max_age_minutes: int | None = None,
    *,
    commit: bool = True,
) -> list[str]:
    """Delete stale planes and return the deleted plane ids."""
    if max_age_minutes is None:
        max_age_minutes = _minutes_from_seconds(settings.STALE_PLANE_SECONDS)
    if commit:
        async with db_write_guard():
            deleted_ids = await delete_old_planes(db, max_age_minutes=max_age_minutes, commit=False)
            await db.commit()
            return deleted_ids

    async with db.execute(
        """
        SELECT id
        FROM planes
        WHERE timestamp IS NULL
           OR julianday(timestamp) IS NULL
           OR julianday(timestamp) < julianday('now', '-' || ? || ' minutes')
        ORDER BY id
        """,
        (max_age_minutes,),
    ) as cursor:
        deleted_ids = [row[0] for row in await cursor.fetchall()]

    if deleted_ids:
        placeholders = ", ".join("?" for _ in deleted_ids)
        await db.execute(f"DELETE FROM planes WHERE id IN ({placeholders})", deleted_ids)

    return deleted_ids


async def upsert_ship(
    db: aiosqlite.Connection,
    ship: dict,
    *,
    commit: bool = True,
) -> None:
    """Insert or update a single ship row using the repo contract."""
    await upsert_ships(db, [ship], commit=commit)


async def upsert_ships(
    db: aiosqlite.Connection,
    ships: list[dict],
    *,
    commit: bool = True,
) -> None:
    """Insert or update ship rows using a single batched statement."""
    if commit:
        async with db_write_guard():
            await upsert_ships(db, ships, commit=False)
            await db.commit()
        return

    if not ships:
        return

    normalized_ships = []
    for ship in ships:
        normalized_ships.append(
            {
                "id": ship["id"],
                "lat": ship.get("lat"),
                "lon": ship.get("lon"),
                "heading": ship.get("heading", 0),
                "speed": ship.get("speed", 0),
                "name": ship.get("name", ""),
                "destination": ship.get("destination", ""),
                "ship_type": ship.get("ship_type", ""),
                "timestamp": ship.get("timestamp"),
            }
        )

    await db.executemany(_SHIP_UPSERT_SQL, normalized_ships)


async def delete_old_ships(
    db: aiosqlite.Connection,
    max_age_minutes: int | None = None,
    *,
    commit: bool = True,
) -> list[str]:
    """Delete stale ships and return the deleted ship ids."""
    if max_age_minutes is None:
        max_age_minutes = _minutes_from_seconds(settings.STALE_SHIP_SECONDS)
    if commit:
        async with db_write_guard():
            deleted_ids = await delete_old_ships(db, max_age_minutes=max_age_minutes, commit=False)
            await db.commit()
            return deleted_ids

    async with db.execute(
        """
        SELECT id
        FROM ships
        WHERE timestamp IS NULL
           OR julianday(timestamp) IS NULL
           OR julianday(timestamp) < julianday('now', '-' || ? || ' minutes')
        ORDER BY id
        """,
        (max_age_minutes,),
    ) as cursor:
        deleted_ids = [row[0] for row in await cursor.fetchall()]

    if deleted_ids:
        placeholders = ", ".join("?" for _ in deleted_ids)
        await db.execute(f"DELETE FROM ships WHERE id IN ({placeholders})", deleted_ids)

    return deleted_ids


async def upsert_event(
    db: aiosqlite.Connection,
    event: dict,
    *,
    commit: bool = True,
) -> None:
    """Insert or update a single event row using the repo contract."""
    await upsert_events(db, [event], commit=commit)


async def upsert_events(
    db: aiosqlite.Connection,
    events: list[dict],
    *,
    commit: bool = True,
) -> None:
    """Insert or update event rows using a single batched statement."""
    if commit:
        async with db_write_guard():
            await upsert_events(db, events, commit=False)
            await db.commit()
        return

    if not events:
        return

    normalized_events = []
    for event in events:
        # GDELT uses "YYYYMM" format (e.g. "202504"). Convert to ISO "YYYY-MM-01"
        # so julianday() correctly parses it for the delete_old_events age filter.
        raw_date = event.get("date") or ""
        if len(raw_date) == 6 and raw_date.isdigit():
            normalized_date = f"{raw_date[:4]}-{raw_date[4:6]}-01"
        else:
            normalized_date = raw_date

        normalized_events.append(
            {
                "id": event["id"],
                "date": normalized_date,
                "lat": event.get("lat"),
                "lon": event.get("lon"),
                "event_text": event.get("event_text", ""),
                "tone": event.get("tone", 0),
                "category": event.get("category", ""),
                "source_url": event.get("source_url", ""),
            }
        )

    await db.executemany(_EVENT_UPSERT_SQL, normalized_events)


async def delete_old_events(
    db: aiosqlite.Connection,
    max_age_days: int | None = None,
    *,
    commit: bool = True,
) -> list[str]:
    """Delete stale events older than max_age_days and return the deleted event ids."""
    if max_age_days is None:
        max_age_days = _days_from_seconds(settings.STALE_EVENT_SECONDS)
    if commit:
        async with db_write_guard():
            deleted_ids = await delete_old_events(db, max_age_days=max_age_days, commit=False)
            await db.commit()
            return deleted_ids

    async with db.execute(
        """
        SELECT id
        FROM events
        WHERE date IS NULL
           OR julianday(date) IS NULL
           OR julianday(date) < julianday('now', '-' || ? || ' days')
        ORDER BY id
        """,
        (max_age_days,),
    ) as cursor:
        deleted_ids = [row[0] for row in await cursor.fetchall()]

    if deleted_ids:
        placeholders = ", ".join("?" for _ in deleted_ids)
        await db.execute(f"DELETE FROM events WHERE id IN ({placeholders})", deleted_ids)

    return deleted_ids
