import "server-only";

import type { ReactNode } from "react";
import { status as GrpcStatus } from "@grpc/grpc-js";
import { notFound } from "next/navigation";
import { FetchErrorState, PageHeader } from "@/components/ui";
import { GrpcCallError } from "@/lib/grpc/client";
import { describeGrpcError } from "@/lib/grpc/errors";

/**
 * Runs a Server Component page's data fetch, turning a thrown error into
 * the `<PageHeader/><FetchErrorState/>` fallback every list/detail page
 * renders in its place instead of crashing. Pass `notFoundOnMissing` for
 * detail pages, where a NOT_FOUND from the backend should become Next's
 * notFound() rather than an inline error banner.
 */
export async function loadPageData<T>(
  fetcher: () => Promise<T>,
  options: { title: string; logLabel: string; notFoundOnMissing?: boolean }
): Promise<{ data: T } | { errorNode: ReactNode }> {
  try {
    return { data: await fetcher() };
  } catch (error) {
    if (
      options.notFoundOnMissing &&
      error instanceof GrpcCallError &&
      error.code === GrpcStatus.NOT_FOUND
    ) {
      notFound();
    }
    console.error(`${options.logLabel} failed:`, error);
    return {
      errorNode: (
        <div>
          <PageHeader title={options.title} />
          <FetchErrorState message={describeGrpcError(error)} />
        </div>
      ),
    };
  }
}
