from fastapi import APIRouter

from backend.models.schemas import ClusterHealth, HealthStatus
from backend.services.docker_client import swarm_client

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthStatus)
async def health_check():
    return HealthStatus(status="ok")


@router.get("/detailed", response_model=ClusterHealth)
async def detailed_health():
    errors: list[str] = []
    nodes = []
    service_count = 0
    swarm_id = ""

    try:
        nodes = swarm_client.list_nodes()
    except Exception as e:
        errors.append(f"Failed to list nodes: {e}")

    try:
        services = swarm_client.list_services()
        service_count = len(services)
    except Exception as e:
        errors.append(f"Failed to list services: {e}")

    try:
        swarm_id = swarm_client.get_swarm_id()
    except Exception as e:
        errors.append(f"Failed to get swarm ID: {e}")

    status = "healthy" if not errors else "degraded"
    return ClusterHealth(
        status=status,
        swarm_id=swarm_id,
        node_count=len(nodes),
        service_count=service_count,
        nodes=nodes,
        errors=errors,
    )
