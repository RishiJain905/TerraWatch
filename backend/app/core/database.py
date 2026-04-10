import aiosqlite

DATABASE_PATH = "./terrawatch.db"

_db_instance: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    """Get a database connection."""
    global _db_instance
    if _db_instance is None:
        _db_instance = await aiosqlite.connect(DATABASE_PATH)
        _db_instance.row_factory = aiosqlite.Row
    return _db_instance


async def close_db() -> None:
    """Close the database connection on shutdown."""
    global _db_instance
    if _db_instance is not None:
        await _db_instance.close()
        _db_instance = None


async def init_db() -> None:
    """Initialize the database with required tables and indexes."""
    db = await get_db()

    # Planes table
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

    # Ships table
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

    # Events table
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

    # Indexes for performance
    await db.execute("CREATE INDEX IF NOT EXISTS idx_planes_timestamp ON planes(timestamp)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_ships_timestamp ON ships(timestamp)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON events(date)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_events_location ON events(lat, lon)")

    await db.commit()
