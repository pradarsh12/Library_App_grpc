"""SQL for loans.

Concurrency safety for borrowing rests on two database-level guarantees this
module cooperates with: the copy is claimed with `FOR UPDATE SKIP LOCKED`
(see `BookRepository.claim_available_copy`), and the partial unique indexes
`uq_loans_active_copy` / `uq_loans_active_member_book` in db/schema.sql
reject a double checkout even if two transactions race past the
application-level checks in `LoanService`.
"""

from __future__ import annotations

import datetime as dt

import asyncpg

from server.domain.models import Loan
from server.errors import ConflictError

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


def _to_loan(row: asyncpg.Record) -> Loan:
    return Loan(
        id=row["id"],
        copy_id=row["copy_id"],
        book_id=row["book_id"],
        book_title=row["book_title"],
        member_id=row["member_id"],
        member_name=row["member_name"],
        borrowed_at=row["borrowed_at"],
        due_at=row["due_at"],
        returned_at=row["returned_at"],
    )


class LoanRepository:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def get(self, loan_id: int) -> Loan | None:
        row = await self._conn.fetchrow(f"{_LOAN_SELECT} WHERE l.id = $1", loan_id)
        return _to_loan(row) if row else None

    async def exists(self, loan_id: int) -> bool:
        found = await self._conn.fetchval("SELECT 1 FROM loans WHERE id = $1", loan_id)
        return found is not None

    async def has_active_loan(self, member_id: int, book_id: int) -> bool:
        found = await self._conn.fetchval(
            """SELECT 1 FROM loans
               WHERE member_id = $1 AND book_id = $2 AND returned_at IS NULL""",
            member_id,
            book_id,
        )
        return found is not None

    async def insert(
        self, *, copy_id: int, book_id: int, member_id: int, due_at: dt.datetime
    ) -> int:
        try:
            return await self._conn.fetchval(
                """INSERT INTO loans (copy_id, book_id, member_id, due_at)
                   VALUES ($1, $2, $3, $4)
                   RETURNING id""",
                copy_id,
                book_id,
                member_id,
                due_at,
            )
        except asyncpg.UniqueViolationError as exc:
            # Backstop for a concurrent borrow of the same book by the same
            # member slipping past the service's check.
            if exc.constraint_name == "uq_loans_active_member_book":
                raise ConflictError("member already has this book on loan") from exc
            raise

    async def mark_returned(self, loan_id: int) -> int | None:
        """Close an open loan; returns its copy id, or None when the loan is
        missing or was already returned."""
        row = await self._conn.fetchrow(
            """UPDATE loans SET returned_at = now(), updated_at = now()
               WHERE id = $1 AND returned_at IS NULL
               RETURNING copy_id""",
            loan_id,
        )
        return row["copy_id"] if row else None

    async def list(
        self,
        *,
        member_id: int | None,
        book_id: int | None,
        only_active: bool,
        limit: int,
        offset: int,
    ) -> list[Loan]:
        rows = await self._conn.fetch(
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
        return [_to_loan(r) for r in rows]
