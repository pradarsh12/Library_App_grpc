"""Edge cases for books and loans not covered by the happy-path tests."""

from __future__ import annotations

import datetime as dt

import grpc
import pytest

from library.v1 import book_pb2, common_pb2, loan_pb2

from _helpers import (
    AbortedError,
    FakeContext,
    book_api,
    loan_api,
    make_book,
    make_member,
)
from server.config import settings


async def _code(coro) -> grpc.StatusCode:
    with pytest.raises(AbortedError) as exc_info:
        await coro
    return exc_info.value.code


def _borrow(pool, book_id, member_id, **fields):
    return loan_api(pool).BorrowBook(
        loan_pb2.BorrowBookRequest(book_id=book_id, member_id=member_id, **fields),
        FakeContext(),
    )


# --- books -----------------------------------------------------------------


async def test_create_book_defaults_to_one_copy(pool):
    book = await book_api(pool).CreateBook(
        book_pb2.CreateBookRequest(title="Solo", author="A"), FakeContext()
    )
    assert (book.total_copies, book.available_copies) == (1, 1)


async def test_isbn_is_stored_normalized(pool):
    book = await make_book(pool, isbn=" 0-8044-2957-x ")
    assert book.isbn == "080442957X"


async def test_same_isbn_in_different_formats_is_a_duplicate(pool):
    await make_book(pool, title="A", isbn="978-0-13-468599-1")
    code = await _code(make_book(pool, title="B", isbn="9780134685991"))
    assert code == grpc.StatusCode.ALREADY_EXISTS


async def test_books_without_isbn_do_not_conflict(pool):
    await make_book(pool, title="A")
    await make_book(pool, title="B")  # two NULL isbns are allowed


async def test_create_book_optional_fields_round_trip(pool):
    book = await make_book(
        pool, publisher="Ace", published_year=1965, genre="Sci-Fi"
    )
    assert (book.publisher, book.published_year, book.genre) == ("Ace", 1965, "Sci-Fi")


@pytest.mark.parametrize("year", [1399, 2101, -5])
async def test_implausible_publication_year_rejected(year):
    code = await _code(
        book_api(pool=None).CreateBook(
            book_pb2.CreateBookRequest(title="T", author="A", published_year=year),
            FakeContext(),
        )
    )
    assert code == grpc.StatusCode.INVALID_ARGUMENT


@pytest.mark.parametrize("year", [1400, 2100])
async def test_publication_year_boundaries_accepted(pool, year):
    book = await make_book(pool, published_year=year)
    assert book.published_year == year


async def test_update_book_changes_fields_and_keeps_copies(pool):
    book = await make_book(pool, title="Old", copies=3)
    updated = await book_api(pool).UpdateBook(
        book_pb2.UpdateBookRequest(
            id=book.id, title="New", author="Other", genre="Drama"
        ),
        FakeContext(),
    )
    assert (updated.title, updated.author, updated.genre) == ("New", "Other", "Drama")
    assert updated.total_copies == 3


async def test_update_missing_book_is_not_found(pool):
    code = await _code(
        book_api(pool).UpdateBook(
            book_pb2.UpdateBookRequest(id=999_999, title="T", author="A"),
            FakeContext(),
        )
    )
    assert code == grpc.StatusCode.NOT_FOUND


async def test_update_book_to_taken_isbn_rejected(pool):
    await make_book(pool, title="A", isbn="111")
    other = await make_book(pool, title="B", isbn="222")
    code = await _code(
        book_api(pool).UpdateBook(
            book_pb2.UpdateBookRequest(id=other.id, title="B", author="X", isbn="111"),
            FakeContext(),
        )
    )
    assert code == grpc.StatusCode.ALREADY_EXISTS


async def test_add_copies_to_missing_book_is_not_found(pool):
    code = await _code(
        book_api(pool).AddBookCopies(
            book_pb2.AddBookCopiesRequest(book_id=999_999, count=1), FakeContext()
        )
    )
    assert code == grpc.StatusCode.NOT_FOUND


@pytest.mark.parametrize("count", [0, -3])
async def test_add_copies_requires_positive_count(count):
    code = await _code(
        book_api(pool=None).AddBookCopies(
            book_pb2.AddBookCopiesRequest(book_id=1, count=count), FakeContext()
        )
    )
    assert code == grpc.StatusCode.INVALID_ARGUMENT


async def _titles(pool, term: str) -> list[str]:
    response = await book_api(pool).ListBooks(
        book_pb2.ListBooksRequest(search=term), FakeContext()
    )
    return [b.title for b in response.books]


