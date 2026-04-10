from fastapi import APIRouter

from app.core.models import MetadataResponse

router = APIRouter(prefix="/api/metadata", tags=["metadata"])


@router.get("", response_model=MetadataResponse)
async def metadata():
    """Return system metadata and status."""
    return MetadataResponse(
        status="ok",
        phase=1,
        planes_count=0,
        ships_count=0,
    )
