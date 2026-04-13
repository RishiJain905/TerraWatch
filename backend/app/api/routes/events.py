import aiosqlite
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.database import get_db
from app.core.models import WorldEvent

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("/count", response_model=dict)
async def get_event_count(db: aiosqlite.Connection = Depends(get_db)):
    """Return total event count."""
    async with db.execute("SELECT COUNT(*) AS count FROM events") as cursor:
        row = await cursor.fetchone()
        return {"count": row["count"]}


@router.get("/{event_id}", response_model=WorldEvent | None)
async def get_event(event_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """Get details for a specific event by id."""
    normalized_id = event_id.strip()
    async with db.execute("SELECT * FROM events WHERE id = ?", (normalized_id,)) as cursor:
        row = await cursor.fetchone()
        if row is None:
            return JSONResponse(status_code=404, content={"detail": "Event not found"})
        return dict(row)


@router.get("", response_model=list[WorldEvent])
async def get_events(db: aiosqlite.Connection = Depends(get_db)):
    """Get all events from the database."""
    async with db.execute("SELECT * FROM events") as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
