"""BookService gRPC servicer: translates between protobuf and BookService."""

from __future__ import annotations

from library.v1 import book_pb2, book_pb2_grpc

from server import mappers
from server.api.error_handling import handle_errors
from server.api.paging import page_args, page_response
from server.services.book_service import BookService


class BookServicer(book_pb2_grpc.BookServiceServicer):
    def __init__(self, service: BookService) -> None:
        self._service = service

    @handle_errors
    async def CreateBook(self, request: book_pb2.CreateBookRequest, context):
        book = await self._service.create_book(
            title=request.title,
            author=request.author,
            published_year=request.published_year,
            isbn=request.isbn,
            publisher=request.publisher,
            genre=request.genre,
            initial_copies=request.initial_copies,
        )
        return mappers.book_to_proto(book)

    @handle_errors
    async def UpdateBook(self, request: book_pb2.UpdateBookRequest, context):
        book = await self._service.update_book(
            book_id=request.id,
            title=request.title,
            author=request.author,
            published_year=request.published_year,
            isbn=request.isbn,
            publisher=request.publisher,
            genre=request.genre,
        )
        return mappers.book_to_proto(book)

    @handle_errors
    async def GetBook(self, request: book_pb2.GetBookRequest, context):
        return mappers.book_to_proto(await self._service.get_book(request.id))

    @handle_errors
    async def ListBooks(self, request: book_pb2.ListBooksRequest, context):
        page = await self._service.list_books(
            search=request.search, **page_args(request.page)
        )
        return book_pb2.ListBooksResponse(
            books=[mappers.book_to_proto(b) for b in page.items],
            page=page_response(page),
        )

    @handle_errors
    async def AddBookCopies(self, request: book_pb2.AddBookCopiesRequest, context):
        book = await self._service.add_book_copies(
            book_id=request.book_id, count=request.count
        )
        return book_pb2.AddBookCopiesResponse(book=mappers.book_to_proto(book))
