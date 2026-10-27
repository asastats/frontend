/**
 * @file Login nonce binding (audit E2, docs/logbook.md).
 */

/**
 * A fresh secret for one sign-in attempt: sent with the nonce request and
 * again with the verify, which refuses the proof without it.
 *
 * @returns 32 random bytes as 64 lower-case hex characters (the server's `BINDING_RE`).
 */
export function newBinding(): string {
  return Array.from(crypto.getRandomValues(new Uint8Array(32)), (b) =>
    b.toString(16).padStart(2, "0")
  ).join("");
}
