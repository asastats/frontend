import type { StepUpSigner } from "./manageAdapters";

/** A privilege-expanding action requested from the manage page. */
export interface StepUpRequest {
  /** "set_primary" or "set_login". */
  operation: string;
  /** The caller's own row the action targets. */
  targetId: number;
  /** For "set_login": the desired state (only `true` reaches step-up). */
  enabled?: boolean;
}

/** Injected collaborators for {@link runStepUp} (all browser concerns isolated). */
export interface RunStepUpDeps {
  /** `fetch` implementation. */
  fetchFn: typeof fetch;
  /** CSRF token for the nonce POST. */
  csrf: string;
  /** Walletauth API base (for `manage/nonce/`). */
  apiBase: string;
  /** Site URL that performs the operation and returns the refreshed list. */
  opsUrl: string;
  /** Wallet step-up signer. */
  stepUpSign: StepUpSigner;
  /** Hands the proof to htmx to POST and swap the list partial. */
  ajax: (url: string, values: Record<string, unknown>) => Promise<void>;
}

/**
 * Obtain a step-up challenge, sign the *operation-bound* message with the
 * current primary, then hand the proof to htmx to POST and swap in the refreshed
 * address list.
 *
 * The signed message is `prefix + "{nonce}:{operation}:{targetId}"`, matching
 * what the server reconstructs and verifies, so a signature obtained for one
 * action cannot be redirected to another. Pure orchestration: every browser,
 * wallet and htmx concern is injected, so this is unit-tested.
 *
 * @param req - The requested operation and target.
 * @param deps - Injected fetch / signer / ajax collaborators.
 */
export async function runStepUp(
  req: StepUpRequest,
  deps: RunStepUpDeps
): Promise<void> {
  const response = await deps.fetchFn(`${deps.apiBase}/manage/nonce/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": deps.csrf },
    body: "{}",
  });
  const challenge = await response.json();
  if (challenge.error) {
    throw new Error(challenge.error);
  }
  const message = `${challenge.prefix}${challenge.nonce}:${req.operation}:${req.targetId}`;
  const proof = await deps.stepUpSign(challenge.address, challenge.chain, message);
  const values: Record<string, unknown> = {
    operation: req.operation,
    target_id: req.targetId,
    nonce: challenge.nonce,
    chain: challenge.chain,
    ...proof,
  };
  if (req.operation === "set_login") {
    values.enabled = req.enabled === true;
  }
  await deps.ajax(deps.opsUrl, values);
}
