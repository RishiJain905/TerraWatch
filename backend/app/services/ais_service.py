"""AIS Service — fetches live ship data from Digitraffic and normalizes it to the Ship contract."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from math import isfinite
from typing import Any, List

import httpx

from app.core.models import Ship, utc_now_iso

DIGITRAFFIC_LOCATIONS_API = "https://meri.digitraffic.fi/api/ais/v1/locations"
DIGITRAFFIC_VESSELS_API = "https://meri.digitraffic.fi/api/ais/v1/vessels"
HTTP_TIMEOUT_SECONDS = 30.0
HTTP_HEADERS = {
    "Accept-Encoding": "gzip",
    "User-Agent": "TerraWatch/0.1",
}


def _safe_float(value: Any, default: float | None = None) -> float | None:
    """Return a finite float or the provided default when parsing fails."""
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
    """Return an integer or the provided default when parsing fails."""
    numeric = _safe_float(value)
    if numeric is None:
        return default
    return int(numeric)


def _normalize_text(value: Any) -> str:
    """Convert optional upstream text values to trimmed strings."""
    if value is None:
        return ""
    return str(value).strip()


def _timestamp_ms_to_iso(timestamp_ms: Any) -> str | None:
    """Convert epoch milliseconds to an ISO-8601 UTC string."""
    numeric_timestamp_ms = _safe_float(timestamp_ms)
    if numeric_timestamp_ms is None:
        return None

    try:
        return datetime.fromtimestamp(numeric_timestamp_ms / 1000, tz=timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def _map_ship_type(code: Any) -> str:
    """Map AIS ship type codes into the stable frontend-facing categories."""
    numeric_code = _safe_int(code)
    if numeric_code is None:
        return "other"

    if 70 <= numeric_code < 80:
        return "cargo"
    if 80 <= numeric_code < 90:
        return "tanker"
    if 60 <= numeric_code < 70:
        return "passenger"
    if numeric_code == 30:
        return "fishing"
    return "other"


def _build_vessel_metadata_index(vessels_payload: list[Any]) -> dict[str, dict[str, Any]]:
    """Index vessel metadata rows by MMSI string."""
    metadata_by_mmsi: dict[str, dict[str, Any]] = {}

    for vessel in vessels_payload:
        if not isinstance(vessel, dict):
            continue

        mmsi = _normalize_text(vessel.get("mmsi"))
        if not mmsi:
            continue

        metadata_by_mmsi[mmsi] = vessel

    return metadata_by_mmsi


def _ship_timestamp(properties: dict[str, Any], fallback_timestamp: str) -> str:
    """Choose the best available timestamp for a ship observation."""
    return _timestamp_ms_to_iso(properties.get("timestampExternal")) or fallback_timestamp or utc_now_iso()


def _normalize_ship_feature(
    feature: dict[str, Any],
    metadata_by_mmsi: dict[str, dict[str, Any]],
    fallback_timestamp: str,
) -> dict[str, Any] | None:
    """Normalize one Digitraffic GeoJSON feature into the internal Ship contract."""
    geometry = feature.get("geometry")
    properties = feature.get("properties")

    if not isinstance(geometry, dict) or not isinstance(properties, dict):
        return None

    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return None

    lon = _safe_float(coordinates[0])
    lat = _safe_float(coordinates[1])
    mmsi = _normalize_text(feature.get("mmsi") or properties.get("mmsi"))

    if not mmsi or lat is None or lon is None:
        return None

    vessel_metadata = metadata_by_mmsi.get(mmsi, {})
    heading = _safe_float(properties.get("heading"))
    if heading is None:
        heading = _safe_float(properties.get("cog"), 0.0)

    ship = Ship(
        id=mmsi,
        lat=lat,
        lon=lon,
        heading=heading if heading is not None else 0.0,
        speed=_safe_float(properties.get("sog"), 0.0) or 0.0,
        name=_normalize_text(vessel_metadata.get("name")),
        destination=_normalize_text(vessel_metadata.get("destination")),
        ship_type=_map_ship_type(vessel_metadata.get("shipType")),
        timestamp=_ship_timestamp(properties, fallback_timestamp),
    )
    return ship.model_dump()


async def _fetch_json(client: httpx.AsyncClient, url: str) -> Any:
    """Fetch and decode a JSON payload from a Digitraffic endpoint."""
    response = await client.get(url)
    response.raise_for_status()
    return response.json()


async def fetch_ships() -> List[dict]:
    """Fetch live ship positions from Digitraffic and normalize them to the Ship contract."""
    try:
        async with httpx.AsyncClient(
            timeout=HTTP_TIMEOUT_SECONDS,
            headers=HTTP_HEADERS,
        ) as client:
            locations_payload, vessels_payload = await asyncio.gather(
                _fetch_json(client, DIGITRAFFIC_LOCATIONS_API),
                _fetch_json(client, DIGITRAFFIC_VESSELS_API),
            )
    except (httpx.HTTPError, ValueError):
        return []

    if not isinstance(locations_payload, dict) or not isinstance(vessels_payload, list):
        return []

    features = locations_payload.get("features")
    if not isinstance(features, list):
        return []

    fallback_timestamp = _normalize_text(locations_payload.get("dataUpdatedTime")) or utc_now_iso()
    metadata_by_mmsi = _build_vessel_metadata_index(vessels_payload)
    ships: List[dict] = []

    for feature in features:
        if not isinstance(feature, dict):
            continue

        ship = _normalize_ship_feature(feature, metadata_by_mmsi, fallback_timestamp)
        if ship is not None:
            ships.append(ship)

    return ships


async def fetch_ship_details(mmsi: str) -> dict | None:
    """Fetch details for a specific ship by MMSI."""
    normalized_mmsi = _normalize_text(mmsi)
    if not normalized_mmsi:
        return None

    ships = await fetch_ships()
    for ship in ships:
        if ship.get("id") == normalized_mmsi:
            return ship

    return None
