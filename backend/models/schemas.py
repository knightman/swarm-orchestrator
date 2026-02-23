from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


# --- Enums ---

class ServiceStatus(StrEnum):
    REGISTERED = "registered"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"


class NodeStatus(StrEnum):
    READY = "ready"
    DOWN = "down"
    DISCONNECTED = "disconnected"
    UNKNOWN = "unknown"


class NodeAvailability(StrEnum):
    ACTIVE = "active"
    PAUSE = "pause"
    DRAIN = "drain"


# --- Service ---

class ServiceDefinition(BaseModel):
    image: str
    replicas: int = 1
    ports: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    labels: dict[str, str] = Field(default_factory=dict)
    networks: list[str] = Field(default_factory=list)
    mounts: list[str] = Field(default_factory=list)
    command: str | None = None


class CatalogService(BaseModel):
    name: str
    description: str = ""
    definition: ServiceDefinition
    status: ServiceStatus = ServiceStatus.REGISTERED
    swarm_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ServiceCreate(BaseModel):
    name: str
    description: str = ""
    definition: ServiceDefinition


class ServiceUpdate(BaseModel):
    description: str | None = None
    definition: ServiceDefinition | None = None


class ScaleRequest(BaseModel):
    replicas: int = Field(ge=0, le=100)


# --- Node ---

class SwarmNode(BaseModel):
    id: str
    hostname: str
    role: str
    status: NodeStatus
    availability: NodeAvailability
    addr: str
    platform_os: str = ""
    platform_arch: str = ""
    engine_version: str = ""
    labels: dict[str, str] = Field(default_factory=dict)
    resources: dict[str, Any] = Field(default_factory=dict)


# --- Health ---

class HealthStatus(BaseModel):
    status: str
    version: str = "0.1.0"


class ClusterHealth(BaseModel):
    status: str
    swarm_id: str = ""
    node_count: int = 0
    service_count: int = 0
    nodes: list[SwarmNode] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


# --- Registry ---

class RegistryRepository(BaseModel):
    name: str
    tags: list[str] = Field(default_factory=list)


class TagDetail(BaseModel):
    tag: str
    digest: str
    media_type: str = ""
    size: int = 0
    architecture: str = ""
    os: str = ""
    created: str = ""


class RegistryRepositoryDetail(BaseModel):
    name: str
    tags: list[TagDetail] = Field(default_factory=list)
    tag_count: int = 0


# --- Swarm Service (live state from Docker) ---

class SwarmService(BaseModel):
    id: str
    name: str
    image: str
    replicas: int = 0
    running_replicas: int = 0
    ports: list[str] = Field(default_factory=list)
    created_at: str = ""
