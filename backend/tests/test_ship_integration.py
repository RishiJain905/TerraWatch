"""
Phase 3 integration tests — verify the TerraWatch ship pipeline end-to-end.

Tests the full flow: Digitraffic AIS API → ais_service → SQLite →
WebSocket broadcast → REST endpoints.

Mirror of the Phase 2 plane integration test (test_integration.py).
"""

import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import httpx

from app.core import database
from app.main import app
from app.services import ais_service


class IntegrationTestBase(unittest.IsolatedAsyncioTestCase):
    """Base class that isolates the database per test."""

    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_database_path = database.DATABASE_PATH
        await database.close_db()
        database.DATABASE_PATH = str(Path(self.temp_dir.name) / "integration.db")
        await database.init_db()

    async def asyncTearDown(self):
        await database.close_db()
        database.DATABASE_PATH = self.original_database_path
        self.temp_dir.cleanup()

    async def _get(self, path: str) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.get(path)


# ---------------------------------------------------------------------------
# HTTP endpoint tests
# ---------------------------------------------------------------------------


class TestHealthEndpoint(IntegrationTestBase):
    async def test_health_endpoint_returns_healthy(self):
        response = await self._get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})


class TestRootEndpoint(IntegrationTestBase):
    async def test_root_endpoint_returns_api_info(self):
        response = await self._get("/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["name"], "TerraWatch API")
        self.assertEqual(body["version"], "0.1.0")
        self.assertEqual(body["status"], "running")


class TestShipEndpoints(IntegrationTestBase):
    async def test_ship_api_health(self):
        """GET /api/ships returns 200 and a list."""
        response = await self._get("/api/ships")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    async def test_ship_count_endpoint(self):
        """GET /api/ships/count returns {"count": N}."""
        response = await self._get("/api/ships/count")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("count", body)
        self.assertIsInstance(body["count"], int)

    async def test_ship_detail_endpoint_found(self):
        """GET /api/ships/{mmsi} returns a ship dict when found."""
        from app.core.database import open_db_connection

        async with open_db_connection() as db:
            await database.upsert_ship(db, {
                "id": "219598000",
                "lat": 55.770832,
                "lon": 20.85169,
                "heading": 79.0,
                "speed": 0.1,
                "name": "NORD SUPERIOR",
                "destination": "NL AMS",
                "ship_type": "tanker",
                "timestamp": "2022-07-30T20:28:58.646000+00:00",
            })

        response = await self._get("/api/ships/219598000")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsInstance(body, dict)
        self.assertEqual(body["id"], "219598000")
        self.assertEqual(body["name"], "NORD SUPERIOR")

    async def test_ship_detail_endpoint_not_found(self):
        """GET /api/ships/{mmsi} returns None (null) when not found."""
        response = await self._get("/api/ships/999999999")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json())


# ---------------------------------------------------------------------------
# WebSocket heartbeat + ship broadcast test
# ---------------------------------------------------------------------------


class TestWebSocketShipBroadcast(unittest.IsolatedAsyncioTestCase):
    async def test_websocket_accepts_connection_and_receives_heartbeat(self):
        """
        Connect to /ws and verify the initial heartbeat arrives immediately.
        """
        from starlette.testclient import TestClient

        with patch("app.main.start_schedulers", AsyncMock()), patch(
            "app.main.stop_schedulers", AsyncMock()
        ):
            with TestClient(app) as client:
                with client.websocket_connect("/ws") as ws:
                    message = ws.receive_json()

        self.assertEqual(message.get("type"), "heartbeat")
        self.assertIn("timestamp", message)

    async def asyncTearDown(self):
        from app.api import websocket
        websocket.connected_clients.clear()


# ---------------------------------------------------------------------------
# AIS service test with mocked Digitraffic data
# ---------------------------------------------------------------------------


class FakeAsyncClient:
    """Minimal async context-manager that behaves like httpx.AsyncClient."""

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


