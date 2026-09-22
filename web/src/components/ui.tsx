import Link from "next/link";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";

// Small, presentational-only primitives shared by the books/members/loans
// pages. No hooks/interactivity here, so these work in both Server and
// Client Components without a "use client" directive.

const buttonBase =
  "inline-flex items-center justify-center rounded-md px-3 py-1.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50";
const buttonVariants = {
  primary: "bg-slate-900 text-white hover:bg-slate-700",
  secondary: "bg-white text-slate-900 ring-1 ring-inset ring-slate-300 hover:bg-slate-50",
  danger: "bg-red-600 text-white hover:bg-red-500",
};

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: keyof typeof buttonVariants;
}) {
  return (
    <button
      className={`${buttonBase} ${buttonVariants[variant]} ${className}`}
      {...props}
    />
  );
}

export function LinkButton({
  href,
  variant = "secondary",
  className = "",
  children,
}: {
  href: string;
  variant?: keyof typeof buttonVariants;
  className?: string;
  children: ReactNode;
}) {
  return (
    <Link href={href} className={`${buttonBase} ${buttonVariants[variant]} ${className}`}>
      {children}
    </Link>
  );
}

const inputStyle =
  "block w-full rounded-md border-0 px-3 py-1.5 text-sm text-slate-900 ring-1 ring-inset ring-slate-300 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-slate-900";

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={inputStyle} {...props} />;
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={inputStyle} {...props} />;
}

export function Field({
  label,
  htmlFor,
  children,
  required,
  error,
}: {
  label: string;
  htmlFor: string;
  children: ReactNode;
  required?: boolean;
  error?: string;
}) {
  return (
    <div>
      <label htmlFor={htmlFor} className="mb-1 block text-sm font-medium text-slate-700">
        {label}
        {required && <span className="text-red-500"> *</span>}
      </label>
      {children}
      {error && (
        <p id={`${htmlFor}-error`} className="mt-1 text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}

/** Shared aria wiring for an invalid Input/Select inside a Field with `error`. */
export function fieldErrorProps(htmlFor: string, error?: string) {
  return error
    ? { "aria-invalid": true as const, "aria-describedby": `${htmlFor}-error` }
    : {};
}

export function ErrorBanner({ message }: { message?: string | null }) {
  if (!message) return null;
  return (
    <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-inset ring-red-200">
      {message}
    </div>
  );
}

/**
 * Full-section fallback for when a page's data fetch itself failed (as
 * opposed to ErrorBanner, which sits inline above a form). Used in place
 * of a page's normal content — e.g. the books table — so a down backend
 * shows a clear, expected message instead of an uncaught-exception crash.
 */
export function FetchErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 px-6 py-8 text-center">
      <p className="text-sm font-medium text-red-800">Couldn&apos;t load this page</p>
      <p className="mx-auto mt-1 max-w-md text-sm text-red-700">{message}</p>
    </div>
  );
}

/**
 * Full-viewport overlay + spinner shown while a create/update/borrow/return
 * (or any other mutation) is in flight, driven by the `pending` flag each
 * form already gets back from `useActionState`. Replaces relying on
 * Next.js's dev-only route indicator badge to notice something's
 * happening — that badge is a debug affordance and isn't present in
 * production at all, so CRUD forms need their own feedback regardless.
 */
export function PendingOverlay({
  show,
  label = "Saving…",
}: {
  show: boolean;
  label?: string;
}) {
  if (!show) return null;
  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-3 bg-slate-900/40 backdrop-blur-[1px]"
    >
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-white/30 border-t-white" />
      <p className="text-sm font-medium text-white">{label}</p>
    </div>
  );
}

/** A gray pulsing placeholder block, used to build up loading.tsx skeletons. */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded bg-slate-200 ${className}`} />;
}

/**
 * Skeleton for the books/members/loans list tables, shown by each route's
 * loading.tsx while the page's server-side data fetch is in flight.
 */
export function TableSkeleton({ columns, rows = 6 }: { columns: string[]; rows?: number }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
          <tr>
            {columns.map((column) => (
              <th key={column} className="px-4 py-2">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200">
          {Array.from({ length: rows }).map((_, i) => (
            <tr key={i}>
              {columns.map((column) => (
                <td key={column} className="px-4 py-2">
                  <Skeleton className="h-4 w-full max-w-[10rem]" />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-md border border-dashed border-slate-300 px-4 py-8 text-center text-sm text-slate-500">
      {children}
    </div>
  );
}

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-6 flex items-start justify-between gap-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
        {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
      </div>
      {action}
    </div>
  );
}

const badgeVariants = {
  green: "bg-green-50 text-green-700 ring-green-600/20",
  amber: "bg-amber-50 text-amber-700 ring-amber-600/20",
  gray: "bg-slate-100 text-slate-600 ring-slate-500/20",
  red: "bg-red-50 text-red-700 ring-red-600/20",
};

export function Badge({
  children,
  color = "gray",
}: {
  children: ReactNode;
  color?: keyof typeof badgeVariants;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${badgeVariants[color]}`}
    >
      {children}
    </span>
  );
}
