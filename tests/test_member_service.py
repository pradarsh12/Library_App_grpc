from __future__ import annotations

from library.v1 import common_pb2, member_pb2
from server.services.member_service import MemberService

from _helpers import FakeContext


async def test_update_member_without_status_keeps_current_status(pool):
    service = MemberService(pool)
    ctx = FakeContext()
    member = await service.CreateMember(
        member_pb2.CreateMemberRequest(
            first_name="Ada", last_name="Lovelace", email="ada@example.com"
        ),
        ctx,
    )
    await service.UpdateMember(
        member_pb2.UpdateMemberRequest(
            id=member.id,
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            status=common_pb2.MEMBER_STATUS_SUSPENDED,
        ),
        ctx,
    )

    updated = await service.UpdateMember(
        member_pb2.UpdateMemberRequest(
            id=member.id,
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            phone="555-0100",
        ),
        ctx,
    )
    assert updated.phone == "555-0100"
    assert updated.status == common_pb2.MEMBER_STATUS_SUSPENDED
