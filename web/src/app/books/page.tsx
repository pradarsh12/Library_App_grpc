import Link from "next/link";
import { Badge, Input, LinkButton, PageHeader } from "@/components/ui";
import { DataTable, type DataTableColumn } from "@/components/data-table";
import { Pagination, parsePagination } from "@/components/pagination";
import { listBooks } from "@/lib/grpc/books";
import { loadPageData } from "@/lib/load-page-data";
import type { Book } from "@/lib/grpc/types";

const columns: DataTableColumn<Book>[] = [
  {
    header: "Title",
    cell: (book) => (
      <Link href={`/books/${book.id}`} className="font-medium text-slate-900 hover:underline">
        {book.title}
      </Link>
    ),
  },
  {
    header: "Author",
    cell: (book) => <span className="text-slate-600">{book.author}</span>,
  },
  {
    header: "Genre",
    cell: (book) => <span className="text-slate-600">{book.genre || "—"}</span>,
  },
  {
    header: "Year",
    cell: (book) => <span className="text-slate-600">{book.publishedYear || "—"}</span>,
  },
  {
    header: "Copies",
    cell: (book) => (
      <Badge color={book.availableCopies > 0 ? "green" : "gray"}>
        {book.availableCopies}/{book.totalCopies} available
      </Badge>
    ),
  },
];

export default async function BooksPage({
  searchParams,
}: PageProps<"/books">) {
  const params = await searchParams;
  const query = typeof params.search === "string" ? params.search : "";
  const { pageToken, prevTokens } = parsePagination(params);

  const result = await loadPageData(() => listBooks(query, { pageToken }), {
    title: "Books",
    logLabel: "listBooks",
  });
  if ("errorNode" in result) return result.errorNode;
  const { books, page } = result.data;

  return (
    <div>
      <PageHeader
        title="Books"
        description="Catalog of titles and their physical copies."
        action={<LinkButton href="/books/new">New book</LinkButton>}
      />

      <form className="mb-4 max-w-sm">
        <Input
          type="search"
          name="search"
          placeholder="Search by title or author…"
          defaultValue={query}
        />
      </form>

      <DataTable
        columns={columns}
        rows={books}
        rowKey={(book) => book.id}
        emptyMessage="No books found."
      />
      <Pagination
        basePath="/books"
        params={{ search: query }}
        pageToken={pageToken}
        prevTokens={prevTokens}
        nextPageToken={page.nextPageToken}
      />
    </div>
  );
}
