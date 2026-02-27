from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.config import settings
from backend.models.schemas import ProjectFolder

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectFolder])
def list_projects():
    path = settings.projects_path
    if not path.exists():
        raise HTTPException(status_code=503, detail=f"Projects directory not found: {path}")
    folders = []
    for entry in sorted(path.iterdir()):
        if entry.is_dir() and not entry.name.startswith("."):
            folders.append(ProjectFolder(
                name=entry.name,
                has_dockerfile=(entry / "Dockerfile").exists(),
                has_compose=(entry / "docker-compose.yml").exists(),
            ))
    return folders
