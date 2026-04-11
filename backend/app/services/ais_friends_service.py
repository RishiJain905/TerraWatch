"""AIS Friends service — fetches live ship data and normalizes it to the Ship contract."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from math import isfinite
from typing import Any, List

import httpx

from app.config import settings
from app.core.models import Ship, utc_now_iso

AIS_FRIENDS_BASE_API = "https://www.aisfriends.com/api/public/v1"
AIS_FRIENDS_BBOX_API = f"{AIS_FRIENDS_BASE_API}/vessels/bbox"
HTTP_TIMEOUT_SECONDS = 30.0
RATE_LIMIT_RETRY_DELAY_SECONDS = 0.1
HTTP_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "TerraWatch/0.1",
}
DEFAULT_BBOX = {
    "lat_min": -90.0,
    "lat_max": 90.0,
    "lon_min": -180.0,
    "lon_max": 180.0,
}

logger = logging.getLogger(__name__)


def _safe_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default

    if not isfinite(numeric):
        return default

    return numeric


def _safe_int(value: Any, default: int | None = None) -> int | None:
    numeric = _safe_float(value)
    if numeric is None:
        return default
    return int(numeric)


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _bbox_value(bbox: dict[str, Any], primary_key: str, fallback_key: str, default: float) -> float:
    primary_value = _safe_float(bbox.get(primary_key))
    if primary_value is not None:
        return primary_value

    fallback_value = _safe_float(bbox.get(fallback_key))
    if fallback_value is not None:
        return fallback_value

    return default


def _normalize_bbox(bbox: dict[str, Any] | None) -> dict[str, float]:
    if not isinstance(bbox, dict):
        return DEFAULT_BBOX.copy()

    return {
        "lat_min": _bbox_value(bbox, "lat_min", "south", DEFAULT_BBOX["lat_min"]),
        "lat_max": _bbox_value(bbox, "lat_max", "north", DEFAULT_BBOX["lat_max"]),
        "lon_min": _bbox_value(bbox, "lon_min", "west", DEFAULT_BBOX["lon_min"]),
        "lon_max": _bbox_value(bbox, "lon_max", "east", DEFAULT_BBOX["lon_max"]),
    }


def _timestamp_to_iso(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None

        try:
            return datetime.fromisoformat(cleaned.replace("Z", "+00:00")).isoformat()
        except ValueError:
            numeric_value = _safe_float(cleaned)
            if numeric_value is None:
                return None
            value = numeric_value

    numeric_timestamp = _safe_float(value)
    if numeric_timestamp is None:
        return None

    if abs(numeric_timestamp) >= 1_000_000_000_000:
        numeric_timestamp /= 1000

    try:
        return datetime.fromtimestamp(numeric_timestamp, tz=timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def _map_ship_type(value: Any) -> str:
    normalized_value = _normalize_text(value)
    if not normalized_value:
        return "other"

    numeric_code = _safe_int(normalized_value)
    if numeric_code is not None:
        if 70 <= numeric_code < 80:
            return "cargo"
        if 80 <= numeric_code < 90:
            return "tanker"
        if 60 <= numeric_code < 70:
            return "passenger"
        if numeric_code == 30:
            return "fishing"
        return "other"

    lowered = normalized_value.lower()
    if "cargo" in lowered or "container" in lowered or "bulk" in lowered or "freight" in lowered:
        return "cargo"
    if "tanker" in lowered:
        return "tanker"
    if "passenger" in lowered or "ferry" in lowered or "cruise" in lowered:
        return "passenger"
    if "fish" in lowered or "trawler" in lowered:
        return "fishing"
    return "other"


def _record_ship_type(record: dict[str, Any]) -> str:
    return _map_ship_type(
        record.get("ship_type")
        or record.get("type")
        or record.get("detailed_type")
    )


def _normalize_record(record: dict[str, Any]) -> dict[str, Any] | None:
    mmsi = _normalize_text(record.get("mmsi"))
    lat = _safe_float(record.get("lat"), _safe_float(record.get("latitude")))
    lon = _safe_float(record.get("lon"), _safe_float(record.get("longitude")))

    if not mmsi or lat is None or lon is None:
        return None

    heading = _safe_float(record.get("true_heading"), _safe_float(record.get("course_over_ground"), 0.0)) or 0.0
    ship = Ship(
        id=mmsi,
        lat=lat,
        lon=lon,
        heading=heading,
        speed=_safe_float(record.get("speed_over_ground"), 0.0) or 0.0,
        name=_normalize_text(record.get("name") or record.get("reported_name")),
        destination=_normalize_text(record.get("destination") or record.get("ais_destination")),
        ship_type=_record_ship_type(record),
        timestamp=_timestamp_to_iso(record.get("timestamp")) or utc_now_iso(),
    )
    return ship.model_dump()


class AisFriendsService:
    """Fetch and normalize AIS Friends vessel payloads."""

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str = AIS_FRIENDS_BBOX_API,
        timeout_seconds: float = HTTP_TIMEOUT_SECONDS,
    ) -> None:
        resolved_api_key = settings.AIS_FRIENDS_API_KEY if api_key is None else api_key
        self.api_key = _normalize_text(resolved_api_key)
        self.api_url = api_url
        self.timeout_seconds = timeout_seconds

    async def _fetch_payload(
        self,
        client: httpx.AsyncClient,
        bbox: dict[str, float],
    ) -> Any:
        for attempt in range(2):
            try:
                response = await client.get(self.api_url, params=bbox)

                if response.status_code == 429:
                    if attempt == 0:
                        logger.warning("AIS Friends rate limited; retrying once for %s", self.api_url)
                        await asyncio.sleep(RATE_LIMIT_RETRY_DELAY_SECONDS)
                        continue

                    logger.warning("AIS Friends rate limited after retry for %s", self.api_url)
                    return None

                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException as exc:
                logger.warning("AIS Friends request timed out for %s: %s", self.api_url, exc)
                return None
            except httpx.HTTPError as exc:
                logger.warning("AIS Friends request failed for %s: %s", self.api_url, exc)
                return None
            except ValueError as exc:
                logger.warning("AIS Friends response could not be parsed for %s: %s", self.api_url, exc)
                return None

        return None

    async def fetch_ships(self, bbox: dict[str, Any] | None = None) -> List[dict]:
        if not self.api_key:
            logger.warning("AIS Friends API key missing; skipping ship fetch")
            return []

        normalized_bbox = _normalize_bbox(bbox)
        headers = {
            **HTTP_HEADERS,
            "Authorization": f"Bearer {self.api_key}",
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds, headers=headers) as client:
            payload = await self._fetch_payload(client, normalized_bbox)

        if not isinstance(payload, dict):
            if payload is not None:
                logger.warning("AIS Friends response had unexpected top-level shape: %s", type(payload).__name__)
            return []

        records = payload.get("data")
        if not isinstance(records, list):
            logger.warning("AIS Friends response missing data list")
            return []

        ships: List[dict] = []
        for record in records:
            if not isinstance(record, dict):
                continue

            ship = _normalize_record(record)
            if ship is not None:
                ships.append(ship)

        return ships


async def fetch_ships(bbox: dict[str, Any] | None = None) -> List[dict]:
    """Module-level wrapper for repo consistency with existing service modules."""
    return await AisFriendsService().fetch_ships(bbox=bbox)
