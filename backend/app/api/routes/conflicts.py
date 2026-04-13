import aiosqlite
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.database import get_db
from app.core.models import Conflict

router = APIRouter(prefix="/api/conflicts", tags=["conflicts"])


@router.get("/count", response_model=dict)
async def get_conflict_count(db: aiosqlite.Connection = Depends(get_db)):
    """Return total conflict count."""
    async with db.execute("SELECT COUNT(*) AS count FROM conflicts") as cursor:
        row = await cursor.fetchone()
        return {"count": row["count"]}


@router.get("/{conflict_id}", response_model=Conflict | None)
async def get_conflict(conflict_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """Get details for a specific conflict by id."""
    normalized_id = conflict_id.strip()
    async with db.execute("SELECT * FROM conflicts WHERE id = ?", (normalized_id,)) as cursor:
        row = await cursor.fetchone()
        if row is None:
            return JSONResponse(status_code=404, content={"detail": "Conflict not found"})
        return dict(row)


@router.get("", response_model=list[Conflict])
async def get_conflicts(db: aiosqlite.Connection = Depends(get_db)):
    """Get all conflicts from the database."""
    async with db.execute("SELECT * FROM conflicts") as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