async def test_search_matches_title_and_author_case_insensitively(pool):
    await make_book(pool, title="Dune", author="Frank Herbert")
    await make_book(pool, title="Emma", author="Jane Austen")

    assert await _titles(pool, "DUNE") == ["Dune"]
    assert await _titles(pool, "austen") == ["Emma"]
    assert await _titles(pool, "  frank    herbert ") == ["Dune"]
    assert await _titles(pool, "missing") == []


async def test_search_matches_isbn_in_any_format(pool):
    await make_book(pool, title="Clean Code", isbn="978-0-13-235088-4")
    await make_book(pool, title="Other", isbn="111-1-11-111111-1")

    assert await _titles(pool, "978-0-13") == ["Clean Code"]
    assert await _titles(pool, "9780132350884") == ["Clean Code"]
    assert await _titles(pool, "978 0 13 235088") == ["Clean Code"]


async def test_search_treats_wildcards_literally(pool):
    await make_book(pool, title="100% Cotton")
    await make_book(pool, title="snake_case")
    await make_book(pool, title="Plain")

    assert await _titles(pool, "%") == ["100% Cotton"]
    assert await _titles(pool, "_") == ["snake_case"]


async def test_list_books_orders_by_title(pool):
    for title in ["Charlie", "Alpha", "Bravo"]:
        await make_book(pool, title=title)
    assert await _titles(pool, "") == ["Alpha", "Bravo", "Charlie"]


async def test_available_copies_tracks_loans(pool):
    book = await make_book(pool, copies=3)
    member = await make_member(pool)
    await _borrow(pool, book.id, member.id)

    refreshed = await book_api(pool).GetBook(
        book_pb2.GetBookRequest(id=book.id), FakeContext()
    )
    assert (refreshed.total_copies, refreshed.available_copies) == (3, 2)


# --- loans -----------------------------------------------------------------


def _loan_days(loan: loan_pb2.Loan) -> int:
    span = loan.due_at.ToDatetime() - loan.borrowed_at.ToDatetime()
    return round(span.total_seconds() / 86400)


async def test_borrow_uses_default_loan_period(pool):
    book, member = await make_book(pool), await make_member(pool)
    loan = await _borrow(pool, book.id, member.id)
    assert _loan_days(loan) == settings.default_loan_period_days


async def test_borrow_honours_custom_loan_period(pool):
    book, member = await make_book(pool), await make_member(pool)
    loan = await _borrow(pool, book.id, member.id, loan_period_days=30)
    assert _loan_days(loan) == 30


@pytest.mark.parametrize("days", [-1, 366])
async def test_borrow_rejects_out_of_range_loan_period(days):
    code = await _code(_borrow(None, 1, 1, loan_period_days=days))
    assert code == grpc.StatusCode.INVALID_ARGUMENT


async def test_loan_period_boundaries_accepted(pool):
    book = await make_book(pool, copies=2)
    a, b = await make_member(pool), await make_member(pool)
    assert _loan_days(await _borrow(pool, book.id, a.id, loan_period_days=1)) == 1
    assert _loan_days(await _borrow(pool, book.id, b.id, loan_period_days=365)) == 365


async def test_borrow_unknown_member_is_not_found_and_keeps_copy_available(pool):
    book = await make_book(pool)
    code = await _code(_borrow(pool, book.id, 999_999))
    assert code == grpc.StatusCode.NOT_FOUND
    refreshed = await book_api(pool).GetBook(
        book_pb2.GetBookRequest(id=book.id), FakeContext()
    )
    assert refreshed.available_copies == 1


@pytest.mark.parametrize(("book_id", "member_id"), [(0, 1), (1, 0), (-1, 1), (1, -1)])
async def test_borrow_requires_positive_ids(book_id, member_id):
    code = await _code(_borrow(None, book_id, member_id))
    assert code == grpc.StatusCode.INVALID_ARGUMENT


async def test_return_unknown_loan_is_not_found(pool):
    code = await _code(
        loan_api(pool).ReturnBook(
            loan_pb2.ReturnBookRequest(loan_id=999_999), FakeContext()
        )
    )
    assert code == grpc.StatusCode.NOT_FOUND


async def test_get_unknown_loan_is_not_found(pool):
    code = await _code(
        loan_api(pool).GetLoan(loan_pb2.GetLoanRequest(loan_id=999_999), FakeContext())
    )
    assert code == grpc.StatusCode.NOT_FOUND


