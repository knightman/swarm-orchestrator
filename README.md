# Swarm Orchestrator

A custom management application for a 3-node Docker Swarm cluster. Provides a web dashboard, REST API, and MCP interface for deploying, monitoring, and cataloging services across the swarm.

## Cluster

| Node | Role | Arch | IP | Notes |
|------|------|------|----|-------|
| mini2 | Manager | x86_64 | 192.168.1.215 | Also runs Portainer CE, Immich |
| spark1 | Worker | aarch64 | 192.168.1.176 | NVIDIA GPU, 20 CPUs, 120GB RAM |
| rog1 | Worker | x86_64 | - | - |

A private registry runs on the manager at `192.168.1.215:5000` (Docker Registry v2).

## Tech Stack

- **Backend**: Python 3.12, FastAPI, Docker SDK, aiosqlite, Pydantic v2
- **Frontend**: React 19, Vite, TypeScript, TanStack Query, Tailwind v4, Lucide icons
- **MCP**: Python `mcp` SDK with FastMCP (8 tools for AI agent integration)
- **Storage**: SQLite (service catalog metadata) + YAML (service definitions)
- **Deployment**: Multi-stage Dockerfile, runs as a Swarm service on the manager node

## Project Structure

```
backend/
  main.py              # FastAPI app, lifespan, SPA routing, router wiring
  config.py            # pydantic-settings configuration
  database.py          # SQLite init + helpers
  mcp_server.py        # MCP tools (standalone stdio server)
  models/
    schemas.py         # Pydantic models (API + DB)
    db_models.py       # Row <-> model mappers
  routers/
    health.py          # GET /api/health, /api/health/detailed
    nodes.py           # Node list, drain, activate
    services.py        # Service CRUD, deploy, stop, scale, logs, live
    registry.py        # Registry image browser
  services/
    docker_client.py   # Docker SDK wrapper (SwarmClient)
    catalog.py         # Service catalog (SQLite + YAML)
    health_monitor.py  # Background health poller
    registry_client.py # Registry HTTP API client
frontend/
  src/
    pages/             # Dashboard, Services, Nodes, Registry
    components/        # Layout, Sidebar, StatusBadge, NodeCard, ServiceRow
    hooks/useApi.ts    # TanStack Query hooks
    api/               # Fetch client + TypeScript types
definitions/
  examples/            # YAML service definitions
deploy.sh              # Deployment helper script
.mcp.json              # Claude Code MCP server config
```

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Liveness check |
| GET | `/api/health/detailed` | Full cluster health with node details |
| GET | `/api/services` | List catalog services |
| GET | `/api/services/live` | List services currently running in swarm |
| GET | `/api/services/{name}` | Get single catalog service |
| POST | `/api/services` | Register service in catalog |
| PUT | `/api/services/{name}` | Update service definition |
| DELETE | `/api/services/{name}` | Remove from catalog |
| POST | `/api/services/{name}/deploy` | Deploy to swarm |
| POST | `/api/services/{name}/stop` | Remove from swarm |
| POST | `/api/services/{name}/scale` | Scale replicas |
| GET | `/api/services/{name}/logs` | Service logs |
| GET | `/api/nodes` | List swarm nodes |
| GET | `/api/nodes/{id}` | Node details |
| POST | `/api/nodes/{id}/drain` | Drain node |
| POST | `/api/nodes/{id}/activate` | Activate node |
| GET | `/api/registry/repositories` | List registry images |
| GET | `/api/registry/repositories/{name}/tags` | Image tags |

## MCP Server

The MCP server exposes 8 tools for AI agent integration via the stdio transport. It uses the official Python `mcp` SDK with `FastMCP`.

### Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `list_services` | — | List all services in the catalog with current status |
| `deploy_service` | `name`, `image`, `replicas?`, `ports?` | Deploy a service (auto-creates catalog entry if needed) |
| `stop_service` | `name` | Stop a running service by removing it from the swarm |
| `scale_service` | `name`, `replicas` | Scale a service to N replicas |
| `get_service_logs` | `name`, `tail?` | Get recent logs from a running service |
| `list_nodes` | — | List all nodes in the Docker Swarm cluster |
| `get_health` | — | Get overall cluster health status |
| `get_registry_images` | — | List all images and tags in the private registry |

