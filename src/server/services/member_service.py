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
        first_name = validation.require_non_empty(
            request.first_name, "first_name", max_length=validation.MAX_NAME_LEN
        )
        last_name = validation.require_non_empty(
            request.last_name, "last_name", max_length=validation.MAX_NAME_LEN
        )
        email = validation.require_email(request.email)
        phone = validation.optional_text(
            request.phone, "phone", max_length=validation.MAX_PHONE_LEN
        )
        address = validation.optional_text(
            request.address, "address", max_length=validation.MAX_ADDRESS_LEN
        )

        row = await member_repository.create_member(
            self._pool,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
        )
        return mappers.member_to_proto(row)

    @handle_errors
    async def UpdateMember(self, request: member_pb2.UpdateMemberRequest, context):
        member_id = validation.require_positive_id(request.id, "id")
        first_name = validation.require_non_empty(
            request.first_name, "first_name", max_length=validation.MAX_NAME_LEN
        )
        last_name = validation.require_non_empty(
            request.last_name, "last_name", max_length=validation.MAX_NAME_LEN
        )
        email = validation.require_email(request.email)
        phone = validation.optional_text(
            request.phone, "phone", max_length=validation.MAX_PHONE_LEN
        )
        address = validation.optional_text(
            request.address, "address", max_length=validation.MAX_ADDRESS_LEN
        )
        # An unset `status` (MEMBER_STATUS_UNSPECIFIED) leaves the member's
        # current status unchanged, so editing contact details can't
        # silently reactivate a suspended member.
        status = mappers.member_status_to_db(request.status)

        row = await member_repository.update_member(
            self._pool,
            member_id=member_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
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
            search=validation.require_search(request.search),
            limit=size + 1,
            offset=offset,
        )
        page_rows, page = build_page_response(rows, size, offset)
        return member_pb2.ListMembersResponse(
            members=[mappers.member_to_proto(r) for r in page_rows], page=page
        )
