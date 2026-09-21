"""asyncpg connection pool lifecycle.

One pool is created at server startup and shared by every repository /
servicer for the life of the process — this is what lets the async server
hold many concurrent RPCs without spinning up a thread or connection per
request.
"""

from __future__ import annotations

import asyncpg

from server.config import settings


async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=settings.db_pool_min_size,
        max_size=settings.db_pool_max_size,
        # Fail a stuck query instead of holding the RPC and connection forever.
        command_timeout=settings.db_command_timeout_seconds,
    )
