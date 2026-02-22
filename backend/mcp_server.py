"""MCP server exposing Swarm Orchestrator tools for AI agents."""
from __future__ import annotations

import asyncio
import json

from mcp.server.fastmcp import FastMCP

from backend.database import init_db
from backend.models.schemas import ServiceCreate, ServiceDefinition
from backend.services import catalog
from backend.services.docker_client import swarm_client
from backend.services.registry_client import registry_client

mcp = FastMCP("swarm-orchestrator", instructions="Docker Swarm management tools")


@mcp.tool()
async def list_services() -> str:
    """List all services in the catalog with their current status."""
    services = await catalog.list_services()
    return json.dumps([s.model_dump(mode="json") for s in services], indent=2)


@mcp.tool()
async def deploy_service(name: str, image: str, replicas: int = 1, ports: list[str] | None = None) -> str:
    """Deploy a service to the swarm. Creates it in the catalog if it doesn't exist."""
    existing = await catalog.get_service(name)
    if not existing:
        defn = ServiceDefinition(image=image, replicas=replicas, ports=ports or [])
        await catalog.create_service(ServiceCreate(name=name, definition=defn))
        existing = await catalog.get_service(name)

    swarm_id = swarm_client.deploy_service(name, existing.definition)
    return json.dumps({"status": "deployed", "name": name, "swarm_id": swarm_id})


@mcp.tool()
async def stop_service(name: str) -> str:
    """Stop a running service by removing it from the swarm."""
    success = swarm_client.remove_service(name)
    return json.dumps({"status": "stopped" if success else "failed", "name": name})


@mcp.tool()
async def scale_service(name: str, replicas: int) -> str:
    """Scale a service to the specified number of replicas."""
    success = swarm_client.scale_service(name, replicas)
    return json.dumps({"status": "scaled" if success else "failed", "name": name, "replicas": replicas})


@mcp.tool()
async def get_service_logs(name: str, tail: int = 100) -> str:
    """Get recent logs from a running service."""
    logs = swarm_client.get_service_logs(name, tail=tail)
    return logs


@mcp.tool()
async def list_nodes() -> str:
    """List all nodes in the Docker Swarm cluster."""
    nodes = swarm_client.list_nodes()
    return json.dumps([n.model_dump(mode="json") for n in nodes], indent=2)


@mcp.tool()
async def get_health() -> str:
    """Get overall cluster health status."""
    errors = []
    nodes = []
    service_count = 0
    try:
        nodes = swarm_client.list_nodes()
    except Exception as e:
        errors.append(str(e))
    try:
        service_count = len(swarm_client.list_services())
    except Exception as e:
        errors.append(str(e))
    return json.dumps({
        "status": "healthy" if not errors else "degraded",
        "node_count": len(nodes),
        "service_count": service_count,
        "errors": errors,
    }, indent=2)


@mcp.tool()
async def get_registry_images() -> str:
    """List all images in the private registry."""
    repos = await registry_client.list_repositories()
    result = []
    for repo in repos:
        tags = await registry_client.list_tags(repo)
        result.append({"name": repo, "tags": tags})
    return json.dumps(result, indent=2)


async def main():
    await init_db()
    await mcp.run_stdio_async()


if __name__ == "__main__":
    asyncio.run(main())
