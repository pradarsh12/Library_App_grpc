"use client";

import {
  Button,
  ErrorBanner,
  Field,
  fieldErrorProps,
  Input,
  PendingOverlay,
  Select,
} from "@/components/ui";
import { memberStatusLabel } from "@/lib/grpc/status-labels";
import { useValidatedForm } from "@/lib/use-validated-form";
import { LIMITS, emailError, optionalLengthError, requiredError } from "@/lib/form-validation";
import type { Member } from "@/lib/grpc/types";
import type { FormState } from "./actions";

const editableStatuses = [
  "MEMBER_STATUS_ACTIVE",
  "MEMBER_STATUS_INACTIVE",
  "MEMBER_STATUS_SUSPENDED",
] as const;

type FieldErrors = Partial<
  Record<"firstName" | "lastName" | "email" | "phone" | "address", string>
>;

export function MemberForm({
  action,
  initial,
  submitLabel,
}: {
  action: (prevState: FormState, formData: FormData) => Promise<FormState>;
  initial?: Member;
  submitLabel: string;
}) {
  const { formAction, pending, errorMessage, errors, handleSubmit } = useValidatedForm<FieldErrors>(
    action,
    (formData) => ({
      firstName: requiredError(String(formData.get("firstName") ?? ""), "First name", LIMITS.name),
      lastName: requiredError(String(formData.get("lastName") ?? ""), "Last name", LIMITS.name),
      email: emailError(String(formData.get("email") ?? "")),
      phone: optionalLengthError(String(formData.get("phone") ?? ""), "Phone", LIMITS.phone),
      address: optionalLengthError(String(formData.get("address") ?? ""), "Address", LIMITS.address),
    })
  );

  return (
    <form action={formAction} onSubmit={handleSubmit} noValidate className="space-y-4">
      <PendingOverlay show={pending} label="Saving member…" />
      <ErrorBanner message={errorMessage} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="First name" htmlFor="firstName" required error={errors.firstName}>
          <Input
            id="firstName"
            name="firstName"
            defaultValue={initial?.firstName}
            required
            {...fieldErrorProps("firstName", errors.firstName)}
          />
        </Field>
        <Field label="Last name" htmlFor="lastName" required error={errors.lastName}>
          <Input
            id="lastName"
            name="lastName"
            defaultValue={initial?.lastName}
            required
            {...fieldErrorProps("lastName", errors.lastName)}
          />
        </Field>
        <Field label="Email" htmlFor="email" required error={errors.email}>
          <Input
            id="email"
            name="email"
            type="email"
            defaultValue={initial?.email}
            required
            {...fieldErrorProps("email", errors.email)}
          />
        </Field>
        <Field label="Phone" htmlFor="phone" error={errors.phone}>
          <Input
            id="phone"
            name="phone"
            defaultValue={initial?.phone}
            {...fieldErrorProps("phone", errors.phone)}
          />
        </Field>
        <Field label="Address" htmlFor="address" error={errors.address}>
          <Input
            id="address"
            name="address"
            defaultValue={initial?.address}
            {...fieldErrorProps("address", errors.address)}
          />
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
