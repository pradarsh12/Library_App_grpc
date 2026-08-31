"""Shared test doubles."""

from __future__ import annotations

import grpc


class AbortedError(Exception):
    """Raised by FakeContext.abort() to mimic context.abort() raising."""

    def __init__(self, code: grpc.StatusCode, details: str) -> None:
        super().__init__(f"{code}: {details}")
        self.code = code
        self.details = details


class FakeContext:
    """Minimal stand-in for grpc.aio.ServicerContext used in unit tests."""

    async def abort(self, code: grpc.StatusCode, details: str):
        raise AbortedError(code, details)
