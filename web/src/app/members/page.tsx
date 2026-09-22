import Link from "next/link";
import { Badge, Input, LinkButton, PageHeader } from "@/components/ui";
import { DataTable, type DataTableColumn } from "@/components/data-table";
import { Pagination, parsePagination } from "@/components/pagination";
import { listMembers } from "@/lib/grpc/members";
import { loadPageData } from "@/lib/load-page-data";
import { memberStatusLabel } from "@/lib/grpc/status-labels";
import type { Member } from "@/lib/grpc/types";

const columns: DataTableColumn<Member>[] = [
  {
    header: "Name",
    cell: (member) => (
      <Link href={`/members/${member.id}`} className="font-medium text-slate-900 hover:underline">
        {member.firstName} {member.lastName}
      </Link>
    ),
  },
  {
    header: "Email",
    cell: (member) => <span className="text-slate-600">{member.email}</span>,
  },
  {
    header: "Phone",
    cell: (member) => <span className="text-slate-600">{member.phone || "—"}</span>,
  },
  {
    header: "Status",
    cell: (member) => (
      <Badge color={memberStatusLabel[member.status].color}>
        {memberStatusLabel[member.status].label}
      </Badge>
    ),
  },
];

export default async function MembersPage({
  searchParams,
}: PageProps<"/members">) {
  const params = await searchParams;
  const query = typeof params.search === "string" ? params.search : "";
  const { pageToken, prevTokens } = parsePagination(params);

  const result = await loadPageData(() => listMembers(query, { pageToken }), {
    title: "Members",
    logLabel: "listMembers",
  });
  if ("errorNode" in result) return result.errorNode;
  const { members, page } = result.data;

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

      <DataTable
        columns={columns}
        rows={members}
        rowKey={(member) => member.id}
        emptyMessage="No members found."
      />
      <Pagination
        basePath="/members"
        params={{ search: query }}
        pageToken={pageToken}
        prevTokens={prevTokens}
        nextPageToken={page.nextPageToken}
      />
    </div>
  );
}
