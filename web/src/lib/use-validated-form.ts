"use client";

import { useActionState, useState, type FormEvent } from "react";
import { useDismissingError } from "./use-dismissing-error";
import type { FormState } from "./run-mutation";

/**
 * Wires up a create/edit form's `useActionState` + client-side validation
 * together, since every form in books/members/loans repeated the same
 * shape: run `validate` against the submitted FormData, store the result,
 * and block the actual submit (so the server action never runs) if any
 * field failed. `validate` runs synchronously against the native FormData
 * from the submit event, not component state, so it works the same whether
 * or not the inputs are controlled.
 */
export function useValidatedForm<TErrors extends Record<string, string | undefined>>(
  action: (prevState: FormState, formData: FormData) => Promise<FormState>,
  validate: (formData: FormData) => TErrors
) {
  const [state, formAction, pending] = useActionState<FormState, FormData>(action, {});
  const errorMessage = useDismissingError(state);
  const [errors, setErrors] = useState<TErrors>({} as TErrors);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    const formData = new FormData(event.currentTarget);
    const nextErrors = validate(formData);
    setErrors(nextErrors);
    if (Object.values(nextErrors).some(Boolean)) {
      event.preventDefault();
    }
  }

  return { formAction, pending, errorMessage, errors, handleSubmit };
}
