"use client";

import { useActionState } from "react";
import { Button, ErrorBanner, Input } from "@/components/ui";
import type { FormState } from "./actions";

export function AddCopiesForm({
  action,
}: {
  action: (prevState: FormState, formData: FormData) => Promise<FormState>;
}) {
  const [state, formAction, pending] = useActionState<FormState, FormData>(action, {});

  return (
    <form action={formAction} className="flex items-end gap-2">
      <div className="w-24">
        <label htmlFor="count" className="mb-1 block text-sm font-medium text-slate-700">
          Add copies
        </label>
        <Input id="count" name="count" type="number" min={1} defaultValue={1} />
      </div>
      <Button type="submit" variant="secondary" disabled={pending}>
        {pending ? "Adding…" : "Add"}
      </Button>
      {state.error && (
        <div className="ml-2">
          <ErrorBanner message={state.error} />
        </div>
      )}
    </form>
  );
}
