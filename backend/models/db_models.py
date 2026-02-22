from __future__ import annotations

import json
from datetime import datetime, timezone

from backend.models.schemas import CatalogService, ServiceDefinition, ServiceStatus


def row_to_catalog_service(row: dict) -> CatalogService:
    return CatalogService(
        name=row["name"],
        description=row.get("description", ""),
        definition=ServiceDefinition(**json.loads(row["definition"])),
        status=ServiceStatus(row.get("status", "registered")),
        swarm_id=row.get("swarm_id"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def catalog_service_to_row(svc: CatalogService) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "name": svc.name,
        "description": svc.description,
        "definition": svc.definition.model_dump_json(),
        "status": svc.status.value,
        "swarm_id": svc.swarm_id,
        "created_at": svc.created_at or now,
        "updated_at": now,
    }
