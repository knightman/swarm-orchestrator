from fastapi import APIRouter, HTTPException

from backend.models.schemas import BuildRequest, CatalogService, ScaleRequest, ServiceCreate, ServiceStatus, ServiceUpdate, SwarmService
from backend.services import catalog, builder
from backend.services.docker_client import swarm_client

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("", response_model=list[CatalogService])
async def list_services():
    return await catalog.list_services()


@router.get("/live", response_model=list[SwarmService])
async def list_live_services():
    """List services currently running in the swarm (not from catalog)."""
    try:
        return swarm_client.list_services()
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"Cannot reach Docker: {e}")


@router.get("/{name}", response_model=CatalogService)
async def get_service(name: str):
    svc = await catalog.get_service(name)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    return svc


@router.post("", response_model=CatalogService, status_code=201)
async def create_service(data: ServiceCreate):
    existing = await catalog.get_service(data.name)
    if existing:
        raise HTTPException(status_code=409, detail="Service already exists")
    return await catalog.create_service(data)


@router.put("/{name}", response_model=CatalogService)
async def update_service(name: str, data: ServiceUpdate):
    svc = await catalog.update_service(name, data)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    return svc


@router.delete("/{name}")
async def delete_service(name: str):
    if not await catalog.delete_service(name):
        raise HTTPException(status_code=404, detail="Service not found")
    return {"status": "deleted", "name": name}


@router.post("/{name}/deploy")
async def deploy_service(name: str):
    svc = await catalog.get_service(name)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found in catalog")
    try:
        swarm_id = swarm_client.deploy_service(name, svc.definition)
        await catalog.set_service_status(name, ServiceStatus.RUNNING, swarm_id)
        return {"status": "deployed", "name": name, "swarm_id": swarm_id}
    except Exception as e:
        await catalog.set_service_status(name, ServiceStatus.FAILED)
        raise HTTPException(status_code=500, detail=f"Deploy failed: {e}")


@router.post("/{name}/stop")
async def stop_service(name: str):
    if not swarm_client.remove_service(name):
        raise HTTPException(status_code=500, detail="Failed to stop service")
    await catalog.set_service_status(name, ServiceStatus.STOPPED, None)
    return {"status": "stopped", "name": name}


@router.post("/{name}/scale")
async def scale_service(name: str, req: ScaleRequest):
    if not swarm_client.scale_service(name, req.replicas):
        raise HTTPException(status_code=500, detail="Failed to scale service")
    return {"status": "scaled", "name": name, "replicas": req.replicas}


@router.post("/{name}/build")
async def build_service(name: str, req: BuildRequest = BuildRequest()):
    svc = await catalog.get_service(name)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    if not svc.definition.build_context:
        raise HTTPException(status_code=422, detail="Service has no build_context defined")
    success, logs = await builder.build_and_push(
        svc.definition.build_context,
        svc.definition.image,
        req.platform,
    )
    if not success:
        raise HTTPException(status_code=500, detail=f"Build failed:\n{logs}")
    return {"status": "built", "name": name, "image": svc.definition.image, "logs": logs}


@router.get("/{name}/logs")
async def get_service_logs(name: str, tail: int = 100):
    logs = swarm_client.get_service_logs(name, tail=tail)
    return {"name": name, "logs": logs}
