"""Convert between domain objects and protobuf messages.

This is the only place that knows how a domain Book/Member/Loan maps onto its
wire representation. Business decisions (e.g. whether a loan is overdue) are
made by the domain model, not here.
"""

from __future__ import annotations

import datetime as dt

from google.protobuf.timestamp_pb2 import Timestamp

from library.v1 import book_pb2, common_pb2, loan_pb2, member_pb2

from server.domain.models import Book, Loan, LoanStatus, Member, MemberStatus


def to_timestamp(value: dt.datetime | None) -> Timestamp | None:
    if value is None:
        return None
    ts = Timestamp()
    ts.FromDatetime(value)
    return ts


_MEMBER_STATUS_TO_PROTO = {
    MemberStatus.ACTIVE: common_pb2.MEMBER_STATUS_ACTIVE,
    MemberStatus.INACTIVE: common_pb2.MEMBER_STATUS_INACTIVE,
    MemberStatus.SUSPENDED: common_pb2.MEMBER_STATUS_SUSPENDED,
}
_MEMBER_STATUS_FROM_PROTO = {v: k for k, v in _MEMBER_STATUS_TO_PROTO.items()}

_LOAN_STATUS_TO_PROTO = {
    LoanStatus.ACTIVE: loan_pb2.LOAN_STATUS_ACTIVE,
    LoanStatus.OVERDUE: loan_pb2.LOAN_STATUS_OVERDUE,
    LoanStatus.RETURNED: loan_pb2.LOAN_STATUS_RETURNED,
}


def member_status_from_proto(
    status: "common_pb2.MemberStatus.V",
) -> MemberStatus | None:
    """None for MEMBER_STATUS_UNSPECIFIED (or any unknown value)."""
    return _MEMBER_STATUS_FROM_PROTO.get(status)


def member_to_proto(member: Member) -> member_pb2.Member:
    return member_pb2.Member(
        id=member.id,
        first_name=member.first_name,
        last_name=member.last_name,
        email=member.email,
        phone=member.phone or "",
        address=member.address or "",
        status=_MEMBER_STATUS_TO_PROTO.get(
            member.status, common_pb2.MEMBER_STATUS_UNSPECIFIED
        ),
        joined_at=to_timestamp(member.joined_at),
        created_at=to_timestamp(member.created_at),
        updated_at=to_timestamp(member.updated_at),
    )


def book_to_proto(book: Book) -> book_pb2.Book:
    return book_pb2.Book(
        id=book.id,
        isbn=book.isbn or "",
        title=book.title,
        author=book.author,
        publisher=book.publisher or "",
        published_year=book.published_year or 0,
        genre=book.genre or "",
        total_copies=book.total_copies,
        available_copies=book.available_copies,
        created_at=to_timestamp(book.created_at),
        updated_at=to_timestamp(book.updated_at),
    )


def loan_to_proto(loan: Loan) -> loan_pb2.Loan:
    message = loan_pb2.Loan(
        id=loan.id,
        copy_id=loan.copy_id,
        book_id=loan.book_id,
        book_title=loan.book_title,
        member_id=loan.member_id,
        member_name=loan.member_name,
        borrowed_at=to_timestamp(loan.borrowed_at),
        due_at=to_timestamp(loan.due_at),
        status=_LOAN_STATUS_TO_PROTO[loan.status],
    )
    if loan.returned_at is not None:
        message.returned_at.CopyFrom(to_timestamp(loan.returned_at))
    return message
