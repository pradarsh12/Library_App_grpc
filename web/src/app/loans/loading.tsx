import { PageHeader, Skeleton, TableSkeleton } from "@/components/ui";

export default function LoansLoading() {
  return (
    <div className="space-y-8">
      <div>
        <PageHeader title="Borrow a book" />
        <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <Skeleton className="h-9" />
            <Skeleton className="h-9" />
            <Skeleton className="h-9" />
          </div>
          <Skeleton className="h-9 w-24" />
        </div>
      </div>

      <div>
        <PageHeader title="Loans" />
        <TableSkeleton columns={["Book", "Member", "Borrowed", "Due", "Status", ""]} />
      </div>
    </div>
  );
}
