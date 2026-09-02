import Link from "next/link";
import { Badge, EmptyState, FetchErrorState, LinkButton, PageHeader } from "@/components/ui";
import { listBooks } from "@/lib/grpc/books";
import { listMembers } from "@/lib/grpc/members";
import { listLoans } from "@/lib/grpc/loans";
import { describeGrpcError } from "@/lib/grpc/errors";
import { formatDate } from "@/lib/grpc/format";
import { loanStatusLabel } from "@/lib/grpc/status-labels";
import type { Book, Loan, Member } from "@/lib/grpc/types";
import { BorrowForm } from "./borrow-form";
import { ReturnButton } from "./return-button";
import { borrowBookAction, returnBookAction } from "./actions";

export default async function LoansPage({
  searchParams,
}: PageProps<"/loans">) {
  const { active } = await searchParams;
  const onlyActive = active !== "0";

  let loans: Loan[], books: Book[], members: Member[];
  try {
    // All three are needed for this page (borrow form + loans table), so
    // one failure means the whole page can't render — Promise.all is fine.
    [{ loans }, { books }, { members }] = await Promise.all([
      listLoans({ onlyActive }),
      listBooks(),
      listMembers(),
    ]);
  } catch (error) {
    console.error("loans page data fetch failed:", error);
    return (
      <div>
        <PageHeader title="Loans" />
        <FetchErrorState message={describeGrpcError(error)} />
      </div>
    );
  }

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

        {loans.length === 0 ? (
          <EmptyState>No loans found.</EmptyState>
        ) : (
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-2">Book</th>
                  <th className="px-4 py-2">Member</th>
                  <th className="px-4 py-2">Borrowed</th>
                  <th className="px-4 py-2">Due</th>
                  <th className="px-4 py-2">Status</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {loans.map((loan) => (
                  <tr key={loan.id} className="hover:bg-slate-50">
                    <td className="px-4 py-2 font-medium text-slate-900">
                      <Link href={`/books/${loan.bookId}`} className="hover:underline">
                        {loan.bookTitle}
                      </Link>
                    </td>
                    <td className="px-4 py-2 text-slate-600">
                      <Link href={`/members/${loan.memberId}`} className="hover:underline">
                        {loan.memberName}
                      </Link>
                    </td>
                    <td className="px-4 py-2 text-slate-600">{formatDate(loan.borrowedAt)}</td>
                    <td className="px-4 py-2 text-slate-600">{formatDate(loan.dueAt)}</td>
                    <td className="px-4 py-2">
                      <Badge color={loanStatusLabel[loan.status].color}>
                        {loanStatusLabel[loan.status].label}
                      </Badge>
                    </td>
                    <td className="px-4 py-2">
                      {loan.status !== "LOAN_STATUS_RETURNED" && (
                        <ReturnButton action={returnBookAction.bind(null, loan.id)} />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
