"use client";

import { useActionState, useState, type FormEvent } from "react";
import {
  Button,
  ErrorBanner,
  Field,
  fieldErrorProps,
  Input,
  PendingOverlay,
} from "@/components/ui";
import { useDismissingError } from "@/lib/use-dismissing-error";
import { LIMITS, optionalLengthError, positiveIntError, requiredError, yearError } from "@/lib/form-validation";
import type { Book } from "@/lib/grpc/types";
import type { FormState } from "./actions";

type FieldErrors = Partial<
  Record<"title" | "author" | "isbn" | "publisher" | "publishedYear" | "genre" | "initialCopies", string>
>;

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
  const errorMessage = useDismissingError(state);
  const [errors, setErrors] = useState<FieldErrors>({});

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    const formData = new FormData(event.currentTarget);
    const nextErrors: FieldErrors = {
      title: requiredError(String(formData.get("title") ?? ""), "Title", LIMITS.title),
      author: requiredError(String(formData.get("author") ?? ""), "Author", LIMITS.title),
      isbn: optionalLengthError(String(formData.get("isbn") ?? ""), "ISBN", LIMITS.isbn),
      publisher: optionalLengthError(
        String(formData.get("publisher") ?? ""),
        "Publisher",
        LIMITS.title
      ),
      publishedYear: yearError(String(formData.get("publishedYear") ?? "")),
      genre: optionalLengthError(String(formData.get("genre") ?? ""), "Genre", LIMITS.genre),
      initialCopies: initial
        ? undefined
        : positiveIntError(String(formData.get("initialCopies") ?? ""), "Initial copies", {
            max: LIMITS.copies,
            allowBlank: true,
          }),
    };

    setErrors(nextErrors);
    if (Object.values(nextErrors).some(Boolean)) {
      event.preventDefault();
    }
  }

  return (
    <form action={formAction} onSubmit={handleSubmit} noValidate className="space-y-4">
      <PendingOverlay show={pending} label="Saving book…" />
      <ErrorBanner message={errorMessage} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Title" htmlFor="title" required error={errors.title}>
          <Input
            id="title"
            name="title"
            defaultValue={initial?.title}
            required
            {...fieldErrorProps("title", errors.title)}
          />
        </Field>
        <Field label="Author" htmlFor="author" required error={errors.author}>
          <Input
            id="author"
            name="author"
            defaultValue={initial?.author}
            required
            {...fieldErrorProps("author", errors.author)}
          />
        </Field>
        <Field label="ISBN" htmlFor="isbn" error={errors.isbn}>
          <Input
            id="isbn"
            name="isbn"
            defaultValue={initial?.isbn}
            {...fieldErrorProps("isbn", errors.isbn)}
          />
        </Field>
        <Field label="Publisher" htmlFor="publisher" error={errors.publisher}>
          <Input
            id="publisher"
            name="publisher"
            defaultValue={initial?.publisher}
            {...fieldErrorProps("publisher", errors.publisher)}
          />
        </Field>
        <Field label="Published year" htmlFor="publishedYear" error={errors.publishedYear}>
          <Input
            id="publishedYear"
            name="publishedYear"
            type="number"
            min={LIMITS.minYear}
            max={LIMITS.maxYear}
            defaultValue={initial?.publishedYear || undefined}
            {...fieldErrorProps("publishedYear", errors.publishedYear)}
          />
        </Field>
        <Field label="Genre" htmlFor="genre" error={errors.genre}>
          <Input
            id="genre"
            name="genre"
            defaultValue={initial?.genre}
            {...fieldErrorProps("genre", errors.genre)}
          />
        </Field>
        {!initial && (
          <Field label="Initial copies" htmlFor="initialCopies" error={errors.initialCopies}>
            <Input
              id="initialCopies"
              name="initialCopies"
              type="number"
              min={1}
              max={LIMITS.copies}
              defaultValue={1}
              {...fieldErrorProps("initialCopies", errors.initialCopies)}
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
