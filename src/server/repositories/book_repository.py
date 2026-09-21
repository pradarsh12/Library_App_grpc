"""SQL for books and their physical copies.

`total_copies`/`available_copies` are always computed from `book_copies`
via the query below rather than stored on `books`, so they can never drift.

Repositories only run SQL on the connection they are given and return domain
objects; business rules and transaction boundaries live in the services.
"""

from __future__ import annotations

import asyncpg

from server.domain.models import Book, CopyStatus
from server.errors import AlreadyExistsError
from server.repositories._search import like_pattern

_BOOK_SELECT = """
    SELECT
        b.id, b.isbn, b.title, b.author, b.publisher, b.published_year, b.genre,
        b.created_at, b.updated_at,
        COUNT(bc.id) AS total_copies,
        COUNT(bc.id) FILTER (WHERE bc.status = 'available') AS available_copies
    FROM books b
    LEFT JOIN book_copies bc ON bc.book_id = b.id
"""


def _to_book(row: asyncpg.Record) -> Book:
    return Book(
        id=row["id"],
        isbn=row["isbn"],
        title=row["title"],
        author=row["author"],
        publisher=row["publisher"],
        published_year=row["published_year"],
        genre=row["genre"],
        total_copies=row["total_copies"],
        available_copies=row["available_copies"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _duplicate_isbn(isbn: str | None) -> AlreadyExistsError:
    return AlreadyExistsError(f"a book with isbn '{isbn}' already exists")


class BookRepository:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def get(self, book_id: int) -> Book | None:
        row = await self._conn.fetchrow(
            f"{_BOOK_SELECT} WHERE b.id = $1 GROUP BY b.id", book_id
        )
        return _to_book(row) if row else None

    async def exists(self, book_id: int) -> bool:
        found = await self._conn.fetchval("SELECT 1 FROM books WHERE id = $1", book_id)
        return found is not None

    async def list(
        self, *, search: str, isbn_search: str, limit: int, offset: int
    ) -> list[Book]:
        """`isbn_search` is `search` in normalized-ISBN form, since ISBNs are
        stored normalized."""
        rows = await self._conn.fetch(
            f"""{_BOOK_SELECT}
                WHERE ($1::text IS NULL
                       OR b.title ILIKE $1
                       OR b.author ILIKE $1
                       OR b.isbn ILIKE $4)
                GROUP BY b.id
                ORDER BY b.title, b.id
                LIMIT $2 OFFSET $3""",
            like_pattern(search),
            limit,
            offset,
            like_pattern(isbn_search),
        )
        return [_to_book(r) for r in rows]

    async def insert(
        self,
        *,
        isbn: str | None,
        title: str,
        author: str,
        publisher: str | None,
        published_year: int | None,
        genre: str | None,
    ) -> int:
        try:
            return await self._conn.fetchval(
                """INSERT INTO books (isbn, title, author, publisher, published_year, genre)
                   VALUES ($1, $2, $3, $4, $5, $6)
                   RETURNING id""",
                isbn,
                title,
                author,
                publisher,
                published_year,
                genre,
            )
        except asyncpg.UniqueViolationError as exc:
            raise _duplicate_isbn(isbn) from exc

    async def update(
        self,
        book_id: int,
        *,
        isbn: str | None,
        title: str,
        author: str,
        publisher: str | None,
        published_year: int | None,
        genre: str | None,
    ) -> bool:
        """Returns False when no book has `book_id`."""
        try:
            updated = await self._conn.fetchval(
                """UPDATE books
                   SET isbn = $2, title = $3, author = $4, publisher = $5,
                       published_year = $6, genre = $7, updated_at = now()
                   WHERE id = $1
                   RETURNING id""",
                book_id,
                isbn,
                title,
                author,
                publisher,
                published_year,
                genre,
            )
        except asyncpg.UniqueViolationError as exc:
            raise _duplicate_isbn(isbn) from exc
        return updated is not None

    async def add_copies(self, book_id: int, count: int) -> None:
        await self._conn.executemany(
            "INSERT INTO book_copies (book_id) VALUES ($1)",
            [(book_id,)] * count,
        )

    async def claim_available_copy(self, book_id: int) -> int | None:
        """Lock and return the id of one available copy, skipping copies
        already locked by a concurrent transaction. Must run inside one."""
        row = await self._conn.fetchrow(
            """SELECT id FROM book_copies
               WHERE book_id = $1 AND status = 'available'
               ORDER BY id
               LIMIT 1
               FOR UPDATE SKIP LOCKED""",
            book_id,
        )
        return row["id"] if row else None

    async def set_copy_status(self, copy_id: int, status: CopyStatus) -> None:
        await self._conn.execute(
            "UPDATE book_copies SET status = $2, updated_at = now() WHERE id = $1",
            copy_id,
            status.value,
        )
