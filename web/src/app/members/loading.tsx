import { Input, LinkButton, PageHeader, TableSkeleton } from "@/components/ui";

export default function MembersLoading() {
  return (
    <div>
      <PageHeader
        title="Members"
        description="Everyone registered with the library."
        action={<LinkButton href="/members/new">New member</LinkButton>}
      />

      <div className="mb-4 max-w-sm">
        <Input type="search" placeholder="Search by name or email…" disabled />
      </div>

      <TableSkeleton columns={["Name", "Email", "Phone", "Status"]} />
    </div>
  );
}
