from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.database import init_db
from backend.routers import health, nodes, projects, registry, services
from backend.services.docker_client import swarm_client
from backend.services.health_monitor import health_monitor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting swarm-orchestrator")
    await init_db()
    await health_monitor.start()
    yield
    await health_monitor.stop()
    swarm_client.close()
    logger.info("Swarm-orchestrator stopped")


app = FastAPI(title="Swarm Orchestrator", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(nodes.router)
app.include_router(services.router)
app.include_router(registry.router)
app.include_router(projects.router)

# Serve frontend static files if the dist directory exists
_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="assets")

    @app.get("/{path:path}")
    async def serve_spa(request: Request, path: str):
        # Serve the file if it exists, otherwise return index.html for SPA routing
        file_path = _frontend_dist / path
        if path and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_frontend_dist / "index.html")
