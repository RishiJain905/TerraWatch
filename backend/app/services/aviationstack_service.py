from __future__ import annotations

from datetime import datetime, timezone
import logging
import math
from time import monotonic
from typing import Any

import httpx

from app.config import settings
from app.core.models import PlaneRoute, PlaneRouteAirport, utc_now_iso

logger = logging.getLogger(__name__)

HTTP_TIMEOUT_SECONDS = 20.0
HTTP_HEADERS = {
    "Accept-Encoding": "gzip",
    "User-Agent": "TerraWatch/0.1",
}

FLIGHTS_ENDPOINT = f"{settings.AVIATIONSTACK_BASE_URL.rstrip('/')}/flights"
AIRPORTS_ENDPOINT = f"{settings.AVIATIONSTACK_BASE_URL.rstrip('/')}/airports"

_route_cache: dict[tuple[str, str], tuple[float, PlaneRoute]] = {}
_airport_cache: dict[tuple[str, str], tuple[float, PlaneRouteAirport | None]] = {}
_CACHE_MISS = object()


class AviationstackError(RuntimeError):
    pass


class AviationstackRateLimitedError(AviationstackError):
    pass


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_code(value: Any) -> str:
    return _normalize_text(value).upper()


def _normalize_plane_id(value: Any) -> str:
    return _normalize_text(value).lower()


def _normalize_callsign(value: Any) -> str:
    return _normalize_text(value).replace(" ", "").upper()


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(numeric):
        return None

    return numeric


def _cache_get(cache: dict[tuple[str, str], tuple[float, Any]], key: tuple[str, str]) -> Any:
    cached = cache.get(key)
    if cached is None:
        return _CACHE_MISS

    expires_at, value = cached
    if expires_at <= monotonic():
        cache.pop(key, None)
        return _CACHE_MISS

    return value


def _cache_set(cache: dict[tuple[str, str], tuple[float, Any]], key: tuple[str, str], value: Any, ttl_seconds: int) -> None:
    cache[key] = (monotonic() + ttl_seconds, value)


