"use client";

import { useActionState, useState, type FormEvent } from "react";
import { Button, ErrorBanner, Input, PendingOverlay } from "@/components/ui";
import { useDismissingError } from "@/lib/use-dismissing-error";
import { LIMITS, positiveIntError } from "@/lib/form-validation";
import type { FormState } from "./actions";

export function AddCopiesForm({
  action,
}: {
  action: (prevState: FormState, formData: FormData) => Promise<FormState>;
}) {
  const [state, formAction, pending] = useActionState<FormState, FormData>(action, {});
  const errorMessage = useDismissingError(state);
  const [countError, setCountError] = useState<string | undefined>();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    const formData = new FormData(event.currentTarget);
    const error = positiveIntError(String(formData.get("count") ?? ""), "Count", {
      max: LIMITS.copies,
    });
    setCountError(error);
    if (error) {
      event.preventDefault();
    }
  }

  return (
    <form action={formAction} onSubmit={handleSubmit} noValidate className="flex items-end gap-2">
      <PendingOverlay show={pending} label="Adding copies…" />
      <div className="w-24">
        <label htmlFor="count" className="mb-1 block text-sm font-medium text-slate-700">
          Add copies
        </label>
        <Input
          id="count"
          name="count"
          type="number"
          min={1}
          max={LIMITS.copies}
          defaultValue={1}
          aria-invalid={countError ? true : undefined}
          aria-describedby={countError ? "count-error" : undefined}
        />
        {countError && (
          <p id="count-error" className="mt-1 text-sm text-red-600">
            {countError}
          </p>
        )}
      </div>
      <Button type="submit" variant="secondary" disabled={pending}>
        {pending ? "Adding…" : "Add"}
      </Button>
      {errorMessage && (
        <div className="ml-2">
          <ErrorBanner message={errorMessage} />
        </div>
      )}
    </form>
  );
}
