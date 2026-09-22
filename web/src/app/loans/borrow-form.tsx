"use client";

import { useActionState, useState, type FormEvent } from "react";
import {
  Button,
  ErrorBanner,
  Field,
  fieldErrorProps,
  Input,
  PendingOverlay,
  Select,
} from "@/components/ui";
import { useDismissingError } from "@/lib/use-dismissing-error";
import { LIMITS, positiveIntError, requiredSelectionError } from "@/lib/form-validation";
import type { FormState } from "./actions";

type FieldErrors = Partial<Record<"bookId" | "memberId" | "loanPeriodDays", string>>;

export function BorrowForm({
  action,
  bookOptions,
  memberOptions,
}: {
  action: (prevState: FormState, formData: FormData) => Promise<FormState>;
  bookOptions: { id: string; label: string }[];
  memberOptions: { id: string; label: string }[];
}) {
  const [state, formAction, pending] = useActionState<FormState, FormData>(action, {});
  const errorMessage = useDismissingError(state);
  const [errors, setErrors] = useState<FieldErrors>({});

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    const formData = new FormData(event.currentTarget);
    const nextErrors: FieldErrors = {
      bookId: requiredSelectionError(String(formData.get("bookId") ?? ""), "Book"),
      memberId: requiredSelectionError(String(formData.get("memberId") ?? ""), "Member"),
      loanPeriodDays: positiveIntError(
        String(formData.get("loanPeriodDays") ?? ""),
        "Loan period",
        { max: LIMITS.loanPeriodDays, allowBlank: true }
      ),
    };

    setErrors(nextErrors);
    if (Object.values(nextErrors).some(Boolean)) {
      event.preventDefault();
    }
  }

  return (
    <form
      action={formAction}
      onSubmit={handleSubmit}
      noValidate
      className="space-y-4 rounded-lg border border-slate-200 bg-white p-4"
    >
      <PendingOverlay show={pending} label="Borrowing book…" />
      <ErrorBanner message={errorMessage} />
      <div className="grid gap-4 sm:grid-cols-3">
        <Field label="Book" htmlFor="bookId" required error={errors.bookId}>
          <Select
            id="bookId"
            name="bookId"
            defaultValue=""
            required
            {...fieldErrorProps("bookId", errors.bookId)}
          >
            <option value="" disabled>
              Select a book…
            </option>
            {bookOptions.map((b) => (
              <option key={b.id} value={b.id}>
                {b.label}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Member" htmlFor="memberId" required error={errors.memberId}>
          <Select
            id="memberId"
            name="memberId"
            defaultValue=""
            required
            {...fieldErrorProps("memberId", errors.memberId)}
          >
            <option value="" disabled>
              Select a member…
            </option>
            {memberOptions.map((m) => (
              <option key={m.id} value={m.id}>
                {m.label}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Loan period (days)" htmlFor="loanPeriodDays" error={errors.loanPeriodDays}>
          <Input
            id="loanPeriodDays"
            name="loanPeriodDays"
            type="number"
            min={1}
            max={LIMITS.loanPeriodDays}
            placeholder="14 (default)"
            {...fieldErrorProps("loanPeriodDays", errors.loanPeriodDays)}
          />
        </Field>
      </div>
      <Button type="submit" disabled={pending}>
        {pending ? "Borrowing…" : "Borrow book"}
      </Button>
    </form>
  );
}
