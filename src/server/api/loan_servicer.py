"""LoanService gRPC servicer: translates between protobuf and LoanService."""

from __future__ import annotations

from library.v1 import loan_pb2, loan_pb2_grpc

from server import mappers
from server.api.error_handling import handle_errors
from server.api.paging import page_args, page_response
from server.services.loan_service import LoanService


class LoanServicer(loan_pb2_grpc.LoanServiceServicer):
    def __init__(self, service: LoanService) -> None:
        self._service = service

    @handle_errors
    async def BorrowBook(self, request: loan_pb2.BorrowBookRequest, context):
        loan = await self._service.borrow_book(
            book_id=request.book_id,
            member_id=request.member_id,
            loan_period_days=request.loan_period_days,
        )
        return mappers.loan_to_proto(loan)

    @handle_errors
    async def ReturnBook(self, request: loan_pb2.ReturnBookRequest, context):
        return mappers.loan_to_proto(await self._service.return_book(request.loan_id))

    @handle_errors
    async def GetLoan(self, request: loan_pb2.GetLoanRequest, context):
        return mappers.loan_to_proto(await self._service.get_loan(request.loan_id))

    @handle_errors
    async def ListLoans(self, request: loan_pb2.ListLoansRequest, context):
        # Proto3 scalars can't be "unset": 0 means "no filter".
        page = await self._service.list_loans(
            member_id=request.member_id or None,
            book_id=request.book_id or None,
            only_active=request.only_active,
            **page_args(request.page),
        )
        return loan_pb2.ListLoansResponse(
            loans=[mappers.loan_to_proto(loan) for loan in page.items],
            page=page_response(page),
        )
