"use client";

import { useActionState } from "react";
import { Button, ErrorBanner, Field, Input, PendingOverlay, Select } from "@/components/ui";
import { memberStatusLabel } from "@/lib/grpc/status-labels";
import { useDismissingError } from "@/lib/use-dismissing-error";
import type { Member } from "@/lib/grpc/types";
import type { FormState } from "./actions";

const editableStatuses = [
  "MEMBER_STATUS_ACTIVE",
  "MEMBER_STATUS_INACTIVE",
  "MEMBER_STATUS_SUSPENDED",
] as const;

export function MemberForm({
  action,
  initial,
  submitLabel,
}: {
  action: (prevState: FormState, formData: FormData) => Promise<FormState>;
  initial?: Member;
  submitLabel: string;
}) {
  const [state, formAction, pending] = useActionState<FormState, FormData>(action, {});
  const errorMessage = useDismissingError(state);

  return (
    <form action={formAction} className="space-y-4">
      <PendingOverlay show={pending} label="Saving member…" />
      <ErrorBanner message={errorMessage} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="First name" htmlFor="firstName" required>
          <Input id="firstName" name="firstName" defaultValue={initial?.firstName} required />
        </Field>
        <Field label="Last name" htmlFor="lastName" required>
          <Input id="lastName" name="lastName" defaultValue={initial?.lastName} required />
        </Field>
        <Field label="Email" htmlFor="email" required>
          <Input
            id="email"
            name="email"
            type="email"
            defaultValue={initial?.email}
            required
          />
        </Field>
        <Field label="Phone" htmlFor="phone">
          <Input id="phone" name="phone" defaultValue={initial?.phone} />
        </Field>
        <Field label="Address" htmlFor="address">
          <Input id="address" name="address" defaultValue={initial?.address} />
        </Field>
        {initial && (
          <Field label="Status" htmlFor="status">
            <Select id="status" name="status" defaultValue={initial.status}>
              {editableStatuses.map((s) => (
                <option key={s} value={s}>
                  {memberStatusLabel[s].label}
                </option>
              ))}
            </Select>
          </Field>
        )}
      </div>
      <Button type="submit" disabled={pending}>
        {pending ? "Saving…" : submitLabel}
      </Button>
    </form>
  );
}
