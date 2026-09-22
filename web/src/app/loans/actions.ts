"use server";

import { borrowBook, returnBook } from "@/lib/grpc/loans";
import { formValue } from "@/lib/form-data";
import { runMutation, type FormState } from "@/lib/run-mutation";

export type { FormState };

export async function borrowBookAction(
  _prevState: FormState,
  formData: FormData
): Promise<FormState> {
  const loanPeriodDays = Number(formValue(formData, "loanPeriodDays") || 0);
  return runMutation(
    () =>
      borrowBook({
        bookId: formValue(formData, "bookId"),
        memberId: formValue(formData, "memberId"),
        loanPeriodDays: loanPeriodDays > 0 ? loanPeriodDays : undefined,
      }),
    "/loans",
    "/books"
  );
}

export async function returnBookAction(
  loanId: string,
  _prevState: FormState,
  _formData: FormData
): Promise<FormState> {
  return runMutation(() => returnBook({ loanId }), "/loans", "/books");
}
