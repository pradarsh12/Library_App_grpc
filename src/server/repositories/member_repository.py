"""SQL for library members."""

from __future__ import annotations

import asyncpg

from server.domain.models import Member, MemberStatus
from server.errors import AlreadyExistsError
from server.repositories._search import like_pattern

_MEMBER_COLUMNS = (
    "id, first_name, last_name, email, phone, address, status, "
    "joined_at, created_at, updated_at"
)


def _to_member(row: asyncpg.Record) -> Member:
    return Member(
        id=row["id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        email=row["email"],
        phone=row["phone"],
        address=row["address"],
        status=MemberStatus(row["status"]),
        joined_at=row["joined_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _duplicate_email(email: str) -> AlreadyExistsError:
    return AlreadyExistsError(f"a member with email '{email}' already exists")


class MemberRepository:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def insert(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        phone: str | None,
        address: str | None,
    ) -> Member:
        try:
            row = await self._conn.fetchrow(
                f"""INSERT INTO members (first_name, last_name, email, phone, address)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING {_MEMBER_COLUMNS}""",
                first_name,
                last_name,
                email,
                phone,
                address,
            )
        except asyncpg.UniqueViolationError as exc:
            raise _duplicate_email(email) from exc
        return _to_member(row)

    async def update(
        self,
        member_id: int,
        *,
        first_name: str,
        last_name: str,
        email: str,
        phone: str | None,
        address: str | None,
        status: MemberStatus | None,
    ) -> Member | None:
        """A `status` of None leaves the current status unchanged. Returns
        None when no member has `member_id`."""
        try:
            row = await self._conn.fetchrow(
                f"""UPDATE members
                    SET first_name = $2, last_name = $3, email = $4, phone = $5,
                        address = $6, status = COALESCE($7, status),
                        updated_at = now()
                    WHERE id = $1
                    RETURNING {_MEMBER_COLUMNS}""",
                member_id,
                first_name,
                last_name,
                email,
                phone,
                address,
                status.value if status else None,
            )
        except asyncpg.UniqueViolationError as exc:
            raise _duplicate_email(email) from exc
        return _to_member(row) if row else None

    async def get(self, member_id: int) -> Member | None:
        row = await self._conn.fetchrow(
            f"SELECT {_MEMBER_COLUMNS} FROM members WHERE id = $1", member_id
        )
        return _to_member(row) if row else None

    async def exists(self, member_id: int) -> bool:
        found = await self._conn.fetchval(
            "SELECT 1 FROM members WHERE id = $1", member_id
        )
        return found is not None

    async def list(self, *, search: str, limit: int, offset: int) -> list[Member]:
        rows = await self._conn.fetch(
            f"""SELECT {_MEMBER_COLUMNS} FROM members
                WHERE ($1::text IS NULL
                       OR first_name ILIKE $1
                       OR last_name ILIKE $1
                       OR (first_name || ' ' || last_name) ILIKE $1
                       OR email ILIKE $1)
                ORDER BY last_name, first_name, id
                LIMIT $2 OFFSET $3""",
            like_pattern(search),
            limit,
            offset,
        )
        return [_to_member(r) for r in rows]
