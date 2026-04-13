from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import websocket
from app.api.routes import conflicts, events, metadata, planes, ships
from app.core.database import close_db, init_db
from app.tasks.schedulers import start_schedulers, stop_schedulers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await start_schedulers()
    yield
    # Shutdown
    await stop_schedulers()
    await close_db()


app = FastAPI(
    title="TerraWatch API",
    description="Real-time GEOINT platform — planes, ships, and world events on a globe",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(metadata.router)
app.include_router(planes.router)
app.include_router(ships.router)
app.include_router(events.router)
app.include_router(conflicts.router)
app.include_router(websocket.router)


@app.get("/")
async def root():
    return {
        "name": "TerraWatch API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
