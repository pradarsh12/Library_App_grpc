"""Paging behaviour of every List* RPC, driven through the gRPC servicers."""

from __future__ import annotations

import grpc
import pytest

from library.v1 import book_pb2, common_pb2, loan_pb2, member_pb2

from _helpers import (
    AbortedError,
    FakeContext,
    book_api,
    loan_api,
    make_book,
    make_member,
    member_api,
)


async def _book_page(pool, *, size=0, token="", search=""):
    return await book_api(pool).ListBooks(
        book_pb2.ListBooksRequest(
            search=search,
            page=common_pb2.PageRequest(page_size=size, page_token=token),
        ),
        FakeContext(),
    )


async def _make_numbered_books(pool, count: int) -> list[int]:
    """Books whose titles sort in creation order: Book 01, Book 02, ..."""
    return [
        (await make_book(pool, title=f"Book {i:02d}")).id for i in range(1, count + 1)
    ]


async def test_walking_all_pages_returns_every_book_once_in_order(pool):
    expected_ids = await _make_numbered_books(pool, 7)

    seen, token, pages = [], "", 0
    while True:
        response = await _book_page(pool, size=3, token=token)
        seen.extend(b.id for b in response.books)
        pages += 1
        token = response.page.next_page_token
        if not token:
            break

    assert seen == expected_ids
    assert pages == 3  # 3 + 3 + 1


async def test_exact_multiple_of_page_size_has_no_trailing_empty_page(pool):
    await _make_numbered_books(pool, 4)

    first = await _book_page(pool, size=2)
    assert len(first.books) == 2
    assert first.page.next_page_token != ""

    last = await _book_page(pool, size=2, token=first.page.next_page_token)
    assert len(last.books) == 2
    assert last.page.next_page_token == ""


async def test_single_page_has_no_next_token(pool):
    await _make_numbered_books(pool, 3)
    response = await _book_page(pool, size=10)
    assert len(response.books) == 3
    assert response.page.next_page_token == ""


async def test_empty_result_has_no_next_token(pool):
    response = await _book_page(pool, size=5)
    assert list(response.books) == []
    assert response.page.next_page_token == ""


async def test_token_past_the_end_returns_empty_page(pool):
    await _make_numbered_books(pool, 2)
    response = await _book_page(pool, token="500")
    assert list(response.books) == []
    assert response.page.next_page_token == ""


async def test_default_page_size_is_20(pool):
    await _make_numbered_books(pool, 22)
    response = await _book_page(pool)
    assert len(response.books) == 20
    assert response.page.next_page_token == "20"


async def test_page_size_is_capped_at_100(pool):
    await _make_numbered_books(pool, 101)
    response = await _book_page(pool, size=10_000)
    assert len(response.books) == 100
    assert response.page.next_page_token == "100"


async def test_negative_page_size_falls_back_to_a_single_row_page(pool):
    await _make_numbered_books(pool, 3)
    response = await _book_page(pool, size=-5)
    assert len(response.books) == 1


async def test_pagination_applies_after_search_filter(pool):
    for i in range(5):
        await make_book(pool, title=f"Match {i}")
    await make_book(pool, title="Other")

    first = await _book_page(pool, size=3, search="match")
    assert [b.title for b in first.books] == ["Match 0", "Match 1", "Match 2"]
    second = await _book_page(
        pool, size=3, search="match", token=first.page.next_page_token
    )
    assert [b.title for b in second.books] == ["Match 3", "Match 4"]
    assert second.page.next_page_token == ""


@pytest.mark.parametrize("token", ["abc", "-1", "1.5", " ", "1e3"])
async def test_invalid_page_tokens_are_rejected(pool, token):
    with pytest.raises(AbortedError) as exc_info:
        await _book_page(pool, token=token)
    assert exc_info.value.code == grpc.StatusCode.INVALID_ARGUMENT


async def test_members_are_paginated(pool):
    for i in range(5):
        await make_member(pool, first_name=f"M{i}", last_name="Smith")

    service = member_api(pool)
    first = await service.ListMembers(
        member_pb2.ListMembersRequest(page=common_pb2.PageRequest(page_size=2)),
        FakeContext(),
    )
    assert [m.first_name for m in first.members] == ["M0", "M1"]
    assert first.page.next_page_token == "2"

    last = await service.ListMembers(
        member_pb2.ListMembersRequest(
            page=common_pb2.PageRequest(page_size=2, page_token="4")
        ),
        FakeContext(),
    )
    assert [m.first_name for m in last.members] == ["M4"]
    assert last.page.next_page_token == ""


async def test_loans_are_paginated_newest_first(pool):
    member = await make_member(pool)
    loans = loan_api(pool)
    loan_ids = []
    for i in range(5):
        book = await make_book(pool, title=f"Title {i}")
        loan = await loans.BorrowBook(
            loan_pb2.BorrowBookRequest(book_id=book.id, member_id=member.id),
            FakeContext(),
        )
        loan_ids.append(loan.id)

    seen, token = [], ""
    while True:
        response = await loans.ListLoans(
            loan_pb2.ListLoansRequest(
                member_id=member.id,
                page=common_pb2.PageRequest(page_size=2, page_token=token),
            ),
            FakeContext(),
        )
        seen.extend(loan.id for loan in response.loans)
        token = response.page.next_page_token
        if not token:
            break

    assert seen == list(reversed(loan_ids))