class TestAISServiceIntegration(unittest.IsolatedAsyncioTestCase):
    async def test_ais_service_fetch_ships_returns_dicts(self):
        """
        Mock the Digitraffic API and verify fetch_ships() returns a list of
        dicts with the expected ship contract keys.
        """
        locations_payload = {
            "type": "FeatureCollection",
            "dataUpdatedTime": "2022-07-30T20:28:58Z",
            "features": [
                {
                    "mmsi": 219598000,
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [20.85169, 55.770832]},
                    "properties": {
                        "mmsi": 219598000,
                        "sog": 0.1,
                        "cog": 79.0,
                        "heading": 79,
                        "navStat": 1,
                        "timestamp": 59,
                        "timestampExternal": 1659212938646,
                    },
                },
            ],
        }

        vessels_payload = [
            {
                "mmsi": 219598000,
                "name": "NORD SUPERIOR",
                "callSign": "OWPA2",
                "imo": 9692129,
                "destination": "NL AMS",
                "draught": 118,
                "eta": 416128,
                "shipType": 80,
                "posType": 1,
            },
        ]

        locations_response = Mock()
        locations_response.raise_for_status = Mock()
        locations_response.json = Mock(return_value=locations_payload)

        vessels_response = Mock()
        vessels_response.raise_for_status = Mock()
        vessels_response.json = Mock(return_value=vessels_payload)

        class CountingFakeClient(FakeAsyncClient):
            async def get(self, url):
                if "locations" in url:
                    return locations_response
                elif "vessels" in url:
                    return vessels_response
                return Mock()

        fake_client = CountingFakeClient()

        with patch(
            "app.services.ais_service.httpx.AsyncClient", return_value=fake_client
        ):
            ships = await ais_service.fetch_ships()

        self.assertIsInstance(ships, list)
        self.assertGreater(len(ships), 0)

        ship = ships[0]
        expected_keys = {
            "id", "lat", "lon", "heading", "speed", "name",
            "destination", "ship_type", "timestamp",
        }
        self.assertTrue(
            expected_keys.issubset(ship.keys()),
            f"Missing keys: {expected_keys - ship.keys()}",
        )

        self.assertEqual(ship["id"], "219598000")
        self.assertIsInstance(ship["lat"], float)
        self.assertIsInstance(ship["lon"], float)
        self.assertIsInstance(ship["heading"], float)
        self.assertIsInstance(ship["speed"], float)
        self.assertIsInstance(ship["name"], str)
        self.assertIsInstance(ship["destination"], str)
        self.assertIsInstance(ship["ship_type"], str)
        self.assertIsInstance(ship["timestamp"], str)

    async def test_ais_service_fetch_ships_empty_on_error(self):
        """
        Verify fetch_ships() returns [] when the HTTP request fails.
        """
        import httpx
        fake_client = FakeAsyncClient(exception=httpx.HTTPError("Network error"))

        with patch(
            "app.services.ais_service.httpx.AsyncClient", return_value=fake_client
        ):
            ships = await ais_service.fetch_ships()

        self.assertIsInstance(ships, list)
        self.assertEqual(len(ships), 0)


# ---------------------------------------------------------------------------
# Ship schema validation test
# ---------------------------------------------------------------------------


class TestShipSchema(IntegrationTestBase):
    async def test_ship_schema_required_fields(self):
        """
        Insert a ship directly and verify it has all required fields via the REST API.
        """
        from app.core.database import open_db_connection

        async with open_db_connection() as db:
            await database.upsert_ship(db, {
                "id": "123456789",
                "lat": 34.5,
                "lon": -122.3,
                "heading": 180.0,
                "speed": 12.5,
                "name": "TEST SHIP",
                "destination": "PORT TEST",
                "ship_type": "cargo",
                "timestamp": "2026-04-11T12:00:00Z",
            }, commit=False)
            await db.commit()

        response = await self._get("/api/ships/123456789")
        self.assertEqual(response.status_code, 200)
        ship = response.json()
        self.assertIsInstance(ship, dict)

        required = {"id", "lat", "lon", "name", "ship_type"}
        self.assertTrue(
            required.issubset(ship.keys()),
            f"Missing required fields: {required - ship.keys()}",
        )


if __name__ == "__main__":
    unittest.main()
