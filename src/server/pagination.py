"""Simple offset-based pagination shared by every List* RPC.

The page_token is just the string-encoded offset — plenty for this scope
(no snapshot/consistency guarantees needed) while still giving callers an
opaque token per the common.proto contract.
"""

from __future__ import annotations

from library.v1 import common_pb2

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def parse_page(page_request: common_pb2.PageRequest) -> tuple[int, int]:
    size = page_request.page_size or DEFAULT_PAGE_SIZE
    size = max(1, min(size, MAX_PAGE_SIZE))
    offset = int(page_request.page_token) if page_request.page_token else 0
    return size, offset


def build_page_response(
    rows: list, size: int, offset: int
) -> tuple[list, common_pb2.PageResponse]:
    """`rows` is expected to have up to `size + 1` entries (the repository
    is called with limit=size+1); the extra row, if present, only signals
    that another page exists and is trimmed off here."""
    has_more = len(rows) > size
    page_rows = rows[:size]
    token = str(offset + size) if has_more else ""
    return page_rows, common_pb2.PageResponse(next_page_token=token)
