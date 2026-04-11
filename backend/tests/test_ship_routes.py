import tempfile
import unittest
from pathlib import Path

import httpx

from app.core import database
from app.main import app


class ShipRouteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_database_path = database.DATABASE_PATH
        await database.close_db()
        database.DATABASE_PATH = str(Path(self.temp_dir.name) / "ship-routes.db")
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

    async def test_get_ships_returns_all_active_ships(self):
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
                "timestamp": "2026-04-11T01:00:00+00:00",
            },
            {
                "id": "230000001",
                "lat": 60.16952,
                "lon": 24.93545,
                "heading": 123.4,
                "speed": 0.0,
                "name": "BALTIC STAR",
                "destination": "EE TLL",
                "ship_type": "passenger",
                "timestamp": "2026-04-11T01:01:00+00:00",
            },
        ]
        await database.upsert_ships(self.db, ships)

        response = await self._get("/api/ships")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 2)
        self.assertEqual({ship["id"] for ship in payload}, {"219598000", "230000001"})

    async def test_get_ship_count_returns_total_active_ships(self):
        await database.upsert_ships(
            self.db,
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
                    "timestamp": "2026-04-11T01:00:00+00:00",
                },
                {
                    "id": "230000001",
                    "lat": 60.16952,
                    "lon": 24.93545,
                    "heading": 123.4,
                    "speed": 0.0,
                    "name": "BALTIC STAR",
                    "destination": "EE TLL",
                    "ship_type": "passenger",
                    "timestamp": "2026-04-11T01:01:00+00:00",
                },
            ],
        )

        response = await self._get("/api/ships/count")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"count": 2})

    async def test_get_ship_returns_matching_ship_by_mmsi(self):
        ship = {
            "id": "219598000",
            "lat": 55.770832,
            "lon": 20.85169,
            "heading": 79.0,
            "speed": 0.1,
            "name": "NORD SUPERIOR",
            "destination": "NL AMS",
            "ship_type": "tanker",
            "timestamp": "2026-04-11T01:00:00+00:00",
        }
        await database.upsert_ship(self.db, ship)

        response = await self._get("/api/ships/219598000")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ship)

    async def test_get_ship_strips_surrounding_whitespace_in_path_param(self):
        ship = {
            "id": "219598000",
            "lat": 55.770832,
            "lon": 20.85169,
            "heading": 79.0,
            "speed": 0.1,
            "name": "NORD SUPERIOR",
            "destination": "NL AMS",
            "ship_type": "tanker",
            "timestamp": "2026-04-11T01:00:00+00:00",
        }
        await database.upsert_ship(self.db, ship)

        response = await self._get("/api/ships/%20219598000%20")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ship)

    async def test_get_ship_returns_null_when_ship_is_missing(self):
        response = await self._get("/api/ships/999999999")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json())