async def test_returning_frees_the_copy_and_member_can_borrow_again(pool):
    book, member = await make_book(pool, copies=1), await make_member(pool)
    first = await _borrow(pool, book.id, member.id)
    await loan_api(pool).ReturnBook(
        loan_pb2.ReturnBookRequest(loan_id=first.id), FakeContext()
    )

    second = await _borrow(pool, book.id, member.id)
    assert second.id != first.id
    assert second.status == loan_pb2.LOAN_STATUS_ACTIVE


async def test_loan_carries_denormalized_names(pool):
    book = await make_book(pool, title="Emma")
    member = await make_member(pool, first_name="Ada", last_name="Lovelace")
    loan = await _borrow(pool, book.id, member.id)
    assert (loan.book_title, loan.member_name) == ("Emma", "Ada Lovelace")
    assert not loan.HasField("returned_at")


async def test_overdue_loan_reports_overdue_until_returned(pool):
    book, member = await make_book(pool), await make_member(pool)
    loan = await _borrow(pool, book.id, member.id)
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE loans SET due_at = now() - interval '2 days' WHERE id = $1",
            loan.id,
        )

    service = loan_api(pool)
    overdue = await service.GetLoan(
        loan_pb2.GetLoanRequest(loan_id=loan.id), FakeContext()
    )
    assert overdue.status == loan_pb2.LOAN_STATUS_OVERDUE

    returned = await service.ReturnBook(
        loan_pb2.ReturnBookRequest(loan_id=loan.id), FakeContext()
    )
    assert returned.status == loan_pb2.LOAN_STATUS_RETURNED


async def test_returned_at_is_set_on_return(pool):
    book, member = await make_book(pool), await make_member(pool)
    loan = await _borrow(pool, book.id, member.id)
    returned = await loan_api(pool).ReturnBook(
        loan_pb2.ReturnBookRequest(loan_id=loan.id), FakeContext()
    )
    assert returned.HasField("returned_at")
    age = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - returned.returned_at.ToDatetime()
    assert abs(age.total_seconds()) < 60


async def _list_loans(pool, **fields):
    response = await loan_api(pool).ListLoans(
        loan_pb2.ListLoansRequest(**fields), FakeContext()
    )
    return list(response.loans)


async def test_list_loans_filters_by_member_book_and_active(pool):
    book_a, book_b = await make_book(pool, title="A", copies=2), await make_book(pool, title="B")
    ann, bob = await make_member(pool), await make_member(pool)

    ann_a = await _borrow(pool, book_a.id, ann.id)
    ann_b = await _borrow(pool, book_b.id, ann.id)
    bob_a = await _borrow(pool, book_a.id, bob.id)
    await loan_api(pool).ReturnBook(
        loan_pb2.ReturnBookRequest(loan_id=ann_b.id), FakeContext()
    )

    def ids(loans):
        return {loan.id for loan in loans}

    assert ids(await _list_loans(pool)) == {ann_a.id, ann_b.id, bob_a.id}
    assert ids(await _list_loans(pool, member_id=ann.id)) == {ann_a.id, ann_b.id}
    assert ids(await _list_loans(pool, book_id=book_a.id)) == {ann_a.id, bob_a.id}
    assert ids(await _list_loans(pool, only_active=True)) == {ann_a.id, bob_a.id}
    assert ids(
        await _list_loans(pool, member_id=ann.id, only_active=True)
    ) == {ann_a.id}
    assert ids(
        await _list_loans(pool, member_id=bob.id, book_id=book_b.id)
    ) == set()


async def test_list_loans_includes_returned_loans_by_default(pool):
    book, member = await make_book(pool), await make_member(pool)
    loan = await _borrow(pool, book.id, member.id)
    await loan_api(pool).ReturnBook(
        loan_pb2.ReturnBookRequest(loan_id=loan.id), FakeContext()
    )

    loans = await _list_loans(pool, member_id=member.id)
    assert [l.status for l in loans] == [loan_pb2.LOAN_STATUS_RETURNED]
    assert await _list_loans(pool, member_id=member.id, only_active=True) == []


async def test_list_loans_rejects_bad_page_token(pool):
    code = await _code(
        loan_api(pool).ListLoans(
            loan_pb2.ListLoansRequest(page=common_pb2.PageRequest(page_token="x")),
            FakeContext(),
        )
    )
    assert code == grpc.StatusCode.INVALID_ARGUMENT
