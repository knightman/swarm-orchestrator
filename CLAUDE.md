# CLAUDE.md

## Project Overview

Swarm Orchestrator is a Docker Swarm management app for local network clusters. It provides a web UI, REST API, and MCP server for deploying, monitoring, and cataloging swarm services.

## Architecture

- **Backend**: FastAPI (Python 3.12) in `backend/` — talks to Docker via socket, stores catalog in SQLite
- **Frontend**: React 19 + Vite + TypeScript + Tailwind v4 in `frontend/` — SPA with TanStack Query
- **MCP**: `backend/mcp_server.py` — 8 tools via FastMCP for AI agent integration (stdio transport)
- **Deployment**: Runs as Swarm service `orchestrator_app` on the manager node, serves frontend as static files via SPA catch-all route

## Configuration

All environment-specific values (IPs, hostnames, paths) are stored in `.env` (gitignored). See `.env.example` for the full list. Run `./setup.sh` for interactive first-time setup.

Key variables used across the project:
- `SWARM_MANAGER_SSH` — SSH target for the manager node (used by `deploy.sh`)
- `REGISTRY_HOST` — private registry address, e.g. `192.168.1.100:5000` (used by `deploy.sh`, `docker-compose.prod.yml`)
- `APP_PORT` — orchestrator port (default 8080)
- `PROJECTS_HOST_PATH` — host dir mounted as `/projects` in the container
- Backend settings (`REGISTRY_URL`, `DATABASE_PATH`, etc.) are read by pydantic-settings in `backend/config.py`

## Key Files

- `backend/main.py` — FastAPI app entry point with lifespan (DB init, health monitor), SPA routing
- `backend/mcp_server.py` — Standalone MCP server with 8 tools, runs via `python -m backend.mcp_server`
- `backend/services/docker_client.py` — `SwarmClient` class wrapping Docker SDK, singleton `swarm_client`
- `backend/services/catalog.py` — async SQLite CRUD for the service catalog
- `backend/services/health_monitor.py` — background task syncing swarm state to catalog
- `backend/services/registry_client.py` — HTTP client for Docker Registry v2 API
- `backend/routers/projects.py` — `GET /api/projects` lists subdirs of `settings.projects_path`
- `backend/config.py` — `Settings` via pydantic-settings, singleton `settings`; reads `.env` automatically
- `frontend/src/hooks/useApi.ts` — all TanStack Query hooks
- `docker-compose.prod.yml` — Swarm stack definition (uses `${VAR}` substitution from `.env`)
- `deploy.sh` — build/deploy helper (sources `.env` for `SWARM_MANAGER_SSH` and `REGISTRY_HOST`)

## Python Environment

Always use the `swarm-orchestrator` conda environment for Python/pip commands:

```sh
conda activate swarm-orchestrator
# Or prefix commands
conda run -n swarm-orchestrator <command>
```

Never run bare `pip` or `python` outside of this conda env.

## Commands

```sh
# Backend dev
conda run -n swarm-orchestrator pip install -e .
conda run -n swarm-orchestrator uvicorn backend.main:app --reload --port 8080

# Frontend dev
cd frontend && npm run dev

# TypeScript check
cd frontend && npx tsc --noEmit

# Frontend build
cd frontend && npm run build

# Build + deploy (uses .env for registry and manager host)
./deploy.sh build      # Build linux/amd64 image and push to registry
./deploy.sh deploy     # SCP compose file to manager and deploy stack
./deploy.sh update     # Force-update running service after image push
./deploy.sh redeploy   # Full cycle: build, remove, deploy

# Run MCP server standalone (stdio)
conda run -n swarm-orchestrator python -m backend.mcp_server
```

## API Notes

- `/api/services` — catalog services (from SQLite)
- `/api/services/live` — live swarm services (from Docker API directly)
- `/api/projects` — lists subdirectories of `PROJECTS_DIR` (container path, mapped from `PROJECTS_HOST_PATH` on manager)
- The Services page in the frontend shows both Swarm Services (live) and Catalog sections
- The Dashboard health endpoint also queries Docker directly for node/service counts
- Service status: `running` = replicas up, `stopped` = tasks completed cleanly (exit 0), `failed` = tasks crashed/rejected

## MCP Tools

8 tools exposed via FastMCP stdio transport:
`list_services`, `deploy_service`, `stop_service`, `scale_service`, `get_service_logs`, `list_nodes`, `get_health`, `get_registry_images`

MCP server initializes its own DB connection and Docker client. It shares the same `backend.services` modules as the FastAPI app.

## Conventions

- Backend uses async throughout (aiosqlite, httpx)
- Docker SDK calls are synchronous (Docker SDK limitation) — wrapped in `SwarmClient`
- Each router file maps to one API resource (`/api/services`, `/api/nodes`, etc.)
- Static routes: `/live` must come before `/{name}` in router to avoid path param capture
- Frontend uses file-per-component, hooks in `hooks/`, API types in `api/types.ts`
- Tailwind v4 (CSS import only, no config file)
- Service definitions can be YAML files in `definitions/` or created via API
- Status syncing happens in `health_monitor.py` on a configurable interval (default 30s)
- `SwarmService.completed_replicas` counts tasks in `complete` state — used to distinguish stopped from failed
- Images must be built with `--platform linux/amd64` if deploying to x86_64 manager nodes (e.g. from an ARM dev machine)
- Bind mounts for service output dirs must be pre-created on the target node before deploying (Docker Swarm does not auto-create host dirs for bind mounts)
- Private registry uses HTTP — all Docker daemons must have it in `insecure-registries`
- For GPU workloads, the target node needs `nvidia-container-runtime` and `default-runtime: nvidia` in `daemon.json`
- For X11 display services, set `DISPLAY`, mount X11 socket and Xauthority, and run `xhost +local:` on the display node
