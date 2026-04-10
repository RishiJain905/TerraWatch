import aiosqlite
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.models import Metadata

router = APIRouter(prefix="/api/metadata", tags=["metadata"])


@router.get("", response_model=Metadata)
async def metadata(db: aiosqlite.Connection = Depends(get_db)):
    """Return system metadata and counts."""
    async with db.execute("SELECT COUNT(*) AS c FROM planes") as cursor:
        planes_count = (await cursor.fetchone())[0]

    async with db.execute("SELECT COUNT(*) AS c FROM ships") as cursor:
        ships_count = (await cursor.fetchone())[0]

    async with db.execute("SELECT COUNT(*) AS c FROM events") as cursor:
        events_count = (await cursor.fetchone())[0]

    async with db.execute(
        "SELECT timestamp FROM planes ORDER BY timestamp DESC LIMIT 1"
    ) as cursor:
        last_plane_row = await cursor.fetchone()

    async with db.execute(
        "SELECT timestamp FROM ships ORDER BY timestamp DESC LIMIT 1"
    ) as cursor:
        last_ship_row = await cursor.fetchone()

    async with db.execute(
        "SELECT date FROM events ORDER BY date DESC LIMIT 1"
    ) as cursor:
        last_event_row = await cursor.fetchone()

    return Metadata(
        status="ok",
        phase=1,
        planes_count=planes_count,
        ships_count=ships_count,
        events_count=events_count,
        last_planes_update=last_plane_row[0] if last_plane_row else None,
        last_ships_update=last_ship_row[0] if last_ship_row else None,
        last_events_update=last_event_row[0] if last_event_row else None,
    )
