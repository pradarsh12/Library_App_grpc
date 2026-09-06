"use client";

import { useActionState } from "react";
import { Button, ErrorBanner, Field, Input, PendingOverlay, Select } from "@/components/ui";
import type { FormState } from "./actions";

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

  return (
    <form action={formAction} className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
      <PendingOverlay show={pending} label="Borrowing book…" />
      <ErrorBanner message={state.error} />
      <div className="grid gap-4 sm:grid-cols-3">
        <Field label="Book" htmlFor="bookId" required>
          <Select id="bookId" name="bookId" required defaultValue="">
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
        <Field label="Member" htmlFor="memberId" required>
          <Select id="memberId" name="memberId" required defaultValue="">
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
        <Field label="Loan period (days)" htmlFor="loanPeriodDays">
          <Input
            id="loanPeriodDays"
            name="loanPeriodDays"
            type="number"
            min={1}
            placeholder="14 (default)"
          />
        </Field>
      </div>
      <Button type="submit" disabled={pending}>
        {pending ? "Borrowing…" : "Borrow book"}
      </Button>
    </form>
  );
}
