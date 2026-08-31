import { PageHeader } from "@/components/ui";
import { MemberForm } from "../member-form";
import { createMemberAction } from "../actions";

export default function NewMemberPage() {
  return (
    <div>
      <PageHeader title="New member" />
      <MemberForm action={createMemberAction} submitLabel="Create member" />
    </div>
  );
}
