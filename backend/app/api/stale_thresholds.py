from fastapi import APIRouter

from app.config import settings

router = APIRouter(prefix="/api/stale-thresholds", tags=["stale-thresholds"])


@router.get("")
async def get_stale_thresholds():
    """Return the configured stale data thresholds (in seconds)."""
    return {
        "planes": settings.STALE_PLANE_SECONDS,
        "ships": settings.STALE_SHIP_SECONDS,
        "events": settings.STALE_EVENT_SECONDS,
        "conflicts": settings.STALE_CONFLICT_SECONDS,
    }
