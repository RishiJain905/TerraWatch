import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aiosqlite

DATABASE_PATH = "./terrawatch.db"

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
    max_age_minutes: int = 5,
    *,
    commit: bool = True,
) -> list[str]:
    """Delete stale planes and return the deleted plane ids."""
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
