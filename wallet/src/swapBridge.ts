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
 * orchestrator handles optional user opt-in and referrer-escrow opt-in legs
 * (shape B prepend), then signs the mix (wallet for user legs, logic-sig for
 * escrow legs), submits and confirms.
 */

import {
  assignGroupID,
  decodeUnsignedTransaction,
  encodeUnsignedTransaction,
  signLogicSigTransactionObject,
  makeAssetTransferTxnWithSuggestedParamsFromObject,
} from "algosdk";
import { getReferrerLogicSig, prepareReferrerOptIntoAsset } from "@folks-router/js-sdk";

/** Options passed from the controller with each swap call. */
export interface SwapOpts {
  /** The output asset id for this swap. */
  outputAssetId: number;
  /** Whether the user still needs to opt into the output asset. */
  userNeedsOptIn: boolean;
  /** Referrer address; omit or pass "" for no referrer leg. */
  referrer?: string;
}

/** Injected collaborators for {@link signAndSend} (all wallet/algod concerns isolated). */
export interface SignAndSendDeps {
  /** Currently active/connected Algorand address, or null when none. */
  activeAddress: () => string | null;
  /**
   * Sign the encoded, grouped, unsigned transactions with the active wallet.
   *
   * Must receive ALL transactions in the group (so Pera/wallets can verify
   * group integrity), with `indexesToSign` indicating which positions the
   * wallet should actually sign. Returns one blob per entry in `indexesToSign`;
   * a null entry marks a transaction the wallet declined to sign.
   */
  signTransactions: (
    txns: Uint8Array[],
    indexesToSign: number[],
  ) => Promise<(Uint8Array | null)[]>;
  /** Fetch current suggested transaction params from algod. */
  suggestedParams: () => Promise<any>;
  /**
   * Return whether `addr` is already opted into `assetId`.
   * (algod accountAssetInformation — 404 means not opted in.)
   */
  isOptedIn: (addr: string, assetId: number) => Promise<boolean>;
  /**
   * Return the number of microAlgos the `addr` can spend without dipping
   * below its min-balance (amount − min-balance).
   */
  availableMicroAlgos: (addr: string) => Promise<bigint>;
  /** Submit the signed transaction blobs; resolves with the submitted txid. */
  submit: (signed: Uint8Array[]) => Promise<string>;
  /** Resolve once `txid` is confirmed on-chain (or reject on failure/timeout). */
  waitForConfirmation: (txid: string) => Promise<void>;
}

/**
 * Sign, submit and confirm a prepared swap transaction group, prepending any
 * required opt-in legs (user and/or referrer escrow) as shape B.
 *
 * Build order:
 *  1. [optional] user opt-in into the output asset (wallet-signed).
 *  2. [optional] referrer-escrow opt-in — lsig-signed self-transfer when the
 *     escrow can self-fund its MBR, or the SDK's two-txn pair (user funds the
 *     MBR, then the lsig opt-in) when it cannot.
 *  3. The swap txns forwarded from the caller (all wallet-signed).
 *
 * All entries are cleared of prior group ids and re-assigned a single atomic
 * group id before signing.
 *
 * @param group  - Encoded, grouped, unsigned swap transactions from the adapter.
 * @param deps   - Injected wallet/algod collaborators.
 * @param opts   - Per-call options: output asset, user opt-in flag, referrer.
 * @returns The confirmed transaction id (first leg of the submitted group).
 */
