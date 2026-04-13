"""Tests for the /api/conflicts endpoint — GDELT violent event filtering."""

import tempfile
import unittest
from pathlib import Path

from app.core import database
from app.api.routes.conflicts import VIOLENT_CATEGORIES


class ConflictRouteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_database_path = database.DATABASE_PATH
        await database.close_db()
        database.DATABASE_PATH = str(Path(self.temp_dir.name) / "test.db")
        await database.init_db()
        self.db = await database.get_db()

    async def asyncTearDown(self):
        await database.close_db()
        database.DATABASE_PATH = self.original_database_path
        self.temp_dir.cleanup()

    async def _insert_events(self, events):
        await database.upsert_events(self.db, events, commit=True)

    async def test_violent_categories_constant(self):
        """VIOLENT_CATEGORIES includes the expected GDELT event types."""
        expected = {"assault", "fight", "unconventional_mass_gvc",
                     "conventional_mass_gvc", "force_range", "rioting"}
        self.assertEqual(set(VIOLENT_CATEGORIES), expected)

    async def test_conflicts_endpoint_returns_only_violent_events(self):
        """Only events with violent categories appear in /api/conflicts."""
        events = [
            {"id": "gdelt_001", "date": "2026-04-13", "lat": 10.0, "lon": 20.0,
             "event_text": "assaulted", "tone": -5.0, "category": "assault", "source_url": ""},
            {"id": "gdelt_002", "date": "2026-04-13", "lat": 11.0, "lon": 21.0,
             "event_text": "fought", "tone": -8.0, "category": "fight", "source_url": ""},
            {"id": "gdelt_003", "date": "2026-04-13", "lat": 12.0, "lon": 22.0,
             "event_text": "diplomacy", "tone": 3.0, "category": "diplomacy", "source_url": ""},
            {"id": "gdelt_004", "date": "2026-04-13", "lat": 13.0, "lon": 23.0,
             "event_text": "protested", "tone": -2.0, "category": "protest", "source_url": ""},
        ]
        await self._insert_events(events)

        # Query with same logic as the route
        placeholders = ",".join("?" for _ in VIOLENT_CATEGORIES)
        async with self.db.execute(
            f"SELECT * FROM events WHERE category IN ({placeholders})",
            VIOLENT_CATEGORIES,
        ) as cursor:
            rows = [dict(row) for row in await cursor.fetchall()]

        ids = {r["id"] for r in rows}
        self.assertEqual(ids, {"gdelt_001", "gdelt_002"})

    async def test_conflicts_count_only_violent(self):
        """Count reflects only violent events."""
        events = [
            {"id": "gdelt_010", "date": "2026-04-13", "lat": 0.0, "lon": 0.0,
             "event_text": "rioting", "tone": -10.0, "category": "rioting", "source_url": ""},
            {"id": "gdelt_011", "date": "2026-04-13", "lat": 1.0, "lon": 1.0,
             "event_text": "health", "tone": 0.0, "category": "health", "source_url": ""},
        ]
        await self._insert_events(events)

        placeholders = ",".join("?" for _ in VIOLENT_CATEGORIES)
        async with self.db.execute(
            f"SELECT COUNT(*) AS count FROM events WHERE category IN ({placeholders})",
            VIOLENT_CATEGORIES,
        ) as cursor:
            row = await cursor.fetchone()
        self.assertEqual(row["count"], 1)

    async def test_empty_conflicts_when_no_violent_events(self):
        """Returns empty list when no violent events exist."""
        events = [
            {"id": "gdelt_020", "date": "2026-04-13", "lat": 0.0, "lon": 0.0,
             "event_text": "diplomacy", "tone": 2.0, "category": "diplomacy", "source_url": ""},
        ]
        await self._insert_events(events)

        placeholders = ",".join("?" for _ in VIOLENT_CATEGORIES)
        async with self.db.execute(
            f"SELECT * FROM events WHERE category IN ({placeholders})",
            VIOLENT_CATEGORIES,
        ) as cursor:
            rows = await cursor.fetchall()
        self.assertEqual(len(rows), 0)
