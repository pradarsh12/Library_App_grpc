"use client";

import { useActionState } from "react";
import { Button, ErrorBanner, Field, Input } from "@/components/ui";
import type { Book } from "@/lib/grpc/types";
import type { FormState } from "./actions";

export function BookForm({
  action,
  initial,
  submitLabel,
}: {
  action: (prevState: FormState, formData: FormData) => Promise<FormState>;
  initial?: Book;
  submitLabel: string;
}) {
  const [state, formAction, pending] = useActionState<FormState, FormData>(action, {});

  return (
    <form action={formAction} className="space-y-4">
      <ErrorBanner message={state.error} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Title" htmlFor="title" required>
          <Input id="title" name="title" defaultValue={initial?.title} required />
        </Field>
        <Field label="Author" htmlFor="author" required>
          <Input id="author" name="author" defaultValue={initial?.author} required />
        </Field>
        <Field label="ISBN" htmlFor="isbn">
          <Input id="isbn" name="isbn" defaultValue={initial?.isbn} />
        </Field>
        <Field label="Publisher" htmlFor="publisher">
          <Input id="publisher" name="publisher" defaultValue={initial?.publisher} />
        </Field>
        <Field label="Published year" htmlFor="publishedYear">
          <Input
            id="publishedYear"
            name="publishedYear"
            type="number"
            defaultValue={initial?.publishedYear || undefined}
          />
        </Field>
        <Field label="Genre" htmlFor="genre">
          <Input id="genre" name="genre" defaultValue={initial?.genre} />
        </Field>
        {!initial && (
          <Field label="Initial copies" htmlFor="initialCopies">
            <Input
              id="initialCopies"
              name="initialCopies"
              type="number"
              min={1}
              defaultValue={1}
            />
          </Field>
        )}
      </div>
      <Button type="submit" disabled={pending}>
        {pending ? "Saving…" : submitLabel}
      </Button>
    </form>
  );
}
