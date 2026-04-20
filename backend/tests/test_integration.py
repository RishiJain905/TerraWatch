"""
Phase 2 integration tests — verify the full TerraWatch pipeline end-to-end.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import httpx

from app.core import database
from app.main import app
from app.services import adsb_service


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


class TestStaleThresholdsEndpoint(IntegrationTestBase):
    async def test_stale_thresholds_returns_expected_keys_and_defaults(self):
        response = await self._get("/api/stale-thresholds")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("planes", body)
        self.assertIn("ships", body)
        self.assertIn("events", body)
        self.assertIn("conflicts", body)
        self.assertIsInstance(body["planes"], int)
        self.assertIsInstance(body["ships"], int)
        self.assertIsInstance(body["events"], int)
        self.assertIsInstance(body["conflicts"], int)


class TestPlaneEndpoints(IntegrationTestBase):
    async def test_get_planes_returns_list(self):
        response = await self._get("/api/planes")

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    async def test_get_plane_count_returns_integer(self):
        response = await self._get("/api/planes/count")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("count", body)
        self.assertIsInstance(body["count"], int)

    async def test_get_plane_by_id_returns_plane_or_null(self):
        response = await self._get("/api/planes/abc123")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        # The plane may be None (null JSON) or a dict with the expected keys.
        if body is not None:
            self.assertIsInstance(body, dict)
            for key in ("id", "lat", "lon", "alt", "heading", "speed", "callsign", "squawk", "timestamp"):
                self.assertIn(key, body)


# ---------------------------------------------------------------------------
# WebSocket heartbeat test
# ---------------------------------------------------------------------------


class TestWebSocketHeartbeat(unittest.IsolatedAsyncioTestCase):
    async def test_websocket_accepts_connection_and_sends_heartbeat(self):
        """
        Connect to /ws via starlette TestClient and verify a heartbeat
        message arrives within 15 seconds.
        """
        from starlette.testclient import TestClient

        with patch("app.main.start_schedulers", AsyncMock()), patch(
            "app.main.stop_schedulers", AsyncMock()
        ):
            with TestClient(app) as client:
                with client.websocket_connect("/ws") as ws:
                    # The WS endpoint sends an initial heartbeat with
                    # status="connected", then periodic heartbeats every 10s.
                    # The initial heartbeat is sent immediately upon connect.
                    message = ws.receive_json()

        self.assertEqual(message.get("type"), "heartbeat")
        self.assertIn("timestamp", message)

    async def asyncTearDown(self):
        from app.api import websocket

        websocket.connected_clients.clear()


# ---------------------------------------------------------------------------
# ADS-B service test with mocked OpenSky data
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


class TestADSBServiceIntegration(unittest.IsolatedAsyncioTestCase):
    async def test_adsb_service_fetch_planes_returns_dicts(self):
        """
        Mock the OpenSky API and verify fetch_planes() returns a list of
        dicts with the expected plane contract keys.
        """
        payload = {
            "time": 1712751234,
            "states": [
                [
                    "abc123",
                    " FLIGHT1 ",
                    "United States",
                    1712751228,
                    1712751230,
                    -73.5673,
                    45.5017,
                    1000.0,
                    False,
                    150.0,
                    270.5,
                    0.0,
                    None,
                    1100.0,
                    "4567",
                    False,
                    0,
                ],
            ],
        }

        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value=payload)
        fake_client = FakeAsyncClient(response=response)

        with patch(
            "app.services.adsb_service.httpx.AsyncClient", return_value=fake_client
        ):
            planes = await adsb_service.fetch_planes()

        self.assertIsInstance(planes, list)
        self.assertGreater(len(planes), 0)

        plane = planes[0]
        expected_keys = {"id", "lat", "lon", "alt", "heading", "speed", "callsign", "squawk", "timestamp"}
        self.assertTrue(expected_keys.issubset(plane.keys()), f"Missing keys: {expected_keys - plane.keys()}")

        self.assertEqual(plane["id"], "abc123")
        self.assertIsInstance(plane["lat"], float)
        self.assertIsInstance(plane["lon"], float)
        self.assertIsInstance(plane["alt"], int)
        self.assertIsInstance(plane["heading"], float)
        self.assertIsInstance(plane["speed"], float)
        self.assertIsInstance(plane["callsign"], str)
        self.assertIsInstance(plane["squawk"], str)
        self.assertIsInstance(plane["timestamp"], str)


if __name__ == "__main__":
    unittest.main()
