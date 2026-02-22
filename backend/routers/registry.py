from fastapi import APIRouter

from backend.models.schemas import RegistryRepository
from backend.services.registry_client import registry_client

router = APIRouter(prefix="/api/registry", tags=["registry"])


@router.get("/repositories", response_model=list[RegistryRepository])
async def list_repositories():
    repos = await registry_client.list_repositories()
    return [RegistryRepository(name=r) for r in repos]


@router.get("/repositories/{name:path}/tags")
async def list_tags(name: str):
    tags = await registry_client.list_tags(name)
    return {"name": name, "tags": tags}
