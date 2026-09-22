"use client";

import { Button, ErrorBanner, Input, PendingOverlay, fieldErrorProps } from "@/components/ui";
import { useValidatedForm } from "@/lib/use-validated-form";
import { LIMITS, positiveIntError } from "@/lib/form-validation";
import type { FormState } from "./actions";

type FieldErrors = Partial<Record<"count", string>>;

export function AddCopiesForm({
  action,
}: {
  action: (prevState: FormState, formData: FormData) => Promise<FormState>;
}) {
  const { formAction, pending, errorMessage, errors, handleSubmit } = useValidatedForm<FieldErrors>(
    action,
    (formData) => ({
      count: positiveIntError(String(formData.get("count") ?? ""), "Count", {
        max: LIMITS.copies,
      }),
    })
  );

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
          {...fieldErrorProps("count", errors.count)}
        />
        {errors.count && (
          <p id="count-error" className="mt-1 text-sm text-red-600">
            {errors.count}
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
