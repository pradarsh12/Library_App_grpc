import { PageHeader } from "@/components/ui";
import { BookForm } from "../book-form";
import { createBookAction } from "../actions";

export default function NewBookPage() {
  return (
    <div>
      <PageHeader title="New book" />
      <BookForm action={createBookAction} submitLabel="Create book" />
    </div>
  );
}
