"""Transport-agnostic paging: services take `PageParams`, return `Page`."""

from __future__ import annotations

import dataclasses
from typing import Generic, TypeVar

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@dataclasses.dataclass(frozen=True)
class PageParams:
    size: int
    offset: int

    @classmethod
    def of(cls, size: int, offset: int) -> "PageParams":
        """Apply the default/maximum page size; `size` of 0 means default."""
        size = size or DEFAULT_PAGE_SIZE
        return cls(size=max(1, min(size, MAX_PAGE_SIZE)), offset=offset)


@dataclasses.dataclass(frozen=True)
class Page(Generic[T]):
    items: list[T]
    next_offset: int | None


def paginate(rows: list[T], params: PageParams) -> Page[T]:
    """`rows` holds up to `size + 1` entries (the repository is queried with
    limit=size+1); the extra row only signals that another page exists."""
    has_more = len(rows) > params.size
    return Page(
        items=rows[: params.size],
        next_offset=params.offset + params.size if has_more else None,
    )
