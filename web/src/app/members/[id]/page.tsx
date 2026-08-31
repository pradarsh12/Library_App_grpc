import { status as GrpcStatus } from "@grpc/grpc-js";
import { notFound } from "next/navigation";
import { PageHeader } from "@/components/ui";
import { GrpcCallError } from "@/lib/grpc/client";
import { getMember } from "@/lib/grpc/members";
import { MemberForm } from "../member-form";
import { updateMemberAction } from "../actions";

export default async function EditMemberPage({
  params,
}: PageProps<"/members/[id]">) {
  const { id } = await params;

  let member;
  try {
    member = await getMember(id);
  } catch (error) {
    if (error instanceof GrpcCallError && error.code === GrpcStatus.NOT_FOUND) {
      notFound();
    }
    throw error;
  }

  return (
    <div>
      <PageHeader title={`${member.firstName} ${member.lastName}`} />
      <MemberForm
        action={updateMemberAction.bind(null, id)}
        initial={member}
        submitLabel="Save changes"
      />
    </div>
  );
}
