import aiosqlite
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.models import Plane

router = APIRouter(prefix="/api/planes", tags=["planes"])


@router.get("", response_model=list[Plane])
async def get_planes(db: aiosqlite.Connection = Depends(get_db)):
    """Get all active planes from the database."""
    async with db.execute("SELECT * FROM planes") as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
