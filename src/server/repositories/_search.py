"""Helpers for building safe ILIKE patterns."""

from __future__ import annotations

_BACKSLASH = chr(92)


def like_pattern(search: str) -> str | None:
    """Contains-pattern for `search`, with LIKE wildcards escaped so a
    user-typed `%`, `_` or backslash matches literally. None when blank."""
    if not search:
        return None
    escaped = search.replace(_BACKSLASH, _BACKSLASH * 2)
    escaped = escaped.replace("%", _BACKSLASH + "%").replace("_", _BACKSLASH + "_")
    return f"%{escaped}%"
