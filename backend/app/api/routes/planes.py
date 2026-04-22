import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db
from app.core.models import Plane, PlaneRoute
from app.services.aviationstack_service import AviationstackService

router = APIRouter(prefix="/api/planes", tags=["planes"])


@router.get("", response_model=list[Plane])
async def get_planes(db: aiosqlite.Connection = Depends(get_db)):
    """Get all active planes from the database."""
    async with db.execute("SELECT * FROM planes") as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/count")
async def get_plane_count(db: aiosqlite.Connection = Depends(get_db)):
    """Get total count of active planes."""
    async with db.execute("SELECT COUNT(*) AS count FROM planes") as cursor:
        row = await cursor.fetchone()
        return {"count": row["count"]}


@router.get("/{icao24}", response_model=Plane | None)
async def get_plane(icao24: str, db: aiosqlite.Connection = Depends(get_db)):
    """Get details for a specific plane by ICAO24 address."""
    normalized_icao24 = icao24.strip().lower()
    async with db.execute("SELECT * FROM planes WHERE id = ?", (normalized_icao24,)) as cursor:
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)


@router.get("/{icao24}/route", response_model=PlaneRoute)
async def get_plane_route(icao24: str, db: aiosqlite.Connection = Depends(get_db)):
    """Get route enrichment for a specific plane by ICAO24 address."""
    normalized_icao24 = icao24.strip().lower()
    async with db.execute("SELECT * FROM planes WHERE id = ?", (normalized_icao24,)) as cursor:
        row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Plane not found")

    plane = dict(row)
    service = AviationstackService()
    return await service.get_plane_route(
        plane_id=plane["id"],
        callsign=plane.get("callsign") or "",
        lat=plane.get("lat") or 0.0,
        lon=plane.get("lon") or 0.0,
    )
