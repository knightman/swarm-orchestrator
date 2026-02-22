from __future__ import annotations

import json
import logging
from pathlib import Path

import yaml

from backend.database import get_db
from backend.models.db_models import catalog_service_to_row, row_to_catalog_service
from backend.models.schemas import (
    CatalogService,
    ServiceCreate,
    ServiceDefinition,
    ServiceStatus,
    ServiceUpdate,
)

logger = logging.getLogger(__name__)


async def list_services() -> list[CatalogService]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM catalog_services ORDER BY name")
        rows = await cursor.fetchall()
        return [row_to_catalog_service(dict(r)) for r in rows]
    finally:
        await db.close()


async def get_service(name: str) -> CatalogService | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM catalog_services WHERE name = ?", (name,))
        row = await cursor.fetchone()
        return row_to_catalog_service(dict(row)) if row else None
    finally:
        await db.close()


async def create_service(data: ServiceCreate) -> CatalogService:
    svc = CatalogService(name=data.name, description=data.description, definition=data.definition)
    row = catalog_service_to_row(svc)
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO catalog_services (name, description, definition, status, swarm_id, created_at, updated_at)
               VALUES (:name, :description, :definition, :status, :swarm_id, :created_at, :updated_at)""",
            row,
        )
        await db.commit()
    finally:
        await db.close()
    return svc


async def update_service(name: str, data: ServiceUpdate) -> CatalogService | None:
    existing = await get_service(name)
    if not existing:
        return None
    if data.description is not None:
        existing.description = data.description
    if data.definition is not None:
        existing.definition = data.definition
    row = catalog_service_to_row(existing)
    db = await get_db()
    try:
        await db.execute(
            """UPDATE catalog_services
               SET description=:description, definition=:definition, updated_at=:updated_at
               WHERE name=:name""",
            row,
        )
        await db.commit()
    finally:
        await db.close()
    return existing


async def delete_service(name: str) -> bool:
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM catalog_services WHERE name = ?", (name,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def set_service_status(name: str, status: ServiceStatus, swarm_id: str | None = None) -> None:
    db = await get_db()
    try:
        if swarm_id is not None:
            await db.execute(
                "UPDATE catalog_services SET status=?, swarm_id=? WHERE name=?",
                (status.value, swarm_id, name),
            )
        else:
            await db.execute(
                "UPDATE catalog_services SET status=? WHERE name=?",
                (status.value, name),
            )
        await db.commit()
    finally:
        await db.close()


def load_yaml_definition(path: Path) -> tuple[str, ServiceDefinition]:
    with open(path) as f:
        data = yaml.safe_load(f)
    name = data.pop("name", path.stem)
    return name, ServiceDefinition(**data)
