import "server-only";

import { loanClient, call } from "./client";
import { LoanMethod } from "./methods";
import type {
  BorrowBookRequest,
  ListLoansRequest,
  ListLoansResponse,
  Loan,
  ReturnBookRequest,
} from "./types";

export const LIST_LOANS_PAGE_SIZE = 20;

export function listLoans(
  filters: {
    memberId?: string;
    bookId?: string;
    onlyActive?: boolean;
    pageToken?: string;
  } = {}
): Promise<ListLoansResponse> {
  const { pageToken, ...rest } = filters;
  const req: ListLoansRequest = {
    ...rest,
    page: { pageSize: LIST_LOANS_PAGE_SIZE, pageToken },
  };
  return call(loanClient, LoanMethod.ListLoans, req);
}

export function getLoan(loanId: string): Promise<Loan> {
  return call(loanClient, LoanMethod.GetLoan, { loanId });
}

export function borrowBook(req: BorrowBookRequest): Promise<Loan> {
  return call(loanClient, LoanMethod.BorrowBook, req);
}

export function returnBook(req: ReturnBookRequest): Promise<Loan> {
  return call(loanClient, LoanMethod.ReturnBook, req);
}
