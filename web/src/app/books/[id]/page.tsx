import { PageHeader } from "@/components/ui";
import { getBook } from "@/lib/grpc/books";
import { loadPageData } from "@/lib/load-page-data";
import { AddCopiesForm } from "../add-copies-form";
import { BookForm } from "../book-form";
import { addBookCopiesAction, updateBookAction } from "../actions";

export default async function EditBookPage({ params }: PageProps<"/books/[id]">) {
  const { id } = await params;

  const result = await loadPageData(() => getBook(id), {
    title: "Book",
    logLabel: "getBook",
    notFoundOnMissing: true,
  });
  if ("errorNode" in result) return result.errorNode;
  const book = result.data;

  return (
    <div className="space-y-8">
      <PageHeader title={book.title} description={`${book.availableCopies}/${book.totalCopies} copies available`} />
      <BookForm
        action={updateBookAction.bind(null, id)}
        initial={book}
        submitLabel="Save changes"
      />
      <div className="border-t border-slate-200 pt-6">
        <AddCopiesForm action={addBookCopiesAction.bind(null, id)} />
      </div>
    </div>
  );
}
