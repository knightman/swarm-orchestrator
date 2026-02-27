# Swarm Orchestrator

A management application for Docker Swarm clusters. Provides a web dashboard, REST API, and MCP interface for deploying, monitoring, and cataloging services across the swarm.

## Tech Stack

- **Backend**: Python 3.12, FastAPI, Docker SDK, aiosqlite, Pydantic v2
- **Frontend**: React 19, Vite, TypeScript, TanStack Query, Tailwind v4, Lucide icons
- **MCP**: Python `mcp` SDK with FastMCP (8 tools for AI agent integration)
- **Storage**: SQLite (service catalog metadata) + YAML (service definitions)
- **Deployment**: Multi-stage Dockerfile, runs as a Swarm service on the manager node

## Quick Start

```sh
# 1. Clone and run setup
git clone <repo-url>
cd swarm-orchestrator
./setup.sh          # Interactive — creates .env and .mcp.json

# 2. Install backend
conda create -n swarm-orchestrator python=3.12 -y
conda run -n swarm-orchestrator pip install -e ".[dev]"

# 3. Install frontend
cd frontend && npm install && cd ..

# 4. Run locally
conda run -n swarm-orchestrator uvicorn backend.main:app --reload --port 8080
cd frontend && npm run dev

# 5. Build and deploy to swarm
./deploy.sh build    # Build image and push to registry
./deploy.sh deploy   # Deploy stack to swarm manager
```

## Configuration

All environment-specific values are stored in a single `.env` file (gitignored). Run `./setup.sh` for interactive setup, or copy `.env.example` and fill in your values.

| Variable | Used By | Description |
|----------|---------|-------------|
| `SWARM_MANAGER_SSH` | `deploy.sh` | SSH target for manager, e.g. `user@manager-host` |
| `REGISTRY_HOST` | `deploy.sh`, compose | Registry address, e.g. `192.168.1.100:5000` |
| `APP_PORT` | compose | Host port for the orchestrator (default `8080`) |
| `PROJECTS_HOST_PATH` | compose | Host dir mounted as `/projects` in container |
| `REGISTRY_URL` | backend | Full registry URL, e.g. `http://192.168.1.100:5000` |
| `DOCKER_HOST` | backend | Docker socket path |
| `DATABASE_PATH` | backend | SQLite database location |
| `DEFINITIONS_DIR` | backend | Service definition YAML directory |
| `PROJECTS_DIR` | backend | Container-side projects mount point |
| `HEALTH_CHECK_INTERVAL` | backend | Seconds between health sync cycles |

## Project Structure

```
backend/
  main.py              # FastAPI app, lifespan, SPA routing, router wiring
  config.py            # pydantic-settings configuration (reads .env)
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
    projects.py        # Projects directory listing
  services/
    docker_client.py   # Docker SDK wrapper (SwarmClient)
    catalog.py         # Service catalog (SQLite + YAML)
    health_monitor.py  # Background health poller
    registry_client.py # Registry HTTP API client
    builder.py         # Docker image build + push via SDK
frontend/
  src/
    pages/             # Dashboard, Services, Nodes, Registry, Projects
    components/        # Layout, Sidebar, StatusBadge, NodeCard, ServiceRow
    hooks/useApi.ts    # TanStack Query hooks
    api/               # Fetch client + TypeScript types
definitions/
  examples/            # Example YAML service definitions
deploy.sh              # Deployment helper script (sources .env)
setup.sh               # Interactive first-time setup
.env.example           # Template for environment variables
.mcp.json.example      # Template for MCP server config
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
| POST | `/api/services/{name}/build` | Build image from `build_context` and push to registry |
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
| GET | `/api/projects` | List project folders in `PROJECTS_DIR` |

## MCP Server

The MCP server exposes 8 tools for AI agent integration via the stdio transport.

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

```sh
conda run -n swarm-orchestrator python -m backend.mcp_server
```

### Claude Code / Claude Desktop

Copy `.mcp.json.example` to `.mcp.json` and edit paths to match your local environment. Claude Code auto-detects `.mcp.json` in the project root.

## Deployment

### Deploy Helper Script

`deploy.sh` sources `.env` for `SWARM_MANAGER_SSH` and `REGISTRY_HOST`:

```sh
./deploy.sh build       # Build linux/amd64 image and push to private registry
./deploy.sh deploy      # SCP compose file to manager and deploy the stack
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

