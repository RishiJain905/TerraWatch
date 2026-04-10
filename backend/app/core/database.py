import aiosqlite
from app.config import settings

DATABASE_PATH = "./terrawatch.db"


async def get_db():
    """Dependency that provides a database connection."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db():
    """Initialize the database with required tables."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS planes (
                id TEXT PRIMARY KEY,
                lat REAL,
                lon REAL,
                alt INTEGER,
                heading REAL,
                callsign TEXT,
                squawk TEXT,
                speed REAL,
                timestamp TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ships (
                id TEXT PRIMARY KEY,
                lat REAL,
                lon REAL,
                heading REAL,
                speed REAL,
                name TEXT,
                destination TEXT,
                ship_type TEXT,
                timestamp TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                date TEXT,
                lat REAL,
                lon REAL,
                event_text TEXT,
                tone REAL,
                category TEXT,
                source_url TEXT
            )
        """)
        await db.commit()
