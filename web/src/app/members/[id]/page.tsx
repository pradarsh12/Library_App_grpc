import { PageHeader } from "@/components/ui";
import { getMember } from "@/lib/grpc/members";
import { loadPageData } from "@/lib/load-page-data";
import { MemberForm } from "../member-form";
import { updateMemberAction } from "../actions";

export default async function EditMemberPage({
  params,
}: PageProps<"/members/[id]">) {
  const { id } = await params;

  const result = await loadPageData(() => getMember(id), {
    title: "Member",
    logLabel: "getMember",
    notFoundOnMissing: true,
  });
  if ("errorNode" in result) return result.errorNode;
  const member = result.data;

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
