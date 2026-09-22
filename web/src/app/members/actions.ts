"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { createMember, updateMember } from "@/lib/grpc/members";
import { formValue, optionalFormValue } from "@/lib/form-data";
import { runMutation, runMutationAndReturn, type FormState } from "@/lib/run-mutation";
import type { MemberStatus } from "@/lib/grpc/types";

export type { FormState };

export async function createMemberAction(
  _prevState: FormState,
  formData: FormData
): Promise<FormState> {
  const result = await runMutationAndReturn(() =>
    createMember({
      firstName: formValue(formData, "firstName"),
      lastName: formValue(formData, "lastName"),
      email: formValue(formData, "email"),
      phone: optionalFormValue(formData, "phone"),
      address: optionalFormValue(formData, "address"),
    })
  );
  if ("error" in result) return result;
  revalidatePath("/members");
  redirect(`/members/${result.data.id}`);
}

export async function updateMemberAction(
  id: string,
  _prevState: FormState,
  formData: FormData
): Promise<FormState> {
  return runMutation(
    () =>
      updateMember({
        id,
        firstName: formValue(formData, "firstName"),
        lastName: formValue(formData, "lastName"),
        email: formValue(formData, "email"),
        phone: optionalFormValue(formData, "phone"),
        address: optionalFormValue(formData, "address"),
        status: formValue(formData, "status") as MemberStatus,
      }),
    "/members",
    `/members/${id}`
  );
}
