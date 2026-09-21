"""Connection/transaction scoping for services.

Services decide *where a transaction starts and ends*; they do that through
`Database.transaction()` (or `.session()` for plain reads), which hands back
repositories bound to one connection. Repositories never acquire connections
or open transactions themselves.
"""

from __future__ import annotations

import contextlib
import dataclasses
from collections.abc import AsyncIterator

import asyncpg

from server.repositories.book_repository import BookRepository
from server.repositories.loan_repository import LoanRepository
from server.repositories.member_repository import MemberRepository


@dataclasses.dataclass(frozen=True)
class Repositories:
    books: BookRepository
    members: MemberRepository
    loans: LoanRepository

    @classmethod
    def on(cls, conn: asyncpg.Connection) -> "Repositories":
        return cls(BookRepository(conn), MemberRepository(conn), LoanRepository(conn))


class Database:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[Repositories]:
        """Repositories on a pooled connection, no explicit transaction."""
        async with self._pool.acquire() as conn:
            yield Repositories.on(conn)

    @contextlib.asynccontextmanager
    async def transaction(self) -> AsyncIterator[Repositories]:
        """Repositories on one connection inside a transaction that commits
        on normal exit and rolls back if the block raises."""
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                yield Repositories.on(conn)
