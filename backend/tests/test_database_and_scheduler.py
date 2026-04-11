import asyncio
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import ANY, AsyncMock, patch

import aiosqlite

from app.core import database
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
        await database.init_db()
        await schedulers.stop_schedulers()

    async def asyncTearDown(self):
        await schedulers.stop_schedulers()
        await database.close_db()
        database.DATABASE_PATH = self.original_database_path
        self.temp_dir.cleanup()

    async def test_refresh_planes_once_persists_planes_cleans_stale_rows_and_broadcasts_plane_upserts_and_removes(self):
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

        planes = [
            {
                "id": "abc123",
                "lat": 10.0,
                "lon": 20.0,
                "alt": 1000,
                "heading": 90.0,
                "callsign": "TEST123",
                "squawk": "7000",
                "speed": 250.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
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
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ]

        with patch("app.tasks.schedulers.fetch_planes", AsyncMock(return_value=planes)), patch(
            "app.tasks.schedulers.broadcast_plane_batch", AsyncMock()
        ) as batch_mock, patch(
            "app.tasks.schedulers.broadcast_plane_update", AsyncMock()
        ) as broadcast_mock:
            refreshed_planes = await schedulers.refresh_planes_once()

        async with db.execute("SELECT id FROM planes ORDER BY id") as cursor:
            stored_ids = [row[0] for row in await cursor.fetchall()]

        self.assertEqual(refreshed_planes, planes)
        self.assertEqual(stored_ids, ["abc123", "def456"])
        # Upserts are now sent as a single batch message
        batch_mock.assert_awaited_once_with(planes)
        # Removes are still sent individually
        broadcast_mock.assert_has_awaits(
            [
                unittest.mock.call({"id": "old-plane"}, action="remove"),
            ]
        )

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
            "app.tasks.schedulers.delete_old_planes", AsyncMock(side_effect=RuntimeError("boom"))
        ), patch("app.tasks.schedulers.broadcast_plane_update", AsyncMock()):
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
        shared_get_db_mock = AsyncMock(side_effect=AssertionError("shared get_db should not be used"))

        with patch("app.tasks.schedulers.fetch_planes", AsyncMock(return_value=planes)), patch(
            "app.tasks.schedulers.get_db", shared_get_db_mock, create=True
        ), patch("app.tasks.schedulers.broadcast_plane_update", AsyncMock()):
            refreshed_planes = await schedulers.refresh_planes_once()

        async with db.execute("SELECT id FROM planes ORDER BY id") as cursor:
            stored_ids = [row[0] for row in await cursor.fetchall()]

        self.assertEqual(refreshed_planes, planes)
        self.assertEqual(stored_ids, ["writer-plane"])
        shared_get_db_mock.assert_not_awaited()

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

    async def test_start_and_stop_schedulers_manage_background_tasks(self):
        started = asyncio.Event()
        cancelled = asyncio.Event()

        async def fake_loop(interval_seconds=schedulers.PLANE_REFRESH_INTERVAL_SECONDS):
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancelled.set()
                raise

        with patch("app.tasks.schedulers.plane_fetch_loop", fake_loop):
            tasks = await schedulers.start_schedulers(interval_seconds=0)
            await asyncio.wait_for(started.wait(), timeout=1)
            self.assertEqual(len(tasks), 1)
            self.assertFalse(tasks[0].done())
            await schedulers.stop_schedulers()

        await asyncio.wait_for(cancelled.wait(), timeout=1)
        self.assertEqual(schedulers.get_scheduler_tasks(), [])


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
