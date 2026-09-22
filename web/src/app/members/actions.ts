"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { createMember, updateMember } from "@/lib/grpc/members";
import { describeGrpcError } from "@/lib/grpc/errors";
import { formValue, optionalFormValue } from "@/lib/form-data";
import type { MemberStatus } from "@/lib/grpc/types";

export type FormState = { error?: string };

export async function createMemberAction(
  _prevState: FormState,
  formData: FormData
): Promise<FormState> {
  // `redirect()` throws internally to signal Next.js, so it must sit
  // outside this try/catch — otherwise the catch below would swallow it.
  let memberId: string;
  try {
    const member = await createMember({
      firstName: formValue(formData, "firstName"),
      lastName: formValue(formData, "lastName"),
      email: formValue(formData, "email"),
      phone: optionalFormValue(formData, "phone"),
      address: optionalFormValue(formData, "address"),
    });
    memberId = member.id;
  } catch (error) {
    return { error: describeGrpcError(error) };
  }
  revalidatePath("/members");
  redirect(`/members/${memberId}`);
}

export async function updateMemberAction(
  id: string,
  _prevState: FormState,
  formData: FormData
): Promise<FormState> {
  try {
    await updateMember({
      id,
      firstName: formValue(formData, "firstName"),
      lastName: formValue(formData, "lastName"),
      email: formValue(formData, "email"),
      phone: optionalFormValue(formData, "phone"),
      address: optionalFormValue(formData, "address"),
      status: formValue(formData, "status") as MemberStatus,
    });
    revalidatePath("/members");
    revalidatePath(`/members/${id}`);
  } catch (error) {
    return { error: describeGrpcError(error) };
  }
  return {};
}
