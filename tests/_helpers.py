"""Shared test doubles."""

from __future__ import annotations

import grpc

from server.api.book_servicer import BookServicer
from server.api.loan_servicer import LoanServicer
from server.api.member_servicer import MemberServicer
from server.db.database import Database
from server.services.book_service import BookService
from server.services.loan_service import LoanService
from server.services.member_service import MemberService


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


def book_api(pool) -> BookServicer:
    return BookServicer(BookService(Database(pool)))


def member_api(pool) -> MemberServicer:
    return MemberServicer(MemberService(Database(pool)))


def loan_api(pool) -> LoanServicer:
    return LoanServicer(LoanService(Database(pool)))
