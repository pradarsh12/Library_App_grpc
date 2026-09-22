import { Input, LinkButton, PageHeader, TableSkeleton } from "@/components/ui";

export default function BooksLoading() {
  return (
    <div>
      <PageHeader
        title="Books"
        description="Catalog of titles and their physical copies."
        action={<LinkButton href="/books/new">New book</LinkButton>}
      />

      <div className="mb-4 max-w-sm">
        <Input type="search" placeholder="Search by title or author…" disabled />
      </div>

      <TableSkeleton columns={["Title", "Author", "Genre", "Year", "Copies"]} />
    </div>
  );
}
