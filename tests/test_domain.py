"""Loan status is a domain rule, independent of any transport or database."""

from __future__ import annotations

import datetime as dt

from server.domain.models import Loan, LoanStatus
from server.domain.pagination import PageParams, paginate

NOW = dt.datetime(2026, 1, 15, tzinfo=dt.timezone.utc)


def _loan(*, due_in_days: int, returned: bool = False) -> Loan:
    return Loan(
        id=1,
        copy_id=1,
        book_id=1,
        book_title="Dune",
        member_id=1,
        member_name="Test Member",
        borrowed_at=NOW - dt.timedelta(days=30),
        due_at=NOW + dt.timedelta(days=due_in_days),
        returned_at=NOW if returned else None,
    )


def test_open_loan_before_due_date_is_active():
    assert _loan(due_in_days=3).status_at(NOW) == LoanStatus.ACTIVE


def test_open_loan_past_due_date_is_overdue():
    assert _loan(due_in_days=-1).status_at(NOW) == LoanStatus.OVERDUE


def test_returned_loan_is_returned_even_if_late():
    assert _loan(due_in_days=-5, returned=True).status_at(NOW) == LoanStatus.RETURNED


def test_page_size_is_clamped_and_defaulted():
    assert PageParams.of(0, 0).size == 20
    assert PageParams.of(10_000, 0).size == 100


def test_paginate_trims_probe_row_and_reports_next_offset():
    params = PageParams(size=2, offset=4)
    page = paginate([1, 2, 3], params)
    assert page.items == [1, 2]
    assert page.next_offset == 6
    assert paginate([1, 2], params).next_offset is None
