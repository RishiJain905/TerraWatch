"""ADSB.lol service — fetches live plane data and normalizes it to the Plane contract."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from math import isfinite
from typing import Any, List

import httpx

from app.config import settings
from app.core.models import Plane, utc_now_iso

LEGACY_ADSBLOL_AIRCRAFT_API = "https://api.adsb.lol/aircraft/json"
ADSBLOL_AIRCRAFT_API = settings.ADSBLOL_API_URL or LEGACY_ADSBLOL_AIRCRAFT_API
HTTP_TIMEOUT_SECONDS = 10.0
HTTP_HEADERS = {
    "Accept-Encoding": "gzip",
    "User-Agent": "TerraWatch/0.1",
}

logger = logging.getLogger(__name__)


def _normalize_url(url: str | None) -> str:
    return str(url or "").strip().rstrip("/")


def _is_legacy_global_url(url: str | None) -> bool:
    return _normalize_url(url) == LEGACY_ADSBLOL_AIRCRAFT_API


def _build_point_url(base_url: str, lat: float, lon: float, radius_nm: int) -> str:
    return f"{_normalize_url(base_url)}/v2/point/{lat}/{lon}/{radius_nm}"


def _resolve_api_url(
    api_url: str | None,
    *,
    base_url: str,
    query_lat: float | None,
    query_lon: float | None,
    query_radius_nm: int | None,
) -> str | None:
    explicit_url = _normalize_url(api_url)
    has_point_query = (
        query_lat is not None
        and query_lon is not None
        and query_radius_nm is not None
    )

    if has_point_query:
        if not explicit_url or _is_legacy_global_url(explicit_url):
            return _build_point_url(base_url, query_lat, query_lon, query_radius_nm)
        return explicit_url

    if explicit_url and not _is_legacy_global_url(explicit_url):
        return explicit_url

    return None


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

    # ADSB.lol v2 public API uses millisecond epoch timestamps for ctime/now.
    if abs(numeric_timestamp) >= 1_000_000_000_000:
        numeric_timestamp /= 1000.0

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
        *,
        base_url: str | None = None,
        query_lat: float | None = None,
        query_lon: float | None = None,
        query_radius_nm: int | None = None,
        timeout_seconds: float = HTTP_TIMEOUT_SECONDS,
    ) -> None:
        self.api_url = api_url if api_url is not None else settings.ADSBLOL_API_URL
        self.base_url = base_url or settings.ADSBLOL_BASE_URL
        self.query_lat = settings.ADSBLOL_LAT if query_lat is None else query_lat
        self.query_lon = settings.ADSBLOL_LON if query_lon is None else query_lon
        self.query_radius_nm = (
            settings.ADSBLOL_RADIUS_NM if query_radius_nm is None else query_radius_nm
        )
        self.timeout_seconds = timeout_seconds

    async def fetch_planes(self) -> List[dict]:
        resolved_api_url = _resolve_api_url(
            self.api_url,
            base_url=self.base_url,
            query_lat=self.query_lat,
            query_lon=self.query_lon,
            query_radius_nm=self.query_radius_nm,
        )
        if not resolved_api_url:
            configured_url = _normalize_url(self.api_url)
            if _is_legacy_global_url(configured_url):
                logger.warning(
                    "ADSB.lol public global endpoint %s is no longer available. "
                    "Configure ADSBLOL_LAT/LON/RADIUS_NM for the public v2 point API, "
                    "or set ADSBLOL_API_URL to a working endpoint. Skipping ADSB.lol fetch.",
                    configured_url,
                )
            else:
                logger.info(
                    "ADSB.lol fetch skipped: no API URL configured. "
                    "Set ADSBLOL_LAT/LON/RADIUS_NM for the public v2 point API, "
                    "or ADSBLOL_API_URL for a custom endpoint.",
                )
            return []

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers=HTTP_HEADERS,
            ) as client:
                response = await client.get(resolved_api_url)
                response.raise_for_status()
                payload = response.json()
        except httpx.TimeoutException as exc:
            logger.warning("ADSB.lol request timed out for %s: %s", resolved_api_url, exc)
            return []
        except httpx.HTTPError as exc:
            logger.warning("ADSB.lol request failed for %s: %s", resolved_api_url, exc)
            return []
        except ValueError as exc:
            logger.warning("ADSB.lol response could not be parsed for %s: %s", resolved_api_url, exc)
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
