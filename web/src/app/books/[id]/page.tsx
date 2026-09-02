import { status as GrpcStatus } from "@grpc/grpc-js";
import { notFound } from "next/navigation";
import { FetchErrorState, PageHeader } from "@/components/ui";
import { GrpcCallError } from "@/lib/grpc/client";
import { getBook } from "@/lib/grpc/books";
import { describeGrpcError } from "@/lib/grpc/errors";
import { AddCopiesForm } from "../add-copies-form";
import { BookForm } from "../book-form";
import { addBookCopiesAction, updateBookAction } from "../actions";

export default async function EditBookPage({ params }: PageProps<"/books/[id]">) {
  const { id } = await params;

  let book;
  try {
    book = await getBook(id);
  } catch (error) {
    if (error instanceof GrpcCallError && error.code === GrpcStatus.NOT_FOUND) {
      notFound();
    }
    // Any other failure (server down, timeout, ...) is still "expected" in
    // the sense that it can happen during normal operation — show it
    // inline rather than letting it become an uncaught-exception crash.
    console.error("getBook failed:", error);
    return (
      <div>
        <PageHeader title="Book" />
        <FetchErrorState message={describeGrpcError(error)} />
      </div>
    );
  }

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
