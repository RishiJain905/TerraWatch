import aiosqlite
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.models import PlaneResponse

router = APIRouter(prefix="/api/planes", tags=["planes"])


@router.get("", response_model=list[PlaneResponse])
async def get_planes(db: aiosqlite.Connection = Depends(get_db)):
    """Get all active planes from the database."""
    cursor = await db.execute("SELECT * FROM planes")
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]
