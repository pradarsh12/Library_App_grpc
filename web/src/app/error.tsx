"use client"; // Error boundaries must be Client Components

import { useEffect } from "react";
import { Button } from "@/components/ui";

// Safety net for genuinely unexpected exceptions (bugs) — anything already
// handled inline (e.g. a down backend on the books/members/loans pages)
// never reaches this. In production Next.js replaces `error.message` from
// a Server Component with a generic message + `digest`, so this
// intentionally doesn't try to show error-specific detail to the user.
export default function GlobalErrorBoundary({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto max-w-md py-16 text-center">
      <h1 className="text-lg font-semibold text-slate-900">Something went wrong</h1>
      <p className="mt-2 text-sm text-slate-500">
        An unexpected error occurred.
        {error.digest && (
          <>
            {" "}
            Reference: <code className="text-xs">{error.digest}</code>
          </>
        )}
      </p>
      <Button className="mt-4" onClick={() => retry()}>
        Try again
      </Button>
    </div>
  );
}
