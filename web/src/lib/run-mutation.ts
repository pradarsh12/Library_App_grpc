import "server-only";

import { revalidatePath } from "next/cache";
import { describeGrpcError } from "@/lib/grpc/errors";

export type FormState = { error?: string };

/**
 * Runs a gRPC mutation for a server action: on success, revalidates the
 * given paths and returns `{}`; on failure, turns the thrown error into the
 * `FormState` the action returns instead of letting it crash. Shared by
 * every update/borrow/return action, which differ only in the mutation
 * itself and which paths it affects.
 */
export async function runMutation(
  mutate: () => Promise<unknown>,
  ...pathsToRevalidate: string[]
): Promise<FormState> {
  try {
    await mutate();
  } catch (error) {
    return { error: describeGrpcError(error) };
  }
  for (const path of pathsToRevalidate) revalidatePath(path);
  return {};
}

/**
 * Variant for actions that redirect to the created resource on success.
 * `redirect()` throws internally to signal Next.js, so it has to run
 * outside any try/catch — this hands the caller a discriminated result
 * instead of swallowing that throw the way `runMutation` would.
 */
export async function runMutationAndReturn<T>(
  mutate: () => Promise<T>
): Promise<{ data: T } | { error: string }> {
  try {
    return { data: await mutate() };
  } catch (error) {
    return { error: describeGrpcError(error) };
  }
}
