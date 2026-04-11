import aiosqlite
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.models import Ship

router = APIRouter(prefix="/api/ships", tags=["ships"])


@router.get("", response_model=list[Ship])
async def get_ships(db: aiosqlite.Connection = Depends(get_db)):
    """Get all active ships from the database."""
    async with db.execute("SELECT * FROM ships") as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/count", response_model=dict)
async def get_ship_count(db: aiosqlite.Connection = Depends(get_db)):
    """Return total active ship count."""
    async with db.execute("SELECT COUNT(*) AS count FROM ships") as cursor:
        row = await cursor.fetchone()
        return {"count": row["count"]}


@router.get("/{mmsi}", response_model=Ship | None)
async def get_ship(mmsi: str, db: aiosqlite.Connection = Depends(get_db)):
    """Get details for a specific ship by MMSI."""
    normalized_mmsi = mmsi.strip()
    async with db.execute("SELECT * FROM ships WHERE id = ?", (normalized_mmsi,)) as cursor:
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)
