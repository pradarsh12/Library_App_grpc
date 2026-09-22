"use server";

import { revalidatePath } from "next/cache";
import { borrowBook, returnBook } from "@/lib/grpc/loans";
import { describeGrpcError } from "@/lib/grpc/errors";
import { formValue } from "@/lib/form-data";

export type FormState = { error?: string };

export async function borrowBookAction(
  _prevState: FormState,
  formData: FormData
): Promise<FormState> {
  try {
    const loanPeriodDays = Number(formValue(formData, "loanPeriodDays") || 0);
    await borrowBook({
      bookId: formValue(formData, "bookId"),
      memberId: formValue(formData, "memberId"),
      loanPeriodDays: loanPeriodDays > 0 ? loanPeriodDays : undefined,
    });
    revalidatePath("/loans");
    revalidatePath("/books");
  } catch (error) {
    return { error: describeGrpcError(error) };
  }
  return {};
}

export async function returnBookAction(
  loanId: string,
  _prevState: FormState,
  _formData: FormData
): Promise<FormState> {
  try {
    await returnBook({ loanId });
    revalidatePath("/loans");
    revalidatePath("/books");
  } catch (error) {
    return { error: describeGrpcError(error) };
  }
  return {};
}
