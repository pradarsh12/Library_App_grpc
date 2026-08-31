"""Small, dependency-free input validation helpers.

Each `require_*` function raises `server.errors.ValidationError` with a
message identifying the offending field. Called at the top of each service
method, before any database access.
"""

from __future__ import annotations

import re

from server.errors import ValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def require_non_empty(value: str, field: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValidationError(f"{field} is required")
    return value


def require_positive_id(value: int, field: str) -> int:
    if value is None or value <= 0:
        raise ValidationError(f"{field} must be a positive id")
    return value


def require_email(value: str, field: str = "email") -> str:
    value = require_non_empty(value, field)
    if not _EMAIL_RE.match(value):
        raise ValidationError(f"{field} is not a valid email address")
    return value


def require_positive_int(value: int, field: str, *, allow_zero: bool = False) -> int:
    minimum = 0 if allow_zero else 1
    if value is None or value < minimum:
        raise ValidationError(f"{field} must be >= {minimum}")
    return value


def require_year(value: int, field: str = "published_year") -> int | None:
    if value in (None, 0):
        return None
    if value < 1400 or value > 2100:
        raise ValidationError(f"{field} must be a plausible year")
    return value
