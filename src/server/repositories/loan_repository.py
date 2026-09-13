"""Data access for borrow/return operations.

`borrow_book` is the concurrency-critical path: it uses
`SELECT ... FOR UPDATE SKIP LOCKED` inside a transaction to atomically claim
one available copy, plus the DB's `uq_loans_active_copy` partial unique
index as a second line of defense, so many simultaneous `BorrowBook` calls
for the same title never double-checkout a copy. The same pattern (app-level
check + partial unique index as the concurrency-safe backstop) also
prevents a member from holding two simultaneous active loans of the same
book — see `uq_loans_active_member_book` in db/schema.sql.
"""

from __future__ import annotations

import datetime as dt

import asyncpg

from server.errors import ConflictError, NotFoundError

_LOAN_SELECT = """
    SELECT
        l.id, l.copy_id, l.book_id, l.member_id, l.borrowed_at, l.due_at,
        l.returned_at,
        b.title AS book_title,
        (m.first_name || ' ' || m.last_name) AS member_name
    FROM loans l
    JOIN books b ON b.id = l.book_id
    JOIN members m ON m.id = l.member_id
"""


async def _fetch_loan(conn: asyncpg.Connection, loan_id: int) -> asyncpg.Record:
    row = await conn.fetchrow(f"{_LOAN_SELECT} WHERE l.id = $1", loan_id)
    if row is None:
        raise NotFoundError(f"loan {loan_id} not found")
    return row


async def borrow_book(
    pool: asyncpg.Pool, *, book_id: int, member_id: int, loan_period_days: int
) -> asyncpg.Record:
    async with pool.acquire() as conn:
        async with conn.transaction():
            member_exists = await conn.fetchval(
                "SELECT 1 FROM members WHERE id = $1", member_id
            )
            if member_exists is None:
                raise NotFoundError(f"member {member_id} not found")

            already_borrowed = await conn.fetchval(
                """SELECT 1 FROM loans
                   WHERE member_id = $1 AND book_id = $2 AND returned_at IS NULL""",
                member_id,
                book_id,
            )
            if already_borrowed:
                raise ConflictError(
                    "member already has this book on loan"
                )

            copy_row = await conn.fetchrow(
                """SELECT id FROM book_copies
                   WHERE book_id = $1 AND status = 'available'
                   ORDER BY id
                   LIMIT 1
                   FOR UPDATE SKIP LOCKED""",
                book_id,
            )
            if copy_row is None:
                book_exists = await conn.fetchval(
                    "SELECT 1 FROM books WHERE id = $1", book_id
                )
                if book_exists is None:
                    raise NotFoundError(f"book {book_id} not found")
                raise ConflictError(f"no available copies of book {book_id}")

            copy_id = copy_row["id"]
            await conn.execute(
                """UPDATE book_copies SET status = 'checked_out', updated_at = now()
                   WHERE id = $1""",
                copy_id,
            )
            due_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
                days=loan_period_days
            )
            try:
                loan_id = await conn.fetchval(
                    """INSERT INTO loans (copy_id, book_id, member_id, due_at)
                       VALUES ($1, $2, $3, $4)
                       RETURNING id""",
                    copy_id,
                    book_id,
                    member_id,
                    due_at,
                )
            except asyncpg.UniqueViolationError as exc:
                # Backstop for a concurrent BorrowBook for the same
                # member+book slipping past the check above — see
                # uq_loans_active_member_book in db/schema.sql.
                if exc.constraint_name == "uq_loans_active_member_book":
                    raise ConflictError(
                        "member already has this book on loan"
                    ) from exc
                raise
            return await _fetch_loan(conn, loan_id)


async def return_book(pool: asyncpg.Pool, loan_id: int) -> asyncpg.Record:
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """UPDATE loans SET returned_at = now(), updated_at = now()
                   WHERE id = $1 AND returned_at IS NULL
                   RETURNING copy_id""",
                loan_id,
            )
            if row is None:
                exists = await conn.fetchval(
                    "SELECT 1 FROM loans WHERE id = $1", loan_id
                )
                if exists is None:
                    raise NotFoundError(f"loan {loan_id} not found")
                raise ConflictError(f"loan {loan_id} has already been returned")

            await conn.execute(
                """UPDATE book_copies SET status = 'available', updated_at = now()
                   WHERE id = $1""",
                row["copy_id"],
            )
            return await _fetch_loan(conn, loan_id)


async def get_loan(pool: asyncpg.Pool, loan_id: int) -> asyncpg.Record:
    async with pool.acquire() as conn:
        return await _fetch_loan(conn, loan_id)


async def list_loans(
    pool: asyncpg.Pool,
    *,
    member_id: int | None,
    book_id: int | None,
    only_active: bool,
    limit: int,
    offset: int,
) -> list[asyncpg.Record]:
    async with pool.acquire() as conn:
        return await conn.fetch(
            f"""{_LOAN_SELECT}
                WHERE ($1::bigint IS NULL OR l.member_id = $1)
                  AND ($2::bigint IS NULL OR l.book_id = $2)
                  AND ($3::bool IS FALSE OR l.returned_at IS NULL)
                ORDER BY l.borrowed_at DESC, l.id DESC
                LIMIT $4 OFFSET $5""",
            member_id,
            book_id,
            only_active,
            limit,
            offset,
        )
