"""
ADSB Service — fetches live plane data from OpenSky Network.

Uses OAuth2 Client Credentials flow (required as of March 18, 2026).
Free registration: https://opensky-network.org/register
"""

from __future__ import annotations

import asyncio
import logging
import httpx
from datetime import datetime, timezone, timedelta
from math import isfinite
from typing import Any, List, Optional

from app.core.models import Plane, utc_now_iso

logger = logging.getLogger(__name__)


def _get_retry_after_seconds(response: httpx.Response) -> int | None:
    raw_value = (
        response.headers.get("X-Rate-Limit-Retry-After-Seconds")
        or response.headers.get("Retry-After")
        or ""
    ).strip()
    if not raw_value:
        return None

    try:
        retry_after_seconds = int(raw_value)
    except ValueError:
        return None

    return retry_after_seconds if retry_after_seconds >= 0 else None


def _log_opensky_rate_limit_hint(exc: httpx.HTTPStatusError) -> None:
    """429 = too many requests in a window or credits exhausted for the day; not a bug in TerraWatch."""
    if exc.response.status_code != 429:
        return
    retry_after_seconds = _get_retry_after_seconds(exc.response)
    retry_after = (
        str(retry_after_seconds) if retry_after_seconds is not None else "(not sent)"
    )
    if retry_after_seconds is not None:
        retry_at_utc = datetime.now(timezone.utc) + timedelta(seconds=retry_after_seconds)
        retry_at_local = retry_at_utc.astimezone()
        retry_at_local_text = retry_at_local.isoformat()
        retry_at_utc_text = retry_at_utc.isoformat()
    else:
        retry_at_local_text = "(unknown)"
        retry_at_utc_text = "(unknown)"
    logger.warning(
        "OpenSky 429: you are being rate-limited (too frequent polls and/or daily credit cap). "
        "retry_after_seconds=%s retry_at_local=%s retry_at_utc=%s. "
        "Mitigations: increase ADSB_REFRESH_SECONDS in .env (e.g. 90 or 120), "
        "run only one backend hitting OpenSky, wait for the window to reset; "
        "see https://openskynetwork.github.io/opensky-api/rest.html",
        retry_after,
        retry_at_local_text,
        retry_at_utc_text,
    )


OPENSKY_STATES_API = "https://opensky-network.org/api/states/all"
TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
HTTP_TIMEOUT_SECONDS = 30.0
METERS_TO_FEET = 3.28084
MPS_TO_KNOTS = 1.94384
_HTTP_HEADERS = {"User-Agent": "TerraWatch/0.1"}
TOKEN_REFRESH_MARGIN_SECONDS = 60  # Refresh 60s before expiry


class OpenSkyTokenManager:
    """Manages OAuth2 access tokens for OpenSky API with auto-refresh."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: str | None = None
        self._expires_at: datetime | None = None
        self._http_client = http_client
        self._lock = asyncio.Lock()  # Async-safe lock for concurrent token refresh

    async def _ensure_token(self) -> str:
        """Return a valid access token, refreshing if necessary."""
        if self._token and self._expires_at and datetime.now(timezone.utc) < self._expires_at:
            return self._token

        async with self._lock:
            # Re-check after acquiring lock — another coroutine may have refreshed
            if self._token and self._expires_at and datetime.now(timezone.utc) < self._expires_at:
                return self._token
            await self._refresh_token()
            return self._token or ""

    async def _refresh_token(self) -> None:
        """Exchange client credentials for a new access token."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
            response.raise_for_status()
            data = response.json()

        self._token = data["access_token"]
        expires_in = data.get("expires_in", 1800)  # Default 30 minutes
        self._expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=expires_in - TOKEN_REFRESH_MARGIN_SECONDS
        )

    def auth_headers(self, token: str) -> dict:
        """Build Authorization header with Bearer token."""
        return {"Authorization": f"Bearer {token}"}


# Global token manager instance per-process (shared across coroutines)
_token_manager: OpenSkyTokenManager | None = None


def _get_token_manager(client_id: str, client_secret: str) -> OpenSkyTokenManager:
    """Get or create the global token manager instance."""
    global _token_manager
    if _token_manager is None:
        _token_manager = OpenSkyTokenManager(client_id, client_secret)
    return _token_manager


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


