from __future__ import annotations

import logging

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)


class RegistryClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.registry_url).rstrip("/")

    async def list_repositories(self) -> list[str]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/v2/_catalog", timeout=10)
                resp.raise_for_status()
                return resp.json().get("repositories", [])
        except Exception as e:
            logger.error("Failed to list repositories: %s", e)
            return []

    async def list_tags(self, repository: str) -> list[str]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/v2/{repository}/tags/list", timeout=10)
                resp.raise_for_status()
                return resp.json().get("tags", []) or []
        except Exception as e:
            logger.error("Failed to list tags for %s: %s", repository, e)
            return []


registry_client = RegistryClient()
