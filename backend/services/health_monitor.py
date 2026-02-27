from __future__ import annotations

import asyncio
import logging

from backend.config import settings
from backend.models.schemas import ServiceStatus
from backend.services import catalog
from backend.services.docker_client import swarm_client

logger = logging.getLogger(__name__)


class HealthMonitor:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("Health monitor started (interval=%ds)", settings.health_check_interval)

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            logger.info("Health monitor stopped")

    async def _poll_loop(self) -> None:
        while True:
            try:
                await self._sync_statuses()
            except Exception as e:
                logger.error("Health poll error: %s", e)
            await asyncio.sleep(settings.health_check_interval)

    async def _sync_statuses(self) -> None:
        try:
            live_services = {s.name: s for s in swarm_client.list_services()}
        except Exception as e:
            logger.error("Cannot reach Docker daemon: %s", e)
            return

        catalog_services = await catalog.list_services()
        for svc in catalog_services:
            live = live_services.get(svc.name)
            if live:
                if live.running_replicas > 0:
                    new_status = ServiceStatus.RUNNING
                elif live.completed_replicas > 0:
                    new_status = ServiceStatus.STOPPED
                else:
                    new_status = ServiceStatus.FAILED
                if svc.status != new_status or svc.swarm_id != live.id:
                    await catalog.set_service_status(svc.name, new_status, live.id)
            elif svc.status == ServiceStatus.RUNNING:
                await catalog.set_service_status(svc.name, ServiceStatus.STOPPED, None)


health_monitor = HealthMonitor()
