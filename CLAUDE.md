# CLAUDE.md

## Project Overview

Swarm Orchestrator is a Docker Swarm management app for a 3-node local network cluster (mini2 manager, spark1/rog1 workers). It provides a web UI, REST API, and MCP server for deploying, monitoring, and cataloging swarm services.

## Architecture

- **Backend**: FastAPI (Python 3.12) in `backend/` — talks to Docker via socket, stores catalog in SQLite
- **Frontend**: React 19 + Vite + TypeScript + Tailwind v4 in `frontend/` — SPA with TanStack Query
- **MCP**: `backend/mcp_server.py` — 8 tools via FastMCP for AI agent integration (stdio transport)
- **Deployment**: Runs as Swarm service `orchestrator_app` on the manager node, serves frontend as static files via SPA catch-all route

## Key Files

- `backend/main.py` — FastAPI app entry point with lifespan (DB init, health monitor), SPA routing
- `backend/mcp_server.py` — Standalone MCP server with 8 tools, runs via `python -m backend.mcp_server`
- `backend/services/docker_client.py` — `SwarmClient` class wrapping Docker SDK, singleton `swarm_client`
- `backend/services/catalog.py` — async SQLite CRUD for the service catalog
- `backend/services/health_monitor.py` — background task syncing swarm state to catalog
- `backend/services/registry_client.py` — HTTP client for Docker Registry v2 API
- `backend/config.py` — `Settings` via pydantic-settings, singleton `settings`
- `frontend/src/hooks/useApi.ts` — all TanStack Query hooks
- `docker-compose.prod.yml` — Swarm stack definition (service name: `app`)

## Swarm Cluster

| Node | IP | Role | Arch | Special |
|------|----|------|------|---------|
| mini2 | 192.168.1.215 | Manager | x86_64 | Portainer, Immich, registry:5000 |
| spark1 | 192.168.1.176 | Worker | aarch64 | NVIDIA GPU, 20 CPUs, 120GB RAM |
| rog1 | - | Worker | x86_64 | - |

Private registry at `192.168.1.215:5000` (HTTP, requires insecure-registries config). Images must use IP address (not hostname) in service definitions.

## Python Environment

Always use the `swarm-orchestrator` conda environment for Python/pip commands:

```sh
# Activate
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

# Docker build + push (must target linux/amd64 for mini2)
docker buildx build --platform linux/amd64 \
  -t 192.168.1.215:5000/swarm-orchestrator:latest --push .

# Deploy stack to swarm (on mini2)
scp docker-compose.prod.yml andrew@mini2:~/swarm-orchestrator-stack.yml
# then on mini2:
docker stack deploy -c ~/swarm-orchestrator-stack.yml orchestrator

# Update running service after new image push (on mini2)
docker service update --force orchestrator_app

# Full redeploy if stack config changed (on mini2)
docker stack rm orchestrator && sleep 5
docker stack deploy -c ~/swarm-orchestrator-stack.yml orchestrator

# Run MCP server standalone (stdio)
conda run -n swarm-orchestrator python -m backend.mcp_server

# Deploy helper (build, deploy, remove, start, stop, etc.)
./deploy.sh <command>   # run ./deploy.sh for usage
```

## API Notes

- `/api/services` — catalog services (from SQLite)
- `/api/services/live` — live swarm services (from Docker API directly)
- The Services page in the frontend shows both sections
- The Dashboard health endpoint also queries Docker directly for node/service counts

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
- Images must be built with `--platform linux/amd64` since dev machine (Mac) is ARM
