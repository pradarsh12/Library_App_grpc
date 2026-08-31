"""pytest-asyncio fixtures: a pooled connection to a disposable test schema.

Point TEST_DATABASE_URL (or DATABASE_URL) at a throwaway Postgres database
before running `python -m pytest` — every test truncates all tables, so
this must not be pointed at real data. `docker compose up -d` provides one
at postgresql://library:library@localhost:5432/library.
"""

from __future__ import annotations

import os
import pathlib

import asyncpg
import pytest
import pytest_asyncio

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA_SQL = (ROOT / "db" / "schema.sql").read_text()

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    os.environ.get(
        "DATABASE_URL", "postgresql://library:library@localhost:5432/library"
    ),
)


@pytest_asyncio.fixture(scope="session")
async def pool():
    try:
        db_pool = await asyncpg.create_pool(
            dsn=TEST_DATABASE_URL, min_size=1, max_size=5
        )
    except OSError as exc:
        pytest.skip(f"Postgres not reachable at {TEST_DATABASE_URL}: {exc}")
    async with db_pool.acquire() as conn:
        await conn.execute(SCHEMA_SQL)
    yield db_pool
    await db_pool.close()


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables(pool):
    async with pool.acquire() as conn:
        await conn.execute(
            "TRUNCATE loans, book_copies, books, members RESTART IDENTITY CASCADE"
        )
    yield
