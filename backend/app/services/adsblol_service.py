"""ADSB.lol service — fetches live plane data and normalizes it to the Plane contract."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from math import isfinite
from typing import Any, List

import httpx

from app.config import settings
from app.core.models import Plane, utc_now_iso

ADSBLOL_AIRCRAFT_API = settings.ADSBLOL_API_URL
HTTP_TIMEOUT_SECONDS = 10.0
HTTP_HEADERS = {
    "Accept-Encoding": "gzip",
    "User-Agent": "TerraWatch/0.1",
}

logger = logging.getLogger(__name__)


def normalize_hex(hex_str: str) -> str:
    """Normalize an ICAO hex identifier to uppercase for matching and dedup keys."""
    return str(hex_str or "").strip().upper()


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


def _safe_int(value: Any, default: int = 0) -> int:
    numeric = _safe_float(value)
    if numeric is None:
        return default
    return int(round(numeric))


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


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
        else:
            return cleaned.replace("Z", "+00:00") if cleaned.endswith("Z") else cleaned

    numeric_timestamp = _safe_float(value)
    if numeric_timestamp is None:
        return None

    try:
        return datetime.fromtimestamp(numeric_timestamp, tz=timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def _record_timestamp(record: dict[str, Any], payload_timestamp: Any = None) -> str:
    return (
        _timestamp_to_iso(payload_timestamp)
        or _timestamp_to_iso(record.get("last_timestamp"))
        or _timestamp_to_iso(record.get("ctime"))
        or utc_now_iso()
    )


def _record_altitude(record: dict[str, Any]) -> int:
    altitude_value = record.get("alt")
    if altitude_value in (None, "", "ground"):
        altitude_value = record.get("alt_baro")
    if altitude_value in (None, "", "ground"):
        altitude_value = record.get("alt_geom")
    if altitude_value in (None, "", "ground"):
        return 0
    return _safe_int(altitude_value, 0)


def _record_speed(record: dict[str, Any]) -> float:
    return _safe_float(record.get("speed"), _safe_float(record.get("gs"), 0.0)) or 0.0


def _record_heading(record: dict[str, Any]) -> float:
    return _safe_float(record.get("dir"), _safe_float(record.get("track"), 0.0)) or 0.0


def _normalize_record(record: dict[str, Any], payload_timestamp: Any = None) -> dict[str, Any] | None:
    icao_hex_upper = normalize_hex(record.get("hex") or "")
    lat = _safe_float(record.get("lat"))
    lon = _safe_float(record.get("lng"), _safe_float(record.get("lon")))

    if not icao_hex_upper or lat is None or lon is None:
        return None

    plane = Plane(
        # Preserve the repo's current lowercase id contract while normalizing
        # uppercase identifiers for matching and future deduplication.
        id=icao_hex_upper.lower(),
        callsign=_normalize_text(record.get("flight") or record.get("callsign")),
        lat=lat,
        lon=lon,
        alt=_record_altitude(record),
        heading=_record_heading(record),
        speed=_record_speed(record),
        squawk=_normalize_text(record.get("squawk")),
        timestamp=_record_timestamp(record, payload_timestamp),
    )
    return plane.model_dump()


class AdsblolService:
    """Fetch and normalize ADSB.lol aircraft payloads."""

    def __init__(
        self,
        api_url: str | None = None,
        timeout_seconds: float = HTTP_TIMEOUT_SECONDS,
    ) -> None:
        self.api_url = api_url or ADSBLOL_AIRCRAFT_API
        self.timeout_seconds = timeout_seconds

    async def fetch_planes(self) -> List[dict]:
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers=HTTP_HEADERS,
            ) as client:
                response = await client.get(self.api_url)
                response.raise_for_status()
                payload = response.json()
        except httpx.TimeoutException as exc:
            logger.warning("ADSB.lol request timed out for %s: %s", self.api_url, exc)
            return []
        except httpx.HTTPError as exc:
            logger.warning("ADSB.lol request failed for %s: %s", self.api_url, exc)
            return []
        except ValueError as exc:
            logger.warning("ADSB.lol response could not be parsed for %s: %s", self.api_url, exc)
            return []

        if not isinstance(payload, dict):
            logger.warning("ADSB.lol response had unexpected top-level shape: %s", type(payload).__name__)
            return []

        aircraft = payload.get("ac")
        if not isinstance(aircraft, list):
            logger.warning("ADSB.lol response missing aircraft list")
            return []

        payload_timestamp = payload.get("last_timestamp")
        if payload_timestamp is None:
            payload_timestamp = payload.get("ctime")

        planes: List[dict] = []
        for record in aircraft:
            if not isinstance(record, dict):
                continue

            plane = _normalize_record(record, payload_timestamp)
            if plane is not None:
                planes.append(plane)

        return planes


async def fetch_planes() -> List[dict]:
    """Module-level wrapper for repo consistency with existing service modules."""
    return await AdsblolService().fetch_planes()
