import "server-only";

import { status as GrpcStatus } from "@grpc/grpc-js";
import { GrpcCallError } from "./client";

/**
 * Turns a failed RPC into a message safe to show in a form. Mirrors the
 * status table in ../../../README.md ("Handling already checked out").
 */
export function describeGrpcError(error: unknown): string {
  if (!(error instanceof GrpcCallError)) {
    return "Something went wrong. Please try again.";
  }
  switch (error.code) {
    case GrpcStatus.INVALID_ARGUMENT:
    case GrpcStatus.NOT_FOUND:
    case GrpcStatus.ALREADY_EXISTS:
    case GrpcStatus.FAILED_PRECONDITION:
      return error.message;
    default:
      return "Something went wrong. Please try again.";
  }
}
