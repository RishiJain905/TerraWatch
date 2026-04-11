import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import httpx

from app.services import ais_friends_service


class FakeAsyncClient:
    def __init__(self, planned_results=None):
        self.planned_results = list(planned_results or [])
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None):
        self.calls.append({"url": url, "params": params})
        if not self.planned_results:
            raise AssertionError("No planned result available for FakeAsyncClient.get")

        result = self.planned_results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def make_response(payload, status_code=200):
    response = Mock()
    response.status_code = status_code
    response.raise_for_status = Mock()
    response.json = Mock(return_value=payload)
    return response


class AisFriendsServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_ships_parses_valid_ais_friends_response(self):
        payload = {
            "data": [
                {
                    "mmsi": 123456789,
                    "name": "  OCEAN SPIRIT  ",
                    "ship_type": "Cargo",
                    "lat": 37.7749,
                    "lon": -122.4194,
                    "speed_over_ground": 12.5,
                    "course_over_ground": 85.0,
                    "true_heading": 90.0,
                    "destination": "  OAKLAND ",
                    "timestamp": 1712751234,
                },
                {
                    "mmsi": 987654321,
                    "name": "SKIPME",
                    "lat": None,
                    "lon": -10.0,
                },
                "bad-row",
            ]
        }
        fake_client = FakeAsyncClient(planned_results=[make_response(payload)])
        service = ais_friends_service.AisFriendsService(api_key="test-token")

        with patch("app.services.ais_friends_service.httpx.AsyncClient", return_value=fake_client) as client_cls:
            ships = await service.fetch_ships()

        client_cls.assert_called_once_with(
            timeout=ais_friends_service.HTTP_TIMEOUT_SECONDS,
            headers={
                **ais_friends_service.HTTP_HEADERS,
                "Authorization": "Bearer test-token",
            },
        )
        self.assertEqual(
            fake_client.calls,
            [
                {
                    "url": ais_friends_service.AIS_FRIENDS_BBOX_API,
                    "params": ais_friends_service.DEFAULT_BBOX,
                }
            ],
        )
        self.assertEqual(
            ships,
            [
                {
                    "id": "123456789",
                    "lat": 37.7749,
                    "lon": -122.4194,
                    "heading": 90.0,
                    "speed": 12.5,
                    "name": "OCEAN SPIRIT",
                    "destination": "OAKLAND",
                    "ship_type": "cargo",
                    "timestamp": datetime.fromtimestamp(1712751234, tz=timezone.utc).isoformat(),
                }
            ],
        )

    async def test_fetch_ships_handles_fallback_field_variants(self):
        payload = {
            "data": [
                {
                    "mmsi": "230000001",
                    "reported_name": "  FRIEND SHIP  ",
                    "type": None,
                    "detailed_type": "Passenger Ferry",
                    "latitude": "60.1699",
                    "longitude": "24.9384",
                    "speed_over_ground": "8.2",
                    "course_over_ground": "182.5",
                    "true_heading": None,
                    "ais_destination": "  HELSINKI ",
                    "timestamp": "2026-04-11T01:44:52Z",
                }
            ]
        }
        service = ais_friends_service.AisFriendsService(api_key="test-token")
        fake_client = FakeAsyncClient(planned_results=[make_response(payload)])

        with patch(
            "app.services.ais_friends_service.httpx.AsyncClient",
            return_value=fake_client,
        ):
            ships = await service.fetch_ships({"lat_min": 0.0, "lat_max": 10.0, "lon_min": 0.0, "lon_max": 20.0})

        self.assertEqual(
            fake_client.calls[0]["params"],
            {"lat_min": 0.0, "lat_max": 10.0, "lon_min": 0.0, "lon_max": 20.0},
        )
        self.assertEqual(
            ships,
            [
                {
                    "id": "230000001",
                    "lat": 60.1699,
                    "lon": 24.9384,
                    "heading": 182.5,
                    "speed": 8.2,
                    "name": "FRIEND SHIP",
                    "destination": "HELSINKI",
                    "ship_type": "passenger",
                    "timestamp": "2026-04-11T01:44:52+00:00",
                }
            ],
        )

    async def test_fetch_ships_returns_empty_list_for_empty_data(self):
        service = ais_friends_service.AisFriendsService(api_key="test-token")

        with patch(
            "app.services.ais_friends_service.httpx.AsyncClient",
            return_value=FakeAsyncClient(planned_results=[make_response({"data": []})]),
        ):
            ships = await service.fetch_ships()

        self.assertEqual(ships, [])

    async def test_fetch_ships_returns_empty_list_on_timeout(self):
        request = httpx.Request("GET", ais_friends_service.AIS_FRIENDS_BBOX_API)
        service = ais_friends_service.AisFriendsService(api_key="test-token")
        fake_client = FakeAsyncClient(planned_results=[httpx.ReadTimeout("timeout", request=request)])

        with patch("app.services.ais_friends_service.httpx.AsyncClient", return_value=fake_client):
            ships = await service.fetch_ships()

        self.assertEqual(ships, [])

    async def test_fetch_ships_retries_once_after_rate_limit_and_succeeds(self):
        payload = {
            "data": [
                {
                    "mmsi": 111222333,
                    "name": "RETRY SUCCESS",
                    "ship_type": "Tanker",
                    "lat": 1.0,
                    "lon": 2.0,
                    "speed_over_ground": 3.0,
                    "course_over_ground": 4.0,
                    "true_heading": 5.0,
                    "destination": "PORT",
                    "timestamp": 1712755555,
                }
            ]
        }
        fake_client = FakeAsyncClient(
            planned_results=[
                make_response({"error": "rate limited"}, status_code=429),
                make_response(payload),
            ]
        )
        service = ais_friends_service.AisFriendsService(api_key="test-token")

        with patch("app.services.ais_friends_service.httpx.AsyncClient", return_value=fake_client), patch(
            "app.services.ais_friends_service.asyncio.sleep",
            AsyncMock(),
        ) as sleep_mock:
            ships = await service.fetch_ships()

        sleep_mock.assert_awaited_once_with(ais_friends_service.RATE_LIMIT_RETRY_DELAY_SECONDS)
        self.assertEqual(len(fake_client.calls), 2)
        self.assertEqual(ships[0]["id"], "111222333")

    async def test_fetch_ships_returns_empty_list_when_rate_limit_persists(self):
        fake_client = FakeAsyncClient(
            planned_results=[
                make_response({"error": "rate limited"}, status_code=429),
                make_response({"error": "still rate limited"}, status_code=429),
            ]
        )
        service = ais_friends_service.AisFriendsService(api_key="test-token")

        with patch("app.services.ais_friends_service.httpx.AsyncClient", return_value=fake_client), patch(
            "app.services.ais_friends_service.asyncio.sleep",
            AsyncMock(),
        ) as sleep_mock:
            ships = await service.fetch_ships()

        sleep_mock.assert_awaited_once_with(ais_friends_service.RATE_LIMIT_RETRY_DELAY_SECONDS)
        self.assertEqual(len(fake_client.calls), 2)
        self.assertEqual(ships, [])

    async def test_fetch_ships_passes_bearer_authorization_header(self):
        fake_client = FakeAsyncClient(planned_results=[make_response({"data": []})])
        service = ais_friends_service.AisFriendsService(api_key="secret-token")

        with patch("app.services.ais_friends_service.httpx.AsyncClient", return_value=fake_client) as client_cls:
            await service.fetch_ships()

        self.assertEqual(
            client_cls.call_args.kwargs["headers"]["Authorization"],
            "Bearer secret-token",
        )

    async def test_fetch_ships_returns_empty_list_when_api_key_missing(self):
        service = ais_friends_service.AisFriendsService(api_key="   ")

        with patch("app.services.ais_friends_service.httpx.AsyncClient") as client_cls:
            ships = await service.fetch_ships()

        client_cls.assert_not_called()
        self.assertEqual(ships, [])

    async def test_fetch_ships_returns_empty_list_for_invalid_json(self):
        response = Mock()
        response.status_code = 200
        response.raise_for_status = Mock()
        response.json = Mock(side_effect=ValueError("bad json"))
        service = ais_friends_service.AisFriendsService(api_key="test-token")

        with patch(
            "app.services.ais_friends_service.httpx.AsyncClient",
            return_value=FakeAsyncClient(planned_results=[response]),
        ):
            ships = await service.fetch_ships()

        self.assertEqual(ships, [])

    async def test_fetch_ships_returns_empty_list_when_data_missing_or_invalid(self):
        service = ais_friends_service.AisFriendsService(api_key="test-token")

        with patch(
            "app.services.ais_friends_service.httpx.AsyncClient",
            return_value=FakeAsyncClient(planned_results=[make_response({"data": "not-a-list"})]),
        ):
            ships = await service.fetch_ships()

        self.assertEqual(ships, [])


if __name__ == "__main__":
    unittest.main()
