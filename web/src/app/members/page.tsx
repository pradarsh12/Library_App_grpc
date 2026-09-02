import Link from "next/link";
import { Badge, EmptyState, FetchErrorState, Input, LinkButton, PageHeader } from "@/components/ui";
import { listMembers } from "@/lib/grpc/members";
import { describeGrpcError } from "@/lib/grpc/errors";
import { memberStatusLabel } from "@/lib/grpc/status-labels";
import type { ListMembersResponse } from "@/lib/grpc/types";

export default async function MembersPage({
  searchParams,
}: PageProps<"/members">) {
  const { search } = await searchParams;
  const query = typeof search === "string" ? search : "";

  let result: ListMembersResponse;
  try {
    result = await listMembers(query);
  } catch (error) {
    console.error("listMembers failed:", error);
    return (
      <div>
        <PageHeader title="Members" />
        <FetchErrorState message={describeGrpcError(error)} />
      </div>
    );
  }
  const { members } = result;

  return (
    <div>
      <PageHeader
        title="Members"
        description="Everyone registered with the library."
        action={<LinkButton href="/members/new">New member</LinkButton>}
      />

      <form className="mb-4 max-w-sm">
        <Input
          type="search"
          name="search"
          placeholder="Search by name or email…"
          defaultValue={query}
        />
      </form>

      {members.length === 0 ? (
        <EmptyState>No members found.</EmptyState>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
              <tr>
                <th className="px-4 py-2">Name</th>
                <th className="px-4 py-2">Email</th>
                <th className="px-4 py-2">Phone</th>
                <th className="px-4 py-2">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {members.map((member) => (
                <tr key={member.id} className="hover:bg-slate-50">
                  <td className="px-4 py-2 font-medium text-slate-900">
                    <Link href={`/members/${member.id}`} className="hover:underline">
                      {member.firstName} {member.lastName}
                    </Link>
                  </td>
                  <td className="px-4 py-2 text-slate-600">{member.email}</td>
                  <td className="px-4 py-2 text-slate-600">{member.phone || "—"}</td>
                  <td className="px-4 py-2">
                    <Badge color={memberStatusLabel[member.status].color}>
                      {memberStatusLabel[member.status].label}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
