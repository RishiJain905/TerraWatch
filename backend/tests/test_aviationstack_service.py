import unittest
from unittest.mock import Mock, patch

import httpx

from app.services import aviationstack_service


class FakeAsyncClient:
    def __init__(self, responses_by_request=None, exceptions_by_request=None):
        self.responses_by_request = responses_by_request or {}
        self.exceptions_by_request = exceptions_by_request or {}
        self.requested_requests = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None):
        key = (url, tuple(sorted((params or {}).items())))
        self.requested_requests.append((url, params or {}))
        if key in self.exceptions_by_request:
            raise self.exceptions_by_request[key]
        return self.responses_by_request[key]


def make_response(payload=None, *, status_code=200, request_url="https://example.test"):
    request = httpx.Request("GET", request_url)
    response = Mock()
    response.status_code = status_code
    response.request = request
    response.raise_for_status = Mock()
    if status_code >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "bad response",
            request=request,
            response=httpx.Response(status_code=status_code, request=request),
        )
    response.json = Mock(return_value=payload)
    return response


class AviationstackServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_access_key = aviationstack_service.settings.AVIATIONSTACK_ACCESS_KEY
        self.original_base_url = aviationstack_service.settings.AVIATIONSTACK_BASE_URL
        self.original_route_ttl = aviationstack_service.settings.AVIATIONSTACK_ROUTE_CACHE_TTL_SECONDS
        self.original_airport_ttl = aviationstack_service.settings.AVIATIONSTACK_AIRPORT_CACHE_TTL_SECONDS
        aviationstack_service._route_cache.clear()
        aviationstack_service._airport_cache.clear()

    def tearDown(self):
        aviationstack_service.settings.AVIATIONSTACK_ACCESS_KEY = self.original_access_key
        aviationstack_service.settings.AVIATIONSTACK_BASE_URL = self.original_base_url
        aviationstack_service.settings.AVIATIONSTACK_ROUTE_CACHE_TTL_SECONDS = self.original_route_ttl
        aviationstack_service.settings.AVIATIONSTACK_AIRPORT_CACHE_TTL_SECONDS = self.original_airport_ttl
        aviationstack_service._route_cache.clear()
        aviationstack_service._airport_cache.clear()

    async def test_get_plane_route_returns_ok_and_uses_airport_cache(self):
        aviationstack_service.settings.AVIATIONSTACK_ACCESS_KEY = "test-key"

        flights_payload = {
            "data": [
                {
                    "airline": {"name": "American Airlines", "iata": "AA", "icao": "AAL", "callsign": "AMERICAN"},
                    "flight": {"iata": "AA1004", "icao": "AAL1004", "number": "1004"},
                    "departure": {"airport": "San Francisco International", "iata": "SFO", "icao": "KSFO"},
                    "arrival": {"airport": "Dallas/Fort Worth International", "iata": "DFW", "icao": "KDFW"},
                    "aircraft": {"icao24": "A0F1BB"},
                    "live": {"updated": "2026-04-10T21:00:00+00:00", "latitude": 37.5, "longitude": -122.3},
                }
            ]
        }
        airports_payload = {
            "data": [
                {
                    "airport_name": "San Francisco International",
                    "iata_code": "SFO",
                    "icao_code": "KSFO",
                    "latitude": "37.6188056",
                    "longitude": "-122.3754167",
                },
                {
                    "airport_name": "Dallas/Fort Worth International",
                    "iata_code": "DFW",
                    "icao_code": "KDFW",
                    "latitude": "32.8998",
                    "longitude": "-97.0403",
                },
            ]
        }
        fake_client = FakeAsyncClient(
            responses_by_request={
                (
                    aviationstack_service.FLIGHTS_ENDPOINT,
                    (("access_key", "test-key"), ("limit", 100)),
                ): make_response(flights_payload, request_url=aviationstack_service.FLIGHTS_ENDPOINT),
                (
                    aviationstack_service.AIRPORTS_ENDPOINT,
                    (("access_key", "test-key"), ("limit", 100), ("search", "SFO")),
                ): make_response(airports_payload, request_url=aviationstack_service.AIRPORTS_ENDPOINT),
                (
                    aviationstack_service.AIRPORTS_ENDPOINT,
                    (("access_key", "test-key"), ("limit", 100), ("search", "DFW")),
                ): make_response(airports_payload, request_url=aviationstack_service.AIRPORTS_ENDPOINT),
            }
        )

        with patch("app.services.aviationstack_service.httpx.AsyncClient", return_value=fake_client):
            service = aviationstack_service.AviationstackService()
            route = await service.get_plane_route(
                plane_id="a0f1bb",
                callsign="AA1004",
                lat=37.6,
                lon=-122.3,
            )

            cached_route = await service.get_plane_route(
                plane_id="a0f1bb",
                callsign="AA1004",
                lat=37.7,
                lon=-122.4,
            )

        self.assertEqual(route.status, "ok")
        self.assertEqual(route.resolved_by, "icao24")
        self.assertEqual(route.flight_iata, "AA1004")
        self.assertEqual(route.departure.iata, "SFO")
        self.assertEqual(route.arrival.icao, "KDFW")
        self.assertEqual(route.departure.lat, 37.6188056)
        self.assertEqual(route.arrival.lon, -97.0403)
        self.assertEqual(cached_route.model_dump(), route.model_dump())
        self.assertEqual(len(fake_client.requested_requests), 3)

    async def test_get_plane_route_reuses_airport_cache_across_different_planes(self):
        aviationstack_service.settings.AVIATIONSTACK_ACCESS_KEY = "test-key"

        flights_payload = {
            "data": [
                {
                    "airline": {"name": "American Airlines", "iata": "AA", "icao": "AAL", "callsign": "AMERICAN"},
                    "flight": {"iata": "AA1004", "icao": "AAL1004", "number": "1004"},
                    "departure": {"airport": "San Francisco International", "iata": "SFO", "icao": "KSFO"},
                    "arrival": {"airport": "Dallas/Fort Worth International", "iata": "DFW", "icao": "KDFW"},
                    "aircraft": {"icao24": "A0F1BB"},
                    "live": {"updated": "2026-04-10T21:00:00+00:00", "latitude": 37.5, "longitude": -122.3},
                },
                {
                    "airline": {"name": "American Airlines", "iata": "AA", "icao": "AAL", "callsign": "AMERICAN"},
                    "flight": {"iata": "AA1005", "icao": "AAL1005", "number": "1005"},
                    "departure": {"airport": "San Francisco International", "iata": "SFO", "icao": "KSFO"},
                    "arrival": {"airport": "Dallas/Fort Worth International", "iata": "DFW", "icao": "KDFW"},
                    "aircraft": {"icao24": "B0F1BB"},
                    "live": {"updated": "2026-04-10T21:05:00+00:00", "latitude": 37.4, "longitude": -122.2},
                },
            ]
        }
        airports_payload = {
            "data": [
                {
                    "airport_name": "San Francisco International",
                    "iata_code": "SFO",
                    "icao_code": "KSFO",
                    "latitude": "37.6188056",
                    "longitude": "-122.3754167",
                },
                {
                    "airport_name": "Dallas/Fort Worth International",
                    "iata_code": "DFW",
                    "icao_code": "KDFW",
                    "latitude": "32.8998",
                    "longitude": "-97.0403",
                },
            ]
        }
        fake_client = FakeAsyncClient(
            responses_by_request={
                (
                    aviationstack_service.FLIGHTS_ENDPOINT,
                    (("access_key", "test-key"), ("limit", 100)),
                ): make_response(flights_payload, request_url=aviationstack_service.FLIGHTS_ENDPOINT),
                (
                    aviationstack_service.AIRPORTS_ENDPOINT,
                    (("access_key", "test-key"), ("limit", 100), ("search", "SFO")),
                ): make_response(airports_payload, request_url=aviationstack_service.AIRPORTS_ENDPOINT),
                (
                    aviationstack_service.AIRPORTS_ENDPOINT,
                    (("access_key", "test-key"), ("limit", 100), ("search", "DFW")),
                ): make_response(airports_payload, request_url=aviationstack_service.AIRPORTS_ENDPOINT),
            }
        )

        with patch("app.services.aviationstack_service.httpx.AsyncClient", return_value=fake_client):
            service = aviationstack_service.AviationstackService()
            first_route = await service.get_plane_route(
                plane_id="a0f1bb",
                callsign="AA1004",
                lat=37.6,
                lon=-122.3,
            )
            second_route = await service.get_plane_route(
                plane_id="b0f1bb",
                callsign="AA1005",
                lat=37.6,
                lon=-122.3,
            )

        self.assertEqual(first_route.status, "ok")
        self.assertEqual(second_route.status, "ok")
        self.assertEqual(len(fake_client.requested_requests), 4)

    async def test_get_plane_route_prefers_exact_icao24_over_callsign_only_match(self):
        aviationstack_service.settings.AVIATIONSTACK_ACCESS_KEY = "test-key"

        flights_payload = {
            "data": [
                {
                    "airline": {"name": "Wrong Match", "iata": "WM", "icao": "WRG", "callsign": "TEST123"},
                    "flight": {"iata": "WM999", "icao": "WRG999", "number": "999"},
                    "departure": {"airport": "A", "iata": "AAA", "icao": "AAAA"},
                    "arrival": {"airport": "B", "iata": "BBB", "icao": "BBBB"},
                    "aircraft": {"icao24": "deadbe"},
                    "live": {"updated": "2026-04-10T21:00:00+00:00", "latitude": 1.0, "longitude": 2.0},
                },
                {
                    "airline": {"name": "Correct Match", "iata": "AA", "icao": "AAL", "callsign": "AMERICAN"},
                    "flight": {"iata": "AA1004", "icao": "AAL1004", "number": "1004"},
                    "departure": {"airport": "San Francisco International", "iata": "SFO", "icao": "KSFO"},
                    "arrival": {"airport": "Dallas/Fort Worth International", "iata": "DFW", "icao": "KDFW"},
                    "aircraft": {"icao24": "A0F1BB"},
                    "live": {"updated": "2026-04-10T21:00:00+00:00", "latitude": 37.5, "longitude": -122.3},
                },
            ]
        }
        airports_payload = {
            "data": [
                {
                    "airport_name": "San Francisco International",
                    "iata_code": "SFO",
                    "icao_code": "KSFO",
                    "latitude": "37.6188056",
                    "longitude": "-122.3754167",
                },
                {
                    "airport_name": "Dallas/Fort Worth International",
                    "iata_code": "DFW",
                    "icao_code": "KDFW",
                    "latitude": "32.8998",
                    "longitude": "-97.0403",
                },
            ]
        }
        fake_client = FakeAsyncClient(
            responses_by_request={
                (
                    aviationstack_service.FLIGHTS_ENDPOINT,
                    (("access_key", "test-key"), ("limit", 100)),
                ): make_response(flights_payload, request_url=aviationstack_service.FLIGHTS_ENDPOINT),
                (
                    aviationstack_service.AIRPORTS_ENDPOINT,
                    (("access_key", "test-key"), ("limit", 100), ("search", "SFO")),
                ): make_response(airports_payload, request_url=aviationstack_service.AIRPORTS_ENDPOINT),
                (
                    aviationstack_service.AIRPORTS_ENDPOINT,
                    (("access_key", "test-key"), ("limit", 100), ("search", "DFW")),
                ): make_response(airports_payload, request_url=aviationstack_service.AIRPORTS_ENDPOINT),
            }
        )

        with patch("app.services.aviationstack_service.httpx.AsyncClient", return_value=fake_client):
            service = aviationstack_service.AviationstackService()
            route = await service.get_plane_route(
                plane_id="a0f1bb",
                callsign="TEST123",
                lat=37.6,
                lon=-122.3,
            )

        self.assertEqual(route.status, "ok")
        self.assertEqual(route.resolved_by, "icao24")
        self.assertEqual(route.flight_iata, "AA1004")
        self.assertEqual(route.airline_icao, "AAL")

    async def test_get_plane_route_returns_not_found_when_no_flight_matches(self):
        aviationstack_service.settings.AVIATIONSTACK_ACCESS_KEY = "test-key"
        fake_client = FakeAsyncClient(
            responses_by_request={
                (
                    aviationstack_service.FLIGHTS_ENDPOINT,
                    (("access_key", "test-key"), ("limit", 100)),
                ): make_response({"data": []}, request_url=aviationstack_service.FLIGHTS_ENDPOINT),
            }
        )

        with patch("app.services.aviationstack_service.httpx.AsyncClient", return_value=fake_client):
            service = aviationstack_service.AviationstackService()
            route = await service.get_plane_route(
                plane_id="a0f1bb",
                callsign="TEST123",
                lat=37.6,
                lon=-122.3,
            )

        self.assertEqual(route.status, "not_found")
        self.assertEqual(route.resolved_by, "none")
        self.assertEqual(len(fake_client.requested_requests), 1)

    async def test_get_plane_route_uses_direct_airport_coordinates_without_lookup_codes(self):
        aviationstack_service.settings.AVIATIONSTACK_ACCESS_KEY = "test-key"
        flights_payload = {
            "data": [
                {
                    "airline": {"name": "Test Air", "iata": "TA", "icao": "TST"},
                    "flight": {"iata": "TA101", "icao": "TST101"},
                    "departure": {"airport": "Dep", "latitude": "37.6188", "longitude": "-122.3754"},
                    "arrival": {"airport": "Arr", "latitude": "32.8998", "longitude": "-97.0403"},
                    "aircraft": {"icao24": "A0F1BB"},
                    "live": {"updated": "2026-04-10T21:00:00+00:00", "latitude": 37.5, "longitude": -122.3},
                }
            ]
        }
        fake_client = FakeAsyncClient(
            responses_by_request={
                (
                    aviationstack_service.FLIGHTS_ENDPOINT,
                    (("access_key", "test-key"), ("limit", 100)),
                ): make_response(flights_payload, request_url=aviationstack_service.FLIGHTS_ENDPOINT),
            }
        )

        with patch("app.services.aviationstack_service.httpx.AsyncClient", return_value=fake_client):
            service = aviationstack_service.AviationstackService()
            route = await service.get_plane_route(
                plane_id="a0f1bb",
                callsign="TA101",
                lat=37.6,
                lon=-122.3,
            )

        self.assertEqual(route.status, "ok")
        self.assertEqual(route.departure.lat, 37.6188)
        self.assertEqual(route.arrival.lon, -97.0403)
        self.assertEqual(len(fake_client.requested_requests), 1)

    async def test_get_plane_route_returns_rate_limited_on_upstream_429(self):
        aviationstack_service.settings.AVIATIONSTACK_ACCESS_KEY = "test-key"
        request = httpx.Request("GET", aviationstack_service.FLIGHTS_ENDPOINT)
        response = httpx.Response(status_code=429, request=request)
        fake_client = FakeAsyncClient(
            exceptions_by_request={
                (
                    aviationstack_service.FLIGHTS_ENDPOINT,
                    (("access_key", "test-key"), ("limit", 100)),
                ): httpx.HTTPStatusError("rate limited", request=request, response=response)
            }
        )

        with patch("app.services.aviationstack_service.httpx.AsyncClient", return_value=fake_client):
            service = aviationstack_service.AviationstackService()
            route = await service.get_plane_route(
                plane_id="a0f1bb",
                callsign="TEST123",
                lat=37.6,
                lon=-122.3,
            )

        self.assertEqual(route.status, "rate_limited")
        self.assertEqual(route.resolved_by, "none")

    async def test_get_plane_route_returns_error_when_access_key_missing(self):
        aviationstack_service.settings.AVIATIONSTACK_ACCESS_KEY = ""

        with patch("app.services.aviationstack_service.httpx.AsyncClient") as client_cls:
            service = aviationstack_service.AviationstackService()
            route = await service.get_plane_route(
                plane_id="a0f1bb",
                callsign="TEST123",
                lat=37.6,
                lon=-122.3,
            )

        client_cls.assert_not_called()
        self.assertEqual(route.status, "error")
        self.assertEqual(route.resolved_by, "none")
        self.assertEqual(route.provider, "aviationstack")
