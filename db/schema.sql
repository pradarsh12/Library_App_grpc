-- Neighborhood Library Service — schema
-- Applied automatically by docker-compose (mounted into
-- /docker-entrypoint-initdb.d/) or manually via:
--   psql "$DATABASE_URL" -f server/db/schema.sql

CREATE TABLE IF NOT EXISTS members (
  id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  first_name TEXT NOT NULL,
  last_name  TEXT NOT NULL,
  email      TEXT NOT NULL UNIQUE,
  phone      TEXT,
  address    TEXT,
  status     TEXT NOT NULL DEFAULT 'active'
             CHECK (status IN ('active', 'inactive', 'suspended')),
  joined_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS books (
  id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  isbn           TEXT UNIQUE,
  title          TEXT NOT NULL,
  author         TEXT NOT NULL,
  publisher      TEXT,
  published_year INT,
  genre          TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One row per physical copy the library owns of a given book title.
CREATE TABLE IF NOT EXISTS book_copies (
  id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  book_id    BIGINT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  barcode    TEXT UNIQUE,
  status     TEXT NOT NULL DEFAULT 'available'
             CHECK (status IN ('available', 'checked_out', 'lost', 'maintenance')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_book_copies_book_id ON book_copies(book_id);

-- One row per borrow event. returned_at IS NULL means the copy is still out.
CREATE TABLE IF NOT EXISTS loans (
  id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  copy_id     BIGINT NOT NULL REFERENCES book_copies(id),
  member_id   BIGINT NOT NULL REFERENCES members(id),
  borrowed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  due_at      TIMESTAMPTZ NOT NULL,
  returned_at TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_loans_member_id ON loans(member_id);
CREATE INDEX IF NOT EXISTS idx_loans_copy_id ON loans(copy_id);

-- DB-level guarantee (on top of the app-level SELECT ... FOR UPDATE SKIP
-- LOCKED in loan_repository.borrow_book): a copy can have at most one
-- active (unreturned) loan at a time, even under concurrent requests.
CREATE UNIQUE INDEX IF NOT EXISTS uq_loans_active_copy
  ON loans(copy_id) WHERE returned_at IS NULL;
