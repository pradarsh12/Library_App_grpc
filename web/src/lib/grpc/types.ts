// Mirrors the message shapes in ../../../proto/library/v1/*.proto as
// decoded by @grpc/proto-loader with { longs: String, enums: String }:
// int64 fields arrive as decimal strings, enums as their string names.

export interface ProtoTimestamp {
  seconds: string;
  nanos: number;
}

export type MemberStatus =
  | "MEMBER_STATUS_UNSPECIFIED"
  | "MEMBER_STATUS_ACTIVE"
  | "MEMBER_STATUS_INACTIVE"
  | "MEMBER_STATUS_SUSPENDED";

export type LoanStatus =
  | "LOAN_STATUS_UNSPECIFIED"
  | "LOAN_STATUS_ACTIVE"
  | "LOAN_STATUS_OVERDUE"
  | "LOAN_STATUS_RETURNED";

export interface PageRequest {
  pageSize?: number;
  pageToken?: string;
}

export interface PageResponse {
  nextPageToken: string;
}

// ---- Book ----

export interface Book {
  id: string;
  isbn: string;
  title: string;
  author: string;
  publisher: string;
  publishedYear: number;
  genre: string;
  totalCopies: number;
  availableCopies: number;
  createdAt?: ProtoTimestamp;
  updatedAt?: ProtoTimestamp;
}

export interface CreateBookRequest {
  isbn?: string;
  title: string;
  author: string;
  publisher?: string;
  publishedYear?: number;
  genre?: string;
  initialCopies?: number;
}

export interface UpdateBookRequest {
  id: string;
  isbn?: string;
  title: string;
  author: string;
  publisher?: string;
  publishedYear?: number;
  genre?: string;
}

export interface ListBooksRequest {
  search?: string;
  page?: PageRequest;
}

export interface ListBooksResponse {
  books: Book[];
  page: PageResponse;
}

export interface AddBookCopiesRequest {
  bookId: string;
  count: number;
}

export interface AddBookCopiesResponse {
  book: Book;
}

// ---- Member ----

export interface Member {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  address: string;
  status: MemberStatus;
  joinedAt?: ProtoTimestamp;
  createdAt?: ProtoTimestamp;
  updatedAt?: ProtoTimestamp;
}

export interface CreateMemberRequest {
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  address?: string;
}

export interface UpdateMemberRequest {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  address?: string;
  status?: MemberStatus;
}

export interface ListMembersRequest {
  search?: string;
  page?: PageRequest;
}

export interface ListMembersResponse {
  members: Member[];
  page: PageResponse;
}

// ---- Loan ----

export interface Loan {
  id: string;
  copyId: string;
  bookId: string;
  bookTitle: string;
  memberId: string;
  memberName: string;
  borrowedAt?: ProtoTimestamp;
  dueAt?: ProtoTimestamp;
  returnedAt?: ProtoTimestamp;
  status: LoanStatus;
}

export interface BorrowBookRequest {
  bookId: string;
  memberId: string;
  loanPeriodDays?: number;
}

export interface ReturnBookRequest {
  loanId: string;
}

export interface ListLoansRequest {
  memberId?: string;
  bookId?: string;
  onlyActive?: boolean;
  page?: PageRequest;
}

export interface ListLoansResponse {
  loans: Loan[];
  page: PageResponse;
}
