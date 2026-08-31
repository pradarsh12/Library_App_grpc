-- Optional sample data for manual testing / demos.
--   psql "$DATABASE_URL" -f server/db/seed.sql

INSERT INTO members (first_name, last_name, email, phone, address) VALUES
  ('Ada', 'Lovelace', 'ada@example.com', '555-0100', '1 Analytical Engine Way'),
  ('Alan', 'Turing', 'alan@example.com', '555-0101', '2 Bletchley Park Rd')
ON CONFLICT (email) DO NOTHING;

INSERT INTO books (isbn, title, author, publisher, published_year, genre) VALUES
  ('9780441172719', 'Dune', 'Frank Herbert', 'Ace Books', 1965, 'Science Fiction'),
  ('9780134685991', 'Effective Java', 'Joshua Bloch', 'Addison-Wesley', 2018, 'Technology')
ON CONFLICT (isbn) DO NOTHING;

-- Two copies of Dune, one copy of Effective Java.
INSERT INTO book_copies (book_id, barcode)
SELECT id, 'DUNE-COPY-1' FROM books WHERE isbn = '9780441172719'
ON CONFLICT (barcode) DO NOTHING;
INSERT INTO book_copies (book_id, barcode)
SELECT id, 'DUNE-COPY-2' FROM books WHERE isbn = '9780441172719'
ON CONFLICT (barcode) DO NOTHING;
INSERT INTO book_copies (book_id, barcode)
SELECT id, 'EFFJAVA-COPY-1' FROM books WHERE isbn = '9780134685991'
ON CONFLICT (barcode) DO NOTHING;
