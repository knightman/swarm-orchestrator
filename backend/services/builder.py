from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from backend.config import settings
from backend.services.docker_client import swarm_client

logger = logging.getLogger(__name__)


def _resolve_context(build_context: str) -> str:
    """Resolve build_context to an absolute path.

    Absolute paths are used as-is. Relative paths are resolved against
    settings.projects_dir, so a build_context of 'my-app' becomes
    '{projects_dir}/my-app' inside the container.
    """
    p = Path(build_context)
    if p.is_absolute():
        return str(p)
    return str(settings.projects_path / p)


def _parse_image(image: str) -> tuple[str, str]:
    """Split 'registry/name:tag' into ('registry/name', 'tag')."""
    last_segment = image.split("/")[-1]
    if ":" in last_segment:
        repository, tag = image.rsplit(":", 1)
    else:
        repository, tag = image, "latest"
    return repository, tag


def _run_build(build_context: str, image: str, platform: str) -> tuple[bool, str]:
    """Synchronous build + push. Intended to be called via asyncio.to_thread."""
    logs: list[str] = []

    try:
        logger.info("Building %s from %s (platform=%s)", image, build_context, platform)
        for chunk in swarm_client.client.api.build(
            path=build_context,
            tag=image,
            platform=platform,
            rm=True,
            decode=True,
        ):
            if "stream" in chunk:
                line = chunk["stream"].rstrip()
                if line:
                    logs.append(line)
                    logger.debug("[build] %s", line)
            elif "error" in chunk:
                logs.append(f"ERROR: {chunk['error'].strip()}")
                logger.error("[build] %s", chunk["error"])
                return False, "\n".join(logs)

        repository, tag = _parse_image(image)
        logs.append(f"Pushing {image}...")
        logger.info("Pushing %s", image)

        seen: set[str] = set()
        for chunk in swarm_client.client.api.push(repository, tag=tag, stream=True, decode=True):
            if "error" in chunk:
                logs.append(f"ERROR: {chunk['error'].strip()}")
                logger.error("[push] %s", chunk["error"])
                return False, "\n".join(logs)
            # Log digest lines and status transitions; skip repeated progress spam
            status = chunk.get("status", "")
            digest = chunk.get("aux", {}).get("Digest", "")
            if digest:
                logs.append(f"Digest: {digest}")
            elif status and status not in seen:
                seen.add(status)
                logs.append(status)

        logs.append("Done.")
        return True, "\n".join(logs)

    except Exception as e:
        logs.append(f"Exception: {e}")
        logger.exception("Build/push failed for %s", image)
        return False, "\n".join(logs)


async def build_and_push(build_context: str, image: str, platform: str) -> tuple[bool, str]:
    """Build a Docker image from build_context and push it to the registry.

    build_context may be an absolute path or a name relative to settings.projects_dir.
    """
    resolved = _resolve_context(build_context)
    return await asyncio.to_thread(_run_build, resolved, image, platform)
