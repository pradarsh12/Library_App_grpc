"""MemberService gRPC servicer."""

from __future__ import annotations

import asyncpg

from library.v1 import member_pb2, member_pb2_grpc

from server import mappers, validation
from server.errors import handle_errors
from server.pagination import build_page_response, parse_page
from server.repositories import member_repository


class MemberService(member_pb2_grpc.MemberServiceServicer):
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @handle_errors
    async def CreateMember(self, request: member_pb2.CreateMemberRequest, context):
        first_name = validation.require_non_empty(request.first_name, "first_name")
        last_name = validation.require_non_empty(request.last_name, "last_name")
        email = validation.require_email(request.email)

        row = await member_repository.create_member(
            self._pool,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=request.phone.strip() or None,
            address=request.address.strip() or None,
        )
        return mappers.member_to_proto(row)

    @handle_errors
    async def UpdateMember(self, request: member_pb2.UpdateMemberRequest, context):
        member_id = validation.require_positive_id(request.id, "id")
        first_name = validation.require_non_empty(request.first_name, "first_name")
        last_name = validation.require_non_empty(request.last_name, "last_name")
        email = validation.require_email(request.email)
        # An unset `status` field (MEMBER_STATUS_UNSPECIFIED) defaults to
        # "active" -- this API expects the full record on every update
        # rather than supporting partial field masks.
        status = mappers.member_status_to_db(request.status) or "active"

        row = await member_repository.update_member(
            self._pool,
            member_id=member_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=request.phone.strip() or None,
            address=request.address.strip() or None,
            status=status,
        )
        return mappers.member_to_proto(row)

    @handle_errors
    async def GetMember(self, request: member_pb2.GetMemberRequest, context):
        member_id = validation.require_positive_id(request.id, "id")
        row = await member_repository.get_member(self._pool, member_id)
        return mappers.member_to_proto(row)

    @handle_errors
    async def ListMembers(self, request: member_pb2.ListMembersRequest, context):
        size, offset = parse_page(request.page)
        rows = await member_repository.list_members(
            self._pool,
            search=request.search.strip(),
            limit=size + 1,
            offset=offset,
        )
        page_rows, page = build_page_response(rows, size, offset)
        return member_pb2.ListMembersResponse(
            members=[mappers.member_to_proto(r) for r in page_rows], page=page
        )
