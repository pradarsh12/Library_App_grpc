"""MemberService gRPC servicer: translates between protobuf and MemberService."""

from __future__ import annotations

from library.v1 import member_pb2, member_pb2_grpc

from server import mappers
from server.api.error_handling import handle_errors
from server.api.paging import page_args, page_response
from server.services.member_service import MemberService


class MemberServicer(member_pb2_grpc.MemberServiceServicer):
    def __init__(self, service: MemberService) -> None:
        self._service = service

    @handle_errors
    async def CreateMember(self, request: member_pb2.CreateMemberRequest, context):
        member = await self._service.create_member(
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            phone=request.phone,
            address=request.address,
        )
        return mappers.member_to_proto(member)

    @handle_errors
    async def UpdateMember(self, request: member_pb2.UpdateMemberRequest, context):
        member = await self._service.update_member(
            member_id=request.id,
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            phone=request.phone,
            address=request.address,
            status=mappers.member_status_from_proto(request.status),
        )
        return mappers.member_to_proto(member)

    @handle_errors
    async def GetMember(self, request: member_pb2.GetMemberRequest, context):
        return mappers.member_to_proto(await self._service.get_member(request.id))

    @handle_errors
    async def ListMembers(self, request: member_pb2.ListMembersRequest, context):
        page = await self._service.list_members(
            search=request.search, **page_args(request.page)
        )
        return member_pb2.ListMembersResponse(
            members=[mappers.member_to_proto(m) for m in page.items],
            page=page_response(page),
        )
