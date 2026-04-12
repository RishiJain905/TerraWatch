import asyncio
import json
import unittest
from unittest.mock import AsyncMock

from websockets.exceptions import ConnectionClosedError

from app.services import aisstream_service


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleep_calls: list[float] = []

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds

    async def sleep(self, seconds: float) -> None:
        self.sleep_calls.append(seconds)
        self.advance(seconds)


class FakeWebSocket:
    def __init__(self, *, planned_results=None, clock: FakeClock | None = None):
        self.planned_results = list(planned_results or [])
        self.clock = clock
        self.sent_messages: list[str] = []
        self.closed = False
        self.close_calls = 0

    async def send(self, message: str) -> None:
        self.sent_messages.append(message)

    async def recv(self):
        if not self.planned_results:
            raise AssertionError("No planned recv result configured")

        result = self.planned_results.pop(0)
        if isinstance(result, dict):
            if self.clock is not None:
                self.clock.advance(result.get("advance", 0.0))
            if "exception" in result:
                raise result["exception"]
            return result.get("value")

        return result

    async def close(self) -> None:
        self.closed = True
        self.close_calls += 1


class AisstreamServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_connect_sends_subscription(self):
        fake_socket = FakeWebSocket()
        connect_mock = AsyncMock(return_value=fake_socket)
        service = aisstream_service.AisstreamService(
            api_key="test-api-key",
            connect_func=connect_mock,
        )

        connected = await service.connect()

        self.assertTrue(connected)
        connect_mock.assert_awaited_once_with(
            aisstream_service.AISSTREAM_STREAM_URL,
            open_timeout=aisstream_service.OPEN_TIMEOUT_SECONDS,
            ping_interval=aisstream_service.PING_INTERVAL_SECONDS,
            ping_timeout=aisstream_service.PING_TIMEOUT_SECONDS,
        )
        self.assertEqual(len(fake_socket.sent_messages), 1)
        self.assertEqual(
            json.loads(fake_socket.sent_messages[0]),
            {
                "APIKey": "test-api-key",
                "BoundingBoxes": [[[-90, -180], [90, 180]]],
                "FiltersShipMMSI": [],
                "FilterMessageTypes": aisstream_service.DEFAULT_MESSAGE_TYPES,
            },
        )
        await service.close()

    async def test_handle_message_parses_position_report(self):
        service = aisstream_service.AisstreamService(api_key="test-api-key")
        raw_message = {
            "MessageType": "PositionReport",
            "MetaData": {
                "ShipName": "  OCEAN SPIRIT  ",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "time_utc": "2026-04-11T01:44:52Z",
            },
            "Message": {
                "PositionReport": {
                    "UserID": 123456789,
                    "Latitude": 37.7749,
                    "Longitude": -122.4194,
                    "TrueHeading": 90,
                    "Sog": 12.5,
                    "ShipType": 70,
                    "Destination": "  OAKLAND  ",
                }
            },
        }

        ship = await service._handle_message(json.dumps(raw_message))

        self.assertEqual(
            ship,
            {
                "id": "123456789",
                "lat": 37.7749,
                "lon": -122.4194,
                "heading": 90.0,
                "speed": 12.5,
                "name": "OCEAN SPIRIT",
                "destination": "OAKLAND",
                "ship_type": "cargo",
                "timestamp": "2026-04-11T01:44:52+00:00",
            },
        )
        self.assertEqual(service._ships["123456789"], ship)

    async def test_shiptype_mapping(self):
        self.assertEqual(aisstream_service._map_ship_type(70), "cargo")
        self.assertEqual(aisstream_service._map_ship_type(80), "tanker")
        self.assertEqual(aisstream_service._map_ship_type(60), "passenger")
        self.assertEqual(aisstream_service._map_ship_type(30), "fishing")
        self.assertEqual(aisstream_service._map_ship_type(99), "other")

    async def test_batch_interval_emit(self):
        clock = FakeClock()
        fake_socket = FakeWebSocket(
            clock=clock,
            planned_results=[
                {
                    "value": json.dumps(
                        {
                            "MessageType": "PositionReport",
                            "MetaData": {
                                "ShipName": "BATCH SHIP",
                                "time_utc": "2026-04-11T01:44:52Z",
                            },
                            "Message": {
                                "PositionReport": {
                                    "UserID": "111000111",
                                    "Latitude": 60.1,
                                    "Longitude": 24.9,
                                    "TrueHeading": 180,
                                    "Sog": 8.2,
                                    "ShipType": 80,
                                }
                            },
                        }
                    ),
                    "advance": 0.6,
                }
            ],
        )
        service = aisstream_service.AisstreamService(
            api_key="test-api-key",
            connect_func=AsyncMock(return_value=fake_socket),
            sleep_func=clock.sleep,
            time_func=clock,
        )

        listener = service.listen(batch_interval=0.5)
        batch = await anext(listener)

        self.assertEqual(len(batch), 1)
        self.assertEqual(batch[0]["id"], "111000111")
        self.assertEqual(batch[0]["ship_type"], "tanker")
        self.assertEqual(service._ships, {})
        await listener.aclose()
        await service.close()

    async def test_reconnect_on_disconnect(self):
        clock = FakeClock()
        first_socket = FakeWebSocket(
            clock=clock,
            planned_results=[{"exception": ConnectionClosedError(None, None)}],
        )
        second_socket = FakeWebSocket(
            clock=clock,
            planned_results=[
                {
                    "value": json.dumps(
                        {
                            "MessageType": "PositionReport",
                            "MetaData": {
                                "ShipName": "RECONNECT SHIP",
                                "time_utc": "2026-04-11T01:44:52Z",
                            },
                            "Message": {
                                "PositionReport": {
                                    "UserID": "222000222",
                                    "Latitude": 61.0,
                                    "Longitude": 25.0,
                                    "Cog": 75.0,
                                    "Sog": 5.5,
                                    "ShipType": 60,
                                }
                            },
                        }
                    ),
                    "advance": 0.6,
                }
            ],
        )
        connect_mock = AsyncMock(side_effect=[first_socket, second_socket])
        service = aisstream_service.AisstreamService(
            api_key="test-api-key",
            connect_func=connect_mock,
            sleep_func=clock.sleep,
            time_func=clock,
        )

        listener = service.listen(batch_interval=0.5)
        batch = await anext(listener)

        self.assertEqual(connect_mock.await_count, 2)
        self.assertEqual(clock.sleep_calls, [aisstream_service.RECONNECT_BASE_DELAY_SECONDS])
        self.assertEqual(batch[0]["id"], "222000222")
        self.assertTrue(first_socket.closed)
        await listener.aclose()
        await service.close()

    async def test_invalid_json_skipped(self):
        service = aisstream_service.AisstreamService(api_key="test-api-key")

        ship = await service._handle_message("{not-json")

        self.assertIsNone(ship)
        self.assertEqual(service._ships, {})

    async def test_handle_message_raises_auth_error_for_rejected_key_message(self):
        service = aisstream_service.AisstreamService(api_key="test-api-key")
        raw_message = {
            "error": "authentication failed",
            "detail": "invalid api key",
        }

        with self.assertRaises(aisstream_service.AisstreamAuthError):
            await service._handle_message(raw_message)

        self.assertTrue(service._auth_failed)
        self.assertEqual(service._ships, {})

    async def test_listen_returns_without_api_key(self):
        clock = FakeClock()
        service = aisstream_service.AisstreamService(
            api_key="",
            sleep_func=clock.sleep,
            time_func=clock,
        )

        listener = service.listen(batch_interval=1)
        with self.assertRaises(StopAsyncIteration):
            await anext(listener)

        self.assertEqual(clock.sleep_calls, [])
        await listener.aclose()


if __name__ == "__main__":
    unittest.main()
