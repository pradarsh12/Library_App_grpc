"""Shared test doubles."""

from __future__ import annotations

import uuid

import grpc

from library.v1 import book_pb2, member_pb2
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


async def make_book(pool, title: str = "Dune", author: str = "Herbert", copies: int = 1, **fields):
    return await book_api(pool).CreateBook(
        book_pb2.CreateBookRequest(
            title=title, author=author, initial_copies=copies, **fields
        ),
        FakeContext(),
    )


async def make_member(pool, first_name: str = "Test", last_name: str = "Member", **fields):
    fields.setdefault("email", f"member.{uuid.uuid4().hex[:10]}@example.com")
    return await member_api(pool).CreateMember(
        member_pb2.CreateMemberRequest(
            first_name=first_name, last_name=last_name, **fields
        ),
        FakeContext(),
    )


def split_outcomes(results: list) -> tuple[list, list[AbortedError]]:
    """Split asyncio.gather(..., return_exceptions=True) results into
    (successes, aborted RPCs); any other exception fails the test."""
    successes, aborted = [], []
    for result in results:
        if isinstance(result, AbortedError):
            aborted.append(result)
        elif isinstance(result, BaseException):
            raise result
        else:
            successes.append(result)
    return successes, aborted
