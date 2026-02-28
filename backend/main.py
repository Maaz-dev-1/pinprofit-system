"""
PinProfit — Main FastAPI Application
Affiliate Marketing + Pinterest Publishing System
"""
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from models.database import init_db
from routers import dashboard, research, products, publisher, analytics, evolution, settings_router
from services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Active WebSocket connections for research progress
research_ws_connections: dict[int, list[WebSocket]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown."""
    logger.info("PinProfit backend starting up...")

    # Initialize Supabase connection + seed defaults
    await init_db()
    logger.info("Database initialized.")

    await start_scheduler()
    logger.info("Scheduler started.")

    yield

    logger.info("PinProfit shutting down...")
    await stop_scheduler()


app = FastAPI(
    title="PinProfit API",
    description="Affiliate Marketing + Pinterest Publishing System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — needed for Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routes ─────────────────────────────────
app.include_router(dashboard.router,         prefix="/api/dashboard",  tags=["Dashboard"])
app.include_router(research.router,          prefix="/api/research",   tags=["Research"])
app.include_router(products.router,          prefix="/api/products",   tags=["Products"])
app.include_router(publisher.router,         prefix="/api/pins",       tags=["Publisher"])
app.include_router(analytics.router,         prefix="/api/analytics",  tags=["Analytics"])
app.include_router(evolution.router,         prefix="/api/evolution",  tags=["Evolution"])
app.include_router(settings_router.router,   prefix="/api/settings",   tags=["Settings"])


# ── Health Check ───────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "PinProfit"}


# ── WebSocket — Research Progress ─────────────
@app.websocket("/ws/research/{session_id}")
async def research_websocket(websocket: WebSocket, session_id: int):
    await websocket.accept()
    if session_id not in research_ws_connections:
        research_ws_connections[session_id] = []
    research_ws_connections[session_id].append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        research_ws_connections[session_id].remove(websocket)


# ── Serve React SPA ───────────────────────────
# Check frontend dist dir (Render: ../frontend/dist, local: static/)
static_dir = Path(__file__).parent.parent / "frontend" / "dist"
if not static_dir.exists():
    static_dir = Path(__file__).parent / "static"

if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        index = static_dir / "index.html"
        return FileResponse(index)
