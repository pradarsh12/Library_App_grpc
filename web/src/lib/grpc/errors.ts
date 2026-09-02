import "server-only";

import { status as GrpcStatus } from "@grpc/grpc-js";
import { GrpcCallError } from "./client";

const CANT_REACH_SERVER =
  "Can't reach the library server. Make sure the backend (python -m server.main) is running, then try again.";
const TIMED_OUT =
  "The library server took too long to respond. It may be overloaded or the database may be unreachable — please try again.";
const GENERIC = "Something went wrong. Please try again.";

/**
 * Turns a failed RPC into a message safe to show in the UI. The
 * INVALID_ARGUMENT/NOT_FOUND/ALREADY_EXISTS/FAILED_PRECONDITION messages
 * mirror the status table in ../../../README.md ("Handling already
 * checked out") and come straight from the server, since those are
 * produced deliberately by server/errors.py for exactly this purpose.
 * Everything else gets a generic, non-leaky message instead of the raw
 * gRPC/Node error text.
 */
export function describeGrpcError(error: unknown): string {
  if (!(error instanceof GrpcCallError)) {
    return GENERIC;
  }
  switch (error.code) {
    case GrpcStatus.INVALID_ARGUMENT:
    case GrpcStatus.NOT_FOUND:
    case GrpcStatus.ALREADY_EXISTS:
    case GrpcStatus.FAILED_PRECONDITION:
      return error.message;
    case GrpcStatus.UNAVAILABLE:
      return CANT_REACH_SERVER;
    case GrpcStatus.DEADLINE_EXCEEDED:
      return TIMED_OUT;
    default:
      return GENERIC;
  }
}

/** True for connectivity failures specifically (backend down/unreachable). */
export function isServerUnreachable(error: unknown): boolean {
  return (
    error instanceof GrpcCallError &&
    (error.code === GrpcStatus.UNAVAILABLE ||
      error.code === GrpcStatus.DEADLINE_EXCEEDED)
  );
}
