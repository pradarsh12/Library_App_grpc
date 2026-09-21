"""Translate domain and database errors into gRPC status codes.

Services and repositories raise the exceptions in `server.errors` instead of
dealing with gRPC directly; the `handle_errors` decorator on each servicer
method is the single place that turns them into `context.abort(...)` calls.
"""

from __future__ import annotations

import asyncio
import functools
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

import asyncpg
import grpc

from server.errors import (
    AlreadyExistsError,
    ConflictError,
    LibraryError,
    NotFoundError,
    ValidationError,
)

logger = logging.getLogger("library.errors")

T = TypeVar("T")


_STATUS_BY_ERROR: dict[type[LibraryError], grpc.StatusCode] = {
    ValidationError: grpc.StatusCode.INVALID_ARGUMENT,
    NotFoundError: grpc.StatusCode.NOT_FOUND,
    AlreadyExistsError: grpc.StatusCode.ALREADY_EXISTS,
    ConflictError: grpc.StatusCode.FAILED_PRECONDITION,
}


def _status_for(exc: LibraryError) -> grpc.StatusCode:
    """Look up the status by walking the MRO so subclasses of a mapped error
    inherit its code rather than falling through to INTERNAL."""
    for cls in type(exc).__mro__:
        code = _STATUS_BY_ERROR.get(cls)
        if code is not None:
            return code
    return grpc.StatusCode.INTERNAL


# Raw database errors carry constraint names and `DETAIL: Key (email)=(...)`
# lines, so clients only ever get these fixed messages; the original error is
# logged for operators.
_DB_ERROR_RESPONSES: tuple[tuple[type[Exception], grpc.StatusCode, str], ...] = (
    (asyncpg.UniqueViolationError, grpc.StatusCode.ALREADY_EXISTS,
     "a record with these values already exists"),
    (asyncpg.ForeignKeyViolationError, grpc.StatusCode.INVALID_ARGUMENT,
     "a referenced record does not exist"),
    (asyncpg.CheckViolationError, grpc.StatusCode.INVALID_ARGUMENT,
     "a value in the request is not allowed"),
    (asyncpg.DataError, grpc.StatusCode.INVALID_ARGUMENT,
     "a value in the request is invalid or out of range"),
    # Transient infrastructure failures: safe for the client to retry.
    (asyncpg.TransactionRollbackError, grpc.StatusCode.ABORTED,
     "the operation was aborted due to a conflict; please retry"),
    (asyncpg.QueryCanceledError, grpc.StatusCode.DEADLINE_EXCEEDED,
     "the database took too long to respond"),
    (asyncpg.PostgresConnectionError, grpc.StatusCode.UNAVAILABLE,
     "the database is temporarily unavailable"),
    (asyncpg.TooManyConnectionsError, grpc.StatusCode.UNAVAILABLE,
     "the database is temporarily unavailable"),
    (asyncpg.CannotConnectNowError, grpc.StatusCode.UNAVAILABLE,
     "the database is temporarily unavailable"),
    (asyncpg.InterfaceError, grpc.StatusCode.UNAVAILABLE,
     "the database is temporarily unavailable"),
    (asyncio.TimeoutError, grpc.StatusCode.DEADLINE_EXCEEDED,
     "the database took too long to respond"),
)


def _db_error_response(exc: Exception) -> tuple[grpc.StatusCode, str] | None:
    for cls, code, message in _DB_ERROR_RESPONSES:
        if isinstance(exc, cls):
            return code, message
    return None


def handle_errors(
    method: Callable[..., Awaitable[T]],
) -> Callable[..., Awaitable[T]]:
    """Decorator for async servicer methods: `(self, request, context)`.

    Catches domain exceptions (and common raw asyncpg errors) and aborts the
    RPC with the appropriate gRPC status code + message.
    """

    @functools.wraps(method)
    async def wrapper(self, request, context):  # noqa: ANN001
        try:
            return await method(self, request, context)
        except LibraryError as exc:
            await context.abort(_status_for(exc), str(exc))
        except (asyncpg.PostgresError, asyncpg.InterfaceError, asyncio.TimeoutError) as exc:
            response = _db_error_response(exc)
            if response is None:
                logger.exception("Unhandled database error in %s", method.__qualname__)
                await context.abort(grpc.StatusCode.INTERNAL, "internal error")
            else:
                logger.warning("Database error in %s: %s", method.__qualname__, exc)
                await context.abort(*response)
        except Exception:
            logger.exception("Unhandled error in %s", method.__qualname__)
            await context.abort(grpc.StatusCode.INTERNAL, "internal error")

    return wrapper
