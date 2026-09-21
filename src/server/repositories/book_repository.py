"""Data access for books and their physical copies.

`total_copies`/`available_copies` are always computed from `book_copies`
via the query below rather than stored on `books`, so they can never drift.
"""

from __future__ import annotations

import re

import asyncpg

from server.repositories._search import like_pattern
from server.errors import AlreadyExistsError, NotFoundError, ValidationError

_BOOK_SELECT = """
    SELECT
        b.id, b.isbn, b.title, b.author, b.publisher, b.published_year, b.genre,
        b.created_at, b.updated_at,
        COUNT(bc.id) AS total_copies,
        COUNT(bc.id) FILTER (WHERE bc.status = 'available') AS available_copies
    FROM books b
    LEFT JOIN book_copies bc ON bc.book_id = b.id
"""


async def _fetch_book(conn: asyncpg.Connection, book_id: int) -> asyncpg.Record:
    row = await conn.fetchrow(
        f"{_BOOK_SELECT} WHERE b.id = $1 GROUP BY b.id", book_id
    )
    if row is None:
        raise NotFoundError(f"book {book_id} not found")
    return row


async def create_book(
    pool: asyncpg.Pool,
    *,
    isbn: str | None,
    title: str,
    author: str,
    publisher: str | None,
    published_year: int | None,
    genre: str | None,
    initial_copies: int,
) -> asyncpg.Record:
    async with pool.acquire() as conn:
        async with conn.transaction():
            try:
                book_id = await conn.fetchval(
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
                raise AlreadyExistsError(
                    f"a book with isbn '{isbn}' already exists"
                ) from exc

            await conn.executemany(
                "INSERT INTO book_copies (book_id) VALUES ($1)",
                [(book_id,)] * initial_copies,
            )
            return await _fetch_book(conn, book_id)


async def update_book(
    pool: asyncpg.Pool,
    *,
    book_id: int,
    isbn: str | None,
    title: str,
    author: str,
    publisher: str | None,
    published_year: int | None,
    genre: str | None,
) -> asyncpg.Record:
    async with pool.acquire() as conn:
        async with conn.transaction():
            try:
                updated = await conn.fetchval(
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
                raise AlreadyExistsError(
                    f"a book with isbn '{isbn}' already exists"
                ) from exc
            if updated is None:
                raise NotFoundError(f"book {book_id} not found")
            return await _fetch_book(conn, book_id)


async def get_book(pool: asyncpg.Pool, book_id: int) -> asyncpg.Record:
    async with pool.acquire() as conn:
        return await _fetch_book(conn, book_id)


async def list_books(
    pool: asyncpg.Pool, *, search: str, limit: int, offset: int
) -> list[asyncpg.Record]:
    pattern = like_pattern(search)
    # ISBNs are stored normalized, so match them against the normalized term.
    isbn_pattern = like_pattern(re.sub(r"[\s-]", "", search).upper())
    async with pool.acquire() as conn:
        return await conn.fetch(
            f"""{_BOOK_SELECT}
                WHERE ($1::text IS NULL
                       OR b.title ILIKE $1
                       OR b.author ILIKE $1
                       OR b.isbn ILIKE $4)
                GROUP BY b.id
                ORDER BY b.title, b.id
                LIMIT $2 OFFSET $3""",
            pattern,
            limit,
            offset,
            isbn_pattern,
        )


async def add_book_copies(
    pool: asyncpg.Pool, *, book_id: int, count: int
) -> asyncpg.Record:
    if count <= 0:
        raise ValidationError("count must be > 0")
    async with pool.acquire() as conn:
        async with conn.transaction():
            exists = await conn.fetchval("SELECT 1 FROM books WHERE id = $1", book_id)
            if exists is None:
                raise NotFoundError(f"book {book_id} not found")
            await conn.executemany(
                "INSERT INTO book_copies (book_id) VALUES ($1)",
                [(book_id,)] * count,
            )
            return await _fetch_book(conn, book_id)
