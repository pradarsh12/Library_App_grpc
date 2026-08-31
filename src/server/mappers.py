"""Convert asyncpg.Record rows into protobuf messages.

Repositories return plain asyncpg.Record rows (already joined/shaped for
the RPC in question); these functions are the only place that knows how a
row maps onto a Book/Member/Loan proto message.
"""

from __future__ import annotations

import datetime as dt

import asyncpg
from google.protobuf.timestamp_pb2 import Timestamp

from library.v1 import book_pb2, common_pb2, loan_pb2, member_pb2


def to_timestamp(value: dt.datetime | None) -> Timestamp | None:
    if value is None:
        return None
    ts = Timestamp()
    ts.FromDatetime(value)
    return ts


_MEMBER_STATUS_TO_PROTO = {
    "active": common_pb2.MEMBER_STATUS_ACTIVE,
    "inactive": common_pb2.MEMBER_STATUS_INACTIVE,
    "suspended": common_pb2.MEMBER_STATUS_SUSPENDED,
}
_MEMBER_STATUS_TO_DB = {v: k for k, v in _MEMBER_STATUS_TO_PROTO.items()}


def member_status_to_db(status: "common_pb2.MemberStatus.V") -> str | None:
    return _MEMBER_STATUS_TO_DB.get(status)


def member_to_proto(row: asyncpg.Record) -> member_pb2.Member:
    return member_pb2.Member(
        id=row["id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        email=row["email"],
        phone=row["phone"] or "",
        address=row["address"] or "",
        status=_MEMBER_STATUS_TO_PROTO.get(
            row["status"], common_pb2.MEMBER_STATUS_UNSPECIFIED
        ),
        joined_at=to_timestamp(row["joined_at"]),
        created_at=to_timestamp(row["created_at"]),
        updated_at=to_timestamp(row["updated_at"]),
    )


def book_to_proto(row: asyncpg.Record) -> book_pb2.Book:
    """`row` must include the computed `total_copies`/`available_copies`
    columns (see book_repository's SELECT)."""
    return book_pb2.Book(
        id=row["id"],
        isbn=row["isbn"] or "",
        title=row["title"],
        author=row["author"],
        publisher=row["publisher"] or "",
        published_year=row["published_year"] or 0,
        genre=row["genre"] or "",
        total_copies=row["total_copies"],
        available_copies=row["available_copies"],
        created_at=to_timestamp(row["created_at"]),
        updated_at=to_timestamp(row["updated_at"]),
    )


def loan_to_proto(row: asyncpg.Record) -> loan_pb2.Loan:
    """`row` must include the denormalized `book_title`/`member_name`
    columns (see loan_repository's SELECT, which joins books/members)."""
    returned_at = row["returned_at"]
    due_at = row["due_at"]
    if returned_at is not None:
        status = loan_pb2.LOAN_STATUS_RETURNED
    elif due_at < dt.datetime.now(dt.timezone.utc):
        status = loan_pb2.LOAN_STATUS_OVERDUE
    else:
        status = loan_pb2.LOAN_STATUS_ACTIVE

    loan = loan_pb2.Loan(
        id=row["id"],
        copy_id=row["copy_id"],
        book_id=row["book_id"],
        book_title=row["book_title"],
        member_id=row["member_id"],
        member_name=row["member_name"],
        borrowed_at=to_timestamp(row["borrowed_at"]),
        due_at=to_timestamp(due_at),
        status=status,
    )
    if returned_at is not None:
        loan.returned_at.CopyFrom(to_timestamp(returned_at))
    return loan
