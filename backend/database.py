from __future__ import annotations

import aiosqlite

from backend.config import settings

_DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS catalog_services (
    name TEXT PRIMARY KEY,
    description TEXT NOT NULL DEFAULT '',
    definition TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'registered',
    swarm_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(str(settings.db_path))
    db.row_factory = aiosqlite.Row
    return db


async def init_db() -> None:
    db = await get_db()
    try:
        await db.executescript(_DB_SCHEMA)
        await db.commit()
    finally:
        await db.close()
