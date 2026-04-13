"""
ACLED Service — fetches conflict data from ACLED (acleddata.com).

Uses OAuth Bearer token flow:
1. POST /oauth/token with credentials to get access_token
2. GET /api/acled/read with Bearer token to fetch conflict events

Graceful degradation: If ACLED_EMAIL or ACLED_PASSWORD env vars are absent,
logs a warning and returns empty list.
"""

import logging
import os
from datetime import datetime, timedelta, timezone

import httpx

logger = logging.getLogger(__name__)

ACLED_EMAIL = os.getenv("ACLED_EMAIL", "")
ACLED_PASSWORD = os.getenv("ACLED_PASSWORD", "")
ACLED_TOKEN_URL = "https://acleddata.com/oauth/token"
ACLED_API_URL = "https://acleddata.com/api/acled/read"

# Module-level token storage
_access_token: str | None = None
_refresh_token: str | None = None
_token_expiry: datetime | None = None


def _credentials_available() -> bool:
    """Check if ACLED credentials are configured."""
    return bool(ACLED_EMAIL and ACLED_PASSWORD)


def _token_is_valid() -> bool:
    """Check if the current access token is still valid."""
    if _access_token is None or _token_expiry is None:
        return False
    # Add a 60-second buffer before actual expiry
    return datetime.now(timezone.utc) < _token_expiry - timedelta(seconds=60)


async def _authenticate(client: httpx.AsyncClient) -> bool:
    """Authenticate with ACLED and store the access token."""
    global _access_token, _refresh_token, _token_expiry

    try:
        response = await client.post(
            ACLED_TOKEN_URL,
            data={
                "username": ACLED_EMAIL,
                "password": ACLED_PASSWORD,
                "grant_type": "password",
                "client_id": "acled",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        token_data = response.json()

        _access_token = token_data.get("access_token")
        _refresh_token = token_data.get("refresh_token")

        # Default to 24 hours if expires_in not provided
        expires_in = token_data.get("expires_in", 86400)
        _token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        logger.info("ACLED authentication successful, token expires in %d seconds", expires_in)
        return True

    except Exception:
        logger.exception("ACLED authentication failed")
        _access_token = None
        _refresh_token = None
        _token_expiry = None
        return False


async def _ensure_authenticated(client: httpx.AsyncClient) -> bool:
    """Ensure we have a valid access token, re-authenticating if needed."""
    if _token_is_valid():
        return True
    return await _authenticate(client)


def _normalize_conflict(item: dict) -> dict:
    """Normalize an ACLED API item to the Conflict contract."""
    event_id = item.get("event_id", "")
    event_date = item.get("event_date", "")
    latitude = item.get("latitude", "")
    longitude = item.get("longitude", "")
    event_type = item.get("event_type", "")
    fatalities_raw = item.get("fatalities", 0)
    country = item.get("country", "")
    region = item.get("region") or item.get("admin1", "")

    # Parse lat/lon safely
    try:
        lat = float(latitude)
    except (ValueError, TypeError):
        lat = 0.0

    try:
        lon = float(longitude)
    except (ValueError, TypeError):
        lon = 0.0

    # Parse fatalities safely
    try:
        fatalities = int(fatalities_raw) if fatalities_raw else 0
    except (ValueError, TypeError):
        fatalities = 0

    return {
        "id": f"acled_{event_id}",
        "date": event_date,
        "lat": lat,
        "lon": lon,
        "event_type": event_type,
        "fatalities": fatalities,
        "country": country,
        "region": region,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _fetch_conflicts_page(client: httpx.AsyncClient) -> list[dict]:
    """Fetch a page of conflict data from the ACLED API."""
    # Calculate date 30 days ago for the filter
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")

    params = {
        "_format": "json",
        "limit": "1000",
        "event_date": thirty_days_ago,
    }

    headers = {
        "Authorization": f"Bearer {_access_token}",
    }

    response = await client.get(
        ACLED_API_URL,
        params=params,
        headers=headers,
        timeout=60.0,
    )
    response.raise_for_status()

    data = response.json()
    items = data.get("data", [])

    conflicts = []
    for item in items:
        conflict = _normalize_conflict(item)
        conflicts.append(conflict)

    return conflicts


async def fetch_conflicts() -> list[dict]:
    """Fetch conflict data from ACLED.

    Returns a list of dicts matching the Conflict contract.
    If credentials are not configured, returns an empty list with a warning.
    """
    if not _credentials_available():
        logger.warning(
            "ACLED_EMAIL or ACLED_PASSWORD not configured; "
            "ACLED conflict data will not be available"
        )
        return []

    async with httpx.AsyncClient(follow_redirects=True) as client:
        authenticated = await _ensure_authenticated(client)
        if not authenticated:
            logger.error("ACLED authentication failed; returning empty conflicts list")
            return []

        try:
            conflicts = await _fetch_conflicts_page(client)
            logger.info("Fetched %d ACLED conflict records", len(conflicts))
            return conflicts
        except Exception:
            logger.exception("Failed to fetch ACLED conflicts")
            return []
