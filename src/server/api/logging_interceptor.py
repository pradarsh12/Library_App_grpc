"""Server-wide request logging.

`handle_errors` (see error_handling.py) only logs the failure path — a
successful RPC produces no log output at all. This interceptor logs every
unary RPC exactly once, with its method name, outcome, and duration,
without touching any of the ~13 servicer methods individually.
"""

from __future__ import annotations

import logging
import time

import grpc
import grpc.aio

logger = logging.getLogger("library.requests")


class RequestLoggingInterceptor(grpc.aio.ServerInterceptor):
    async def intercept_service(self, continuation, handler_call_details):
        handler = await continuation(handler_call_details)
        # Every RPC in this service is unary-unary today; anything else
        # (streaming) is passed through unlogged rather than guessed at.
        if handler is None or handler.request_streaming or handler.response_streaming:
            return handler

        method = handler_call_details.method
        inner_behavior = handler.unary_unary

        async def logged_behavior(request, context):
            start = time.monotonic()
            status_code = grpc.StatusCode.OK
            try:
                return await inner_behavior(request, context)
            except grpc.aio.AbortError:
                # `context.abort()` (via handle_errors) sets the code before
                # raising this to unwind the handler; recover it for the log.
                status_code = context.code() or grpc.StatusCode.UNKNOWN
                raise
            except Exception:
                status_code = grpc.StatusCode.UNKNOWN
                raise
            finally:
                duration_ms = (time.monotonic() - start) * 1000
                logger.info(
                    "%s status=%s duration_ms=%.1f", method, status_code.name, duration_ms
                )

        return grpc.unary_unary_rpc_method_handler(
            logged_behavior,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )
