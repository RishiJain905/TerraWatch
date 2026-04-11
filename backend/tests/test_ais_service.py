import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import httpx

from app.services import ais_service


class FakeAsyncClient:
    def __init__(self, responses_by_url=None, exceptions_by_url=None):
        self.responses_by_url = responses_by_url or {}
        self.exceptions_by_url = exceptions_by_url or {}
        self.requested_urls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url):
        self.requested_urls.append(url)
        if url in self.exceptions_by_url:
            raise self.exceptions_by_url[url]
        return self.responses_by_url[url]


def make_response(payload):
    response = Mock()
    response.raise_for_status = Mock()
    response.json = Mock(return_value=payload)
    return response


class AISServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_ships_normalizes_and_merges_digitraffic_payloads(self):
        locations_payload = {
            "type": "FeatureCollection",
            "dataUpdatedTime": "2026-04-11T01:44:52Z",
            "features": [
                {
                    "mmsi": 219598000,
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [20.85169, 55.770832]},
                    "properties": {
                        "mmsi": 219598000,
                        "sog": 0.1,
                        "cog": 346.5,
                        "heading": 79,
                        "timestampExternal": 1659212938646,
                    },
                },
                {
                    "mmsi": 111111111,
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [20.0]},
                    "properties": {"sog": 10.0, "cog": 180.0},
                },
            ],
        }
        vessels_payload = [
            {
                "mmsi": 219598000,
                "name": "  NORD SUPERIOR  ",
                "destination": "  NL AMS ",
                "shipType": 80,
            },
            {
                "mmsi": 999999999,
                "name": "UNUSED",
                "destination": "NOWHERE",
                "shipType": 70,
            },
        ]

        fake_client = FakeAsyncClient(
            responses_by_url={
                ais_service.DIGITRAFFIC_LOCATIONS_API: make_response(locations_payload),
                ais_service.DIGITRAFFIC_VESSELS_API: make_response(vessels_payload),
            }
        )

        with patch("app.services.ais_service.httpx.AsyncClient", return_value=fake_client) as client_cls:
            ships = await ais_service.fetch_ships()

        client_cls.assert_called_once_with(
            timeout=ais_service.HTTP_TIMEOUT_SECONDS,
            headers=ais_service.HTTP_HEADERS,
        )
        self.assertEqual(
            fake_client.requested_urls,
            [ais_service.DIGITRAFFIC_LOCATIONS_API, ais_service.DIGITRAFFIC_VESSELS_API],
        )
        self.assertEqual(
            ships,
            [
                {
                    "id": "219598000",
                    "lat": 55.770832,
                    "lon": 20.85169,
                    "heading": 79.0,
                    "speed": 0.1,
                    "name": "NORD SUPERIOR",
                    "destination": "NL AMS",
                    "ship_type": "tanker",
                    "timestamp": datetime.fromtimestamp(1659212938646 / 1000, tz=timezone.utc).isoformat(),
                }
            ],
        )

    async def test_fetch_ships_falls_back_to_cog_and_safe_defaults(self):
        locations_payload = {
            "type": "FeatureCollection",
            "dataUpdatedTime": "2026-04-11T01:44:52Z",
            "features": [
                {
                    "mmsi": 230000001,
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [24.93545, 60.16952]},
                    "properties": {
                        "mmsi": 230000001,
                        "sog": "bad-speed",
                        "cog": 123.4,
                        "heading": None,
                        "timestampExternal": None,
                    },
                }
            ],
        }
        vessels_payload = [
            {
                "mmsi": 230000001,
                "name": None,
                "destination": "   ",
                "shipType": 31,
            }
        ]

        with patch(
            "app.services.ais_service.httpx.AsyncClient",
            return_value=FakeAsyncClient(
                responses_by_url={
                    ais_service.DIGITRAFFIC_LOCATIONS_API: make_response(locations_payload),
                    ais_service.DIGITRAFFIC_VESSELS_API: make_response(vessels_payload),
                }
            ),
        ):
            ships = await ais_service.fetch_ships()

        self.assertEqual(
            ships,
            [
                {
                    "id": "230000001",
                    "lat": 60.16952,
                    "lon": 24.93545,
                    "heading": 123.4,
                    "speed": 0.0,
                    "name": "",
                    "destination": "",
                    "ship_type": "other",
                    "timestamp": "2026-04-11T01:44:52Z",
                }
            ],
        )

    async def test_fetch_ships_returns_empty_list_on_request_failure(self):
        request = httpx.Request("GET", ais_service.DIGITRAFFIC_VESSELS_API)
        fake_client = FakeAsyncClient(
            responses_by_url={
                ais_service.DIGITRAFFIC_LOCATIONS_API: make_response(
                    {"type": "FeatureCollection", "features": []}
                )
            },
            exceptions_by_url={
                ais_service.DIGITRAFFIC_VESSELS_API: httpx.RequestError("boom", request=request)
            },
        )

        with patch("app.services.ais_service.httpx.AsyncClient", return_value=fake_client):
            ships = await ais_service.fetch_ships()

        self.assertEqual(ships, [])

    async def test_fetch_ships_returns_empty_list_for_unexpected_json_shapes(self):
        fake_client = FakeAsyncClient(
            responses_by_url={
                ais_service.DIGITRAFFIC_LOCATIONS_API: make_response(["not", "a", "dict"]),
                ais_service.DIGITRAFFIC_VESSELS_API: make_response({"not": "a-list"}),
            }
        )

        with patch("app.services.ais_service.httpx.AsyncClient", return_value=fake_client):
            ships = await ais_service.fetch_ships()

        self.assertEqual(ships, [])

    async def test_fetch_ship_details_filters_by_normalized_mmsi(self):
        ships = [
            {
                "id": "219598000",
                "lat": 55.770832,
                "lon": 20.85169,
                "heading": 79.0,
                "speed": 0.1,
                "name": "NORD SUPERIOR",
                "destination": "NL AMS",
                "ship_type": "tanker",
                "timestamp": "2022-07-30T22:48:58+00:00",
            }
        ]

        with patch("app.services.ais_service.fetch_ships", AsyncMock(return_value=ships)):
            ship = await ais_service.fetch_ship_details(" 219598000 ")
            missing = await ais_service.fetch_ship_details("missing")
            blank = await ais_service.fetch_ship_details("   ")

        self.assertEqual(ship, ships[0])
        self.assertIsNone(missing)
        self.assertIsNone(blank)


if __name__ == "__main__":
    unittest.main()
