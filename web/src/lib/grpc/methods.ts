/**
 * RPC method names, mirroring the `rpc` declarations in proto/library/v1/*.
 * `call()` in ./client takes the method name as a plain string (the
 * dynamically-loaded clients have no static types) — these constants are the
 * single place that has to stay in sync with the .proto files, so a rename
 * there is a compile error here instead of a runtime "not a function".
 */

export const BookMethod = {
  ListBooks: "ListBooks",
  GetBook: "GetBook",
  CreateBook: "CreateBook",
  UpdateBook: "UpdateBook",
  AddBookCopies: "AddBookCopies",
} as const;
export type BookMethodName = (typeof BookMethod)[keyof typeof BookMethod];

export const MemberMethod = {
  ListMembers: "ListMembers",
  GetMember: "GetMember",
  CreateMember: "CreateMember",
  UpdateMember: "UpdateMember",
} as const;
export type MemberMethodName = (typeof MemberMethod)[keyof typeof MemberMethod];

export const LoanMethod = {
  ListLoans: "ListLoans",
  GetLoan: "GetLoan",
  BorrowBook: "BorrowBook",
  ReturnBook: "ReturnBook",
} as const;
export type LoanMethodName = (typeof LoanMethod)[keyof typeof LoanMethod];

export type GrpcMethodName = BookMethodName | MemberMethodName | LoanMethodName;
