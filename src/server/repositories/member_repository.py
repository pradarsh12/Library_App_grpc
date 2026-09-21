"""Data access for library members."""

from __future__ import annotations

import asyncpg

from server.errors import AlreadyExistsError, NotFoundError

_MEMBER_COLUMNS = (
    "id, first_name, last_name, email, phone, address, status, "
    "joined_at, created_at, updated_at"
)


async def create_member(
    pool: asyncpg.Pool,
    *,
    first_name: str,
    last_name: str,
    email: str,
    phone: str | None,
    address: str | None,
) -> asyncpg.Record:
    async with pool.acquire() as conn:
        try:
            return await conn.fetchrow(
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
            raise AlreadyExistsError(
                f"a member with email '{email}' already exists"
            ) from exc


async def update_member(
    pool: asyncpg.Pool,
    *,
    member_id: int,
    first_name: str,
    last_name: str,
    email: str,
    phone: str | None,
    address: str | None,
    status: str | None,
) -> asyncpg.Record:
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
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
                status,
            )
        except asyncpg.UniqueViolationError as exc:
            raise AlreadyExistsError(
                f"a member with email '{email}' already exists"
            ) from exc
        if row is None:
            raise NotFoundError(f"member {member_id} not found")
        return row


async def get_member(pool: asyncpg.Pool, member_id: int) -> asyncpg.Record:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            f"SELECT {_MEMBER_COLUMNS} FROM members WHERE id = $1", member_id
        )
        if row is None:
            raise NotFoundError(f"member {member_id} not found")
        return row


async def list_members(
    pool: asyncpg.Pool, *, search: str, limit: int, offset: int
) -> list[asyncpg.Record]:
    pattern = f"%{search}%" if search else None
    async with pool.acquire() as conn:
        return await conn.fetch(
            f"""SELECT {_MEMBER_COLUMNS} FROM members
                WHERE ($1::text IS NULL
                       OR first_name ILIKE $1
                       OR last_name ILIKE $1
                       OR email ILIKE $1)
                ORDER BY last_name, first_name, id
                LIMIT $2 OFFSET $3""",
            pattern,
            limit,
            offset,
        )
