"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { addBookCopies, createBook, updateBook } from "@/lib/grpc/books";
import { describeGrpcError } from "@/lib/grpc/errors";
import { formValue, optionalFormValue } from "@/lib/form-data";

export type FormState = { error?: string };

function parseYear(value: string): number | undefined {
  if (!value) return undefined;
  const n = Number(value);
  return Number.isFinite(n) && n > 0 ? n : undefined;
}

export async function createBookAction(
  _prevState: FormState,
  formData: FormData
): Promise<FormState> {
  // `redirect()` throws internally to signal Next.js, so the call must sit
  // outside this try/catch — otherwise the catch below would swallow it.
  let bookId: string;
  try {
    const book = await createBook({
      isbn: optionalFormValue(formData, "isbn"),
      title: formValue(formData, "title"),
      author: formValue(formData, "author"),
      publisher: optionalFormValue(formData, "publisher"),
      publishedYear: parseYear(formValue(formData, "publishedYear")),
      genre: optionalFormValue(formData, "genre"),
      initialCopies: Number(formValue(formData, "initialCopies") || 1),
    });
    bookId = book.id;
  } catch (error) {
    return { error: describeGrpcError(error) };
  }
  revalidatePath("/books");
  redirect(`/books/${bookId}`);
}

export async function updateBookAction(
  id: string,
  _prevState: FormState,
  formData: FormData
): Promise<FormState> {
  try {
    await updateBook({
      id,
      isbn: optionalFormValue(formData, "isbn"),
      title: formValue(formData, "title"),
      author: formValue(formData, "author"),
      publisher: optionalFormValue(formData, "publisher"),
      publishedYear: parseYear(formValue(formData, "publishedYear")),
      genre: optionalFormValue(formData, "genre"),
    });
    revalidatePath("/books");
    revalidatePath(`/books/${id}`);
  } catch (error) {
    return { error: describeGrpcError(error) };
  }
  return {};
}

export async function addBookCopiesAction(
  id: string,
  _prevState: FormState,
  formData: FormData
): Promise<FormState> {
  try {
    const count = Number(formValue(formData, "count") || 0);
    await addBookCopies({ bookId: id, count });
    revalidatePath("/books");
    revalidatePath(`/books/${id}`);
  } catch (error) {
    return { error: describeGrpcError(error) };
  }
  return {};
}
