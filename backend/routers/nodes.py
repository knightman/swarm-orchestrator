from fastapi import APIRouter, HTTPException

from backend.models.schemas import SwarmNode
from backend.services.docker_client import swarm_client

router = APIRouter(prefix="/api/nodes", tags=["nodes"])


@router.get("", response_model=list[SwarmNode])
async def list_nodes():
    try:
        return swarm_client.list_nodes()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Cannot reach Docker: {e}")


@router.get("/{node_id}", response_model=SwarmNode)
async def get_node(node_id: str):
    node = swarm_client.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.post("/{node_id}/drain")
async def drain_node(node_id: str):
    if not swarm_client.drain_node(node_id):
        raise HTTPException(status_code=500, detail="Failed to drain node")
    return {"status": "draining", "node_id": node_id}


@router.post("/{node_id}/activate")
async def activate_node(node_id: str):
    if not swarm_client.activate_node(node_id):
        raise HTTPException(status_code=500, detail="Failed to activate node")
    return {"status": "active", "node_id": node_id}
