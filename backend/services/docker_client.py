from __future__ import annotations

import logging
from typing import Any

import docker
from docker.errors import APIError, NotFound
from docker.types import EndpointSpec, Mount, RestartPolicy, ServiceMode

from backend.config import settings
from backend.models.schemas import (
    NodeAvailability,
    NodeStatus,
    ServiceDefinition,
    SwarmNode,
    SwarmService,
)

logger = logging.getLogger(__name__)


class SwarmClient:
    def __init__(self) -> None:
        self._client: docker.DockerClient | None = None

    @property
    def client(self) -> docker.DockerClient:
        if self._client is None:
            self._client = docker.DockerClient(base_url=settings.docker_host)
        return self._client

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    # --- Nodes ---

    def list_nodes(self) -> list[SwarmNode]:
        nodes = []
        for n in self.client.nodes.list():
            attrs = n.attrs or {}
            desc = attrs.get("Description", {})
            status = attrs.get("Status", {})
            spec = attrs.get("Spec", {})
            platform = desc.get("Platform", {})
            resources = desc.get("Resources", {})
            engine = desc.get("Engine", {})

            nano_cpu = resources.get("NanoCPUs", 0)
            mem_bytes = resources.get("MemoryBytes", 0)

            nodes.append(SwarmNode(
                id=attrs.get("ID", n.id),
                hostname=desc.get("Hostname", ""),
                role=spec.get("Role", "worker"),
                status=NodeStatus(status.get("State", "unknown")),
                availability=NodeAvailability(spec.get("Availability", "active")),
                addr=status.get("Addr", ""),
                platform_os=platform.get("OS", ""),
                platform_arch=platform.get("Architecture", ""),
                engine_version=engine.get("EngineVersion", ""),
                labels=spec.get("Labels", {}),
                resources={
                    "cpus": nano_cpu / 1e9 if nano_cpu else 0,
                    "memory_mb": mem_bytes / (1024 * 1024) if mem_bytes else 0,
                    "gpus": _count_gpus(resources),
                },
            ))
        return nodes

    def get_node(self, node_id: str) -> SwarmNode | None:
        for node in self.list_nodes():
            if node.id == node_id or node.hostname == node_id:
                return node
        return None

    def drain_node(self, node_id: str) -> bool:
        return self._set_availability(node_id, "drain")

    def activate_node(self, node_id: str) -> bool:
        return self._set_availability(node_id, "active")

    def _set_availability(self, node_id: str, availability: str) -> bool:
        try:
            node = self.client.nodes.get(node_id)
            spec = node.attrs["Spec"]
            spec["Availability"] = availability
            node.update(spec)
            return True
        except (NotFound, APIError) as e:
            logger.error("Failed to set node %s availability: %s", node_id, e)
            return False

    # --- Services ---

    def list_services(self) -> list[SwarmService]:
        services = []
        for svc in self.client.services.list():
            attrs = svc.attrs or {}
            spec = attrs.get("Spec", {})
            task_template = spec.get("TaskTemplate", {})
            container_spec = task_template.get("ContainerSpec", {})
            mode = spec.get("Mode", {})
            replicated = mode.get("Replicated", {})
            endpoint = attrs.get("Endpoint", {})

            ports = []
            for p in endpoint.get("Ports", []):
                published = p.get("PublishedPort", "")
                target = p.get("TargetPort", "")
                if published and target:
                    ports.append(f"{published}:{target}")

            running = 0
            try:
                tasks = svc.tasks(filters={"desired-state": "running"})
                running = sum(
                    1 for t in tasks
                    if t.get("Status", {}).get("State") == "running"
                )
            except Exception:
                pass

            services.append(SwarmService(
                id=attrs.get("ID", svc.id),
                name=spec.get("Name", svc.name),
                image=container_spec.get("Image", ""),
                replicas=replicated.get("Replicas", 1),
                running_replicas=running,
                ports=ports,
                created_at=attrs.get("CreatedAt", ""),
            ))
        return services

    def deploy_service(self, name: str, defn: ServiceDefinition) -> str:
        kwargs: dict[str, Any] = {
            "image": defn.image,
            "name": name,
            "mode": ServiceMode("replicated", replicas=defn.replicas),
            "restart_policy": RestartPolicy(condition="on-failure"),
        }

        if defn.ports:
            port_configs: dict[int, int] = {}
            for p in defn.ports:
                parts = p.split(":")
                if len(parts) == 2:
                    port_configs[int(parts[0])] = int(parts[1])
            if port_configs:
                kwargs["endpoint_spec"] = EndpointSpec(ports=port_configs)

        if defn.env:
            kwargs["env"] = [f"{k}={v}" for k, v in defn.env.items()]

        if defn.constraints:
            kwargs["constraints"] = defn.constraints

        if defn.labels:
            kwargs["labels"] = defn.labels

        if defn.mounts:
            mounts = []
            for m in defn.mounts:
                parts = m.split(":")
                if len(parts) >= 2:
                    mounts.append(Mount(target=parts[1], source=parts[0], type="bind"))
            if mounts:
                kwargs["mounts"] = mounts

        if defn.networks:
            kwargs["networks"] = defn.networks

        if defn.command:
            kwargs["command"] = defn.command

        svc = self.client.services.create(**kwargs)
        return svc.id

    def remove_service(self, name: str) -> bool:
        try:
            svc = self.client.services.get(name)
            svc.remove()
            return True
        except (NotFound, APIError) as e:
            logger.error("Failed to remove service %s: %s", name, e)
            return False

    def scale_service(self, name: str, replicas: int) -> bool:
        try:
            svc = self.client.services.get(name)
            svc.scale(replicas)
            return True
        except (NotFound, APIError) as e:
            logger.error("Failed to scale service %s: %s", name, e)
            return False

    def get_service_logs(self, name: str, tail: int = 100) -> str:
        try:
            svc = self.client.services.get(name)
            logs = svc.logs(stdout=True, stderr=True, tail=tail)
            if isinstance(logs, bytes):
                return logs.decode("utf-8", errors="replace")
            return "".join(
                chunk.decode("utf-8", errors="replace") if isinstance(chunk, bytes) else chunk
                for chunk in logs
            )
        except (NotFound, APIError) as e:
            return f"Error fetching logs: {e}"

    def get_swarm_id(self) -> str:
        try:
            info = self.client.info()
            return info.get("Swarm", {}).get("Cluster", {}).get("ID", "")
        except Exception:
            return ""


def _count_gpus(resources: dict) -> int:
    for gr in resources.get("GenericResources", []):
        spec = gr.get("DiscreteResourceSpec", {})
        if spec.get("Kind") == "GPU":
            return spec.get("Value", 0)
    return 0


swarm_client = SwarmClient()
