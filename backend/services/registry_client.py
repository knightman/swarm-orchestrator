from __future__ import annotations

import logging
from typing import Any

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

MANIFEST_ACCEPT = ", ".join([
    "application/vnd.docker.distribution.manifest.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
])


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

    async def get_manifest(self, repository: str, tag: str) -> dict[str, Any]:
        """Fetch manifest for a repo:tag. Returns digest, media_type, size, layer_count."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/v2/{repository}/manifests/{tag}",
                    headers={"Accept": MANIFEST_ACCEPT},
                    timeout=10,
                )
                resp.raise_for_status()
                digest = resp.headers.get("Docker-Content-Digest", "")
                manifest = resp.json()
                media_type = manifest.get("mediaType", resp.headers.get("Content-Type", ""))

                config = manifest.get("config", {})
                layers = manifest.get("layers", [])
                total_size = config.get("size", 0) + sum(l.get("size", 0) for l in layers)

                return {
                    "digest": digest,
                    "media_type": media_type,
                    "size": total_size,
                    "layer_count": len(layers),
                    "config_digest": config.get("digest", ""),
                }
        except Exception as e:
            logger.error("Failed to get manifest for %s:%s: %s", repository, tag, e)
            return {"digest": "", "media_type": "", "size": 0, "layer_count": 0, "config_digest": ""}

    async def get_image_config(self, repository: str, config_digest: str) -> dict[str, Any]:
        """Fetch the image config blob. Returns created, architecture, os."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/v2/{repository}/blobs/{config_digest}",
                    timeout=10,
                )
                resp.raise_for_status()
                config = resp.json()
                return {
                    "created": config.get("created", ""),
                    "architecture": config.get("architecture", ""),
                    "os": config.get("os", ""),
                }
        except Exception as e:
            logger.error("Failed to get image config %s@%s: %s", repository, config_digest, e)
            return {"created": "", "architecture": "", "os": ""}

    async def delete_manifest(self, repository: str, digest: str) -> bool:
        """Delete a manifest by digest. Registry must have REGISTRY_STORAGE_DELETE_ENABLED=true."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.delete(
                    f"{self.base_url}/v2/{repository}/manifests/{digest}",
                    headers={"Accept": MANIFEST_ACCEPT},
                    timeout=10,
                )
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error("Failed to delete manifest %s@%s: %s", repository, digest, e)
            return False


registry_client = RegistryClient()
