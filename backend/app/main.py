from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import websocket
from app.api.routes import events, metadata, planes, ships
from app.core.database import init_db

app = FastAPI(
    title="TerraWatch API",
    description="Real-time GEOINT platform API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(planes.router)
app.include_router(ships.router)
app.include_router(events.router)
app.include_router(metadata.router)
app.include_router(websocket.router)


@app.on_event("startup")
async def startup_event():
    await init_db()


@app.get("/")
async def root():
    return {"message": "TerraWatch API", "docs": "/docs"}
