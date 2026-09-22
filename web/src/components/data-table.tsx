import type { ReactNode } from "react";
import { EmptyState } from "./ui";

export type DataTableColumn<T> = {
  header: string;
  cell: (row: T) => ReactNode;
};

/**
 * Shared table chrome for the books/members/loans list pages. Each page
 * supplies its own column definitions and gets the empty state, borders,
 * and header/row styling for free — and the same `columns` array doubles
 * as the source of header labels for that page's loading.tsx skeleton, so
 * the two can't drift apart.
 */
export function DataTable<T>({
  columns,
  rows,
  rowKey,
  emptyMessage,
}: {
  columns: DataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  emptyMessage: ReactNode;
}) {
  if (rows.length === 0) {
    return <EmptyState>{emptyMessage}</EmptyState>;
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
          <tr>
            {columns.map((column) => (
              <th key={column.header} className="px-4 py-2">
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200">
          {rows.map((row) => (
            <tr key={rowKey(row)} className="hover:bg-slate-50">
              {columns.map((column) => (
                <td key={column.header} className="px-4 py-2">
                  {column.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
