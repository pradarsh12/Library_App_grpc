import { status as GrpcStatus } from "@grpc/grpc-js";
import { notFound } from "next/navigation";
import { FetchErrorState, PageHeader } from "@/components/ui";
import { GrpcCallError } from "@/lib/grpc/client";
import { getMember } from "@/lib/grpc/members";
import { describeGrpcError } from "@/lib/grpc/errors";
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
    console.error("getMember failed:", error);
    return (
      <div>
        <PageHeader title="Member" />
        <FetchErrorState message={describeGrpcError(error)} />
      </div>
    );
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
