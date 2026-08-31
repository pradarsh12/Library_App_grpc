"""Domain exceptions and their mapping onto gRPC status codes.

Repositories/services raise the exceptions below instead of dealing with
gRPC directly; the `handle_errors` decorator on each servicer method is the
single place that translates them into `context.abort(...)` calls.
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

import asyncpg
import grpc

logger = logging.getLogger("library.errors")

T = TypeVar("T")


class LibraryError(Exception):
    """Base class for all domain errors raised by repositories/services."""


class NotFoundError(LibraryError):
    """A requested entity (book, member, loan, copy) does not exist."""


class AlreadyExistsError(LibraryError):
    """A unique constraint (email, ISBN, barcode) would be violated."""


class ValidationError(LibraryError):
    """Request data failed validation before it reached the database."""


class ConflictError(LibraryError):
    """The request is well-formed but conflicts with current state
    (e.g. no copies available, loan already returned)."""


_STATUS_BY_ERROR: dict[type[LibraryError], grpc.StatusCode] = {
    ValidationError: grpc.StatusCode.INVALID_ARGUMENT,
    NotFoundError: grpc.StatusCode.NOT_FOUND,
    AlreadyExistsError: grpc.StatusCode.ALREADY_EXISTS,
    ConflictError: grpc.StatusCode.FAILED_PRECONDITION,
}


def handle_errors(
    method: Callable[..., Awaitable[T]],
) -> Callable[..., Awaitable[T]]:
    """Decorator for async servicer methods: `(self, request, context)`.

    Catches domain exceptions (and a couple of common raw asyncpg errors)
    and aborts the RPC with the appropriate gRPC status code + message.
    """

    @functools.wraps(method)
    async def wrapper(self, request, context):  # noqa: ANN001
        try:
            return await method(self, request, context)
        except LibraryError as exc:
            code = _STATUS_BY_ERROR.get(type(exc), grpc.StatusCode.INTERNAL)
            await context.abort(code, str(exc))
        except asyncpg.UniqueViolationError as exc:
            await context.abort(grpc.StatusCode.ALREADY_EXISTS, str(exc))
        except asyncpg.ForeignKeyViolationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except Exception:
            logger.exception("Unhandled error in %s", method.__qualname__)
            await context.abort(grpc.StatusCode.INTERNAL, "internal error")

    return wrapper
