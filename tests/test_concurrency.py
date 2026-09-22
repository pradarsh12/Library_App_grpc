"""Races between simultaneous RPCs must never over-issue copies or duplicate rows.

Each test fires its calls with asyncio.gather so the requests genuinely
overlap on the shared connection pool, then checks the invariants the schema
and services promise: a copy is lent to at most one member, a member holds at
most one active loan per book, and a loan is returned at most once.
"""

from __future__ import annotations

import asyncio

import grpc

from library.v1 import book_pb2, loan_pb2, member_pb2

from _helpers import (
    FakeContext,
    book_api,
    loan_api,
    make_book,
    make_member,
    member_api,
    split_outcomes,
)


def _borrow(pool, book_id: int, member_id: int):
    return loan_api(pool).BorrowBook(
        loan_pb2.BorrowBookRequest(book_id=book_id, member_id=member_id),
        FakeContext(),
    )


async def _book(pool, book_id: int):
    return await book_api(pool).GetBook(
        book_pb2.GetBookRequest(id=book_id), FakeContext()
    )


async def test_only_one_of_many_borrowers_gets_the_last_copy(pool):
    book = await make_book(pool, copies=1)
    members = [await make_member(pool) for _ in range(12)]

    results = await asyncio.gather(
        *(_borrow(pool, book.id, m.id) for m in members), return_exceptions=True
    )
    won, lost = split_outcomes(results)

    assert len(won) == 1
    assert len(lost) == 11
    assert {e.code for e in lost} == {grpc.StatusCode.FAILED_PRECONDITION}
    assert (await _book(pool, book.id)).available_copies == 0


async def test_borrowers_never_exceed_available_copies(pool):
    book = await make_book(pool, copies=4)
    members = [await make_member(pool) for _ in range(10)]

    results = await asyncio.gather(
        *(_borrow(pool, book.id, m.id) for m in members), return_exceptions=True
    )
    won, lost = split_outcomes(results)

    assert len(won) == 4
    assert len(lost) == 6
    assert len({loan.copy_id for loan in won}) == 4  # each copy lent once
    assert (await _book(pool, book.id)).available_copies == 0


async def test_same_member_borrowing_same_book_concurrently_gets_one_loan(pool):
    book = await make_book(pool, copies=3)
    member = await make_member(pool)

    results = await asyncio.gather(
        *(_borrow(pool, book.id, member.id) for _ in range(6)),
        return_exceptions=True,
    )
    won, lost = split_outcomes(results)

    assert len(won) == 1
    assert {e.code for e in lost} == {grpc.StatusCode.FAILED_PRECONDITION}
    # Failed attempts must roll back their copy claim.
    assert (await _book(pool, book.id)).available_copies == 2


async def test_concurrent_returns_of_one_loan_free_the_copy_only_once(pool):
    book = await make_book(pool, copies=1)
    member = await make_member(pool)
    loan = await _borrow(pool, book.id, member.id)

    results = await asyncio.gather(
        *(
            loan_api(pool).ReturnBook(
                loan_pb2.ReturnBookRequest(loan_id=loan.id), FakeContext()
            )
            for _ in range(6)
        ),
        return_exceptions=True,
    )
    won, lost = split_outcomes(results)

    assert len(won) == 1
    assert {e.code for e in lost} == {grpc.StatusCode.FAILED_PRECONDITION}
    refreshed = await _book(pool, book.id)
    assert (refreshed.total_copies, refreshed.available_copies) == (1, 1)


async def test_returned_copy_can_be_borrowed_again_under_contention(pool):
    book = await make_book(pool, copies=1)
    first = await make_member(pool)
    contenders = [await make_member(pool) for _ in range(6)]
    loan = await _borrow(pool, book.id, first.id)

    return_call = loan_api(pool).ReturnBook(
        loan_pb2.ReturnBookRequest(loan_id=loan.id), FakeContext()
    )
    results = await asyncio.gather(
        return_call,
        *(_borrow(pool, book.id, m.id) for m in contenders),
        return_exceptions=True,
    )
    won, _ = split_outcomes(results)

    # Whatever the interleaving, the copy is either out with exactly one
    # active borrower or back on the shelf — never lent twice.
    active = await loan_api(pool).ListLoans(
        loan_pb2.ListLoansRequest(book_id=book.id, only_active=True), FakeContext()
    )
    available = (await _book(pool, book.id)).available_copies
    assert len(active.loans) + available == 1


async def test_concurrent_member_creation_with_same_email_creates_one(pool):
    results = await asyncio.gather(
        *(
            member_api(pool).CreateMember(
                member_pb2.CreateMemberRequest(
                    first_name="Race", last_name="Condition", email="race@example.com"
                ),
                FakeContext(),
            )
            for _ in range(8)
        ),
        return_exceptions=True,
    )
    won, lost = split_outcomes(results)

    assert len(won) == 1
    assert {e.code for e in lost} == {grpc.StatusCode.ALREADY_EXISTS}


async def test_concurrent_book_creation_with_same_isbn_creates_one_with_its_copies(pool):
    results = await asyncio.gather(
        *(
            book_api(pool).CreateBook(
                book_pb2.CreateBookRequest(
                    isbn="978-0-13-468599-1", title="Race", author="A", initial_copies=2
                ),
                FakeContext(),
            )
            for _ in range(8)
        ),
        return_exceptions=True,
    )
    won, lost = split_outcomes(results)

    assert len(won) == 1
    assert {e.code for e in lost} == {grpc.StatusCode.ALREADY_EXISTS}
    # Losers' transactions rolled back, so no orphaned copies were added.
    assert (await _book(pool, won[0].id)).total_copies == 2


async def test_concurrent_add_copies_all_apply(pool):
    book = await make_book(pool, copies=1)

    results = await asyncio.gather(
        *(
            book_api(pool).AddBookCopies(
                book_pb2.AddBookCopiesRequest(book_id=book.id, count=2), FakeContext()
            )
            for _ in range(10)
        ),
        return_exceptions=True,
    )
    won, lost = split_outcomes(results)

    assert (len(won), len(lost)) == (10, 0)
    refreshed = await _book(pool, book.id)
    assert (refreshed.total_copies, refreshed.available_copies) == (21, 21)
