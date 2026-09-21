"""Plain domain objects shared by services and repositories.

Nothing here knows about asyncpg or protobuf: repositories build these from
DB rows, services hand them back to the API layer, and `mappers` turns them
into wire messages.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import enum


class MemberStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class CopyStatus(str, enum.Enum):
    AVAILABLE = "available"
    CHECKED_OUT = "checked_out"


class LoanStatus(enum.Enum):
    ACTIVE = "active"
    OVERDUE = "overdue"
    RETURNED = "returned"


@dataclasses.dataclass(frozen=True)
class Member:
    id: int
    first_name: str
    last_name: str
    email: str
    phone: str | None
    address: str | None
    status: MemberStatus
    joined_at: dt.datetime
    created_at: dt.datetime
    updated_at: dt.datetime


@dataclasses.dataclass(frozen=True)
class Book:
    id: int
    isbn: str | None
    title: str
    author: str
    publisher: str | None
    published_year: int | None
    genre: str | None
    total_copies: int
    available_copies: int
    created_at: dt.datetime
    updated_at: dt.datetime


@dataclasses.dataclass(frozen=True)
class Loan:
    id: int
    copy_id: int
    book_id: int
    book_title: str
    member_id: int
    member_name: str
    borrowed_at: dt.datetime
    due_at: dt.datetime
    returned_at: dt.datetime | None

    def status_at(self, now: dt.datetime) -> LoanStatus:
        if self.returned_at is not None:
            return LoanStatus.RETURNED
        if self.due_at < now:
            return LoanStatus.OVERDUE
        return LoanStatus.ACTIVE

    @property
    def status(self) -> LoanStatus:
        return self.status_at(dt.datetime.now(dt.timezone.utc))
