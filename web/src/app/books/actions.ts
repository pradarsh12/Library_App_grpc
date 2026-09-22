"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { addBookCopies, createBook, updateBook } from "@/lib/grpc/books";
import { formValue, optionalFormValue } from "@/lib/form-data";
import { runMutation, runMutationAndReturn, type FormState } from "@/lib/run-mutation";

export type { FormState };

function parseYear(value: string): number | undefined {
  if (!value) return undefined;
  const n = Number(value);
  return Number.isFinite(n) && n > 0 ? n : undefined;
}

export async function createBookAction(
  _prevState: FormState,
  formData: FormData
): Promise<FormState> {
  const result = await runMutationAndReturn(() =>
    createBook({
      isbn: optionalFormValue(formData, "isbn"),
      title: formValue(formData, "title"),
      author: formValue(formData, "author"),
      publisher: optionalFormValue(formData, "publisher"),
      publishedYear: parseYear(formValue(formData, "publishedYear")),
      genre: optionalFormValue(formData, "genre"),
      initialCopies: Number(formValue(formData, "initialCopies") || 1),
    })
  );
  if ("error" in result) return result;
  revalidatePath("/books");
  redirect(`/books/${result.data.id}`);
}

export async function updateBookAction(
  id: string,
  _prevState: FormState,
  formData: FormData
): Promise<FormState> {
  return runMutation(
    () =>
      updateBook({
        id,
        isbn: optionalFormValue(formData, "isbn"),
        title: formValue(formData, "title"),
        author: formValue(formData, "author"),
        publisher: optionalFormValue(formData, "publisher"),
        publishedYear: parseYear(formValue(formData, "publishedYear")),
        genre: optionalFormValue(formData, "genre"),
      }),
    "/books",
    `/books/${id}`
  );
}

export async function addBookCopiesAction(
  id: string,
  _prevState: FormState,
  formData: FormData
): Promise<FormState> {
  const count = Number(formValue(formData, "count") || 0);
  return runMutation(
    () => addBookCopies({ bookId: id, count }),
    "/books",
    `/books/${id}`
  );
}
