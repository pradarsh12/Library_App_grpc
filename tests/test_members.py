"""Member CRUD, uniqueness, validation and search."""

from __future__ import annotations

import grpc
import pytest

from library.v1 import common_pb2, member_pb2

from _helpers import AbortedError, FakeContext, make_member, member_api


async def _code(coro) -> grpc.StatusCode:
    with pytest.raises(AbortedError) as exc_info:
        await coro
    return exc_info.value.code


async def test_create_and_get_member(pool):
    created = await make_member(
        pool,
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        phone="555-0100",
        address="1 Analytical St",
    )
    assert created.id > 0
    assert created.status == common_pb2.MEMBER_STATUS_ACTIVE
    assert created.HasField("joined_at")

    fetched = await member_api(pool).GetMember(
        member_pb2.GetMemberRequest(id=created.id), FakeContext()
    )
    assert fetched.email == "ada@example.com"
    assert fetched.phone == "555-0100"
    assert fetched.address == "1 Analytical St"


async def test_create_member_trims_and_lowercases(pool):
    created = await make_member(
        pool, first_name="  Ada ", last_name=" Lovelace  ", email="  ADA@Example.COM "
    )
    assert (created.first_name, created.last_name) == ("Ada", "Lovelace")
    assert created.email == "ada@example.com"


async def test_duplicate_email_rejected_case_insensitively(pool):
    await make_member(pool, email="ada@example.com")
    code = await _code(make_member(pool, email="ADA@example.com"))
    assert code == grpc.StatusCode.ALREADY_EXISTS


async def test_update_member_changes_fields(pool):
    member = await make_member(pool, first_name="Ada", last_name="Lovelace")
    updated = await member_api(pool).UpdateMember(
        member_pb2.UpdateMemberRequest(
            id=member.id,
            first_name="Augusta",
            last_name="King",
            email="augusta@example.com",
            status=common_pb2.MEMBER_STATUS_INACTIVE,
        ),
        FakeContext(),
    )
    assert (updated.first_name, updated.last_name) == ("Augusta", "King")
    assert updated.email == "augusta@example.com"
    assert updated.status == common_pb2.MEMBER_STATUS_INACTIVE


async def test_update_member_to_taken_email_rejected(pool):
    await make_member(pool, email="taken@example.com")
    other = await make_member(pool, email="other@example.com")
    code = await _code(
        member_api(pool).UpdateMember(
            member_pb2.UpdateMemberRequest(
                id=other.id,
                first_name="Test",
                last_name="Member",
                email="taken@example.com",
            ),
            FakeContext(),
        )
    )
    assert code == grpc.StatusCode.ALREADY_EXISTS


async def test_update_member_keeping_own_email_is_allowed(pool):
    member = await make_member(pool, email="same@example.com")
    updated = await member_api(pool).UpdateMember(
        member_pb2.UpdateMemberRequest(
            id=member.id,
            first_name="New",
            last_name="Name",
            email="same@example.com",
        ),
        FakeContext(),
    )
    assert updated.first_name == "New"


async def test_update_clears_optional_fields_when_blank(pool):
    member = await make_member(pool, phone="555-0100", address="Somewhere")
    updated = await member_api(pool).UpdateMember(
        member_pb2.UpdateMemberRequest(
            id=member.id,
            first_name=member.first_name,
            last_name=member.last_name,
            email=member.email,
        ),
        FakeContext(),
    )
    assert updated.phone == ""
    assert updated.address == ""


async def test_get_missing_member_is_not_found(pool):
    code = await _code(
        member_api(pool).GetMember(
            member_pb2.GetMemberRequest(id=999_999), FakeContext()
        )
    )
    assert code == grpc.StatusCode.NOT_FOUND


async def test_update_missing_member_is_not_found(pool):
    code = await _code(
        member_api(pool).UpdateMember(
            member_pb2.UpdateMemberRequest(
                id=999_999,
                first_name="A",
                last_name="B",
                email="a@example.com",
            ),
            FakeContext(),
        )
    )
    assert code == grpc.StatusCode.NOT_FOUND


@pytest.mark.parametrize(
    "request_kwargs",
    [
        {"first_name": "", "last_name": "L", "email": "a@example.com"},
        {"first_name": "F", "last_name": "   ", "email": "a@example.com"},
        {"first_name": "F", "last_name": "L", "email": ""},
        {"first_name": "F", "last_name": "L", "email": "not-an-email"},
        {"first_name": "F", "last_name": "L", "email": "two@@example.com"},
        {"first_name": "F" * 101, "last_name": "L", "email": "a@example.com"},
        {"first_name": "F", "last_name": "L", "email": "a" * 200 + "@example.com"},
        {"first_name": "F", "last_name": "L", "email": "a@example.com", "phone": "1" * 33},
        {"first_name": "F", "last_name": "L", "email": "a@example.com", "address": "x" * 501},
    ],
)
async def test_create_member_rejects_invalid_input(request_kwargs):
    service = member_api(pool=None)  # validation fails before any DB access
    code = await _code(
        service.CreateMember(
            member_pb2.CreateMemberRequest(**request_kwargs), FakeContext()
        )
    )
    assert code == grpc.StatusCode.INVALID_ARGUMENT


@pytest.mark.parametrize("member_id", [0, -1])
async def test_member_id_must_be_positive(member_id):
    service = member_api(pool=None)
    assert (
        await _code(
            service.GetMember(member_pb2.GetMemberRequest(id=member_id), FakeContext())
        )
        == grpc.StatusCode.INVALID_ARGUMENT
    )
    assert (
        await _code(
            service.UpdateMember(
                member_pb2.UpdateMemberRequest(
                    id=member_id, first_name="A", last_name="B", email="a@example.com"
                ),
                FakeContext(),
            )
        )
        == grpc.StatusCode.INVALID_ARGUMENT
    )


async def _search(pool, term: str) -> list[str]:
    response = await member_api(pool).ListMembers(
        member_pb2.ListMembersRequest(search=term), FakeContext()
    )
    return [f"{m.first_name} {m.last_name}" for m in response.members]


async def test_list_members_orders_by_last_then_first_name(pool):
    await make_member(pool, first_name="Zed", last_name="Adams")
    await make_member(pool, first_name="Amy", last_name="Adams")
    await make_member(pool, first_name="Bob", last_name="Baker")
    assert await _search(pool, "") == ["Amy Adams", "Zed Adams", "Bob Baker"]


async def test_search_matches_name_full_name_and_email_case_insensitively(pool):
    await make_member(pool, first_name="Ada", last_name="Lovelace", email="countess@example.com")
    await make_member(pool, first_name="Grace", last_name="Hopper", email="grace@navy.mil")

    assert await _search(pool, "ADA") == ["Ada Lovelace"]
    assert await _search(pool, "hopper") == ["Grace Hopper"]
    assert await _search(pool, "ada love") == ["Ada Lovelace"]
    assert await _search(pool, "NAVY.mil") == ["Grace Hopper"]
    assert await _search(pool, "nobody") == []


async def test_search_treats_wildcards_literally(pool):
    await make_member(pool, first_name="Fifty%", last_name="Off")
    await make_member(pool, first_name="Under_score", last_name="Name")
    await make_member(pool, first_name="Plain", last_name="Person")

    assert await _search(pool, "%") == ["Fifty% Off"]
    assert await _search(pool, "_") == ["Under_score Name"]


async def test_search_rejects_oversized_term(pool):
    code = await _code(
        member_api(pool).ListMembers(
            member_pb2.ListMembersRequest(search="x" * 101), FakeContext()
        )
    )
    assert code == grpc.StatusCode.INVALID_ARGUMENT
