import aiosqlite
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.models import EventResponse

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=list[EventResponse])
async def get_events(db: aiosqlite.Connection = Depends(get_db)):
    """Get all events from the database."""
    cursor = await db.execute("SELECT * FROM events")
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]
