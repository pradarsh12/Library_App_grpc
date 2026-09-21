"""LoanService gRPC servicer — borrow/return/list operations."""

from __future__ import annotations

import asyncpg

from library.v1 import loan_pb2, loan_pb2_grpc

from server import mappers, validation
from server.config import settings
from server.errors import handle_errors
from server.pagination import build_page_response, parse_page
from server.repositories import loan_repository


class LoanService(loan_pb2_grpc.LoanServiceServicer):
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @handle_errors
    async def BorrowBook(self, request: loan_pb2.BorrowBookRequest, context):
        book_id = validation.require_positive_id(request.book_id, "book_id")
        member_id = validation.require_positive_id(request.member_id, "member_id")
        loan_period_days = (
            request.loan_period_days or settings.default_loan_period_days
        )
        validation.require_positive_int(
            loan_period_days,
            "loan_period_days",
            maximum=validation.MAX_LOAN_PERIOD_DAYS,
        )

        row = await loan_repository.borrow_book(
            self._pool,
            book_id=book_id,
            member_id=member_id,
            loan_period_days=loan_period_days,
        )
        return mappers.loan_to_proto(row)

    @handle_errors
    async def ReturnBook(self, request: loan_pb2.ReturnBookRequest, context):
        loan_id = validation.require_positive_id(request.loan_id, "loan_id")
        row = await loan_repository.return_book(self._pool, loan_id)
        return mappers.loan_to_proto(row)

    @handle_errors
    async def GetLoan(self, request: loan_pb2.GetLoanRequest, context):
        loan_id = validation.require_positive_id(request.loan_id, "loan_id")
        row = await loan_repository.get_loan(self._pool, loan_id)
        return mappers.loan_to_proto(row)

    @handle_errors
    async def ListLoans(self, request: loan_pb2.ListLoansRequest, context):
        size, offset = parse_page(request.page)
        rows = await loan_repository.list_loans(
            self._pool,
            member_id=request.member_id or None,
            book_id=request.book_id or None,
            only_active=request.only_active,
            limit=size + 1,
            offset=offset,
        )
        page_rows, page = build_page_response(rows, size, offset)
        return loan_pb2.ListLoansResponse(
            loans=[mappers.loan_to_proto(r) for r in page_rows], page=page
        )
