"""Loan use cases — the borrow/return business rules.

Borrowing claims one available copy, marks it checked out and records the
loan in a single transaction. The rules enforced here are: the member must
exist, a member may hold only one active loan per book, and a copy must be
available. Return closes an open loan and frees its copy.
"""

from __future__ import annotations

import datetime as dt

from server import validation
from server.config import settings
from server.db.database import Database, Repositories
from server.domain.models import CopyStatus, Loan
from server.domain.pagination import Page, PageParams, paginate
from server.errors import ConflictError, NotFoundError


def _loan_not_found(loan_id: int) -> NotFoundError:
    return NotFoundError(f"loan {loan_id} not found")


class LoanService:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def borrow_book(
        self, *, book_id: int, member_id: int, loan_period_days: int
    ) -> Loan:
        book_id = validation.require_positive_id(book_id, "book_id")
        member_id = validation.require_positive_id(member_id, "member_id")
        loan_period_days = loan_period_days or settings.default_loan_period_days
        validation.require_positive_int(
            loan_period_days,
            "loan_period_days",
            maximum=validation.MAX_LOAN_PERIOD_DAYS,
        )

        async with self._db.transaction() as repos:
            if not await repos.members.exists(member_id):
                raise NotFoundError(f"member {member_id} not found")
            if await repos.loans.has_active_loan(member_id, book_id):
                raise ConflictError("member already has this book on loan")

            copy_id = await repos.books.claim_available_copy(book_id)
            if copy_id is None:
                if not await repos.books.exists(book_id):
                    raise NotFoundError(f"book {book_id} not found")
                raise ConflictError(f"no available copies of book {book_id}")

            await repos.books.set_copy_status(copy_id, CopyStatus.CHECKED_OUT)
            due_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
                days=loan_period_days
            )
            loan_id = await repos.loans.insert(
                copy_id=copy_id, book_id=book_id, member_id=member_id, due_at=due_at
            )
            return await self._get(repos, loan_id)

    async def return_book(self, loan_id: int) -> Loan:
        loan_id = validation.require_positive_id(loan_id, "loan_id")

        async with self._db.transaction() as repos:
            copy_id = await repos.loans.mark_returned(loan_id)
            if copy_id is None:
                if not await repos.loans.exists(loan_id):
                    raise _loan_not_found(loan_id)
                raise ConflictError(f"loan {loan_id} has already been returned")

            await repos.books.set_copy_status(copy_id, CopyStatus.AVAILABLE)
            return await self._get(repos, loan_id)

    async def get_loan(self, loan_id: int) -> Loan:
        loan_id = validation.require_positive_id(loan_id, "loan_id")
        async with self._db.session() as repos:
            return await self._get(repos, loan_id)

    async def list_loans(
        self,
        *,
        member_id: int | None,
        book_id: int | None,
        only_active: bool,
        page_size: int,
        offset: int,
    ) -> Page[Loan]:
        params = PageParams.of(page_size, offset)
        async with self._db.session() as repos:
            loans = await repos.loans.list(
                member_id=member_id,
                book_id=book_id,
                only_active=only_active,
                limit=params.size + 1,
                offset=params.offset,
            )
        return paginate(loans, params)

    @staticmethod
    async def _get(repos: Repositories, loan_id: int) -> Loan:
        loan = await repos.loans.get(loan_id)
        if loan is None:
            raise _loan_not_found(loan_id)
        return loan