def _unique_keys(*keys: tuple[str, str]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    ordered: list[tuple[str, str]] = []
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        ordered.append(key)
    return ordered


def _airport_cache_keys(iata: str, icao: str) -> list[tuple[str, str]]:
    normalized_iata = _normalize_code(iata)
    normalized_icao = _normalize_code(icao)
    if not normalized_iata and not normalized_icao:
        return []
    return _unique_keys(
        (normalized_iata, normalized_icao),
        (normalized_iata, ""),
        ("", normalized_icao),
    )


def _airport_key_variants(airport: dict[str, Any]) -> list[tuple[str, str]]:
    return _airport_cache_keys(airport.get("iata") or airport.get("iata_code"), airport.get("icao") or airport.get("icao_code"))


def _extract_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = payload.get("data")
    if not isinstance(records, list):
        records = payload.get("results")
    if not isinstance(records, list):
        raise AviationstackError("Unexpected Aviationstack payload shape")
    return [record for record in records if isinstance(record, dict)]


def _response_text_error(payload: dict[str, Any]) -> str:
    error = payload.get("error")
    if not isinstance(error, dict):
        return ""
    return _normalize_text(error.get("message") or error.get("code"))


def _flight_identifier_candidates(flight: dict[str, Any]) -> set[str]:
    airline = flight.get("airline") if isinstance(flight.get("airline"), dict) else {}
    flight_info = flight.get("flight") if isinstance(flight.get("flight"), dict) else {}
    aircraft = flight.get("aircraft") if isinstance(flight.get("aircraft"), dict) else {}

    return {
        _normalize_callsign(airline.get("callsign")),
        _normalize_callsign(airline.get("iata")),
        _normalize_callsign(airline.get("icao")),
        _normalize_callsign(flight_info.get("iata")),
        _normalize_callsign(flight_info.get("icao")),
        _normalize_callsign(flight_info.get("number")),
        _normalize_callsign(aircraft.get("registration")),
    }


def _flight_aircraft_icao24(flight: dict[str, Any]) -> str:
    aircraft = flight.get("aircraft") if isinstance(flight.get("aircraft"), dict) else {}
    return _normalize_plane_id(aircraft.get("icao24"))


def _flight_live_coordinates(flight: dict[str, Any]) -> tuple[float | None, float | None]:
    live = flight.get("live") if isinstance(flight.get("live"), dict) else {}
    lat = _safe_float(live.get("latitude"))
    lon = _safe_float(live.get("longitude"))
    return lat, lon


def _flight_live_updated(flight: dict[str, Any]) -> str:
    live = flight.get("live") if isinstance(flight.get("live"), dict) else {}
    return _normalize_text(live.get("updated"))


def _flight_live_updated_epoch(flight: dict[str, Any]) -> float:
    updated = _flight_live_updated(flight)
    if not updated:
        return float("-inf")
    try:
        return datetime.fromisoformat(updated.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp()
    except ValueError:
        return float("-inf")


def _distance_km(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    # Haversine distance is sufficient here; the values only drive tie-breaking.
    radius_km = 6371.0
    phi1 = math.radians(lat_a)
    phi2 = math.radians(lat_b)
    delta_phi = math.radians(lat_b - lat_a)
    delta_lambda = math.radians(lon_b - lon_a)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return 2 * radius_km * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _best_flight_match(
    flights: list[dict[str, Any]],
    *,
    plane_id: str,
    callsign: str,
    lat: float,
    lon: float,
) -> dict[str, Any] | None:
    normalized_plane_id = _normalize_plane_id(plane_id)
    normalized_callsign = _normalize_callsign(callsign)

    exact_icao24_matches = [flight for flight in flights if _flight_aircraft_icao24(flight) == normalized_plane_id]
    if exact_icao24_matches:
        return sorted(exact_icao24_matches, key=_flight_live_updated_epoch, reverse=True)[0]

    if not normalized_callsign:
        return None

    callsign_matches = [flight for flight in flights if normalized_callsign in _flight_identifier_candidates(flight)]
    if not callsign_matches:
        return None

    def sort_key(flight: dict[str, Any]) -> tuple[float, float]:
        flight_lat, flight_lon = _flight_live_coordinates(flight)
        if flight_lat is None or flight_lon is None:
            return (float("inf"), float("inf"))
        return (_distance_km(lat, lon, flight_lat, flight_lon), -_flight_live_updated_epoch(flight))

    return sorted(callsign_matches, key=sort_key)[0]


def _airport_from_record(record: dict[str, Any]) -> PlaneRouteAirport:
    lat = _safe_float(record.get("latitude"))
    lon = _safe_float(record.get("longitude"))
    return PlaneRouteAirport(
        name=_normalize_text(record.get("airport_name")),
        iata=_normalize_code(record.get("iata_code")),
        icao=_normalize_code(record.get("icao_code")),
        lat=lat,
        lon=lon,
    )


def _cache_airport(airport: PlaneRouteAirport | None, source_keys: list[tuple[str, str]], ttl_seconds: int) -> None:
    for key in source_keys:
        _cache_set(_airport_cache, key, airport, ttl_seconds)


class AviationstackService:
    def __init__(self) -> None:
        self.access_key = settings.AVIATIONSTACK_ACCESS_KEY
        self.base_url = settings.AVIATIONSTACK_BASE_URL
        self.route_cache_ttl_seconds = settings.AVIATIONSTACK_ROUTE_CACHE_TTL_SECONDS
        self.airport_cache_ttl_seconds = settings.AVIATIONSTACK_AIRPORT_CACHE_TTL_SECONDS
        self.flights_endpoint = f"{self.base_url.rstrip('/')}/flights"
        self.airports_endpoint = f"{self.base_url.rstrip('/')}/airports"

    async def _request_json(self, client: httpx.AsyncClient, url: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await client.get(url, params=params)
        except httpx.RequestError as exc:
            raise AviationstackError(str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise AviationstackRateLimitedError(str(exc)) from exc
            raise AviationstackError(str(exc)) from exc

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise AviationstackRateLimitedError(str(exc)) from exc
            raise AviationstackError(str(exc)) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise AviationstackError("Invalid JSON from Aviationstack") from exc

        if not isinstance(payload, dict):
            raise AviationstackError("Unexpected Aviationstack payload shape")

        error_text = _response_text_error(payload)
        if error_text:
            error_code = _normalize_text(payload.get("error", {}).get("code")).lower() if isinstance(payload.get("error"), dict) else ""
            if "rate" in error_code:
                raise AviationstackRateLimitedError(error_text)
            raise AviationstackError(error_text)

        return payload

    async def _fetch_flights(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        payload = await self._request_json(
            client,
            self.flights_endpoint,
            {
                "access_key": self.access_key,
                "limit": 100,
            },
        )
        return _extract_records(payload)

    async def _resolve_airport(self, client: httpx.AsyncClient, airport_data: dict[str, Any]) -> PlaneRouteAirport | None:
        source_keys = _airport_key_variants(airport_data)

        if source_keys:
            for key in source_keys:
                cached = _cache_get(_airport_cache, key)
                if cached is not _CACHE_MISS:
                    return cached

        direct_airport = None
        if _safe_float(airport_data.get("latitude")) is not None and _safe_float(airport_data.get("longitude")) is not None:
            direct_airport = PlaneRouteAirport(
                name=_normalize_text(airport_data.get("airport") or airport_data.get("airport_name")),
                iata=_normalize_code(airport_data.get("iata") or airport_data.get("iata_code")),
                icao=_normalize_code(airport_data.get("icao") or airport_data.get("icao_code")),
                lat=_safe_float(airport_data.get("latitude")),
                lon=_safe_float(airport_data.get("longitude")),
            )
            if source_keys:
                _cache_airport(direct_airport, source_keys, self.airport_cache_ttl_seconds)
            return direct_airport

        if not source_keys:
            return None

        lookup_code = _normalize_code(airport_data.get("iata") or airport_data.get("iata_code") or airport_data.get("icao") or airport_data.get("icao_code"))
        if not lookup_code:
            _cache_airport(None, source_keys, self.airport_cache_ttl_seconds)
            return None

        payload = await self._request_json(
            client,
            self.airports_endpoint,
            {
                "access_key": self.access_key,
                "limit": 100,
                "search": lookup_code,
            },
        )
        airports = _extract_records(payload)
        if not airports:
            _cache_airport(None, source_keys, self.airport_cache_ttl_seconds)
            return None

        selected = None
        for record in airports:
            airport = _airport_from_record(record)
            if airport.iata == lookup_code or airport.icao == lookup_code:
                selected = airport
                break
            if selected is None:
                selected = airport

        if selected is None or (selected.lat is None and selected.lon is None):
            _cache_airport(None, source_keys, self.airport_cache_ttl_seconds)
            return None

        cache_keys = _unique_keys(*source_keys, *_airport_cache_keys(selected.iata, selected.icao))
        _cache_airport(selected, cache_keys, self.airport_cache_ttl_seconds)
        return selected

    def _error_route(self, *, plane_id: str, status: str) -> PlaneRoute:
        return PlaneRoute(
            plane_id=plane_id,
            resolved_by="none",
            status=status,  # type: ignore[arg-type]
            provider="aviationstack",
            last_updated=utc_now_iso(),
        )

    async def get_plane_route(
        self,
        *,
        plane_id: str,
        callsign: str,
        lat: float,
        lon: float,
    ) -> PlaneRoute:
        normalized_plane_id = _normalize_plane_id(plane_id)
        normalized_callsign = _normalize_callsign(callsign)
        cache_key = (normalized_plane_id, normalized_callsign)

        cached_route = _cache_get(_route_cache, cache_key)
        if cached_route is not _CACHE_MISS:
            return cached_route

        if not self.access_key:
            route = self._error_route(plane_id=normalized_plane_id, status="error")
            _cache_set(_route_cache, cache_key, route, self.route_cache_ttl_seconds)
            return route

        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS, headers=HTTP_HEADERS) as client:
                flights = await self._fetch_flights(client)
                matched_flight = _best_flight_match(
                    flights,
                    plane_id=normalized_plane_id,
                    callsign=normalized_callsign,
                    lat=lat,
                    lon=lon,
                )

                if matched_flight is None:
                    route = PlaneRoute(
                        plane_id=normalized_plane_id,
                        resolved_by="none",
                        status="not_found",
                        provider="aviationstack",
                        last_updated=utc_now_iso(),
                    )
                    _cache_set(_route_cache, cache_key, route, self.route_cache_ttl_seconds)
                    return route

                departure_data = matched_flight.get("departure") if isinstance(matched_flight.get("departure"), dict) else {}
                arrival_data = matched_flight.get("arrival") if isinstance(matched_flight.get("arrival"), dict) else {}
                airline_data = matched_flight.get("airline") if isinstance(matched_flight.get("airline"), dict) else {}
                flight_data = matched_flight.get("flight") if isinstance(matched_flight.get("flight"), dict) else {}

                departure = await self._resolve_airport(client, departure_data)
                arrival = await self._resolve_airport(client, arrival_data)

                if departure is None or arrival is None or departure.lat is None or departure.lon is None or arrival.lat is None or arrival.lon is None:
                    route = PlaneRoute(
                        plane_id=normalized_plane_id,
                        resolved_by="icao24" if _flight_aircraft_icao24(matched_flight) == normalized_plane_id else "callsign",
                        status="not_found",
                        provider="aviationstack",
                        flight_iata=_normalize_text(flight_data.get("iata")),
                        flight_icao=_normalize_text(flight_data.get("icao")),
                        airline_name=_normalize_text(airline_data.get("name")),
                        airline_iata=_normalize_text(airline_data.get("iata")),
                        airline_icao=_normalize_text(airline_data.get("icao")),
                        departure=departure or PlaneRouteAirport(),
                        arrival=arrival or PlaneRouteAirport(),
                        last_updated=utc_now_iso(),
                    )
                    _cache_set(_route_cache, cache_key, route, self.route_cache_ttl_seconds)
                    return route

                route = PlaneRoute(
                    plane_id=normalized_plane_id,
                    resolved_by="icao24" if _flight_aircraft_icao24(matched_flight) == normalized_plane_id else "callsign",
                    status="ok",
                    provider="aviationstack",
                    flight_iata=_normalize_text(flight_data.get("iata")),
                    flight_icao=_normalize_text(flight_data.get("icao")),
                    airline_name=_normalize_text(airline_data.get("name")),
                    airline_iata=_normalize_text(airline_data.get("iata")),
                    airline_icao=_normalize_text(airline_data.get("icao")),
                    departure=departure,
                    arrival=arrival,
                    last_updated=utc_now_iso(),
                )
                _cache_set(_route_cache, cache_key, route, self.route_cache_ttl_seconds)
                return route
        except AviationstackRateLimitedError:
            route = self._error_route(plane_id=normalized_plane_id, status="rate_limited")
            _cache_set(_route_cache, cache_key, route, self.route_cache_ttl_seconds)
            return route
        except AviationstackError:
            route = self._error_route(plane_id=normalized_plane_id, status="error")
            _cache_set(_route_cache, cache_key, route, self.route_cache_ttl_seconds)
            return route
