"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { createMember, updateMember } from "@/lib/grpc/members";
import { describeGrpcError } from "@/lib/grpc/errors";
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
      firstName: formData.get("firstName") as string,
      lastName: formData.get("lastName") as string,
      email: formData.get("email") as string,
      phone: (formData.get("phone") as string) || undefined,
      address: (formData.get("address") as string) || undefined,
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
      firstName: formData.get("firstName") as string,
      lastName: formData.get("lastName") as string,
      email: formData.get("email") as string,
      phone: (formData.get("phone") as string) || undefined,
      address: (formData.get("address") as string) || undefined,
      status: formData.get("status") as MemberStatus,
    });
    revalidatePath("/members");
    revalidatePath(`/members/${id}`);
  } catch (error) {
    return { error: describeGrpcError(error) };
  }
  return {};
}
