/**
 * Trimmed FormData reads shared by every server action.
 *
 * Server Actions can be invoked directly (a form with JS disabled, a
 * non-browser client hitting the endpoint), so trimming happens here rather
 * than relying on a form's client-side validation having run first.
 */

export function formValue(formData: FormData, key: string): string {
  return ((formData.get(key) as string | null) ?? "").trim();
}

/** Trimmed value, or undefined when blank — for optional fields the gRPC
 * client should omit rather than send as an empty string. */
export function optionalFormValue(formData: FormData, key: string): string | undefined {
  const value = formValue(formData, key);
  return value || undefined;
}
