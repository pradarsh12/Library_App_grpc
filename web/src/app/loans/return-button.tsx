"use client";

import { useActionState } from "react";
import { Button, PendingOverlay } from "@/components/ui";
import { useDismissingError } from "@/lib/use-dismissing-error";
import type { FormState } from "./actions";

export function ReturnButton({
  action,
}: {
  action: (prevState: FormState, formData: FormData) => Promise<FormState>;
}) {
  const [state, formAction, pending] = useActionState<FormState, FormData>(action, {});
  const errorMessage = useDismissingError(state);

  return (
    <form action={formAction}>
      <PendingOverlay show={pending} label="Returning book…" />
      <Button type="submit" variant="secondary" disabled={pending}>
        {pending ? "Returning…" : "Return"}
      </Button>
      {errorMessage && <p className="mt-1 text-xs text-red-600">{errorMessage}</p>}
    </form>
  );
}
