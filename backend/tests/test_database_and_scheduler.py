import asyncio
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import ANY, AsyncMock, patch

import aiosqlite

from app.core import database, dedup as dedup_core
from app.tasks import schedulers


class DatabaseHelperTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_database_path = database.DATABASE_PATH
        await database.close_db()
        database.DATABASE_PATH = str(Path(self.temp_dir.name) / "test.db")
        await database.init_db()

    async def asyncTearDown(self):
        await database.close_db()
        database.DATABASE_PATH = self.original_database_path
        self.temp_dir.cleanup()

    async def test_upsert_helpers_insert_and_update_plane_rows(self):
        db = await database.get_db()
        original_plane = {
            "id": "abc123",
            "lat": 10.25,
            "lon": 20.5,
            "alt": 32000,
            "heading": 90.0,
            "callsign": "TEST123",
            "squawk": "7000",
            "speed": 450.5,
            "timestamp": "2026-04-10T20:00:00+00:00",
        }
        updated_plane = {
            **original_plane,
            "lat": 11.5,
            "heading": 95.0,
            "timestamp": "2026-04-10T20:00:30+00:00",
        }
        second_plane = {
            "id": "def456",
            "lat": 1.0,
            "lon": 2.0,
            "alt": 500,
            "heading": 180.0,
            "callsign": "SECOND",
            "squawk": "1234",
            "speed": 120.0,
            "timestamp": "2026-04-10T20:01:00+00:00",
        }

        await database.upsert_plane(db, original_plane, commit=False)
        await database.upsert_planes(db, [updated_plane, second_plane])

        async with db.execute("SELECT * FROM planes ORDER BY id") as cursor:
            rows = [dict(row) for row in await cursor.fetchall()]

        self.assertEqual(
            rows,
            [
                {
                    "id": "abc123",
                    "lat": 11.5,
                    "lon": 20.5,
                    "alt": 32000,
                    "heading": 95.0,
                    "callsign": "TEST123",
                    "squawk": "7000",
                    "speed": 450.5,
                    "timestamp": "2026-04-10T20:00:30+00:00",
                },
                {
                    "id": "def456",
                    "lat": 1.0,
                    "lon": 2.0,
                    "alt": 500,
                    "heading": 180.0,
                    "callsign": "SECOND",
                    "squawk": "1234",
                    "speed": 120.0,
                    "timestamp": "2026-04-10T20:01:00+00:00",
                },
            ],
        )

    async def test_upsert_ship_helpers_insert_and_update_ship_rows(self):
        db = await database.get_db()
        original_ship = {
            "id": "219598000",
            "lat": 55.770832,
            "lon": 20.85169,
            "heading": 79.0,
            "speed": 0.1,
            "name": "NORD SUPERIOR",
            "destination": "NL AMS",
            "ship_type": "tanker",
            "timestamp": "2026-04-11T01:44:52+00:00",
        }
        updated_ship = {
            **original_ship,
            "speed": 1.2,
            "destination": "FI HEL",
            "timestamp": "2026-04-11T01:45:52+00:00",
        }
        second_ship = {
            "id": "230000001",
            "lat": 60.16952,
            "lon": 24.93545,
            "heading": 123.4,
            "speed": 0.0,
            "name": "BALTIC STAR",
            "destination": "EE TLL",
            "ship_type": "passenger",
            "timestamp": "2026-04-11T01:46:00+00:00",
        }

        await database.upsert_ship(db, original_ship, commit=False)
        await database.upsert_ships(db, [updated_ship, second_ship])

        async with db.execute("SELECT * FROM ships ORDER BY id") as cursor:
            rows = [dict(row) for row in await cursor.fetchall()]

        self.assertEqual(
            rows,
            [
                {
                    "id": "219598000",
                    "lat": 55.770832,
                    "lon": 20.85169,
                    "heading": 79.0,
                    "speed": 1.2,
                    "name": "NORD SUPERIOR",
                    "destination": "FI HEL",
                    "ship_type": "tanker",
                    "timestamp": "2026-04-11T01:45:52+00:00",
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
                    "timestamp": "2026-04-11T01:46:00+00:00",
                },
            ],
        )

    async def test_delete_old_planes_removes_rows_older_than_max_age(self):
        db = await database.get_db()
        fresh_timestamp = datetime.now(timezone.utc).isoformat()
        stale_timestamp = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()

        await database.upsert_planes(
            db,
            [
                {
                    "id": "fresh-plane",
                    "lat": 42.0,
                    "lon": -71.0,
                    "alt": 1000,
                    "heading": 45.0,
                    "callsign": "FRESH",
                    "squawk": "1111",
                    "speed": 200.0,
                    "timestamp": fresh_timestamp,
                },
                {
                    "id": "stale-plane",
                    "lat": 43.0,
                    "lon": -72.0,
                    "alt": 2000,
                    "heading": 90.0,
                    "callsign": "STALE",
                    "squawk": "2222",
                    "speed": 210.0,
                    "timestamp": stale_timestamp,
                },
            ],
            commit=False,
        )
        deleted_ids = await database.delete_old_planes(db, max_age_minutes=5)

        async with db.execute("SELECT id FROM planes ORDER BY id") as cursor:
            remaining_ids = [row[0] for row in await cursor.fetchall()]

        self.assertEqual(deleted_ids, ["stale-plane"])
        self.assertEqual(remaining_ids, ["fresh-plane"])

    async def test_delete_old_ships_removes_rows_older_than_max_age(self):
        db = await database.get_db()
        fresh_timestamp = datetime.now(timezone.utc).isoformat()
        stale_timestamp = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()

        await database.upsert_ships(
            db,
            [
                {
                    "id": "fresh-ship",
                    "lat": 60.0,
                    "lon": 24.0,
                    "heading": 180.0,
                    "speed": 12.5,
                    "name": "FRESH VESSEL",
                    "destination": "FI TKU",
                    "ship_type": "cargo",
                    "timestamp": fresh_timestamp,
                },
                {
                    "id": "stale-ship",
                    "lat": 61.0,
                    "lon": 25.0,
                    "heading": 90.0,
                    "speed": 4.5,
                    "name": "STALE VESSEL",
                    "destination": "SE STO",
                    "ship_type": "other",
                    "timestamp": stale_timestamp,
                },
            ],
            commit=False,
        )
        deleted_ids = await database.delete_old_ships(db, max_age_minutes=10)

        async with db.execute("SELECT id FROM ships ORDER BY id") as cursor:
            remaining_ids = [row[0] for row in await cursor.fetchall()]

        self.assertEqual(deleted_ids, ["stale-ship"])
        self.assertEqual(remaining_ids, ["fresh-ship"])

    def test_stale_threshold_helpers_clamp_to_one_or_more(self):
        self.assertEqual(database._minutes_from_seconds(30), 1)
        self.assertEqual(database._minutes_from_seconds(61), 2)
        self.assertEqual(database._days_from_seconds(3600), 1)
        self.assertEqual(database._days_from_seconds(86401), 2)


class DatabaseMigrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_database_path = database.DATABASE_PATH
        await database.close_db()
        self.database_path = str(Path(self.temp_dir.name) / "legacy.db")
        database.DATABASE_PATH = self.database_path

    async def asyncTearDown(self):
        await database.close_db()
        database.DATABASE_PATH = self.original_database_path
        self.temp_dir.cleanup()

    async def test_init_db_migrates_legacy_planes_table_to_repo_contract(self):
        migrated_timestamp = datetime.now(timezone.utc).isoformat()

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                """
                CREATE TABLE planes (
                    icao24 TEXT PRIMARY KEY,
                    lat REAL,
                    lon REAL,
                    alt INTEGER,
                    heading REAL,
                    callsign TEXT,
                    squawk TEXT,
                    speed REAL,
                    last_seen TEXT
                )
                """
            )
            await db.execute(
                """
                INSERT INTO planes (icao24, lat, lon, alt, heading, callsign, squawk, speed, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "legacy-icao24",
                    51.5,
                    -0.12,
                    32000,
                    180.0,
                    "LEGACY1",
                    "7000",
                    450.0,
                    migrated_timestamp,
                ),
            )
            await db.commit()

        await database.init_db()
        db = await database.get_db()

        async with db.execute("PRAGMA table_info(planes)") as cursor:
            columns = [row[1] for row in await cursor.fetchall()]
        async with db.execute("SELECT * FROM planes") as cursor:
            rows = [dict(row) for row in await cursor.fetchall()]

        self.assertIn("id", columns)
        self.assertIn("timestamp", columns)
        self.assertNotIn("icao24", columns)
        self.assertNotIn("last_seen", columns)
        self.assertEqual(
            rows,
            [
                {
                    "id": "legacy-icao24",
                    "lat": 51.5,
                    "lon": -0.12,
                    "alt": 32000,
                    "heading": 180.0,
                    "callsign": "LEGACY1",
                    "squawk": "7000",
                    "speed": 450.0,
                    "timestamp": migrated_timestamp,
                }
            ],
        )


class SchedulerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_database_path = database.DATABASE_PATH
        await database.close_db()
        database.DATABASE_PATH = str(Path(self.temp_dir.name) / "scheduler.db")
        schedulers.reset_ship_scheduler_state()
        await database.init_db()
        await schedulers.stop_schedulers()
        schedulers.reset_ship_scheduler_state()

    async def asyncTearDown(self):
        await schedulers.stop_schedulers()
        schedulers.reset_ship_scheduler_state()
        await database.close_db()
        database.DATABASE_PATH = self.original_database_path
        self.temp_dir.cleanup()

    async def test_refresh_planes_once_merges_dual_sources_persists_planes_cleans_stale_rows_and_broadcasts_plane_upserts_and_removes(self):
        db = await database.get_db()
        stale_timestamp = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        await database.upsert_plane(
            db,
            {
                "id": "old-plane",
                "lat": 0.0,
                "lon": 0.0,
                "alt": 0,
                "heading": 0.0,
                "callsign": "",
                "squawk": "",
                "speed": 0.0,
                "timestamp": stale_timestamp,
            },
        )

        open_sky_planes = [
            {
                "id": "abc123",
                "lat": 10.0,
                "lon": 20.0,
                "alt": 1000,
                "heading": 90.0,
                "callsign": "OPEN-OLDER",
                "squawk": "7000",
                "speed": 250.0,
                "timestamp": (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat(),
            },
            {
                "id": "def456",
                "lat": 11.0,
                "lon": 21.0,
                "alt": 2000,
                "heading": 180.0,
                "callsign": "OPEN-ONLY",
                "squawk": "7700",
                "speed": 350.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ]
        adsblol_planes = [
            {
                "id": "ABC123",
                "lat": 10.5,
                "lon": 20.5,
                "alt": 1100,
                "heading": 95.0,
                "callsign": "ADSB-NEWER",
                "squawk": "7001",
                "speed": 255.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": "GHI789",
                "lat": 12.0,
                "lon": 22.0,
                "alt": 3000,
                "heading": 270.0,
                "callsign": "ADSB-ONLY",
                "squawk": "6600",
                "speed": 410.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ]
        expected_planes = dedup_core.deduplicate_planes(open_sky_planes, adsblol_planes)

        with patch("app.tasks.schedulers.fetch_planes", AsyncMock(return_value=open_sky_planes)), patch(
            "app.tasks.schedulers.fetch_adsblol_planes", AsyncMock(return_value=adsblol_planes)
        ), patch("app.tasks.schedulers.broadcast_plane_batch", AsyncMock()) as batch_mock, patch(
            "app.tasks.schedulers.broadcast_plane_update", AsyncMock()
        ) as broadcast_mock:
            refreshed_planes = await schedulers.refresh_planes_once()

        async with db.execute("SELECT id, callsign FROM planes ORDER BY id") as cursor:
            stored_rows = [tuple(row) for row in await cursor.fetchall()]

        self.assertEqual(refreshed_planes, expected_planes)
        self.assertEqual(
            stored_rows,
            [
                ("abc123", "ADSB-NEWER"),
                ("def456", "OPEN-ONLY"),
                ("ghi789", "ADSB-ONLY"),
            ],
        )
        batch_mock.assert_awaited_once_with(expected_planes)
        broadcast_mock.assert_has_awaits(
            [
                unittest.mock.call({"id": "old-plane"}, action="remove"),
            ]
        )

    async def test_refresh_planes_once_filters_stale_source_records_before_persist_and_broadcast(self):
        db = await database.get_db()
        now = datetime.now(timezone.utc)
        open_sky_planes = [
            {
                "id": "abc123",
                "lat": 50.0,
                "lon": 10.0,
                "alt": 9000,
                "heading": 45.0,
                "callsign": "OPEN-FRESH",
                "squawk": "1111",
                "speed": 220.0,
                "timestamp": (now - timedelta(seconds=20)).isoformat(),
            },
            {
                "id": "stale-open",
                "lat": 51.0,
                "lon": 11.0,
                "alt": 9100,
                "heading": 50.0,
                "callsign": "OPEN-STALE",
                "squawk": "1112",
                "speed": 225.0,
                "timestamp": (now - timedelta(minutes=6)).isoformat(),
            },
        ]
        adsblol_planes = [
            {
                "id": "ABC123",
                "lat": 50.5,
                "lon": 10.5,
                "alt": 9200,
                "heading": 55.0,
                "callsign": "ADSB-WINNER",
                "squawk": "2221",
                "speed": 230.0,
                "timestamp": (now - timedelta(seconds=5)).isoformat(),
            },
            {
                "id": "STALE-ADSB",
                "lat": 52.0,
                "lon": 12.0,
                "alt": 9300,
                "heading": 60.0,
                "callsign": "ADSB-STALE",
                "squawk": "2222",
                "speed": 235.0,
                "timestamp": (now - timedelta(minutes=6)).isoformat(),
            },
        ]
        expected_planes = dedup_core.deduplicate_planes(open_sky_planes, adsblol_planes)

        with patch("app.tasks.schedulers.fetch_planes", AsyncMock(return_value=open_sky_planes)), patch(
            "app.tasks.schedulers.fetch_adsblol_planes", AsyncMock(return_value=adsblol_planes)
        ), patch("app.tasks.schedulers.broadcast_plane_batch", AsyncMock()) as batch_mock, patch(
            "app.tasks.schedulers.broadcast_plane_update", AsyncMock()
        ) as broadcast_mock:
            refreshed_planes = await schedulers.refresh_planes_once()

        async with db.execute("SELECT id, callsign FROM planes ORDER BY id") as cursor:
            stored_rows = [tuple(row) for row in await cursor.fetchall()]

        self.assertEqual(refreshed_planes, expected_planes)
        self.assertEqual(stored_rows, [("abc123", "ADSB-WINNER")])
        self.assertEqual([plane["id"] for plane in refreshed_planes], ["abc123"])
        batch_mock.assert_awaited_once_with(expected_planes)
        broadcast_mock.assert_not_awaited()

    async def test_refresh_planes_once_falls_back_to_single_source_when_other_plane_source_fails(self):
        db = await database.get_db()
        adsblol_planes = [
            {
                "id": "ABC123",
                "lat": 10.5,
                "lon": 20.5,
                "alt": 1100,
                "heading": 95.0,
                "callsign": "ADSB-ONLY",
                "squawk": "7001",
                "speed": 255.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]
        expected_planes = dedup_core.deduplicate_planes([], adsblol_planes)

        with patch("app.tasks.schedulers.fetch_planes", AsyncMock(side_effect=RuntimeError("opensky boom"))), patch(
            "app.tasks.schedulers.fetch_adsblol_planes", AsyncMock(return_value=adsblol_planes)
        ), patch("app.tasks.schedulers.broadcast_plane_batch", AsyncMock()) as batch_mock, patch(
            "app.tasks.schedulers.broadcast_plane_update", AsyncMock()
        ) as broadcast_mock, patch("app.tasks.schedulers.logger.warning") as warning_mock:
            refreshed_planes = await schedulers.refresh_planes_once()

        async with db.execute("SELECT id, callsign FROM planes ORDER BY id") as cursor:
            stored_rows = [tuple(row) for row in await cursor.fetchall()]

        self.assertEqual(refreshed_planes, expected_planes)
        self.assertEqual(stored_rows, [("abc123", "ADSB-ONLY")])
        batch_mock.assert_awaited_once_with(expected_planes)
        broadcast_mock.assert_not_awaited()
        warning_mock.assert_called_once()

    async def test_refresh_planes_once_rolls_back_failed_write_batch_and_leaves_state_unchanged(self):
        db = await database.get_db()
        existing_plane = {
            "id": "existing-plane",
            "lat": 33.0,
            "lon": -117.0,
            "alt": 1500,
            "heading": 30.0,
            "callsign": "EXIST",
            "squawk": "1200",
            "speed": 140.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await database.upsert_plane(db, existing_plane)

        incoming_planes = [
            {
                "id": "new-plane",
                "lat": 34.0,
                "lon": -118.0,
                "alt": 2500,
                "heading": 60.0,
                "callsign": "NEW123",
                "squawk": "7700",
                "speed": 240.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]

        with patch("app.tasks.schedulers.fetch_planes", AsyncMock(return_value=incoming_planes)), patch(
            "app.tasks.schedulers.fetch_adsblol_planes", AsyncMock(return_value=[])
        ), patch("app.tasks.schedulers.delete_old_planes", AsyncMock(side_effect=RuntimeError("boom"))), patch(
            "app.tasks.schedulers.broadcast_plane_update", AsyncMock()
        ):
            with self.assertRaises(RuntimeError):
                await schedulers.refresh_planes_once()

        async with db.execute("SELECT * FROM planes ORDER BY id") as cursor:
            rows = [dict(row) for row in await cursor.fetchall()]

        self.assertEqual(rows, [existing_plane])

    async def test_refresh_planes_once_uses_dedicated_connection_instead_of_shared_get_db(self):
        db = await database.get_db()
        planes = [
            {
                "id": "writer-plane",
                "lat": 41.0,
                "lon": -70.0,
                "alt": 5000,
                "heading": 270.0,
                "callsign": "WRITER",
                "squawk": "4455",
                "speed": 300.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]
        expected_planes = dedup_core.deduplicate_planes(planes, [])
        shared_get_db_mock = AsyncMock(side_effect=AssertionError("shared get_db should not be used"))

        with patch("app.tasks.schedulers.fetch_planes", AsyncMock(return_value=planes)), patch(
            "app.tasks.schedulers.fetch_adsblol_planes", AsyncMock(return_value=[])
        ), patch("app.tasks.schedulers.get_db", shared_get_db_mock, create=True), patch(
            "app.tasks.schedulers.broadcast_plane_update", AsyncMock()
        ):
            refreshed_planes = await schedulers.refresh_planes_once()

        async with db.execute("SELECT id FROM planes ORDER BY id") as cursor:
            stored_ids = [row[0] for row in await cursor.fetchall()]

        self.assertEqual(refreshed_planes, expected_planes)
        self.assertEqual(stored_ids, ["writer-plane"])
        shared_get_db_mock.assert_not_awaited()

    async def test_refresh_ships_once_persists_ships_cleans_stale_rows_and_broadcasts_ship_upserts_and_removes(self):
        db = await database.get_db()
        stale_timestamp = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
        await database.upsert_ship(
            db,
            {
                "id": "old-ship",
                "lat": 55.0,
                "lon": 20.0,
                "heading": 0.0,
                "speed": 0.0,
                "name": "",
                "destination": "",
                "ship_type": "other",
                "timestamp": stale_timestamp,
            },
        )

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
                "timestamp": datetime.now(timezone.utc).isoformat(),
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
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ]

        expected_ships = dedup_core.deduplicate_ships(ships, [])

        with patch("app.tasks.schedulers.fetch_ships", AsyncMock(return_value=ships)), patch(
            "app.tasks.schedulers.broadcast_ship_batch", AsyncMock()
        ) as batch_mock, patch(
            "app.tasks.schedulers.broadcast_ship_update", AsyncMock()
        ) as broadcast_mock:
            refreshed_ships = await schedulers.refresh_ships_once()

        async with db.execute("SELECT id FROM ships ORDER BY id") as cursor:
            stored_ids = [row[0] for row in await cursor.fetchall()]

        self.assertEqual(refreshed_ships, expected_ships)
        self.assertEqual(stored_ids, ["219598000", "230000001"])
        batch_mock.assert_awaited_once_with(expected_ships)
        broadcast_mock.assert_has_awaits(
            [
                unittest.mock.call({"id": "old-ship"}, action="remove"),
            ]
        )

    async def test_refresh_ships_once_rolls_back_failed_write_batch_and_leaves_state_unchanged(self):
        db = await database.get_db()
        existing_ship = {
            "id": "existing-ship",
            "lat": 60.0,
            "lon": 24.0,
            "heading": 180.0,
            "speed": 12.5,
            "name": "EXISTING",
            "destination": "FI HEL",
            "ship_type": "cargo",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await database.upsert_ship(db, existing_ship)
        schedulers._latest_digitraffic_ships = {existing_ship["id"]: existing_ship}
        schedulers._latest_aisstream_ships = {
            "cached-ais": {
                "id": "cached-ais",
                "lat": 61.0,
                "lon": 25.0,
                "heading": 90.0,
                "speed": 7.5,
                "name": "CACHED AIS",
                "destination": "SE STO",
                "ship_type": "other",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }
        original_digitraffic = dict(schedulers._latest_digitraffic_ships)
        original_aisstream = dict(schedulers._latest_aisstream_ships)

        incoming_ships = [
            {
                "id": "new-ship",
                "lat": 61.0,
                "lon": 25.0,
                "heading": 90.0,
                "speed": 7.5,
                "name": "NEW SHIP",
                "destination": "SE STO",
                "ship_type": "other",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]

        with patch("app.tasks.schedulers.fetch_ships", AsyncMock(return_value=incoming_ships)), patch(
            "app.tasks.schedulers.delete_old_ships", AsyncMock(side_effect=RuntimeError("boom"))
        ), patch("app.tasks.schedulers.broadcast_ship_update", AsyncMock()):
            with self.assertRaises(RuntimeError):
                await schedulers.refresh_ships_once()

        async with db.execute("SELECT * FROM ships ORDER BY id") as cursor:
            rows = [dict(row) for row in await cursor.fetchall()]

        self.assertEqual(rows, [existing_ship])
        self.assertEqual(schedulers._latest_digitraffic_ships, original_digitraffic)
        self.assertEqual(schedulers._latest_aisstream_ships, original_aisstream)

    async def test_refresh_ships_once_uses_dedicated_connection_instead_of_shared_get_db(self):
        db = await database.get_db()
        ships = [
            {
                "id": "writer-ship",
                "lat": 60.5,
                "lon": 25.5,
                "heading": 45.0,
                "speed": 8.5,
                "name": "WRITER SHIP",
                "destination": "LV RIX",
                "ship_type": "other",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]
        expected_ships = dedup_core.deduplicate_ships(ships, [])
        shared_get_db_mock = AsyncMock(side_effect=AssertionError("shared get_db should not be used"))

        with patch("app.tasks.schedulers.fetch_ships", AsyncMock(return_value=ships)), patch(
            "app.tasks.schedulers.get_db", shared_get_db_mock, create=True
        ), patch("app.tasks.schedulers.broadcast_ship_update", AsyncMock()):
            refreshed_ships = await schedulers.refresh_ships_once()

        async with db.execute("SELECT id FROM ships ORDER BY id") as cursor:
            stored_ids = [row[0] for row in await cursor.fetchall()]

        self.assertEqual(refreshed_ships, expected_ships)
        self.assertEqual(stored_ids, ["writer-ship"])
        shared_get_db_mock.assert_not_awaited()

    async def test_refresh_ships_once_retains_previous_digitraffic_snapshot_when_fetch_returns_empty(self):
        previous_digitraffic_ship = {
            "id": "111000111",
            "lat": 60.0,
            "lon": 24.0,
            "heading": 90.0,
            "speed": 12.0,
            "name": "PREVIOUS DIGITRAFFIC",
            "destination": "FI HEL",
            "ship_type": "cargo",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        schedulers._latest_digitraffic_ships = {previous_digitraffic_ship["id"]: previous_digitraffic_ship}
        expected_ships = dedup_core.deduplicate_ships([previous_digitraffic_ship], [])

        with patch("app.tasks.schedulers.fetch_ships", AsyncMock(return_value=[])), patch(
            "app.tasks.schedulers.broadcast_ship_batch", AsyncMock()
        ) as batch_mock, patch("app.tasks.schedulers.broadcast_ship_update", AsyncMock()), patch(
            "app.tasks.schedulers.logger.warning"
        ) as warning_mock:
            refreshed_ships = await schedulers.refresh_ships_once()

        self.assertEqual(refreshed_ships, expected_ships)
        self.assertEqual(schedulers._latest_digitraffic_ships, {previous_digitraffic_ship["id"]: previous_digitraffic_ship})
        batch_mock.assert_awaited_once_with(expected_ships)
        warning_mock.assert_called_once()

    async def test_refresh_ships_once_merges_cached_aisstream_ships_with_latest_digitraffic_snapshot(self):
        db = await database.get_db()
        fresh_timestamp = datetime.now(timezone.utc).isoformat()
        newer_timestamp = (datetime.now(timezone.utc) + timedelta(seconds=5)).isoformat()
        digitraffic_ship = {
            "id": "111000111",
            "lat": 60.0,
            "lon": 24.0,
            "heading": 90.0,
            "speed": 12.0,
            "name": "DIGITRAFFIC VESSEL",
            "destination": "FI HEL",
            "ship_type": "cargo",
            "timestamp": fresh_timestamp,
        }
        duplicate_aisstream_ship = {
            "id": "111000111",
            "lat": 60.1,
            "lon": 24.1,
            "heading": 95.0,
            "speed": 13.0,
            "name": "",
            "destination": "",
            "ship_type": "other",
            "timestamp": fresh_timestamp,
        }
        unique_aisstream_ship = {
            "id": "222000222",
            "lat": 61.0,
            "lon": 25.0,
            "heading": 180.0,
            "speed": 9.0,
            "name": "AISSTREAM ONLY",
            "destination": "SE STO",
            "ship_type": "tanker",
            "timestamp": newer_timestamp,
        }
        schedulers._latest_aisstream_ships = {
            duplicate_aisstream_ship["id"]: duplicate_aisstream_ship,
            unique_aisstream_ship["id"]: unique_aisstream_ship,
        }
        expected_ships = dedup_core.deduplicate_ships(
            [digitraffic_ship],
            [duplicate_aisstream_ship, unique_aisstream_ship],
        )

        with patch("app.tasks.schedulers.fetch_ships", AsyncMock(return_value=[digitraffic_ship])), patch(
            "app.tasks.schedulers.deduplicate_ships", wraps=dedup_core.deduplicate_ships
        ) as dedup_mock, patch("app.tasks.schedulers.broadcast_ship_batch", AsyncMock()) as batch_mock, patch(
            "app.tasks.schedulers.broadcast_ship_update", AsyncMock()
        ):
            merged_ships = await schedulers.refresh_ships_once()

        self.assertEqual(merged_ships, expected_ships)
        dedup_mock.assert_called_once_with([digitraffic_ship], [duplicate_aisstream_ship, unique_aisstream_ship])
        batch_mock.assert_awaited_once_with(merged_ships)

        async with db.execute("SELECT id, name, destination FROM ships ORDER BY id") as cursor:
            rows = [tuple(row) for row in await cursor.fetchall()]

        self.assertEqual(
            rows,
            [
                ("111000111", "DIGITRAFFIC VESSEL", "FI HEL"),
                ("222000222", "AISSTREAM ONLY", "SE STO"),
            ],
        )

    async def test_ingest_aisstream_batch_prefers_newer_timestamp_and_merges_missing_metadata(self):
        base_timestamp = datetime.now(timezone.utc) - timedelta(minutes=2)
        digitraffic_ship = {
            "id": "333000333",
            "lat": 62.0,
            "lon": 26.0,
            "heading": 45.0,
            "speed": 10.0,
            "name": "",
            "destination": "FI TKU",
            "ship_type": "cargo",
            "timestamp": base_timestamp.isoformat(),
        }
        schedulers._latest_digitraffic_ships = {digitraffic_ship["id"]: digitraffic_ship}
        aisstream_ship = {
            "id": "333000333",
            "lat": 62.5,
            "lon": 26.5,
            "heading": 55.0,
            "speed": 11.0,
            "name": "AISSTREAM WINNER",
            "destination": "",
            "ship_type": "other",
            "timestamp": (base_timestamp + timedelta(minutes=1)).isoformat(),
        }
        expected_ships = dedup_core.deduplicate_ships([digitraffic_ship], [aisstream_ship])

        with patch("app.tasks.schedulers.deduplicate_ships", wraps=dedup_core.deduplicate_ships) as dedup_mock, patch(
            "app.tasks.schedulers.broadcast_ship_batch", AsyncMock()
        ) as batch_mock, patch("app.tasks.schedulers.broadcast_ship_update", AsyncMock()):
            merged_ships = await schedulers.ingest_aisstream_batch([aisstream_ship])

        self.assertEqual(merged_ships, expected_ships)
        dedup_mock.assert_called_once_with([digitraffic_ship], [aisstream_ship])
        batch_mock.assert_awaited_once_with(merged_ships)

    async def test_ingest_aisstream_batch_rolls_back_cache_when_persist_fails(self):
        base_timestamp = datetime.now(timezone.utc) - timedelta(minutes=2)
        digitraffic_ship = {
            "id": "333000333",
            "lat": 62.0,
            "lon": 26.0,
            "heading": 45.0,
            "speed": 10.0,
            "name": "DIGITRAFFIC",
            "destination": "FI TKU",
            "ship_type": "cargo",
            "timestamp": base_timestamp.isoformat(),
        }
        existing_aisstream_ship = {
            "id": "444000444",
            "lat": 63.0,
            "lon": 27.0,
            "heading": 90.0,
            "speed": 8.0,
            "name": "CACHED AIS",
            "destination": "SE STO",
            "ship_type": "tanker",
            "timestamp": base_timestamp.isoformat(),
        }
        schedulers._latest_digitraffic_ships = {digitraffic_ship["id"]: digitraffic_ship}
        schedulers._latest_aisstream_ships = {existing_aisstream_ship["id"]: existing_aisstream_ship}
        original_digitraffic = dict(schedulers._latest_digitraffic_ships)
        original_aisstream = dict(schedulers._latest_aisstream_ships)
        incoming_aisstream_ship = {
            "id": "555000555",
            "lat": 64.0,
            "lon": 28.0,
            "heading": 120.0,
            "speed": 9.0,
            "name": "NEW AIS",
            "destination": "EE TLL",
            "ship_type": "other",
            "timestamp": (base_timestamp + timedelta(minutes=1)).isoformat(),
        }

        with patch("app.tasks.schedulers._persist_and_broadcast_ships", AsyncMock(side_effect=RuntimeError("boom"))):
            with self.assertRaises(RuntimeError):
                await schedulers.ingest_aisstream_batch([incoming_aisstream_ship])

        self.assertEqual(schedulers._latest_digitraffic_ships, original_digitraffic)
        self.assertEqual(schedulers._latest_aisstream_ships, original_aisstream)

    async def test_plane_fetch_loop_recovers_after_refresh_failure(self):
        refresh_mock = AsyncMock(side_effect=[RuntimeError("boom"), asyncio.CancelledError()])
        sleep_mock = AsyncMock(return_value=None)

        with patch("app.tasks.schedulers.refresh_planes_once", refresh_mock), patch(
            "app.tasks.schedulers.asyncio.sleep", sleep_mock
        ), patch("app.tasks.schedulers.logger.exception") as log_exception_mock:
            with self.assertRaises(asyncio.CancelledError):
                await schedulers.plane_fetch_loop(interval_seconds=0)

        self.assertEqual(refresh_mock.await_count, 2)
        sleep_mock.assert_awaited_once_with(0)
        log_exception_mock.assert_called_once()

    async def test_ships_refresh_loop_recovers_after_refresh_failure(self):
        refresh_mock = AsyncMock(side_effect=[RuntimeError("boom"), asyncio.CancelledError()])
        sleep_mock = AsyncMock(return_value=None)

        with patch("app.tasks.schedulers.refresh_ships_once", refresh_mock), patch(
            "app.tasks.schedulers.asyncio.sleep", sleep_mock
        ), patch("app.tasks.schedulers.logger.exception") as log_exception_mock:
            with self.assertRaises(asyncio.CancelledError):
                await schedulers.ships_refresh_loop(interval_seconds=0)

        self.assertEqual(refresh_mock.await_count, 2)
        sleep_mock.assert_awaited_once_with(0)
        log_exception_mock.assert_called_once()

    async def test_aisstream_listener_loop_retries_after_listen_failure(self):
        class FakeAisstreamService:
            def __init__(self, *, batches=None, error: Exception | None = None):
                self.api_key = "test-key"
                self._batches = list(batches or [])
                self._error = error
                self.close = AsyncMock()

            async def listen(self, batch_interval=schedulers.AISSTREAM_BATCH_INTERVAL_SECONDS):
                if self._error is not None:
                    error = self._error
                    self._error = None
                    raise error
                for batch in self._batches:
                    yield batch

        initial_service = FakeAisstreamService(error=RuntimeError("boom"))
        recovery_service = FakeAisstreamService(batches=[[{"id": "111000111", "timestamp": datetime.now(timezone.utc).isoformat()}]])
        sleep_mock = AsyncMock(return_value=None)

        with patch("app.tasks.schedulers.AisstreamService", return_value=recovery_service), patch(
            "app.tasks.schedulers.asyncio.sleep", sleep_mock
        ), patch("app.tasks.schedulers.ingest_aisstream_batch", AsyncMock()) as ingest_mock:
            await schedulers.aisstream_listener_loop(batch_interval_seconds=0, service=initial_service)

        sleep_mock.assert_awaited_once_with(1)
        initial_service.close.assert_awaited()
        recovery_service.close.assert_awaited()
        ingest_mock.assert_awaited_once_with(recovery_service._batches[0])

    async def test_start_and_stop_schedulers_manage_background_tasks(self):
        plane_started = asyncio.Event()
        ship_started = asyncio.Event()
        gdelt_started = asyncio.Event()
        plane_cancelled = asyncio.Event()
        ship_cancelled = asyncio.Event()
        gdelt_cancelled = asyncio.Event()

        async def fake_plane_loop(interval_seconds=schedulers.PLANE_REFRESH_INTERVAL_SECONDS):
            plane_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                plane_cancelled.set()
                raise

        async def fake_ship_loop(interval_seconds=schedulers.SHIP_REFRESH_INTERVAL_SECONDS):
            ship_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                ship_cancelled.set()
                raise

        async def fake_gdelt_loop(interval_seconds=schedulers.GDELT_REFRESH_SECONDS):
            gdelt_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                gdelt_cancelled.set()
                raise

        with patch.object(schedulers.settings, "AISSTREAM_API_KEY", ""), patch(
            "app.tasks.schedulers.plane_fetch_loop", fake_plane_loop
        ), patch("app.tasks.schedulers.ships_refresh_loop", fake_ship_loop), patch(
            "app.tasks.schedulers.gdelt_refresh_loop", fake_gdelt_loop
        ):
            tasks = await schedulers.start_schedulers(interval_seconds=0, ship_interval_seconds=0)
            await asyncio.wait_for(plane_started.wait(), timeout=1)
            await asyncio.wait_for(ship_started.wait(), timeout=1)
            await asyncio.wait_for(gdelt_started.wait(), timeout=1)
            self.assertEqual(len(tasks), 3)
            self.assertTrue(all(not task.done() for task in tasks))
            await schedulers.stop_schedulers()

        await asyncio.wait_for(plane_cancelled.wait(), timeout=1)
        await asyncio.wait_for(ship_cancelled.wait(), timeout=1)
        await asyncio.wait_for(gdelt_cancelled.wait(), timeout=1)
        self.assertEqual(schedulers.get_scheduler_tasks(), [])

    async def test_start_schedulers_starts_aisstream_listener_when_api_key_present(self):
        plane_started = asyncio.Event()
        ship_started = asyncio.Event()
        aisstream_started = asyncio.Event()
        gdelt_started = asyncio.Event()
        plane_cancelled = asyncio.Event()
        ship_cancelled = asyncio.Event()
        aisstream_cancelled = asyncio.Event()
        gdelt_cancelled = asyncio.Event()

        async def fake_plane_loop(interval_seconds=schedulers.PLANE_REFRESH_INTERVAL_SECONDS):
            plane_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                plane_cancelled.set()
                raise

        async def fake_ship_loop(interval_seconds=schedulers.SHIP_REFRESH_INTERVAL_SECONDS):
            ship_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                ship_cancelled.set()
                raise

        async def fake_aisstream_loop(*, batch_interval_seconds=schedulers.AISSTREAM_BATCH_INTERVAL_SECONDS, service=None):
            aisstream_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                aisstream_cancelled.set()
                raise

        async def fake_gdelt_loop(interval_seconds=schedulers.GDELT_REFRESH_SECONDS):
            gdelt_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                gdelt_cancelled.set()
                raise

        fake_service = AsyncMock()
        fake_service.close = AsyncMock()

        with patch.object(schedulers.settings, "AISSTREAM_API_KEY", "test-key"), patch(
            "app.tasks.schedulers.plane_fetch_loop", fake_plane_loop
        ), patch("app.tasks.schedulers.ships_refresh_loop", fake_ship_loop), patch(
            "app.tasks.schedulers.aisstream_listener_loop", fake_aisstream_loop
        ), patch("app.tasks.schedulers.AisstreamService", return_value=fake_service), patch(
            "app.tasks.schedulers.gdelt_refresh_loop", fake_gdelt_loop
        ):
            tasks = await schedulers.start_schedulers(
                interval_seconds=0,
                ship_interval_seconds=0,
                aisstream_batch_interval_seconds=0,
            )
            await asyncio.wait_for(plane_started.wait(), timeout=1)
            await asyncio.wait_for(ship_started.wait(), timeout=1)
            await asyncio.wait_for(aisstream_started.wait(), timeout=1)
            await asyncio.wait_for(gdelt_started.wait(), timeout=1)
            self.assertEqual(len(tasks), 4)
            await schedulers.stop_schedulers()

        fake_service.close.assert_awaited()

        await asyncio.wait_for(plane_cancelled.wait(), timeout=1)
        await asyncio.wait_for(ship_cancelled.wait(), timeout=1)
        await asyncio.wait_for(aisstream_cancelled.wait(), timeout=1)
        await asyncio.wait_for(gdelt_cancelled.wait(), timeout=1)
        self.assertEqual(schedulers.get_scheduler_tasks(), [])

    async def test_start_schedulers_restarts_missing_aisstream_task_without_duplicating_others(self):
        plane_started_count = 0
        ship_started_count = 0
        aisstream_started_count = 0
        gdelt_started_count = 0
        plane_started = asyncio.Event()
        ship_started = asyncio.Event()
        aisstream_started = asyncio.Event()
        gdelt_started = asyncio.Event()
        plane_cancelled = asyncio.Event()
        ship_cancelled = asyncio.Event()
        aisstream_cancelled = asyncio.Event()
        gdelt_cancelled = asyncio.Event()

        async def fake_plane_loop(interval_seconds=schedulers.PLANE_REFRESH_INTERVAL_SECONDS):
            nonlocal plane_started_count
            plane_started_count += 1
            plane_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                plane_cancelled.set()
                raise

        async def fake_ship_loop(interval_seconds=schedulers.SHIP_REFRESH_INTERVAL_SECONDS):
            nonlocal ship_started_count
            ship_started_count += 1
            ship_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                ship_cancelled.set()
                raise

        async def fake_aisstream_loop(*, batch_interval_seconds=schedulers.AISSTREAM_BATCH_INTERVAL_SECONDS, service=None):
            nonlocal aisstream_started_count
            aisstream_started_count += 1
            aisstream_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                aisstream_cancelled.set()
                raise

        async def fake_gdelt_loop(interval_seconds=schedulers.GDELT_REFRESH_SECONDS):
            nonlocal gdelt_started_count
            gdelt_started_count += 1
            gdelt_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                gdelt_cancelled.set()
                raise

        fake_service = AsyncMock()
        fake_service.close = AsyncMock()

        with patch.object(schedulers.settings, "AISSTREAM_API_KEY", "test-key"), patch(
            "app.tasks.schedulers.plane_fetch_loop", fake_plane_loop
        ), patch("app.tasks.schedulers.ships_refresh_loop", fake_ship_loop), patch(
            "app.tasks.schedulers.aisstream_listener_loop", fake_aisstream_loop
        ), patch("app.tasks.schedulers.AisstreamService", return_value=fake_service), patch(
            "app.tasks.schedulers.gdelt_refresh_loop", fake_gdelt_loop
        ):
            tasks = await schedulers.start_schedulers(
                interval_seconds=0,
                ship_interval_seconds=0,
                aisstream_batch_interval_seconds=0,
            )
            await asyncio.wait_for(plane_started.wait(), timeout=1)
            await asyncio.wait_for(ship_started.wait(), timeout=1)
            await asyncio.wait_for(aisstream_started.wait(), timeout=1)
            await asyncio.wait_for(gdelt_started.wait(), timeout=1)
            self.assertEqual(len(tasks), 4)
            self.assertEqual(plane_started_count, 1)
            self.assertEqual(ship_started_count, 1)
            self.assertEqual(aisstream_started_count, 1)
            self.assertEqual(gdelt_started_count, 1)

            aisstream_started.clear()
            aisstream_task = next(task for task in schedulers.get_scheduler_tasks() if task.get_name() == "aisstream-listener-loop")
            aisstream_task.cancel()
            await asyncio.gather(aisstream_task, return_exceptions=True)

            tasks = await schedulers.start_schedulers(
                interval_seconds=0,
                ship_interval_seconds=0,
                aisstream_batch_interval_seconds=0,
            )
            await asyncio.wait_for(aisstream_started.wait(), timeout=1)
            self.assertEqual(len(tasks), 4)
            self.assertEqual(plane_started_count, 1)
            self.assertEqual(ship_started_count, 1)
            self.assertEqual(aisstream_started_count, 2)
            self.assertEqual(gdelt_started_count, 1)

            await schedulers.stop_schedulers()

        fake_service.close.assert_awaited()
        await asyncio.wait_for(plane_cancelled.wait(), timeout=1)
        await asyncio.wait_for(ship_cancelled.wait(), timeout=1)
        await asyncio.wait_for(aisstream_cancelled.wait(), timeout=1)
        await asyncio.wait_for(gdelt_cancelled.wait(), timeout=1)


class MainLifespanTests(unittest.IsolatedAsyncioTestCase):
    async def test_app_lifespan_starts_and_stops_schedulers(self):
        from app import main

        with patch("app.main.init_db", AsyncMock()) as init_db_mock, patch(
            "app.main.start_schedulers", AsyncMock()
        ) as start_mock, patch("app.main.stop_schedulers", AsyncMock()) as stop_mock, patch(
            "app.main.close_db", AsyncMock()
        ) as close_db_mock:
            async with main.lifespan(main.app):
                init_db_mock.assert_awaited_once()
                start_mock.assert_awaited_once()
                stop_mock.assert_not_awaited()
                close_db_mock.assert_not_awaited()

        stop_mock.assert_awaited_once()
        close_db_mock.assert_awaited_once()


class WebSocketBroadcastTests(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        from app.api import websocket

        websocket.connected_clients.clear()

    async def test_broadcast_plane_update_sends_single_plane_payload_and_logs_dead_clients(self):
        from app.api import websocket

        live_client = AsyncMock()
        dead_client = AsyncMock()
        dead_client.send_json.side_effect = RuntimeError("socket closed")
        websocket.connected_clients[:] = [live_client, dead_client]
        plane = {
            "id": "abc123",
            "lat": 10.0,
            "lon": 20.0,
            "alt": 1000,
            "heading": 90.0,
            "callsign": "TEST123",
            "squawk": "7000",
            "speed": 250.0,
            "timestamp": "2026-04-10T20:00:00+00:00",
        }

        with patch("app.api.websocket.logger.warning") as log_warning_mock:
            await websocket.broadcast_plane_update(plane)

        live_client.send_json.assert_awaited_once_with(
            {
                "type": "plane",
                "action": "upsert",
                "data": plane,
                "timestamp": ANY,
            }
        )
        self.assertEqual(websocket.connected_clients, [live_client])
        log_warning_mock.assert_called_once()

    async def test_broadcast_plane_update_supports_remove_action_payload(self):
        from app.api import websocket

        live_client = AsyncMock()
        websocket.connected_clients[:] = [live_client]

        await websocket.broadcast_plane_update({"id": "stale-plane"}, action="remove")

        live_client.send_json.assert_awaited_once_with(
            {
                "type": "plane",
                "action": "remove",
                "data": {"id": "stale-plane"},
                "timestamp": ANY,
            }
        )

    async def test_broadcast_ship_update_sends_single_ship_payload_and_logs_dead_clients(self):
        from app.api import websocket

        live_client = AsyncMock()
        dead_client = AsyncMock()
        dead_client.send_json.side_effect = RuntimeError("socket closed")
        websocket.connected_clients[:] = [live_client, dead_client]
        ship = {
            "id": "219598000",
            "lat": 55.770832,
            "lon": 20.85169,
            "heading": 79.0,
            "speed": 0.1,
            "name": "NORD SUPERIOR",
            "destination": "NL AMS",
            "ship_type": "tanker",
            "timestamp": "2026-04-11T01:44:52+00:00",
        }

        with patch("app.api.websocket.logger.warning") as log_warning_mock:
            await websocket.broadcast_ship_update(ship)

        live_client.send_json.assert_awaited_once_with(
            {
                "type": "ship",
                "action": "upsert",
                "data": ship,
                "timestamp": ANY,
            }
        )
        self.assertEqual(websocket.connected_clients, [live_client])
        log_warning_mock.assert_called_once()

    async def test_broadcast_ship_update_supports_remove_action_payload(self):
        from app.api import websocket

        live_client = AsyncMock()
        websocket.connected_clients[:] = [live_client]

        await websocket.broadcast_ship_update({"id": "stale-ship"}, action="remove")

        live_client.send_json.assert_awaited_once_with(
            {
                "type": "ship",
                "action": "remove",
                "data": {"id": "stale-ship"},
                "timestamp": ANY,
            }
        )

    async def test_broadcast_ship_batch_sends_one_batch_payload(self):
        from app.api import websocket

        live_client = AsyncMock()
        websocket.connected_clients[:] = [live_client]
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
                "timestamp": "2026-04-11T01:44:52+00:00",
            }
        ]

        await websocket.broadcast_ship_batch(ships)

        live_client.send_json.assert_awaited_once_with(
            {
                "type": "ship_batch",
                "action": "upsert",
                "data": ships,
                "timestamp": ANY,
            }
        )

    async def test_send_heartbeat_treats_closed_socket_runtime_error_as_disconnect(self):
        from app.api import websocket

        closed_client = AsyncMock()
        closed_client.send_json.side_effect = RuntimeError(
            'Cannot call "send" once a close message has been sent.'
        )
        websocket.connected_clients[:] = [closed_client]

        sent = await websocket.send_heartbeat(closed_client)

        self.assertFalse(sent)
        self.assertEqual(websocket.connected_clients, [])


if __name__ == "__main__":
    unittest.main()
