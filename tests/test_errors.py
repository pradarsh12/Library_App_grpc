"""handle_errors maps exceptions to gRPC codes without leaking DB details."""

from __future__ import annotations

import asyncio

import asyncpg
import grpc
import pytest

from server.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
    handle_errors,
)

from _helpers import AbortedError, FakeContext


class _SubValidationError(ValidationError):
    pass


def _raiser(exc: Exception):
    @handle_errors
    async def method(self, request, context):
        raise exc

    return method


async def _code_and_details(exc: Exception) -> tuple[grpc.StatusCode, str]:
    with pytest.raises(AbortedError) as exc_info:
        await _raiser(exc)(None, None, FakeContext())
    return exc_info.value.code, exc_info.value.details


@pytest.mark.parametrize(
    ("exc", "code"),
    [
        (ValidationError("bad"), grpc.StatusCode.INVALID_ARGUMENT),
        (NotFoundError("gone"), grpc.StatusCode.NOT_FOUND),
        (ConflictError("busy"), grpc.StatusCode.FAILED_PRECONDITION),
        (_SubValidationError("bad sub"), grpc.StatusCode.INVALID_ARGUMENT),
        (RuntimeError("boom"), grpc.StatusCode.INTERNAL),
    ],
)
async def test_maps_exception_to_status(exc, code):
    got_code, _ = await _code_and_details(exc)
    assert got_code == code


@pytest.mark.parametrize(
    ("exc", "code"),
    [
        (asyncpg.UniqueViolationError("duplicate key"), grpc.StatusCode.ALREADY_EXISTS),
        (asyncpg.ForeignKeyViolationError("fk"), grpc.StatusCode.INVALID_ARGUMENT),
        (asyncpg.CheckViolationError("check"), grpc.StatusCode.INVALID_ARGUMENT),
        (asyncpg.DataError("out of range"), grpc.StatusCode.INVALID_ARGUMENT),
        (asyncpg.CharacterNotInRepertoireError("0x00"), grpc.StatusCode.INVALID_ARGUMENT),
    ],
)
async def test_maps_database_error_to_status(exc, code):
    got_code, _ = await _code_and_details(exc)
    assert got_code == code



@pytest.mark.parametrize(
    ("exc", "code"),
    [
        (asyncpg.DeadlockDetectedError("deadlock"), grpc.StatusCode.ABORTED),
        (asyncpg.SerializationError("serialize"), grpc.StatusCode.ABORTED),
        (asyncpg.QueryCanceledError("cancel"), grpc.StatusCode.DEADLINE_EXCEEDED),
        (asyncio.TimeoutError(), grpc.StatusCode.DEADLINE_EXCEEDED),
        (asyncpg.ConnectionDoesNotExistError("gone"), grpc.StatusCode.UNAVAILABLE),
        (asyncpg.TooManyConnectionsError("full"), grpc.StatusCode.UNAVAILABLE),
        (asyncpg.CannotConnectNowError("starting"), grpc.StatusCode.UNAVAILABLE),
        (asyncpg.InterfaceError("pool is closed"), grpc.StatusCode.UNAVAILABLE),
    ],
)
async def test_maps_infrastructure_error_to_retryable_status(exc, code):
    got_code, _ = await _code_and_details(exc)
    assert got_code == code


async def test_database_error_details_are_not_leaked():
    secret = (
        'duplicate key value violates unique constraint "members_email_key" '
        "DETAIL: Key (email)=(ada@example.com) already exists."
    )
    _, details = await _code_and_details(asyncpg.UniqueViolationError(secret))
    assert "members_email_key" not in details
    assert "ada@example.com" not in details


async def test_unmapped_database_error_is_internal_and_generic():
    code, details = await _code_and_details(asyncpg.UndefinedTableError("secret"))
    assert code == grpc.StatusCode.INTERNAL
    assert details == "internal error"


async def test_successful_call_passes_through():
    @handle_errors
    async def method(self, request, context):
        return "ok"

    assert await method(None, None, FakeContext()) == "ok"
