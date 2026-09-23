"""gRPC health checking (grpc.health.v1.Health).

Registers the standard health service orchestrators/load balancers use
(`grpcurl -plaintext localhost:50051 grpc.health.v1.Health/Check`), and
keeps its status tied to whether the database is actually reachable —
"the process is alive" isn't the same as "requests will succeed", since
every RPC in this service needs the DB.
"""

from __future__ import annotations

import asyncio
import logging

import asyncpg
from grpc_health.v1 import health, health_pb2

logger = logging.getLogger("library.health")

OVERALL_SERVICE = ""
DEFAULT_CHECK_INTERVAL_SECONDS = 10.0


def create_health_servicer() -> health.aio.HealthServicer:
    return health.aio.HealthServicer()


async def _database_is_reachable(pool: asyncpg.Pool) -> bool:
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception:
        logger.exception("Health check: database probe failed")
        return False


async def watch_database_health(
    servicer: health.aio.HealthServicer,
    pool: asyncpg.Pool,
    service_names: tuple[str, ...],
    interval_seconds: float = DEFAULT_CHECK_INTERVAL_SECONDS,
) -> None:
    """Runs until cancelled, probing the database on an interval and setting
    the overall ("") and per-service health status to match."""
    services = (OVERALL_SERVICE, *service_names)
    while True:
        healthy = await _database_is_reachable(pool)
        status = (
            health_pb2.HealthCheckResponse.SERVING
            if healthy
            else health_pb2.HealthCheckResponse.NOT_SERVING
        )
        for service in services:
            await servicer.set(service, status)
        await asyncio.sleep(interval_seconds)