def _epoch_to_iso(epoch_seconds: int | float | None) -> str:
    numeric_epoch = _safe_float(epoch_seconds)
    if numeric_epoch is None:
        return utc_now_iso()

    try:
        return datetime.fromtimestamp(numeric_epoch, tz=timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return utc_now_iso()


def _state_timestamp(state: list[Any], response_time: int | float | None) -> str:
    last_contact = state[4] if len(state) > 4 else None
    if _safe_float(last_contact) is not None:
        return _epoch_to_iso(last_contact)
    if _safe_float(response_time) is not None:
        return _epoch_to_iso(response_time)
    return utc_now_iso()


def _normalize_state(state: list[Any], response_time: int | float | None) -> dict | None:
    if len(state) < 17:
        return None

    icao24 = (state[0] or "").strip().lower()
    lon = _safe_float(state[5])
    lat = _safe_float(state[6])

    if not icao24 or lat is None or lon is None:
        return None

    callsign = (state[1] or "").strip()
    altitude_meters = _safe_float(state[7])
    velocity_mps = _safe_float(state[9])
    heading = _safe_float(state[10], 0.0) or 0.0
    squawk = state[14] or ""

    plane = Plane(
        id=icao24,
        callsign=callsign,
        lat=lat,
        lon=lon,
        alt=round(altitude_meters * METERS_TO_FEET) if altitude_meters is not None else 0,
        heading=heading,
        speed=round(velocity_mps * MPS_TO_KNOTS, 3) if velocity_mps is not None else 0.0,
        squawk=str(squawk),
        timestamp=_state_timestamp(state, response_time),
    )
    return plane.model_dump()


async def fetch_planes(
    client_id: str | None = None,
    client_secret: str | None = None,
) -> List[dict]:
    """Fetch live plane positions from OpenSky and normalize them to the Plane contract.

    Args:
        client_id: OpenSky OAuth2 client_id (from https://opensky-network.org/my-opensky/account)
        client_secret: OpenSky OAuth2 client_secret
    """
    if not client_id or not client_secret:
        logger.info(
            "OpenSky: OPENSKY_CLIENT_ID/SECRET not set; using anonymous /states/all "
            "(strict limits — set credentials in TerraWatch/.env for Docker)"
        )
        return await _fetch_planes_unauthenticated()

    try:
        token_manager = _get_token_manager(client_id, client_secret)
        token = await token_manager._ensure_token()
        headers = {**_HTTP_HEADERS, **token_manager.auth_headers(token)}

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.get(OPENSKY_STATES_API, headers=headers)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as e:
        logger.warning(
            "OpenSky authenticated request failed (token or /states/all): %s",
            e,
        )
        if isinstance(e, httpx.HTTPStatusError):
            logger.warning(
                "OpenSky HTTP %s body (truncated): %s",
                e.response.status_code,
                (e.response.text or "")[:400],
            )
            _log_opensky_rate_limit_hint(e)
        return []

    if not isinstance(data, dict):
        return []

    response_time = data.get("time")
    states = data.get("states") or []
    planes: List[dict] = []

    for state in states:
        if not isinstance(state, list):
            continue

        plane = _normalize_state(state, response_time)
        if plane is not None:
            planes.append(plane)

    return planes


async def _fetch_planes_unauthenticated() -> List[dict]:
    """Fallback: fetch from OpenSky without authentication (strict rate limits)."""
    try:
        async with httpx.AsyncClient(
            timeout=HTTP_TIMEOUT_SECONDS,
            headers=_HTTP_HEADERS,
        ) as client:
            response = await client.get(OPENSKY_STATES_API)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("OpenSky anonymous /states/all failed: %s", e)
        if isinstance(e, httpx.HTTPStatusError):
            logger.warning(
                "OpenSky HTTP %s body (truncated): %s",
                e.response.status_code,
                (e.response.text or "")[:400],
            )
            _log_opensky_rate_limit_hint(e)
        return []

    if not isinstance(data, dict):
        return []

    response_time = data.get("time")
    states = data.get("states") or []
    planes: List[dict] = []

    for state in states:
        if not isinstance(state, list):
            continue

        plane = _normalize_state(state, response_time)
        if plane is not None:
            planes.append(plane)

    return planes


async def fetch_plane_details(icao24: str, client_id: str | None = None, client_secret: str | None = None) -> dict | None:
    """Fetch details for a specific plane by ICAO24 identifier."""
    normalized_icao24 = icao24.strip().lower()
    if not normalized_icao24:
        return None

    planes = await fetch_planes(client_id=client_id, client_secret=client_secret)
    for plane in planes:
        if plane.get("id") == normalized_icao24:
            return plane

    return None
