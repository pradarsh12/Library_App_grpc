import type { ProtoTimestamp } from "./types";

/**
 * Converts a decoded google.protobuf.Timestamp to a JS Date.
 *
 * Handles it either as the plain { seconds, nanos } shape proto-loader
 * normally decodes, or as an ISO string, in case protobufjs's well-known
 * type wrapper kicks in — defensive since this project doesn't control
 * that decoding behavior directly.
 */
export function timestampToDate(
  ts: ProtoTimestamp | string | null | undefined
): Date | null {
  if (!ts) return null;
  if (typeof ts === "string") {
    const parsed = new Date(ts);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }
  const seconds = Number(ts.seconds ?? 0);
  if (seconds === 0 && (ts.nanos ?? 0) === 0) return null;
  return new Date(seconds * 1000 + Math.round((ts.nanos ?? 0) / 1e6));
}

export function formatDate(
  ts: ProtoTimestamp | string | null | undefined
): string {
  const date = timestampToDate(ts);
  if (!date) return "—";
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(
  ts: ProtoTimestamp | string | null | undefined
): string {
  const date = timestampToDate(ts);
  if (!date) return "—";
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}
