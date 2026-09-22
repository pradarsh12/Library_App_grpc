/**
 * Client-side field validation shared by every create/edit form.
 *
 * These mirror the limits the backend enforces in server/validation.py, so a
 * mistake is caught (and trimmed) before the round trip instead of only
 * after a gRPC error comes back. The backend remains the source of truth —
 * these are UX affordances, not a security boundary.
 */

export const LIMITS = {
  title: 100,
  name: 100,
  email: 200,
  isbn: 32,
  phone: 32,
  genre: 100,
  address: 500,
  copies: 1000,
  loanPeriodDays: 365,
  minYear: 1400,
  maxYear: 2100,
} as const;

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export function isBlank(value: string): boolean {
  return value.trim().length === 0;
}

/** A required text field: must be non-blank after trimming, within `maxLength`. */
export function requiredError(
  value: string,
  label: string,
  maxLength?: number
): string | undefined {
  const trimmed = value.trim();
  if (!trimmed) return `${label} is required`;
  if (maxLength !== undefined && trimmed.length > maxLength) {
    return `${label} must be at most ${maxLength} characters`;
  }
  return undefined;
}

/** An optional text field: blank is fine, but if present it must fit `maxLength`. */
export function optionalLengthError(
  value: string,
  label: string,
  maxLength: number
): string | undefined {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  if (trimmed.length > maxLength) return `${label} must be at most ${maxLength} characters`;
  return undefined;
}

export function emailError(value: string): string | undefined {
  const trimmed = value.trim();
  if (!trimmed) return "Email is required";
  if (trimmed.length > LIMITS.email) {
    return `Email must be at most ${LIMITS.email} characters`;
  }
  if (!EMAIL_RE.test(trimmed)) return "Email is not a valid email address";
  return undefined;
}

/** Published year: optional, but if present must be a plausible whole year. */
export function yearError(value: string): string | undefined {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  const n = Number(trimmed);
  if (!Number.isInteger(n)) return "Published year must be a whole number";
  if (n < LIMITS.minYear || n > LIMITS.maxYear) {
    return `Published year must be between ${LIMITS.minYear} and ${LIMITS.maxYear}`;
  }
  return undefined;
}

/** A positive whole number field (copy counts, loan period). */
export function positiveIntError(
  value: string,
  label: string,
  { max, allowBlank = false }: { max?: number; allowBlank?: boolean } = {}
): string | undefined {
  const trimmed = value.trim();
  if (!trimmed) return allowBlank ? undefined : `${label} is required`;
  const n = Number(trimmed);
  if (!Number.isInteger(n)) return `${label} must be a whole number`;
  if (n < 1) return `${label} must be at least 1`;
  if (max !== undefined && n > max) return `${label} must be at most ${max}`;
  return undefined;
}

/** A required selection (e.g. a <select> that must have a non-empty value). */
export function requiredSelectionError(value: string, label: string): string | undefined {
  return value.trim() ? undefined : `${label} is required`;
}
