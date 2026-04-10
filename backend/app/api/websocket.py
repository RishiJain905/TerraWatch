import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.models import WSMessage

router = APIRouter()

connected_clients: list[WebSocket] = []


async def broadcast(message: dict):
    """Broadcast a message to all connected WebSocket clients."""
    for client in connected_clients[:]:
        try:
            await client.send_json(message)
        except Exception:
            if client in connected_clients:
                connected_clients.remove(client)


async def send_heartbeat(websocket: WebSocket, *, status: str | None = None) -> None:
    payload = {}
    if status is not None:
        payload["status"] = status

    message = WSMessage(type="heartbeat", data=payload)
    await websocket.send_json(message.model_dump())


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections and send periodic heartbeat."""
    await websocket.accept()
    connected_clients.append(websocket)

    try:
        await send_heartbeat(websocket, status="connected")

        while True:
            await asyncio.sleep(10)
            await send_heartbeat(websocket)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
