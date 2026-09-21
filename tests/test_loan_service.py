from __future__ import annotations

import uuid

import grpc
import pytest

from library.v1 import book_pb2, loan_pb2, member_pb2

from _helpers import AbortedError, FakeContext, book_api, loan_api, member_api


async def _make_member(pool):
    return await member_api(pool).CreateMember(
        member_pb2.CreateMemberRequest(
            first_name="Test",
            last_name="Member",
            email=f"member.{uuid.uuid4().hex[:8]}@example.com",
        ),
        FakeContext(),
    )


async def test_borrow_and_return_flow(pool):
    books, members, loans = book_api(pool), member_api(pool), loan_api(pool)
    ctx = FakeContext()

    book = await books.CreateBook(
        book_pb2.CreateBookRequest(title="Dune", author="Herbert", initial_copies=1),
        ctx,
    )
    member = await _make_member(pool)

    loan = await loans.BorrowBook(
        loan_pb2.BorrowBookRequest(book_id=book.id, member_id=member.id), ctx
    )
    assert loan.status == loan_pb2.LOAN_STATUS_ACTIVE
    assert loan.book_title == "Dune"
    assert loan.member_name == "Test Member"

    refreshed = await books.GetBook(book_pb2.GetBookRequest(id=book.id), ctx)
    assert refreshed.available_copies == 0

    # No copies left -> FAILED_PRECONDITION.
    with pytest.raises(AbortedError) as exc_info:
        await loans.BorrowBook(
            loan_pb2.BorrowBookRequest(book_id=book.id, member_id=member.id), ctx
        )
    assert exc_info.value.code == grpc.StatusCode.FAILED_PRECONDITION

    returned = await loans.ReturnBook(loan_pb2.ReturnBookRequest(loan_id=loan.id), ctx)
    assert returned.status == loan_pb2.LOAN_STATUS_RETURNED
    assert returned.HasField("returned_at")

    # Already returned -> FAILED_PRECONDITION.
    with pytest.raises(AbortedError) as exc_info:
        await loans.ReturnBook(loan_pb2.ReturnBookRequest(loan_id=loan.id), ctx)
    assert exc_info.value.code == grpc.StatusCode.FAILED_PRECONDITION


async def test_borrow_same_book_twice_by_same_member_rejected(pool):
    books, loans = book_api(pool), loan_api(pool)
    ctx = FakeContext()

    # Two copies available, so this isn't the "no copies left" case —
    # it's specifically the one-active-loan-per-member-per-book rule.
    book = await books.CreateBook(
        book_pb2.CreateBookRequest(title="Dune", author="Herbert", initial_copies=2),
        ctx,
    )
    member = await _make_member(pool)

    await loans.BorrowBook(
        loan_pb2.BorrowBookRequest(book_id=book.id, member_id=member.id), ctx
    )

    with pytest.raises(AbortedError) as exc_info:
        await loans.BorrowBook(
            loan_pb2.BorrowBookRequest(book_id=book.id, member_id=member.id), ctx
        )
    assert exc_info.value.code == grpc.StatusCode.FAILED_PRECONDITION

    refreshed = await books.GetBook(book_pb2.GetBookRequest(id=book.id), ctx)
    assert refreshed.available_copies == 1  # second copy never got claimed

    # A different member can still borrow the remaining copy.
    other_member = await _make_member(pool)
    loan = await loans.BorrowBook(
        loan_pb2.BorrowBookRequest(book_id=book.id, member_id=other_member.id), ctx
    )
    assert loan.status == loan_pb2.LOAN_STATUS_ACTIVE


async def test_borrow_nonexistent_book_raises_not_found(pool):
    loans = loan_api(pool)
    member = await _make_member(pool)
    with pytest.raises(AbortedError) as exc_info:
        await loans.BorrowBook(
            loan_pb2.BorrowBookRequest(book_id=999_999, member_id=member.id),
            FakeContext(),
        )
    assert exc_info.value.code == grpc.StatusCode.NOT_FOUND


async def test_list_loans_for_member(pool):
    books, loans = book_api(pool), loan_api(pool)
    ctx = FakeContext()
    book = await books.CreateBook(
        book_pb2.CreateBookRequest(
            title="Foundation", author="Asimov", initial_copies=1
        ),
        ctx,
    )
    member = await _make_member(pool)
    await loans.BorrowBook(
        loan_pb2.BorrowBookRequest(book_id=book.id, member_id=member.id), ctx
    )

    response = await loans.ListLoans(
        loan_pb2.ListLoansRequest(member_id=member.id, only_active=True), ctx
    )
    assert len(response.loans) == 1
    assert response.loans[0].book_id == book.id


async def test_borrow_rejects_excessive_loan_period():
    import grpc
    from library.v1 import loan_pb2
    import pytest

    service = loan_api(pool=None)
    with pytest.raises(AbortedError) as exc_info:
        await service.BorrowBook(
            loan_pb2.BorrowBookRequest(book_id=1, member_id=1, loan_period_days=100_000),
            FakeContext(),
        )
    assert exc_info.value.code == grpc.StatusCode.INVALID_ARGUMENT
