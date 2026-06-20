/**
 * Pure orchestration for executing a prepared swap: sign the group with the
 * connected wallet, submit it, and wait for confirmation.
 *
 * Every wallet, algod and browser concern is injected via {@link SignAndSendDeps},
 * so this module imports neither use-wallet nor algosdk and is unit-tested
 * headless — mirroring `manageBridge`. The browser/wallet wiring lives in
 * `swapBootstrap` (isolated, not covered).
 *
 * Trust model: the group is built upstream by the widget's router adapter
 * (Folks SDK), already grouped and with the ASA Stats fee txn appended. This
 * orchestrator never inspects or mutates the group — it only signs, submits and
 * confirms. The live signature over the atomic group is the non-custodial
 * guarantee: nothing here can move funds the user did not sign for, and a failed
 * signature or submission simply aborts with no effect.
 */

/** Injected collaborators for {@link signAndSend} (all wallet/algod concerns isolated). */
export interface SignAndSendDeps {
  /** Currently active/connected Algorand address, or null when none. */
  activeAddress: () => string | null;
  /**
   * Sign the encoded, grouped, unsigned transactions with the active wallet.
   * Returns one entry per input position; a null entry marks a transaction the
   * wallet did not sign (use-wallet's contract).
   */
  signTransactions: (txns: Uint8Array[]) => Promise<(Uint8Array | null)[]>;
  /** Submit the signed transaction blobs; resolves with the submitted txid. */
  submit: (signed: Uint8Array[]) => Promise<string>;
  /** Resolve once `txid` is confirmed on-chain (or reject on failure/timeout). */
  waitForConfirmation: (txid: string) => Promise<void>;
}

/**
 * Sign, submit and confirm a prepared swap transaction group.
 *
 * Pure orchestration: guards the preconditions, then drives
 * sign → submit → confirm through the injected collaborators in order. Throws
 * (and submits nothing) when the group is empty, no wallet account is active, or
 * the wallet does not return a signature for every transaction in the group. The
 * "every transaction signed" check assumes a single-signer group (the user's
 * account signs the input transfer, the router app call(s) and the fee txn); if
 * a future router needs a foreign- or logicsig-signed leg, relax this here.
 *
 * @param group - Encoded, grouped, unsigned transactions ready to sign.
 * @param deps - Injected wallet/algod collaborators.
 * @returns The confirmed transaction id.
 */
export async function signAndSend(
  group: Uint8Array[],
  deps: SignAndSendDeps
): Promise<string> {
  if (!group || group.length === 0) {
    throw new Error("Empty transaction group");
  }
  if (!deps.activeAddress()) {
    throw new Error("No active wallet account");
  }

  const signed = await deps.signTransactions(group);
  const present = signed.filter((s): s is Uint8Array => s != null);
  if (present.length !== group.length) {
    throw new Error("Wallet did not return a signature for every transaction");
  }

  const txid = await deps.submit(present);
  await deps.waitForConfirmation(txid);
  return txid;
}


/** Extra collaborator for {@link optIn}: build the (impure) opt-in transaction. */
export interface OptInDeps extends SignAndSendDeps {
  /** Build the encoded, unsigned 0-amount self asset-transfer that opts in. */
  buildOptIn: (assetId: number) => Promise<Uint8Array[]>;
}

/**
 * Opt the active account into `assetId` as a standalone pre-flight transaction.
 *
 * The Folks swap group does not opt the user into the output asset (the SDK's
 * only opt-in helper opts the *router app* in, not the user), and receiving an
 * ASA you are not opted into fails the whole atomic group. So when holdings show
 * the target is not yet opted in, the controller calls this first: build a
 * 0-amount self asset-transfer (locking 0.1 ALGO of MBR) and sign + submit +
 * confirm it through the very same orchestration as a swap. Keeping it a separate
 * group means Folks' pre-grouped, self-validated transactions are never mutated;
 * the cost is one extra approval the first time into a new asset, none after.
 *
 * @param assetId - The output asset to opt into.
 * @param deps - Injected collaborators, incl. the impure {@link OptInDeps.buildOptIn}.
 * @returns The confirmed opt-in transaction id.
 */
export async function optIn(assetId: number, deps: OptInDeps): Promise<string> {
  const group = await deps.buildOptIn(assetId);
  return signAndSend(group, deps);
}
