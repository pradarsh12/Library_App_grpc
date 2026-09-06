"use client";

import { useActionState } from "react";
import { Button, PendingOverlay } from "@/components/ui";
import type { FormState } from "./actions";

export function ReturnButton({
  action,
}: {
  action: (prevState: FormState, formData: FormData) => Promise<FormState>;
}) {
  const [state, formAction, pending] = useActionState<FormState, FormData>(action, {});

  return (
    <form action={formAction}>
      <PendingOverlay show={pending} label="Returning book…" />
      <Button type="submit" variant="secondary" disabled={pending}>
        {pending ? "Returning…" : "Return"}
      </Button>
      {state.error && <p className="mt-1 text-xs text-red-600">{state.error}</p>}
    </form>
  );
}
