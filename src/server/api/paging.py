"""gRPC-side page handling: the opaque `page_token` <-> a row offset.

The token is just the string-encoded offset — plenty for this scope (no
snapshot/consistency guarantees needed) while still giving callers an opaque
token per the common.proto contract.
"""

from __future__ import annotations

from library.v1 import common_pb2

from server.domain.pagination import Page
from server.errors import ValidationError


def page_args(page_request: common_pb2.PageRequest) -> dict[str, int]:
    """`page_size`/`offset` keyword arguments for a service list call."""
    offset = 0
    if page_request.page_token:
        try:
            offset = int(page_request.page_token)
        except ValueError:
            raise ValidationError("invalid page_token") from None
        if offset < 0:
            raise ValidationError("invalid page_token")
    return {"page_size": page_request.page_size, "offset": offset}


def page_response(page: Page) -> common_pb2.PageResponse:
    token = "" if page.next_offset is None else str(page.next_offset)
    return common_pb2.PageResponse(next_page_token=token)