Images must target the manager node's architecture. For example, if deploying from an ARM Mac to an x86_64 manager:

```sh
docker buildx build --platform linux/amd64 \
  -t ${REGISTRY_HOST}/swarm-orchestrator:latest \
  --push .
```

#### Deploy to Swarm

```sh
# Copy stack file to manager
scp docker-compose.prod.yml ${SWARM_MANAGER_SSH}:~/swarm-orchestrator-stack.yml

# On the manager node
docker stack deploy -c ~/swarm-orchestrator-stack.yml orchestrator
```

Update after a new image push:

```sh
docker service update --force orchestrator_app
```

## Service Definitions

Service definitions are YAML files in `definitions/`. See `definitions/examples/hello-world.yaml` for the schema. Custom definitions are gitignored — each environment creates its own.

### Definition Schema

```yaml
name: my-service
image: registry:5000/my-image:latest
replicas: 1
ports:
  - "8080:80"
env:
  KEY: value
constraints:
  - node.hostname == my-node
labels: {}
networks: []
mounts:
  - /host/path:/container/path
```

### Build & Deploy Workflow

```
DEV MACHINE
  docker buildx build --platform linux/amd64 \
    -t ${REGISTRY_HOST}/myapp:latest --push .
      │
      ▼
PRIVATE REGISTRY (on manager)
  ${REGISTRY_HOST}/myapp:latest
      │
      ▼
SWARM MANAGER
  docker stack deploy → distributes across nodes
```

### Building via the Orchestrator API

```sh
# 1. Upload project to the manager's projects directory
rsync -av --exclude='.git' ./my-project/ ${SWARM_MANAGER_SSH}:${PROJECTS_HOST_PATH}/my-project/

# 2. Register in catalog
curl -X POST http://${MANAGER_HOST}:${APP_PORT}/api/services \
  -H 'Content-Type: application/json' \
  -d '{"name": "my-project", "definition": {"image": "${REGISTRY_HOST}/my-project:latest", "build_context": "my-project", ...}}'

# 3. Build and deploy
curl -X POST http://${MANAGER_HOST}:${APP_PORT}/api/services/my-project/build
curl -X POST http://${MANAGER_HOST}:${APP_PORT}/api/services/my-project/deploy
```

### Batch Jobs vs Long-Running Services

- **Long-running service**: should never exit — swarm restarts on failure
- **Batch job**: exits with code 0 on success — task state becomes `Complete`

The UI distinguishes these: `complete` state = **stopped** (gray), non-zero exit = **failed** (red).

For batch jobs that produce output, use bind mounts and pre-create the output directory on the target node.

## Swarm Setup Notes

### Private Registry

The registry uses HTTP. All Docker daemons must configure it as an insecure registry in `/etc/docker/daemon.json`:

```json
{
  "insecure-registries": ["<your-registry-ip>:5000"]
}
```

Then restart Docker. If the node already has a `daemon.json` (e.g. with NVIDIA runtime), merge the `insecure-registries` key — don't replace the file.

### GPU Services

To deploy GPU workloads to a node with NVIDIA GPUs:

1. Install `nvidia-container-runtime` on the node
2. Set `"default-runtime": "nvidia"` in the node's `daemon.json`
3. Use `NVIDIA_VISIBLE_DEVICES=all` in the service env
4. Constrain to the GPU node: `node.hostname == <gpu-node>`
5. For PyTorch: add a tmpfs mount at `/dev/shm` (4GB+ recommended)

Images for ARM GPU nodes (e.g. Jetson, aarch64) must be built for `linux/arm64`.

### X11 Display Services

For services that render to a node's physical display:

1. Run `DISPLAY=:<N> xhost +local:` on the display node
2. Set env: `DISPLAY=:<N>`, `XAUTHORITY=/tmp/.Xauthority`
3. Use `networks: [host]`
4. Mount: `/tmp/.X11-unix:/tmp/.X11-unix` and the Xauthority file

### Key Rules

1. **Never use `build:` in stack files** — Swarm ignores it. Build separately and push.
2. **Pin architecture at build time** — `docker buildx build --platform linux/amd64 ...`
3. **Use IP addresses for the registry** — hostname resolution isn't guaranteed across all nodes.
4. **Force-update when using `:latest`** — `docker service update --force ...`
5. **One stack per logical application** — deploy and remove independently.
6. **Pre-create bind mount directories** — Swarm doesn't auto-create host dirs.