### Running

Standalone (stdio mode):

```sh
conda run -n swarm-orchestrator python -m backend.mcp_server
```

### Claude Code Configuration

A `.mcp.json` file is included in the project root. Claude Code will automatically detect it when working in this directory. The config uses the conda environment Python binary directly:

```json
{
  "mcpServers": {
    "swarm-orchestrator": {
      "command": "/opt/homebrew/Caskroom/miniconda/base/envs/swarm-orchestrator/bin/python",
      "args": ["-m", "backend.mcp_server"],
      "cwd": "/Users/andrew/CODE/swarm-orchestrator"
    }
  }
}
```

### Claude Desktop Configuration

Add to your Claude Desktop MCP settings (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "swarm-orchestrator": {
      "command": "/opt/homebrew/Caskroom/miniconda/base/envs/swarm-orchestrator/bin/python",
      "args": ["-m", "backend.mcp_server"],
      "cwd": "/path/to/swarm-orchestrator"
    }
  }
}
```

The MCP server requires Docker socket access for swarm operations. Without it, Docker-dependent tools degrade gracefully (returning error details instead of crashing). DB-only tools (catalog operations) work regardless.

## Development

### Python Environment

This project uses a conda environment named `swarm-orchestrator` (Python 3.12). All Python/pip commands must run inside it:

```sh
# Create the environment (first time)
conda create -n swarm-orchestrator python=3.12 -y

# Install dependencies
conda run -n swarm-orchestrator pip install -e ".[dev]"
```

### Backend

```sh
conda run -n swarm-orchestrator uvicorn backend.main:app --reload --port 8080
```

### Frontend

```sh
cd frontend
npm install
npm run dev
```

Vite proxies `/api` requests to `http://localhost:8080`.

## Deployment

### Deploy Helper Script

`deploy.sh` wraps all deployment operations. Run from your dev machine:

```sh
./deploy.sh build       # Build linux/amd64 image and push to private registry
./deploy.sh deploy      # SCP compose file to mini2 and deploy the stack
./deploy.sh update      # Force-update running service (quick refresh after image push)
./deploy.sh redeploy    # Full cycle: build, push, remove stack, wait, redeploy
./deploy.sh remove      # Remove the stack from the swarm
./deploy.sh stop        # Scale service to 0 (pause without removing)
./deploy.sh start       # Scale service back to 1
./deploy.sh logs        # Tail service logs
./deploy.sh status      # Show service and task status
```

### Manual Deployment

#### Build

Images must be built for `linux/amd64` since the manager (mini2) is x86_64:

```sh
docker buildx build --platform linux/amd64 \
  -t 192.168.1.215:5000/swarm-orchestrator:latest \
  --push .
```

#### Local run

```sh
docker compose up
```

#### Deploy to Swarm

First deploy:

```sh
# Copy stack file to manager
scp docker-compose.prod.yml andrew@mini2:~/swarm-orchestrator-stack.yml

# On mini2
docker stack deploy -c ~/swarm-orchestrator-stack.yml orchestrator
```

The stack creates a service named `orchestrator_app` constrained to the manager node.

Update after a new image push:

```sh
# On mini2
docker service update --force orchestrator_app
```

Full redeploy (if stack config changed):

```sh
# On mini2
docker stack rm orchestrator
sleep 5
docker stack deploy -c ~/swarm-orchestrator-stack.yml orchestrator
```

## Registry Setup

The private registry at `192.168.1.215:5000` uses HTTP. All Docker daemons in the swarm (and any dev machine pushing images) must configure it as an insecure registry.

**On Linux nodes** (`/etc/docker/daemon.json`):

```json
{
  "insecure-registries": ["192.168.1.215:5000"]
}
```

Then restart Docker: `sudo systemctl restart docker`

**On macOS with OrbStack** (`~/.orbstack/config/docker.json`):

```json
{
  "insecure-registries": ["192.168.1.215:5000"]
}
```

Then restart: `orb restart docker`

Images must reference the registry by IP in service definitions:

```yaml
image: 192.168.1.215:5000/my-app:latest
```
