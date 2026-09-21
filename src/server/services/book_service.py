"""Book use cases: validation, defaults and transaction boundaries."""

from __future__ import annotations

from server import validation
from server.db.database import Database, Repositories
from server.domain.models import Book
from server.domain.pagination import Page, PageParams, paginate
from server.errors import NotFoundError


def _not_found(book_id: int) -> NotFoundError:
    return NotFoundError(f"book {book_id} not found")


def _normalized_isbn(raw: str) -> str | None:
    isbn = validation.optional_text(raw, "isbn", max_length=validation.MAX_ISBN_LEN)
    return validation.normalize_isbn(isbn) if isbn else None


class BookService:
    def __init__(self, db: Database) -> None:
        self._db = db

    @staticmethod
    def _validated_fields(
        *,
        title: str,
        author: str,
        published_year: int,
        isbn: str,
        publisher: str,
        genre: str,
    ) -> dict:
        return {
            "title": validation.require_non_empty(
                title, "title", max_length=validation.MAX_TITLE_LEN
            ),
            "author": validation.require_non_empty(
                author, "author", max_length=validation.MAX_TITLE_LEN
            ),
            "published_year": validation.require_year(published_year),
            "isbn": _normalized_isbn(isbn),
            "publisher": validation.optional_text(
                publisher, "publisher", max_length=validation.MAX_TITLE_LEN
            ),
            "genre": validation.optional_text(
                genre, "genre", max_length=validation.MAX_GENRE_LEN
            ),
        }

    async def create_book(
        self,
        *,
        title: str,
        author: str,
        published_year: int,
        isbn: str,
        publisher: str,
        genre: str,
        initial_copies: int,
    ) -> Book:
        fields = self._validated_fields(
            title=title,
            author=author,
            published_year=published_year,
            isbn=isbn,
            publisher=publisher,
            genre=genre,
        )
        initial_copies = initial_copies or 1
        validation.require_positive_int(
            initial_copies, "initial_copies", maximum=validation.MAX_COPIES
        )

        async with self._db.transaction() as repos:
            book_id = await repos.books.insert(**fields)
            await repos.books.add_copies(book_id, initial_copies)
            return await self._get(repos, book_id)

    async def update_book(
        self,
        *,
        book_id: int,
        title: str,
        author: str,
        published_year: int,
        isbn: str,
        publisher: str,
        genre: str,
    ) -> Book:
        book_id = validation.require_positive_id(book_id, "id")
        fields = self._validated_fields(
            title=title,
            author=author,
            published_year=published_year,
            isbn=isbn,
            publisher=publisher,
            genre=genre,
        )

        async with self._db.transaction() as repos:
            if not await repos.books.update(book_id, **fields):
                raise _not_found(book_id)
            return await self._get(repos, book_id)

    async def get_book(self, book_id: int) -> Book:
        book_id = validation.require_positive_id(book_id, "id")
        async with self._db.session() as repos:
            return await self._get(repos, book_id)

    async def list_books(
        self, *, search: str, page_size: int, offset: int
    ) -> Page[Book]:
        search = validation.require_search(search)
        params = PageParams.of(page_size, offset)
        async with self._db.session() as repos:
            books = await repos.books.list(
                search=search,
                isbn_search=validation.normalize_isbn(search),
                limit=params.size + 1,
                offset=params.offset,
            )
        return paginate(books, params)

    async def add_book_copies(self, *, book_id: int, count: int) -> Book:
        book_id = validation.require_positive_id(book_id, "book_id")
        count = validation.require_positive_int(
            count, "count", maximum=validation.MAX_COPIES
        )
        async with self._db.transaction() as repos:
            if not await repos.books.exists(book_id):
                raise _not_found(book_id)
            await repos.books.add_copies(book_id, count)
            return await self._get(repos, book_id)

    @staticmethod
    async def _get(repos: Repositories, book_id: int) -> Book:
        book = await repos.books.get(book_id)
        if book is None:
            raise _not_found(book_id)
        return book
