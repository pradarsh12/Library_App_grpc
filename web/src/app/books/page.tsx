import Link from "next/link";
import { Badge, EmptyState, Input, LinkButton, PageHeader } from "@/components/ui";
import { listBooks } from "@/lib/grpc/books";

export default async function BooksPage({
  searchParams,
}: PageProps<"/books">) {
  const { search } = await searchParams;
  const query = typeof search === "string" ? search : "";
  const { books } = await listBooks(query);

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

      {books.length === 0 ? (
        <EmptyState>No books found.</EmptyState>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
              <tr>
                <th className="px-4 py-2">Title</th>
                <th className="px-4 py-2">Author</th>
                <th className="px-4 py-2">Genre</th>
                <th className="px-4 py-2">Year</th>
                <th className="px-4 py-2">Copies</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {books.map((book) => (
                <tr key={book.id} className="hover:bg-slate-50">
                  <td className="px-4 py-2 font-medium text-slate-900">
                    <Link href={`/books/${book.id}`} className="hover:underline">
                      {book.title}
                    </Link>
                  </td>
                  <td className="px-4 py-2 text-slate-600">{book.author}</td>
                  <td className="px-4 py-2 text-slate-600">{book.genre || "—"}</td>
                  <td className="px-4 py-2 text-slate-600">{book.publishedYear || "—"}</td>
                  <td className="px-4 py-2">
                    <Badge color={book.availableCopies > 0 ? "green" : "gray"}>
                      {book.availableCopies}/{book.totalCopies} available
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
