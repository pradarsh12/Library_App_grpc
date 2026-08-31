"""Scripted end-to-end walkthrough of the Neighborhood Library gRPC API.

    python client_examples/sample_client.py

Requires the server to be running (`python -m server.main`) against a
Postgres instance with db/schema.sql applied.
"""

from __future__ import annotations

import asyncio
import uuid

import grpc

from library.v1 import book_pb2, book_pb2_grpc
from library.v1 import loan_pb2, loan_pb2_grpc
from library.v1 import member_pb2, member_pb2_grpc

TARGET = "localhost:50051"


async def main() -> None:
    async with grpc.aio.insecure_channel(TARGET) as channel:
        books = book_pb2_grpc.BookServiceStub(channel)
        members = member_pb2_grpc.MemberServiceStub(channel)
        loans = loan_pb2_grpc.LoanServiceStub(channel)

        print("== CreateMember ==")
        member = await members.CreateMember(
            member_pb2.CreateMemberRequest(
                first_name="Grace",
                last_name="Hopper",
                email=f"grace.hopper.{uuid.uuid4().hex[:8]}@example.com",
                phone="555-0110",
                address="1 Compiler Ave",
            )
        )
        print(member)

        print("== CreateBook (2 copies) ==")
        book = await books.CreateBook(
            book_pb2.CreateBookRequest(
                title="The Pragmatic Programmer",
                author="Andrew Hunt & David Thomas",
                publisher="Addison-Wesley",
                published_year=1999,
                genre="Technology",
                initial_copies=2,
            )
        )
        print(book)

        print("== BorrowBook ==")
        loan = await loans.BorrowBook(
            loan_pb2.BorrowBookRequest(book_id=book.id, member_id=member.id)
        )
        print(loan)

        print("== ListLoans (this member's active loans) ==")
        active_loans = await loans.ListLoans(
            loan_pb2.ListLoansRequest(member_id=member.id, only_active=True)
        )
        print(active_loans)

        print("== ReturnBook ==")
        returned = await loans.ReturnBook(loan_pb2.ReturnBookRequest(loan_id=loan.id))
        print(returned)

        print("== Borrow both copies, then attempt a third (expect FAILED_PRECONDITION) ==")
        for _ in range(2):
            await loans.BorrowBook(
                loan_pb2.BorrowBookRequest(book_id=book.id, member_id=member.id)
            )
        try:
            await loans.BorrowBook(
                loan_pb2.BorrowBookRequest(book_id=book.id, member_id=member.id)
            )
        except grpc.aio.AioRpcError as exc:
            print(f"Got expected error: {exc.code()} - {exc.details()}")


if __name__ == "__main__":
    asyncio.run(main())
