from fastapi import APIRouter, HTTPException

from backend.models.schemas import RegistryRepository, RegistryRepositoryDetail, TagDetail
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


@router.get("/repositories/{name:path}/details", response_model=RegistryRepositoryDetail)
async def get_repository_details(name: str):
    tags = await registry_client.list_tags(name)
    tag_details: list[TagDetail] = []
    for tag in tags:
        manifest = await registry_client.get_manifest(name, tag)
        config_info: dict = {"created": "", "architecture": "", "os": ""}
        if manifest.get("config_digest"):
            config_info = await registry_client.get_image_config(name, manifest["config_digest"])
        tag_details.append(TagDetail(
            tag=tag,
            digest=manifest.get("digest", ""),
            media_type=manifest.get("media_type", ""),
            size=manifest.get("size", 0),
            architecture=config_info.get("architecture", ""),
            os=config_info.get("os", ""),
            created=config_info.get("created", ""),
        ))
    return RegistryRepositoryDetail(name=name, tags=tag_details, tag_count=len(tag_details))


@router.delete("/repositories/{name:path}/tags/{tag}")
async def delete_tag(name: str, tag: str):
    manifest = await registry_client.get_manifest(name, tag)
    digest = manifest.get("digest")
    if not digest:
        raise HTTPException(status_code=404, detail=f"Tag '{tag}' not found in '{name}'")
    success = await registry_client.delete_manifest(name, digest)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete manifest. Is REGISTRY_STORAGE_DELETE_ENABLED=true?")
    return {"deleted": True}
