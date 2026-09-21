"""BookService gRPC servicer."""

from __future__ import annotations

import asyncpg

from library.v1 import book_pb2, book_pb2_grpc

from server import mappers, validation
from server.errors import handle_errors
from server.pagination import build_page_response, parse_page
from server.repositories import book_repository


def _optional_fields(request) -> tuple[str | None, str | None, str | None]:
    return (
        validation.optional_text(request.isbn, "isbn", max_length=validation.MAX_ISBN_LEN),
        validation.optional_text(
            request.publisher, "publisher", max_length=validation.MAX_TITLE_LEN
        ),
        validation.optional_text(
            request.genre, "genre", max_length=validation.MAX_GENRE_LEN
        ),
    )


class BookService(book_pb2_grpc.BookServiceServicer):
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @handle_errors
    async def CreateBook(self, request: book_pb2.CreateBookRequest, context):
        title = validation.require_non_empty(
            request.title, "title", max_length=validation.MAX_TITLE_LEN
        )
        author = validation.require_non_empty(
            request.author, "author", max_length=validation.MAX_TITLE_LEN
        )
        published_year = validation.require_year(request.published_year)
        isbn, publisher, genre = _optional_fields(request)
        initial_copies = request.initial_copies or 1
        validation.require_positive_int(
            initial_copies, "initial_copies", maximum=validation.MAX_COPIES
        )

        row = await book_repository.create_book(
            self._pool,
            isbn=isbn,
            title=title,
            author=author,
            publisher=publisher,
            published_year=published_year,
            genre=genre,
            initial_copies=initial_copies,
        )
        return mappers.book_to_proto(row)

    @handle_errors
    async def UpdateBook(self, request: book_pb2.UpdateBookRequest, context):
        book_id = validation.require_positive_id(request.id, "id")
        title = validation.require_non_empty(
            request.title, "title", max_length=validation.MAX_TITLE_LEN
        )
        author = validation.require_non_empty(
            request.author, "author", max_length=validation.MAX_TITLE_LEN
        )
        published_year = validation.require_year(request.published_year)
        isbn, publisher, genre = _optional_fields(request)

        row = await book_repository.update_book(
            self._pool,
            book_id=book_id,
            isbn=isbn,
            title=title,
            author=author,
            publisher=publisher,
            published_year=published_year,
            genre=genre,
        )
        return mappers.book_to_proto(row)

    @handle_errors
    async def GetBook(self, request: book_pb2.GetBookRequest, context):
        book_id = validation.require_positive_id(request.id, "id")
        row = await book_repository.get_book(self._pool, book_id)
        return mappers.book_to_proto(row)

    @handle_errors
    async def ListBooks(self, request: book_pb2.ListBooksRequest, context):
        size, offset = parse_page(request.page)
        rows = await book_repository.list_books(
            self._pool,
            search=validation.require_search(request.search),
            limit=size + 1,
            offset=offset,
        )
        page_rows, page = build_page_response(rows, size, offset)
        return book_pb2.ListBooksResponse(
            books=[mappers.book_to_proto(r) for r in page_rows], page=page
        )

    @handle_errors
    async def AddBookCopies(self, request: book_pb2.AddBookCopiesRequest, context):
        book_id = validation.require_positive_id(request.book_id, "book_id")
        count = validation.require_positive_int(
            request.count, "count", maximum=validation.MAX_COPIES
        )
        row = await book_repository.add_book_copies(
            self._pool, book_id=book_id, count=count
        )
        return book_pb2.AddBookCopiesResponse(book=mappers.book_to_proto(row))
