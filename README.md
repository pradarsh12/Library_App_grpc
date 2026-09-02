# Neighborhood Library Service

A gRPC service for a small library to manage **books**, **members**, and
**borrow/return** operations. Built with **Python (async gRPC)**,
**Protocol Buffers**, and **PostgreSQL**, with a **Next.js** web frontend
(`web/`) — see [Web frontend](#web-frontend) below.

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
    db/
      pool.py                   asyncpg pool creation
    repositories/               raw-SQL data access (book/member/loan)
    services/                   BookService / MemberService / LoanService servicers
    mappers.py                  DB row -> protobuf message
    errors.py                   domain exceptions -> gRPC status codes
    validation.py                input validation helpers
    pagination.py                 offset-based pagination helper
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
| Returning an already-returned loan             | `FAILED_PRECONDITION` |
| Unexpected server error                       | `INTERNAL`            |

## Prerequisites

- Python 3.11+ (tested with 3.14)
- Docker Desktop (for Postgres via `docker-compose.yml`)
- Node.js 20+ (only needed for the `web/` frontend — see [Web frontend](#web-frontend))

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

**Note on "CRUD":** the backend only exposes Create/Read/Update for books
and members (see `proto/library/v1/*.proto` — there's no `DeleteBook` or
`DeleteMember` RPC), so the UI doesn't have delete buttons either.
Deactivating a member is done by editing their `status` to
`Inactive`/`Suspended`, matching how the backend itself models it. Loans
aren't edited/deleted — only borrowed and returned.

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
