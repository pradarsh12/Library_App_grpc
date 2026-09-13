"use client";

import { useEffect, useState } from "react";

/**
 * Extracts the error message from a `useActionState` result and clears it
 * after `ms` (default 5s), so validation errors (e.g. "member already has
 * this book on loan") behave like a toast — disappearing on their own —
 * instead of lingering until the next form submission.
 *
 * Tracks `state`'s object identity, not just the message text: every
 * action call returns a fresh object (even `{ error: "same text" }`
 * twice in a row is two different objects), so resubmitting and hitting
 * the *same* error again still re-shows it and restarts the 5s timer,
 * rather than staying stuck hidden from the first time it dismissed.
 */
export function useDismissingError(
  state: { error?: string | null },
  ms = 5000
): string | null {
  // Adjusting state during render (the React-recommended pattern for
  // deriving state from a changed value) rather than in a useEffect,
  // which would cause an extra render pass every time.
  const [prevState, setPrevState] = useState(state);
  const [visible, setVisible] = useState<string | null>(state.error ?? null);
  if (state !== prevState) {
    setPrevState(state);
    setVisible(state.error ?? null);
  }

  useEffect(() => {
    if (!visible) return;
    const timer = setTimeout(() => setVisible(null), ms);
    return () => clearTimeout(timer);
  }, [visible, ms]);

  return visible;
}
