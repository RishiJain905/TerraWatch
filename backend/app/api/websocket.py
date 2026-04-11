import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.models import WSMessage

router = APIRouter()
logger = logging.getLogger(__name__)

connected_clients: list[WebSocket] = []
HEARTBEAT_INTERVAL_SECONDS = 10
_CLOSE_MESSAGE_SENT_ERROR = 'Cannot call "send" once a close message has been sent.'


def register_client(websocket: WebSocket) -> None:
    if websocket not in connected_clients:
        connected_clients.append(websocket)


def unregister_client(websocket: WebSocket) -> bool:
    if websocket in connected_clients:
        connected_clients.remove(websocket)
        return True
    return False


def _is_expected_close_error(error: Exception) -> bool:
    return isinstance(error, RuntimeError) and _CLOSE_MESSAGE_SENT_ERROR in str(error)


async def broadcast(message: dict) -> None:
    """Broadcast a message to all connected WebSocket clients."""
    clients = connected_clients[:]
    if not clients:
        return

    results = await asyncio.gather(
        *(client.send_json(message) for client in clients),
        return_exceptions=True,
    )
    for client, result in zip(clients, results):
        if isinstance(result, Exception):
            was_removed = unregister_client(client)
            if was_removed:
                logger.warning("WebSocket broadcast failed; dropping client: %s", result)


async def broadcast_plane_update(plane: dict, *, action: str | None = "upsert") -> None:
    """Broadcast a single plane payload that matches the frontend contract."""
    message = {
        "type": "plane",
        "data": plane,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if action is not None:
        message["action"] = action

    await broadcast(message)


async def broadcast_plane_batch(planes: list[dict]) -> None:
    """Broadcast all plane upserts in a single WebSocket message."""
    message = {
        "type": "plane_batch",
        "action": "upsert",
        "data": planes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await broadcast(message)


async def broadcast_ship_update(ship: dict, *, action: str | None = "upsert") -> None:
    """Broadcast a single ship payload that matches the frontend contract."""
    message = {
        "type": "ship",
        "data": ship,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if action is not None:
        message["action"] = action

    await broadcast(message)


async def broadcast_ship_batch(ships: list[dict]) -> None:
    """Broadcast all ship upserts in a single WebSocket message."""
    message = {
        "type": "ship_batch",
        "action": "upsert",
        "data": ships,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await broadcast(message)


async def send_heartbeat(websocket: WebSocket, *, status: str | None = None) -> bool:
    payload = {}
    if status is not None:
        payload["status"] = status

    message = WSMessage(type="heartbeat", data=payload)
    try:
        await websocket.send_json(message.model_dump())
        return True
    except WebSocketDisconnect:
        unregister_client(websocket)
        return False
    except Exception as error:
        if _is_expected_close_error(error):
            unregister_client(websocket)
            return False
        raise


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections and keep them alive for scheduler broadcasts."""
    await websocket.accept()
    register_client(websocket)

    try:
        if not await send_heartbeat(websocket, status="connected"):
            return

        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
            if not await send_heartbeat(websocket):
                logger.info("WebSocket client disconnected")
                break
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception:
        logger.exception("WebSocket connection failed")
    finally:
        unregister_client(websocket)
