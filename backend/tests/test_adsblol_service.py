import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import httpx

from app.services import adsblol_service

TEST_ADSBLOL_API_URL = "https://example.test/aircraft"


class FakeAsyncClient:
    def __init__(self, response=None, exception=None):
        self.response = response
        self.exception = exception
        self.requested_url = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url):
        self.requested_url = url
        if self.exception is not None:
            raise self.exception
        return self.response


class AdsblolServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_api_url = adsblol_service.settings.ADSBLOL_API_URL
        self.original_constant = adsblol_service.ADSBLOL_AIRCRAFT_API
        adsblol_service.settings.ADSBLOL_API_URL = TEST_ADSBLOL_API_URL
        adsblol_service.ADSBLOL_AIRCRAFT_API = TEST_ADSBLOL_API_URL

    def tearDown(self):
        adsblol_service.settings.ADSBLOL_API_URL = self.original_api_url
        adsblol_service.ADSBLOL_AIRCRAFT_API = self.original_constant

    async def test_fetch_planes_uses_point_endpoint_when_region_configured(self):
        payload = {
            "ctime": 1712751234,
            "ac": [
                {
                    "hex": "76cccd",
                    "flight": " TEST123 ",
                    "lat": 37.6188056,
                    "lon": -122.3754167,
                    "alt_baro": 34000,
                    "track": 271.2,
                    "gs": 451.5,
                    "squawk": "1234",
                }
            ],
        }
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value=payload)
        fake_client = FakeAsyncClient(response=response)
        service = adsblol_service.AdsblolService(
            api_url="https://api.adsb.lol/aircraft/json",
            query_lat=37.6188056,
            query_lon=-122.3754167,
            query_radius_nm=50,
        )

        with patch("app.services.adsblol_service.httpx.AsyncClient", return_value=fake_client):
            planes = await service.fetch_planes()

        self.assertEqual(
            fake_client.requested_url,
            "https://api.adsb.lol/v2/point/37.6188056/-122.3754167/50",
        )
        self.assertEqual(planes[0]["id"], "76cccd")

    async def test_fetch_planes_parses_response(self):
        payload = {
            "last_timestamp": 1712751234,
            "ac": [
                {
                    "hex": "76cccd",
                    "flight": " TEST123 ",
                    "lat": 37.6188056,
                    "lng": -122.3754167,
                    "alt": 34000,
                    "dir": 271.2,
                    "speed": 451.5,
                    "squawk": "1234",
                },
                {
                    "hex": "missingpos",
                    "flight": "SKIPME",
                    "lat": None,
                    "lng": -122.0,
                },
                "bad-row",
            ]
        }
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value=payload)
        fake_client = FakeAsyncClient(response=response)

        with patch("app.services.adsblol_service.httpx.AsyncClient", return_value=fake_client):
            planes = await adsblol_service.fetch_planes()

        self.assertEqual(fake_client.requested_url, adsblol_service.ADSBLOL_AIRCRAFT_API)
        self.assertEqual(
            planes,
            [
                {
                    "id": "76cccd",
                    "callsign": "TEST123",
                    "lat": 37.6188056,
                    "lon": -122.3754167,
                    "alt": 34000,
                    "heading": 271.2,
                    "speed": 451.5,
                    "squawk": "1234",
                    "timestamp": datetime.fromtimestamp(1712751234, tz=timezone.utc).isoformat(),
                }
            ],
        )

    async def test_fetch_planes_uses_top_level_ctime_before_record_timestamp_fallbacks(self):
        payload = {
            "ctime": 1712759999,
            "ac": [
                {
                    "hex": "abc123",
                    "flight": "FALLBACK1",
                    "lat": 40.0,
                    "lng": -70.0,
                    "alt": 12000,
                    "dir": 90,
                    "speed": 320,
                    "last_timestamp": 1712700000,
                }
            ],
        }
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value=payload)

        with patch(
            "app.services.adsblol_service.httpx.AsyncClient",
            return_value=FakeAsyncClient(response=response),
        ):
            planes = await adsblol_service.fetch_planes()

        self.assertEqual(
            planes[0]["timestamp"],
            datetime.fromtimestamp(1712759999, tz=timezone.utc).isoformat(),
        )

    async def test_fetch_planes_converts_millisecond_ctime_from_v2_api(self):
        payload = {
            "ctime": 1712759999000,
            "ac": [
                {
                    "hex": "abc123",
                    "flight": "FALLBACK1",
                    "lat": 40.0,
                    "lon": -70.0,
                    "alt_baro": 12000,
                    "track": 90,
                    "gs": 320,
                }
            ],
        }
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value=payload)

        with patch(
            "app.services.adsblol_service.httpx.AsyncClient",
            return_value=FakeAsyncClient(response=response),
        ):
            planes = await adsblol_service.fetch_planes()

        self.assertEqual(
            planes[0]["timestamp"],
            datetime.fromtimestamp(1712759999, tz=timezone.utc).isoformat(),
        )

    def test_hex_normalized_to_uppercase(self):
        self.assertEqual(adsblol_service.normalize_hex("76cccd"), "76CCCD")

    async def test_fetch_planes_handles_empty_response(self):
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value={"ac": []})

        with patch(
            "app.services.adsblol_service.httpx.AsyncClient",
            return_value=FakeAsyncClient(response=response),
        ):
            planes = await adsblol_service.fetch_planes()

        self.assertEqual(planes, [])

    async def test_fetch_planes_handles_timeout(self):
        request = httpx.Request("GET", adsblol_service.ADSBLOL_AIRCRAFT_API)
        fake_client = FakeAsyncClient(exception=httpx.ReadTimeout("timeout", request=request))

        with patch("app.services.adsblol_service.httpx.AsyncClient", return_value=fake_client):
            planes = await adsblol_service.fetch_planes()

        self.assertEqual(planes, [])

    async def test_fetch_planes_handles_http_error(self):
        request = httpx.Request("GET", adsblol_service.ADSBLOL_AIRCRAFT_API)
        response = Mock()
        response.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError(
                "bad response",
                request=request,
                response=httpx.Response(status_code=404, request=request),
            )
        )
        response.json = Mock(return_value={"ac": []})

        with patch(
            "app.services.adsblol_service.httpx.AsyncClient",
            return_value=FakeAsyncClient(response=response),
        ):
            planes = await adsblol_service.fetch_planes()

        self.assertEqual(planes, [])

    async def test_fetch_planes_returns_empty_list_for_unexpected_top_level_json_shape(self):
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value=["not", "a", "dict"])

        with patch(
            "app.services.adsblol_service.httpx.AsyncClient",
            return_value=FakeAsyncClient(response=response),
        ):
            planes = await adsblol_service.fetch_planes()

        self.assertEqual(planes, [])

    async def test_fetch_planes_returns_empty_list_for_invalid_json(self):
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(side_effect=ValueError("bad json"))

        with patch(
            "app.services.adsblol_service.httpx.AsyncClient",
            return_value=FakeAsyncClient(response=response),
        ):
            planes = await adsblol_service.fetch_planes()

        self.assertEqual(planes, [])

    async def test_fetch_planes_uses_fallback_fields_when_primary_spec_fields_missing(self):
        payload = {
            "ctime": 1712757777,
            "ac": [
                {
                    "hex": "ABCDEF",
                    "flight": None,
                    "lat": 51.5,
                    "lon": -0.12,
                    "alt_baro": 12000,
                    "track": 180.0,
                    "gs": 250.5,
                    "squawk": None,
                }
            ],
        }
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value=payload)

        with patch(
            "app.services.adsblol_service.httpx.AsyncClient",
            return_value=FakeAsyncClient(response=response),
        ):
            planes = await adsblol_service.fetch_planes()

        self.assertEqual(
            planes,
            [
                {
                    "id": "abcdef",
                    "callsign": "",
                    "lat": 51.5,
                    "lon": -0.12,
                    "alt": 12000,
                    "heading": 180.0,
                    "speed": 250.5,
                    "squawk": "",
                    "timestamp": datetime.fromtimestamp(1712757777, tz=timezone.utc).isoformat(),
                }
            ],
        )

    async def test_fetch_planes_returns_empty_list_when_aircraft_list_missing_or_invalid(self):
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value={"ac": "not-a-list"})

        with patch(
            "app.services.adsblol_service.httpx.AsyncClient",
            return_value=FakeAsyncClient(response=response),
        ):
            planes = await adsblol_service.fetch_planes()

        self.assertEqual(planes, [])


if __name__ == "__main__":
    unittest.main()
