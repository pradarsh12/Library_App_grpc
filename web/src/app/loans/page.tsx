import Link from "next/link";
import { Badge, LinkButton, PageHeader } from "@/components/ui";
import { DataTable, type DataTableColumn } from "@/components/data-table";
import { Pagination, parsePagination } from "@/components/pagination";
import { listBooks } from "@/lib/grpc/books";
import { listMembers } from "@/lib/grpc/members";
import { listLoans } from "@/lib/grpc/loans";
import { loadPageData } from "@/lib/load-page-data";
import { formatDate } from "@/lib/grpc/format";
import { loanStatusLabel } from "@/lib/grpc/status-labels";
import type { Loan } from "@/lib/grpc/types";
import { BorrowForm } from "./borrow-form";
import { ReturnButton } from "./return-button";
import { borrowBookAction, returnBookAction } from "./actions";

const columns: DataTableColumn<Loan>[] = [
  {
    header: "Book",
    cell: (loan) => (
      <Link href={`/books/${loan.bookId}`} className="font-medium text-slate-900 hover:underline">
        {loan.bookTitle}
      </Link>
    ),
  },
  {
    header: "Member",
    cell: (loan) => (
      <Link href={`/members/${loan.memberId}`} className="text-slate-600 hover:underline">
        {loan.memberName}
      </Link>
    ),
  },
  {
    header: "Borrowed",
    cell: (loan) => <span className="text-slate-600">{formatDate(loan.borrowedAt)}</span>,
  },
  {
    header: "Due",
    cell: (loan) => <span className="text-slate-600">{formatDate(loan.dueAt)}</span>,
  },
  {
    header: "Status",
    cell: (loan) => (
      <Badge color={loanStatusLabel[loan.status].color}>
        {loanStatusLabel[loan.status].label}
      </Badge>
    ),
  },
  {
    header: "",
    cell: (loan) =>
      loan.status !== "LOAN_STATUS_RETURNED" ? (
        <ReturnButton action={returnBookAction.bind(null, loan.id)} />
      ) : null,
  },
];

export default async function LoansPage({
  searchParams,
}: PageProps<"/loans">) {
  const params = await searchParams;
  const onlyActive = params.active !== "0";
  const { pageToken, prevTokens } = parsePagination(params);

  const result = await loadPageData(
    async () => {
      // All three are needed for this page (borrow form + loans table), so
      // one failure means the whole page can't render — Promise.all is fine.
      // The book/member lists here populate the borrow form's dropdowns, so
      // they ask for the server's max page size rather than the smaller
      // default used for the paginated loans table itself.
      const [loansResult, { books }, { members }] = await Promise.all([
        listLoans({ onlyActive, pageToken }),
        listBooks("", { pageSize: 100 }),
        listMembers("", { pageSize: 100 }),
      ]);
      return { loans: loansResult.loans, page: loansResult.page, books, members };
    },
    { title: "Loans", logLabel: "loans page data fetch" }
  );
  if ("errorNode" in result) return result.errorNode;
  const { loans, page, books, members } = result.data;

  const bookOptions = books
    .filter((b) => b.availableCopies > 0)
    .map((b) => ({ id: b.id, label: `${b.title} (${b.availableCopies} available)` }));
  const memberOptions = members.map((m) => ({
    id: m.id,
    label: `${m.firstName} ${m.lastName}`,
  }));

  return (
    <div className="space-y-8">
      <div>
        <PageHeader title="Borrow a book" />
        <BorrowForm
          action={borrowBookAction}
          bookOptions={bookOptions}
          memberOptions={memberOptions}
        />
      </div>

      <div>
        <PageHeader
          title="Loans"
          description={onlyActive ? "Currently checked out." : "Full loan history."}
          action={
            <LinkButton href={onlyActive ? "/loans?active=0" : "/loans?active=1"}>
              {onlyActive ? "Show all" : "Show active only"}
            </LinkButton>
          }
        />

        <DataTable
          columns={columns}
          rows={loans}
          rowKey={(loan) => loan.id}
          emptyMessage="No loans found."
        />
        <Pagination
          basePath="/loans"
          params={{ active: onlyActive ? undefined : "0" }}
          pageToken={pageToken}
          prevTokens={prevTokens}
          nextPageToken={page.nextPageToken}
        />
      </div>
    </div>
  );
}
