import aiosqlite
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.database import get_db
from app.core.models import WorldEvent

router = APIRouter(prefix="/api/conflicts", tags=["conflicts"])

# GDELT event root codes for violent/aggressive events
VIOLENT_CATEGORIES = [
    "assault",                # code 08
    "fight",                  # code 09
    "unconventional_mass_gvc", # code 10
    "conventional_mass_gvc",  # code 12
    "force_range",            # code 13
    "rioting",                # code 18
]


@router.get("/count", response_model=dict)
async def get_conflict_count(db: aiosqlite.Connection = Depends(get_db)):
    """Return total violent-event count sourced from GDELT."""
    placeholders = ",".join("?" for _ in VIOLENT_CATEGORIES)
    async with db.execute(
        f"SELECT COUNT(*) AS count FROM events WHERE category IN ({placeholders})",
        VIOLENT_CATEGORIES,
    ) as cursor:
        row = await cursor.fetchone()
        return {"count": row["count"]}


@router.get("/{conflict_id}", response_model=WorldEvent | None)
async def get_conflict(conflict_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """Get details for a specific violent event by id. Returns None if not found."""
    normalized_id = conflict_id.strip()
    placeholders = ",".join("?" for _ in VIOLENT_CATEGORIES)
    async with db.execute(
        f"SELECT * FROM events WHERE id = ? AND category IN ({placeholders})",
        [normalized_id, *VIOLENT_CATEGORIES],
    ) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None


@router.get("", response_model=list)
async def get_conflicts(db: aiosqlite.Connection = Depends(get_db)):
    """Get all violent GDELT events for the conflicts heatmap."""
    placeholders = ",".join("?" for _ in VIOLENT_CATEGORIES)
    async with db.execute(
        f"SELECT * FROM events WHERE category IN ({placeholders})",
        VIOLENT_CATEGORIES,
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
