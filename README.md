# Neighborhood Library Service

A gRPC service for a small library to manage **books**, **members**, and
**borrow/return** operations. Built with **Python (async gRPC)**,
**Protocol Buffers**, and **PostgreSQL**, with a **Next.js** web frontend
(`web/`) — see [Web frontend](#web-frontend) below.

## What this application can do

Three gRPC services define everything the app supports (`BookService`,
`MemberService`, `LoanService` — see `proto/library/v1/*.proto` for the
exact RPCs and message shapes). Every operation below is available both as
a direct gRPC call and through the `web/` UI.

**Books**
- Create a book, with an initial number of physical copies
- View a book, including how many of its copies are currently available
- List/search the catalog by title or author
- Update a book's details (title, author, ISBN, publisher, year, genre)
- Add more physical copies to an existing title

**Members**
- Register a member
- View a member's details
- List/search members by name or email
- Update a member's details, including their status
  (`active` / `inactive` / `suspended`)

**Loans**
- Borrow a book — the server automatically picks an available copy; you
  never handle copy IDs directly (see
  [Handling "already checked out"](#handling-already-checked-out)). A
  member can't hold two active loans of the *same* book at once — that's
  rejected with `FAILED_PRECONDITION` even if other copies are available.
- Return a borrowed book
- View a single loan
- List loans, filterable by member, by book, and/or active-only vs. full
  history (a loan's active/overdue/returned status is computed at read
  time from `borrowed_at`/`due_at`/`returned_at`, not stored)

**Not supported, by design:** deleting a book or a member (there's no
`DeleteBook`/`DeleteMember` RPC — deactivate a member via their `status`
instead), editing or deleting a loan once created, and
authentication/authorization. See
[Known simplifications](#known-simplifications) for the full list.

## Quick start (backend + frontend)

Condensed, copy-pasteable version of the full [Setup](#setup) /
[Running the server](#running-the-server) / [Web frontend](#web-frontend)
sections below — read those for the "why" behind each step.

**1. Configure environment variables** (must happen before step 2 —
`docker-compose.yml` reads `.env` for the Postgres credentials):

```bash
cp .env.example .env
# edit .env: fill in POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB
# and update DATABASE_URL to match
```

**2. Start Postgres:**

```bash
docker compose up -d
```

**3. Run the backend** (in one terminal):

> Windows only, if not already set: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`
> (PowerShell blocks running the venv's `Activate.ps1` script otherwise.)

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -e ".[test]"
python -m server.main
```

Leave this running — it logs `Neighborhood Library gRPC server listening
on [::]:50051` once it's up.

**4. Run the frontend** (in a second terminal):

```bash
cd web
npm install
cp .env.local.example .env.local   # defaults already match a local server
npm run dev
```

**5. Open the app:** http://localhost:3000

## Why async gRPC?

The server uses `grpc.aio` (not the sync `grpc.server`) together with
`asyncpg`, an async-native Postgres driver, so a single process/event loop
can hold many in-flight RPCs without needing a dedicated OS thread per
request, the way a sync thread-pool server would.

## Project layout

```
proto/library/v1/           .proto source (common, book, member, loan)
db/
  schema.sql                 DDL (auto-applied by docker-compose)
  seed.sql                    optional sample data
src/
  library/v1/                compiled *_pb2.py / *_pb2_grpc.py stubs (committed; regenerate with scripts/generate_proto.py)
  server/
    config.py                 env-driven settings
    api/                        gRPC layer: servicers (proto <-> service calls), error -> status mapping, page tokens
    services/                   business logic: validation, defaults, borrow/return rules, transactions (no gRPC/proto)
    repositories/               SQL only: run queries on a given connection, return domain objects
    domain/                     plain dataclasses (Book/Member/Loan, loan status rule) and paging types
    db/
      pool.py                     asyncpg pool creation
      database.py                 Database: hands services repositories bound to a connection/transaction
    mappers.py                  domain object <-> protobuf message
    errors.py                   domain exceptions
    validation.py                input validation helpers
    main.py                      server entrypoint (python -m server.main)
client_examples/
  sample_client.py             scripted walkthrough of every RPC
tests/                         pytest + pytest-asyncio integration tests
web/                          Next.js frontend (independent Node project; see Web frontend below)
docker-compose.yml            Postgres only
pyproject.toml               dependencies, packaging, pytest config
.env.example
```

## Database schema

Four normalized tables (see `db/schema.sql` for the full DDL):

- **members** — name, email (unique), phone, address, status
- **books** — title, author, ISBN (unique), publisher, year, genre
- **book_copies** — one row per physical copy the library owns of a book
  (a title can have several copies); `status` is `available` /
  `checked_out` / `lost` / `maintenance`
- **loans** — one row per borrow event: `copy_id`, `member_id`,
  `borrowed_at`, `due_at`, `returned_at` (`NULL` while still out)

All primary keys are `BIGINT GENERATED ALWAYS AS IDENTITY`. A loan's
active/overdue/returned status is **derived** from `returned_at`/`due_at`
at read time rather than stored, so there's a single source of truth. A
partial unique index, `uq_loans_active_copy ON loans(copy_id) WHERE
returned_at IS NULL`, guarantees at the database level that a copy can
never have two simultaneous active loans — this is what makes the
already-checked-out handling correct (see below).

## Handling "already checked out"

`BorrowBook` takes a `book_id`, not a `copy_id` — the server picks an
available copy for you. Internally (`src/server/repositories/loan_repository.py`):

```sql
SELECT id FROM book_copies
WHERE book_id = $1 AND status = 'available'
ORDER BY id LIMIT 1
FOR UPDATE SKIP LOCKED;
```

runs inside a transaction. If no copy is available, the RPC fails with
`FAILED_PRECONDITION`.

| Situation                                   | gRPC status          |
|----------------------------------------------|-----------------------|
| Missing required field / bad email / bad year | `INVALID_ARGUMENT`   |
| Book/member/loan id not found                 | `NOT_FOUND`           |
| Duplicate email / ISBN                        | `ALREADY_EXISTS`      |
| No available copies to borrow                 | `FAILED_PRECONDITION` |
| Member already has this book on loan          | `FAILED_PRECONDITION` |
| Returning an already-returned loan             | `FAILED_PRECONDITION` |
| Unexpected server error                       | `INTERNAL`            |

## Prerequisites

These are **hard minimums**, not just recommendations — each one is
enforced by the tooling itself, so setup fails outright on an older
version rather than behaving unpredictably:

| Tool | Minimum | Why |
|---|---|---|
| **Python** | **3.11** | Enforced by `pyproject.toml` (`requires-python = ">=3.11"`) — `pip install -e .` refuses to install on anything older. Verified working here on 3.12.10. |
| **Docker Desktop** | Any version with **Compose V2** (the `docker compose` command) | `docker-compose.yml` uses the modern Compose file format with no `version:` key, which the old standalone `docker-compose` (V1) doesn't support. |
| **Node.js** | **20.9** | Required by Next.js 16 itself — its own `package.json` declares `"engines": {"node": ">=20.9.0"}`. Only needed for the `web/` frontend, see [Web frontend](#web-frontend). |
| **PostgreSQL** | 16 | Provisioned automatically via the `postgres:16` image in `docker-compose.yml` — no local Postgres install needed. |

Check what you have installed:

```bash
python --version
docker --version && docker compose version
node --version
```

## Setup

### 1. Configure environment variables

```bash
cp .env.example .env
```

`.env.example` uses placeholder values (`USERNAME`/`PASSWORD`/`DBNAME`), so
this step is required, and must happen **before** step 2 — fill in real
credentials in `.env` for `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB`
(and update `DATABASE_URL` to match). `docker-compose.yml` reads these to
create the Postgres role/db; if `.env` doesn't exist yet, Docker Compose
substitutes empty values and Postgres fails to start.

All environment variables the server reads (via `server/config.py`,
loaded with `python-dotenv`):

| Variable | Default | Purpose |
|---|---|---|
| `POSTGRES_USER` | *(placeholder — must set)* | Postgres role created by `docker-compose.yml` |
| `POSTGRES_PASSWORD` | *(placeholder — must set)* | Postgres role's password |
| `POSTGRES_DB` | *(placeholder — must set)* | Database name created on first boot |
| `DATABASE_URL` | *(placeholder — must set)* | Full connection string the server uses; must match the three vars above |
| `GRPC_HOST` | `[::]` | Interface the gRPC server binds to (all interfaces, IPv4+IPv6) |
| `GRPC_PORT` | `50051` | Port the gRPC server listens on |
| `DB_POOL_MIN_SIZE` | `5` | Minimum size of the asyncpg connection pool |
| `DB_POOL_MAX_SIZE` | `20` | Maximum size of the asyncpg connection pool |
| `DEFAULT_LOAN_PERIOD_DAYS` | `14` | Applied to `BorrowBook` when the caller doesn't specify `loan_period_days` |

Only the four Postgres-related variables are required; the rest have
working defaults (`server/config.py` falls back to them if unset).

### 2. Start Postgres

```bash
docker compose up -d
```

This starts Postgres 16 on `localhost:5432` using the credentials from
`.env`, and automatically applies `db/schema.sql` and `db/seed.sql` on
first boot (via `docker-entrypoint-initdb.d`). To re-apply after schema
changes, either `docker compose down -v` (drops the volume) and start
again, or run the SQL manually against `$DATABASE_URL` from your `.env`:

```bash
psql "$DATABASE_URL" -f db/schema.sql
```

### 3. Create a virtualenv and install dependencies

> Windows only, if not already set: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`
> (PowerShell blocks running the venv's `Activate.ps1` script otherwise.)

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -e ".[test]"
```

This installs every required library, all pinned in `pyproject.toml`:

| Library | Used for |
|---|---|
| `grpcio` | The gRPC runtime itself (`grpc.aio` async server) |
| `grpcio-tools` | Compiles `.proto` files into Python stubs (step 4 below) |
| `grpcio-reflection` | Powers server reflection, so `grpcurl` works without `.proto` files on the client |
| `grpcio-health-checking` | Standard `grpc.health.v1.Health` service, kept in sync with real database connectivity |
| `protobuf` | Protocol Buffers message runtime |
| `asyncpg` | Async-native PostgreSQL driver |
| `python-dotenv` | Loads `.env` into the process environment |
| `pytest` / `pytest-asyncio` | Test runner (`[test]` extra only — not needed to run the server itself) |

### 4. (Re)generate the protobuf/gRPC stubs

Only needed if you change a `.proto` file — `src/library/` is committed so a
fresh checkout works without this step.

```bash
python scripts/generate_proto.py
```

## Running the server

```bash
python -m server.main
```

Logs `Neighborhood Library gRPC server listening on [::]:50051` once it's
up. Stop with Ctrl+C.

Every RPC is logged once it completes (method, status, duration), and the
standard `grpc.health.v1.Health` service is registered alongside the app
services — its status tracks real database connectivity (checked on an
interval), not just whether the process is running:

```bash
grpcurl -plaintext localhost:50051 grpc.health.v1.Health/Check
```

## Testing the service

With the server running (`python -m server.main`) in one terminal:

**Scripted walkthrough** — create a member, create a book with 2 copies,
borrow, list the member's active loans, return, then borrow both copies
and show a `FAILED_PRECONDITION` on the third attempt:

```bash
python client_examples/sample_client.py
```

**Ad-hoc calls via grpcurl** (reflection is enabled, so no `.proto` files
needed on the client side):

```bash
grpcurl -plaintext localhost:50051 list
grpcurl -plaintext -d '{"first_name":"Ada","last_name":"Lovelace","email":"ada@example.com"}' \
  localhost:50051 library.v1.MemberService/CreateMember
```

**Automated tests** (spins up against the Postgres started above; every
test truncates all tables, so point it at a disposable DB only):

```bash
python -m pytest
```

> **Note on this environment:** the code in this repo was written and
> statically verified (proto compilation, module imports, `pytest
> --collect-only`) in a sandbox without Docker/Postgres available, so the
> DB-backed tests above could not be executed end-to-end here. Please run
> `docker compose up -d` followed by `python -m pytest` /
> `python client_examples/sample_client.py` on your machine to exercise
> them fully.

Dependencies, packaging metadata, and pytest config all live in
`pyproject.toml`; there's no separate `requirements.txt` or `pytest.ini`.

## Web frontend

`web/` is a **Next.js (App Router) + TypeScript + Tailwind CSS** frontend
for the three entities, kept as its own independent Node project (own
`package.json`, `node_modules`, no shared tooling with the Python side).

Since the backend is gRPC-only and browsers can't call gRPC directly, `web/`
uses `@grpc/grpc-js` + `@grpc/proto-loader` **inside Next.js Server
Components and Server Actions** (which run in Node) to talk to the Python
server directly — no grpc-web, no Envoy proxy. The browser only ever
receives plain HTML/JSON; the `.proto` files under `proto/` are loaded at
runtime as the single source of truth (no separate JS codegen step).

```
web/
  src/
    app/
      books/      list, create, edit + add copies
      members/    list, create, edit
      loans/      borrow, return, active/history view
    lib/grpc/      client.ts (proto-loader setup), typed wrappers, error mapping
    components/    shared Tailwind UI primitives
  .env.local.example   GRPC_SERVER_ADDR (defaults to localhost:50051)
```

The UI mirrors the backend's capabilities exactly — see
[What this application can do](#what-this-application-can-do) for the
full list of supported operations (in short: no delete buttons, since
there's no delete RPC either).

### Running it

With Postgres and the gRPC server already running (see above):

```bash
cd web
npm install
cp .env.local.example .env.local   # defaults already match a local server
npm run dev
```

Then open http://localhost:3000.

## Known simplifications

- `UpdateMember`/`UpdateBook` replace the whole record (no field masks); an
  omitted `status` on `UpdateMember` resets it to `active`.
- Pagination is offset-based (`page_token` is just a stringified offset) —
  fine for this scope, not snapshot-consistent under concurrent writes.
- No authentication/authorization layer — out of scope per the assignment.
