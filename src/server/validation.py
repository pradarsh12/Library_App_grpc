"""Small, dependency-free input validation helpers.

Each `require_*` function raises `server.errors.ValidationError` with a
message identifying the offending field. Called at the top of each service
method, before any database access.
"""

from __future__ import annotations

import re

from server.errors import ValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Upper bounds shared by the services.
MAX_NAME_LEN = 100
MAX_TITLE_LEN = 100
MAX_EMAIL_LEN = 200
MAX_ISBN_LEN = 32
MAX_PHONE_LEN = 32
MAX_GENRE_LEN = 100
MAX_ADDRESS_LEN = 500
MAX_SEARCH_LEN = 100
MAX_COPIES = 1000
MAX_LOAN_PERIOD_DAYS = 365


def require_non_empty(value: str, field: str, *, max_length: int | None = None) -> str:
    value = (value or "").strip()
    if not value:
        raise ValidationError(f"{field} is required")
    if max_length is not None and len(value) > max_length:
        raise ValidationError(f"{field} must be at most {max_length} characters")
    return value


def optional_text(value: str, field: str, *, max_length: int) -> str | None:
    """Strip `value`; return None when blank, else enforce `max_length`."""
    value = (value or "").strip()
    if not value:
        return None
    if len(value) > max_length:
        raise ValidationError(f"{field} must be at most {max_length} characters")
    return value


def require_positive_id(value: int, field: str) -> int:
    if value is None or value <= 0:
        raise ValidationError(f"{field} must be a positive id")
    return value


def require_email(value: str, field: str = "email") -> str:
    value = require_non_empty(value, field, max_length=MAX_EMAIL_LEN)
    if not _EMAIL_RE.match(value):
        raise ValidationError(f"{field} is not a valid email address")
    # Emails are case-insensitive in practice; store one canonical form so the
    # UNIQUE constraint can't be sidestepped by changing case.
    return value.lower()


def require_positive_int(
    value: int,
    field: str,
    *,
    allow_zero: bool = False,
    maximum: int | None = None,
) -> int:
    minimum = 0 if allow_zero else 1
    if value is None or value < minimum:
        raise ValidationError(f"{field} must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise ValidationError(f"{field} must be <= {maximum}")
    return value


def require_year(value: int, field: str = "published_year") -> int | None:
    if value in (None, 0):
        return None
    if value < 1400 or value > 2100:
        raise ValidationError(f"{field} must be a plausible year")
    return value


def normalize_isbn(value: str) -> str:
    """Canonical ISBN form: no hyphens/spaces, uppercase check digit."""
    return re.sub(r"[\s-]", "", value or "").upper()


def require_search(value: str) -> str:
    value = " ".join((value or "").split())
    if len(value) > MAX_SEARCH_LEN:
        raise ValidationError(f"search must be at most {MAX_SEARCH_LEN} characters")
    return value
