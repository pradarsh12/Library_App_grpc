"""Member use cases: validation and transaction boundaries."""

from __future__ import annotations

from server import validation
from server.db.database import Database
from server.domain.models import Member, MemberStatus
from server.domain.pagination import Page, PageParams, paginate
from server.errors import NotFoundError


def _not_found(member_id: int) -> NotFoundError:
    return NotFoundError(f"member {member_id} not found")


class MemberService:
    def __init__(self, db: Database) -> None:
        self._db = db

    @staticmethod
    def _validated_fields(
        *,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        address: str,
    ) -> dict:
        return {
            "first_name": validation.require_non_empty(
                first_name, "first_name", max_length=validation.MAX_NAME_LEN
            ),
            "last_name": validation.require_non_empty(
                last_name, "last_name", max_length=validation.MAX_NAME_LEN
            ),
            "email": validation.require_email(email),
            "phone": validation.optional_text(
                phone, "phone", max_length=validation.MAX_PHONE_LEN
            ),
            "address": validation.optional_text(
                address, "address", max_length=validation.MAX_ADDRESS_LEN
            ),
        }

    async def create_member(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        address: str,
    ) -> Member:
        fields = self._validated_fields(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
        )
        async with self._db.session() as repos:
            return await repos.members.insert(**fields)

    async def update_member(
        self,
        *,
        member_id: int,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        address: str,
        status: MemberStatus | None,
    ) -> Member:
        """A `status` of None leaves the member's current status unchanged,
        so editing contact details can't silently reactivate a suspended
        member."""
        member_id = validation.require_positive_id(member_id, "id")
        fields = self._validated_fields(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
        )
        async with self._db.session() as repos:
            member = await repos.members.update(member_id, status=status, **fields)
        if member is None:
            raise _not_found(member_id)
        return member

    async def get_member(self, member_id: int) -> Member:
        member_id = validation.require_positive_id(member_id, "id")
        async with self._db.session() as repos:
            member = await repos.members.get(member_id)
        if member is None:
            raise _not_found(member_id)
        return member

    async def list_members(
        self, *, search: str, page_size: int, offset: int
    ) -> Page[Member]:
        search = validation.require_search(search)
        params = PageParams.of(page_size, offset)
        async with self._db.session() as repos:
            members = await repos.members.list(
                search=search, limit=params.size + 1, offset=params.offset
            )
        return paginate(members, params)
