import "server-only";

import { bookClient, call } from "./client";
import { BookMethod } from "./methods";
import type {
  AddBookCopiesRequest,
  AddBookCopiesResponse,
  Book,
  CreateBookRequest,
  ListBooksRequest,
  ListBooksResponse,
  UpdateBookRequest,
} from "./types";

export function listBooks(search = ""): Promise<ListBooksResponse> {
  const req: ListBooksRequest = { search, page: { pageSize: 100 } };
  return call(bookClient, BookMethod.ListBooks, req);
}

export function getBook(id: string): Promise<Book> {
  return call(bookClient, BookMethod.GetBook, { id });
}

export function createBook(req: CreateBookRequest): Promise<Book> {
  return call(bookClient, BookMethod.CreateBook, req);
}

export function updateBook(req: UpdateBookRequest): Promise<Book> {
  return call(bookClient, BookMethod.UpdateBook, req);
}

export function addBookCopies(
  req: AddBookCopiesRequest
): Promise<AddBookCopiesResponse> {
  return call(bookClient, BookMethod.AddBookCopies, req);
}
