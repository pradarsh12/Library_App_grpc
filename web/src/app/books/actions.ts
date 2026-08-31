"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { addBookCopies, createBook, updateBook } from "@/lib/grpc/books";
import { describeGrpcError } from "@/lib/grpc/errors";

export type FormState = { error?: string };

function parseYear(value: FormDataEntryValue | null): number | undefined {
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
      isbn: (formData.get("isbn") as string) || undefined,
      title: formData.get("title") as string,
      author: formData.get("author") as string,
      publisher: (formData.get("publisher") as string) || undefined,
      publishedYear: parseYear(formData.get("publishedYear")),
      genre: (formData.get("genre") as string) || undefined,
      initialCopies: Number(formData.get("initialCopies") || 1),
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
      isbn: (formData.get("isbn") as string) || undefined,
      title: formData.get("title") as string,
      author: formData.get("author") as string,
      publisher: (formData.get("publisher") as string) || undefined,
      publishedYear: parseYear(formData.get("publishedYear")),
      genre: (formData.get("genre") as string) || undefined,
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
    const count = Number(formData.get("count") || 0);
    await addBookCopies({ bookId: id, count });
    revalidatePath("/books");
    revalidatePath(`/books/${id}`);
  } catch (error) {
    return { error: describeGrpcError(error) };
  }
  return {};
}
