import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx

from app.core import database
from app.core.models import PlaneRoute
from app.main import app


class PlaneRouteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_database_path = database.DATABASE_PATH
        await database.close_db()
        database.DATABASE_PATH = str(Path(self.temp_dir.name) / "plane-routes.db")
        await database.init_db()
        self.db = await database.get_db()

    async def asyncTearDown(self):
        await database.close_db()
        database.DATABASE_PATH = self.original_database_path
        self.temp_dir.cleanup()

    async def _get(self, path: str) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.get(path)

    async def test_get_plane_count_returns_total_active_planes(self):
        await database.upsert_planes(
            self.db,
            [
                {
                    "id": "abc123",
                    "lat": 10.0,
                    "lon": 20.0,
                    "alt": 1000,
                    "heading": 90.0,
                    "callsign": "TEST123",
                    "squawk": "7000",
                    "speed": 250.0,
                    "timestamp": "2026-04-10T21:00:00+00:00",
                },
                {
                    "id": "def456",
                    "lat": 11.0,
                    "lon": 21.0,
                    "alt": 2000,
                    "heading": 180.0,
                    "callsign": "TEST456",
                    "squawk": "7700",
                    "speed": 350.0,
                    "timestamp": "2026-04-10T21:00:30+00:00",
                },
            ],
        )

        response = await self._get("/api/planes/count")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"count": 2})

    async def test_get_plane_returns_matching_plane_by_case_insensitive_icao24_path_param(self):
        plane = {
            "id": "abc123",
            "lat": 10.0,
            "lon": 20.0,
            "alt": 1000,
            "heading": 90.0,
            "callsign": "TEST123",
            "squawk": "7000",
            "speed": 250.0,
            "timestamp": "2026-04-10T21:00:00+00:00",
        }
        await database.upsert_plane(self.db, plane)

        response = await self._get("/api/planes/ABC123")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), plane)

    async def test_get_plane_returns_null_when_plane_is_missing(self):
        response = await self._get("/api/planes/missing01")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json())

    async def test_get_plane_route_returns_404_when_plane_is_missing(self):
        response = await self._get("/api/planes/missing01/route")

        self.assertEqual(response.status_code, 404)

    async def test_get_plane_route_returns_error_payload_when_access_key_missing(self):
        plane = {
            "id": "abc123",
            "lat": 10.0,
            "lon": 20.0,
            "alt": 1000,
            "heading": 90.0,
            "callsign": "TEST123",
            "squawk": "7000",
            "speed": 250.0,
            "timestamp": "2026-04-10T21:00:00+00:00",
        }
        await database.upsert_plane(self.db, plane)

        with patch("app.config.settings.AVIATIONSTACK_ACCESS_KEY", ""):
            response = await self._get("/api/planes/abc123/route")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["plane_id"], "abc123")
        self.assertEqual(payload["provider"], "aviationstack")
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["resolved_by"], "none")

    async def test_get_plane_route_returns_service_payload_for_matching_plane(self):
        plane = {
            "id": "abc123",
            "lat": 10.0,
            "lon": 20.0,
            "alt": 1000,
            "heading": 90.0,
            "callsign": "TEST123",
            "squawk": "7000",
            "speed": 250.0,
            "timestamp": "2026-04-10T21:00:00+00:00",
        }
        await database.upsert_plane(self.db, plane)

        route = PlaneRoute(
            plane_id="abc123",
            resolved_by="icao24",
            status="ok",
            provider="aviationstack",
            flight_iata="AA1004",
            flight_icao="AAL1004",
            airline_name="American Airlines",
            airline_iata="AA",
            airline_icao="AAL",
            last_updated="2026-04-10T21:10:00+00:00",
        )

        with patch(
            "app.api.routes.planes.AviationstackService.get_plane_route",
            AsyncMock(return_value=route),
        ) as route_mock:
            response = await self._get("/api/planes/abc123/route")

        route_mock.assert_awaited_once()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), route.model_dump())
