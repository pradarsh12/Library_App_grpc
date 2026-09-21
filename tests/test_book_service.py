from __future__ import annotations

import grpc
import pytest

from library.v1 import book_pb2
from server.services.book_service import BookService

from _helpers import AbortedError, FakeContext


async def test_create_and_get_book(pool):
    service = BookService(pool)
    ctx = FakeContext()

    created = await service.CreateBook(
        book_pb2.CreateBookRequest(
            title="Dune", author="Frank Herbert", initial_copies=3
        ),
        ctx,
    )
    assert created.id > 0
    assert created.total_copies == 3
    assert created.available_copies == 3

    fetched = await service.GetBook(book_pb2.GetBookRequest(id=created.id), ctx)
    assert fetched.title == "Dune"
    assert fetched.author == "Frank Herbert"


async def test_create_book_requires_title():
    service = BookService(pool=None)  # never reaches the DB
    with pytest.raises(AbortedError) as exc_info:
        await service.CreateBook(
            book_pb2.CreateBookRequest(title="", author="Someone"), FakeContext()
        )
    assert exc_info.value.code == grpc.StatusCode.INVALID_ARGUMENT


async def test_get_missing_book_raises_not_found(pool):
    service = BookService(pool)
    with pytest.raises(AbortedError) as exc_info:
        await service.GetBook(book_pb2.GetBookRequest(id=999_999), FakeContext())
    assert exc_info.value.code == grpc.StatusCode.NOT_FOUND


async def test_add_book_copies_increases_availability(pool):
    service = BookService(pool)
    ctx = FakeContext()
    book = await service.CreateBook(
        book_pb2.CreateBookRequest(title="1984", author="Orwell", initial_copies=1),
        ctx,
    )

    grown = await service.AddBookCopies(
        book_pb2.AddBookCopiesRequest(book_id=book.id, count=2), ctx
    )
    assert grown.book.total_copies == 3
    assert grown.book.available_copies == 3


async def test_duplicate_isbn_rejected(pool):
    service = BookService(pool)
    ctx = FakeContext()
    await service.CreateBook(
        book_pb2.CreateBookRequest(isbn="123", title="Book A", author="X"), ctx
    )
    with pytest.raises(AbortedError) as exc_info:
        await service.CreateBook(
            book_pb2.CreateBookRequest(isbn="123", title="Book B", author="Y"), ctx
        )
    assert exc_info.value.code == grpc.StatusCode.ALREADY_EXISTS


@pytest.mark.parametrize(
    "kwargs",
    [
        {"title": "x" * 256, "author": "A"},
        {"title": "T", "author": "A", "isbn": "9" * 33},
        {"title": "T", "author": "A", "initial_copies": 1001},
    ],
)
async def test_create_book_rejects_oversized_input(kwargs):
    service = BookService(pool=None)  # never reaches the DB
    with pytest.raises(AbortedError) as exc_info:
        await service.CreateBook(book_pb2.CreateBookRequest(**kwargs), FakeContext())
    assert exc_info.value.code == grpc.StatusCode.INVALID_ARGUMENT


async def test_add_book_copies_rejects_huge_count():
    service = BookService(pool=None)
    with pytest.raises(AbortedError) as exc_info:
        await service.AddBookCopies(
            book_pb2.AddBookCopiesRequest(book_id=1, count=10_000_000), FakeContext()
        )
    assert exc_info.value.code == grpc.StatusCode.INVALID_ARGUMENT


@pytest.mark.parametrize("token", ["abc", "-5", "1.5"])
async def test_list_books_rejects_invalid_page_token(token):
    from library.v1 import common_pb2

    service = BookService(pool=None)
    with pytest.raises(AbortedError) as exc_info:
        await service.ListBooks(
            book_pb2.ListBooksRequest(page=common_pb2.PageRequest(page_token=token)),
            FakeContext(),
        )
    assert exc_info.value.code == grpc.StatusCode.INVALID_ARGUMENT
