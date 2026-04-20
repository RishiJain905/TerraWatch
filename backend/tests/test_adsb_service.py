import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import httpx

from app.services import adsb_service


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


class ADSBServiceTests(unittest.IsolatedAsyncioTestCase):
    def test_log_opensky_rate_limit_hint_uses_opensky_retry_header(self):
        request = httpx.Request("GET", adsb_service.OPENSKY_STATES_API)
        response = httpx.Response(
            429,
            request=request,
            headers={"X-Rate-Limit-Retry-After-Seconds": "45684"},
            text="Too many requests",
        )
        exc = httpx.HTTPStatusError("429 Too Many Requests", request=request, response=response)

        with patch.object(adsb_service.logger, "warning") as mock_warning:
            adsb_service._log_opensky_rate_limit_hint(exc)

        mock_warning.assert_called_once()
        message, retry_after, retry_at_local, retry_at_utc = mock_warning.call_args.args[:4]
        self.assertIn("retry_after_seconds=%s", message)
        self.assertIn("retry_at_local=%s", message)
        self.assertIn("retry_at_utc=%s", message)
        self.assertEqual(retry_after, "45684")
        self.assertNotEqual(retry_at_local, "(unknown)")
        self.assertNotEqual(retry_at_utc, "(unknown)")

    async def test_fetch_planes_normalizes_opensky_states(self):
        payload = {
            "time": 1712751234,
            "states": [
                [
                    "abc123",
                    " TEST123 ",
                    "United States",
                    1712751228,
                    1712751230,
                    20.5,
                    10.25,
                    1000.0,
                    False,
                    100.0,
                    180.5,
                    0.0,
                    None,
                    1100.0,
                    "1234",
                    False,
                    0,
                ],
                [
                    "skip01",
                    "NOPOS",
                    "United States",
                    1712751228,
                    1712751230,
                    None,
                    10.25,
                    1000.0,
                    False,
                    100.0,
                    180.5,
                    0.0,
                    None,
                    1100.0,
                    "2200",
                    False,
                    0,
                ],
                ["too-short"],
            ],
        }
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value=payload)
        fake_client = FakeAsyncClient(response=response)

        with patch("app.services.adsb_service.httpx.AsyncClient", return_value=fake_client):
            planes = await adsb_service.fetch_planes()

        self.assertEqual(fake_client.requested_url, adsb_service.OPENSKY_STATES_API)
        self.assertEqual(len(planes), 1)
        self.assertEqual(
            planes[0],
            {
                "id": "abc123",
                "callsign": "TEST123",
                "lat": 10.25,
                "lon": 20.5,
                "alt": 3281,
                "heading": 180.5,
                "speed": 194.384,
                "squawk": "1234",
                "timestamp": datetime.fromtimestamp(1712751230, tz=timezone.utc).isoformat(),
            },
        )

    async def test_fetch_planes_uses_safe_defaults_for_missing_optional_values(self):
        payload = {
            "time": 1712752000,
            "states": [
                [
                    "ABCDEF",
                    None,
                    "Canada",
                    None,
                    None,
                    -73.5673,
                    45.5017,
                    None,
                    False,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    False,
                    0,
                ]
            ],
        }
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value=payload)

        with patch(
            "app.services.adsb_service.httpx.AsyncClient",
            return_value=FakeAsyncClient(response=response),
        ):
            planes = await adsb_service.fetch_planes()

        self.assertEqual(
            planes,
            [
                {
                    "id": "abcdef",
                    "callsign": "",
                    "lat": 45.5017,
                    "lon": -73.5673,
                    "alt": 0,
                    "heading": 0.0,
                    "speed": 0.0,
                    "squawk": "",
                    "timestamp": datetime.fromtimestamp(1712752000, tz=timezone.utc).isoformat(),
                }
            ],
        )

    async def test_fetch_planes_skips_states_with_malformed_numeric_values(self):
        payload = {
            "time": 1712753555,
            "states": [
                [
                    "good01",
                    " GOOD01 ",
                    "France",
                    None,
                    "bad-last-contact",
                    2.3522,
                    48.8566,
                    "not-a-number",
                    False,
                    "also-bad",
                    "bad-heading",
                    None,
                    None,
                    None,
                    None,
                    False,
                    0,
                ],
                [
                    "skip02",
                    "SKIP",
                    "France",
                    None,
                    1712753000,
                    "bad-lon",
                    48.8566,
                    1000.0,
                    False,
                    100.0,
                    180.0,
                    None,
                    None,
                    None,
                    None,
                    False,
                    0,
                ],
            ],
        }
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value=payload)

        with patch(
            "app.services.adsb_service.httpx.AsyncClient",
            return_value=FakeAsyncClient(response=response),
        ):
            planes = await adsb_service.fetch_planes()

        self.assertEqual(len(planes), 1)
        self.assertEqual(planes[0]["id"], "good01")
        self.assertEqual(planes[0]["alt"], 0)
        self.assertEqual(planes[0]["speed"], 0.0)
        self.assertEqual(planes[0]["heading"], 0.0)
        self.assertEqual(
            planes[0]["timestamp"],
            datetime.fromtimestamp(1712753555, tz=timezone.utc).isoformat(),
        )

    async def test_fetch_planes_returns_empty_list_for_unexpected_top_level_json_shape(self):
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value=["not", "a", "dict"])

        with patch(
            "app.services.adsb_service.httpx.AsyncClient",
            return_value=FakeAsyncClient(response=response),
        ):
            planes = await adsb_service.fetch_planes()

        self.assertEqual(planes, [])

    async def test_fetch_planes_returns_empty_list_on_request_failure(self):
        request = httpx.Request("GET", adsb_service.OPENSKY_STATES_API)
        fake_client = FakeAsyncClient(exception=httpx.RequestError("boom", request=request))

        with patch("app.services.adsb_service.httpx.AsyncClient", return_value=fake_client):
            planes = await adsb_service.fetch_planes()

        self.assertEqual(planes, [])

    async def test_fetch_plane_details_filters_by_normalized_id(self):
        planes = [
            {
                "id": "abc123",
                "callsign": "TEST123",
                "lat": 10.0,
                "lon": 20.0,
                "alt": 1000,
                "heading": 90.0,
                "speed": 250.0,
                "squawk": "7000",
                "timestamp": "2026-04-10T18:00:00+00:00",
            }
        ]

        with patch("app.services.adsb_service.fetch_planes", AsyncMock(return_value=planes)):
            plane = await adsb_service.fetch_plane_details("ABC123")
            missing = await adsb_service.fetch_plane_details("missing")

        self.assertEqual(plane, planes[0])
        self.assertIsNone(missing)


if __name__ == "__main__":
    unittest.main()
