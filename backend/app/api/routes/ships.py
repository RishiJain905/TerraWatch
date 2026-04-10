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
