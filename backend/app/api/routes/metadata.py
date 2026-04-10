import aiosqlite
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.models import Metadata

router = APIRouter(prefix="/api/metadata", tags=["metadata"])


@router.get("", response_model=Metadata)
async def metadata(db: aiosqlite.Connection = Depends(get_db)):
    """Return system metadata and counts."""
    planes_cur = await db.execute("SELECT COUNT(*) AS c FROM planes")
    ships_cur = await db.execute("SELECT COUNT(*) AS c FROM ships")
    events_cur = await db.execute("SELECT COUNT(*) AS c FROM events")

    planes_count = (await planes_cur.fetchone())[0]
    ships_count = (await ships_cur.fetchone())[0]
    events_count = (await events_cur.fetchone())[0]

    last_plane = await db.execute(
        "SELECT timestamp FROM planes ORDER BY timestamp DESC LIMIT 1"
    )
    last_ship = await db.execute(
        "SELECT timestamp FROM ships ORDER BY timestamp DESC LIMIT 1"
    )
    last_event = await db.execute(
        "SELECT date FROM events ORDER BY date DESC LIMIT 1"
    )

    last_plane_row = await last_plane.fetchone()
    last_ship_row = await last_ship.fetchone()
    last_event_row = await last_event.fetchone()

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
