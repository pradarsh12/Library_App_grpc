"""Server entrypoint.

    python -m server.main

Builds an async grpc.aio server backed by a single shared asyncpg pool,
wires database -> services -> gRPC servicers, registers them plus gRPC
reflection (so `grpcurl` works without needing the .proto files on hand),
and serves until interrupted.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging

import grpc
import grpc.aio
from grpc_health.v1 import health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from library.v1 import book_pb2, book_pb2_grpc, loan_pb2, loan_pb2_grpc, member_pb2, member_pb2_grpc

from server.api.book_servicer import BookServicer
from server.api.health import create_health_servicer, watch_database_health
from server.api.loan_servicer import LoanServicer
from server.api.logging_interceptor import RequestLoggingInterceptor
from server.api.member_servicer import MemberServicer
from server.config import settings
from server.db.database import Database
from server.db.pool import create_pool
from server.services.book_service import BookService
from server.services.loan_service import LoanService
from server.services.member_service import MemberService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("library.server")


async def serve() -> None:
    pool = await create_pool()
    db = Database(pool)
    server = grpc.aio.server(interceptors=[RequestLoggingInterceptor()])

    book_pb2_grpc.add_BookServiceServicer_to_server(
        BookServicer(BookService(db)), server
    )
    member_pb2_grpc.add_MemberServiceServicer_to_server(
        MemberServicer(MemberService(db)), server
    )
    loan_pb2_grpc.add_LoanServiceServicer_to_server(
        LoanServicer(LoanService(db)), server
    )

    service_full_names = (
        book_pb2.DESCRIPTOR.services_by_name["BookService"].full_name,
        member_pb2.DESCRIPTOR.services_by_name["MemberService"].full_name,
        loan_pb2.DESCRIPTOR.services_by_name["LoanService"].full_name,
    )

    health_servicer = create_health_servicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

    service_names = (
        *service_full_names,
        health_pb2.DESCRIPTOR.services_by_name["Health"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, server)

    listen_addr = f"{settings.grpc_host}:{settings.grpc_port}"
    server.add_insecure_port(listen_addr)

    await server.start()
    logger.info("Neighborhood Library gRPC server listening on %s", listen_addr)

    health_watch = asyncio.create_task(
        watch_database_health(health_servicer, pool, service_full_names)
    )
    try:
        await server.wait_for_termination()
    finally:
        health_watch.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await health_watch
        await health_servicer.enter_graceful_shutdown()
        await pool.close()


def main() -> None:
    asyncio.run(serve())


if __name__ == "__main__":
    main()
