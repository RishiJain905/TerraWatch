import asyncio
from datetime import datetime

from fastapi import APIRouter, WebSocket

router = APIRouter()

connected_clients: list[WebSocket] = []


async def broadcast(message: dict):
    """Broadcast a message to all connected WebSocket clients."""
    for client in connected_clients[:]:
        try:
            await client.send_json(message)
        except Exception:
            connected_clients.remove(client)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections and send periodic heartbeat."""
    await websocket.accept()
    connected_clients.append(websocket)

    try:
        await websocket.send_json(
            {
                "type": "heartbeat",
                "data": {"timestamp": datetime.utcnow().isoformat(), "status": "connected"},
            }
        )

        while True:
            await asyncio.sleep(10)
            await websocket.send_json(
                {
                    "type": "heartbeat",
                    "data": {"timestamp": datetime.utcnow().isoformat()},
                }
            )
    except Exception:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