export async function signAndSend(
  group: Uint8Array[],
  deps: SignAndSendDeps,
  opts: SwapOpts,
): Promise<string> {
  if (!group || group.length === 0) {
    throw new Error("Empty transaction group");
  }
  const sender = deps.activeAddress();
  if (!sender) {
    throw new Error("No active wallet account");
  }
  const sp = await deps.suggestedParams();

  // ALGO (asset id 0) is never opted into; only a real ASA output can need it.
  const outputNeedsOptIn = opts.outputAssetId !== 0;

  // entries: { txn, lsig? } — lsig legs are escrow-signed, the rest wallet-signed.
  const entries: { txn: any; lsig?: any }[] = [];

  // 1) user opt-in into the output asset (their own account), if needed
  if (opts.userNeedsOptIn && outputNeedsOptIn) {
    entries.push({
      txn: makeAssetTransferTxnWithSuggestedParamsFromObject({
        sender,
        receiver: sender,
        amount: 0,
        assetIndex: opts.outputAssetId,
        suggestedParams: { ...sp, flatFee: true, fee: 1000 },
      }),
    });
  }

  // 2) referrer escrow opt-in (lazy, one-time per (escrow, asset))
  if (opts.referrer && outputNeedsOptIn) {
    const lsig = getReferrerLogicSig(opts.referrer);
    const escrow = lsig.address().toString();
    if (!(await deps.isOptedIn(escrow, opts.outputAssetId))) {
      // The escrow's logic-sig REQUIRES the opt-in to be immediately preceded by
      // a payment of exactly MinBalance (0.1 ALGO) to the escrow — it asserts
      // prev.Receiver == escrow (pc=148) and prev.Amount == global MinBalance
      // (pc=158). So there is no "self-fund" shortcut even when the escrow holds
      // ALGO: we always use the SDK pair [0.1-ALGO payment, lsig opt-in]. Pass
      // flatFee so the SDK's fee-0 opt-in stays a literal 0 (logic asserts
      // Fee == 0 at pc=25; without flatFee algosdk recomputes it to 1000).
      // The escrow still needs its base 0.1 ALGO funded once (so balance reaches
      // the 0.2 MBR for its first asset); each opt-in's required 0.1 payment then
      // supplies that asset's own MBR.
      const ref = prepareReferrerOptIntoAsset(
        sender,
        opts.referrer,
        opts.outputAssetId,
        { ...sp, flatFee: true },
      );
      for (const r of ref) {
        entries.push({
          txn: decodeUnsignedTransaction(r.unsignedTxn),
          lsig: r.lsig ? lsig : undefined,
        });
      }
    }
  }

  // 3) the swap txns (all user-signed)
  for (const b of group) {
    entries.push({ txn: decodeUnsignedTransaction(b) });
  }

  // Regroup everything (clear prior group ids, then one assignGroupID).
  entries.forEach((e) => {
    e.txn.group = undefined;
  });
  assignGroupID(entries.map((e) => e.txn));

  // Sign: wallet for non-lsig legs (by index), logic-sig for escrow legs.
  const walletIdx: number[] = [];
  entries.forEach((e, i) => {
    if (!e.lsig) walletIdx.push(i);
  });
  const encoded = entries.map((e) => encodeUnsignedTransaction(e.txn));
  // Pass ALL encoded transactions so the wallet (e.g. Pera) can verify group
  // integrity from the group-id field in each txn header, plus the explicit
  // indexes it should sign. Sending only the wallet-signed subset causes Pera
  // to reject with "Missing transaction(s)" / DataView errors.
  const walletSigned = await deps.signTransactions(encoded, walletIdx);

  // walletSigned is parallel to encoded (length = full group): use-wallet
  // returns null at positions it didn't sign and a blob at positions it did.
  // Index directly by i, not via walletIdx.indexOf(i) — that was correct only
  // when we passed a compact subset; now we pass the full group.
  const signedBlobs: Uint8Array[] = entries.map((e, i) => {
    if (e.lsig) return signLogicSigTransactionObject(e.txn, e.lsig).blob;
    const s = walletSigned[i];
    if (!s) throw new Error("Wallet did not sign a required transaction");
    return s;
  });

  const txid = await deps.submit(signedBlobs);
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
 * @param assetId - The output asset to opt into.
 * @param deps    - Injected collaborators, incl. the impure {@link OptInDeps.buildOptIn}.
 * @returns The confirmed opt-in transaction id.
 */
export async function optIn(assetId: number, deps: OptInDeps): Promise<string> {
  const group = await deps.buildOptIn(assetId);
  // optIn is a plain single-signer group; no referrer or output-asset opt-in needed.
  return signAndSend(group, deps, {
    outputAssetId: assetId,
    userNeedsOptIn: false,
  });
}
