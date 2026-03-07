from fastapi import APIRouter, HTTPException

from backend.models.schemas import SwarmStack
from backend.services.docker_client import swarm_client

router = APIRouter(prefix="/api/stacks", tags=["stacks"])


@router.get("", response_model=list[SwarmStack])
async def list_stacks():
    try:
        return swarm_client.list_stacks()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Cannot reach Docker: {e}")
