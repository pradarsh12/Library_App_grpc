"""Domain exceptions raised by services and repositories.

These carry no transport knowledge; `server.api.error_handling` is the single
place that translates them into gRPC status codes.
"""

from __future__ import annotations


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
