/**
 * Pure orchestration for executing a prepared swap: sign the group with the
 * connected wallet, submit it, and wait for confirmation.
 *
 * Every wallet, algod and browser concern is injected via {@link SignAndSendDeps},
 * so this module imports neither use-wallet nor algosdk-specific wallet code and is unit-tested
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
  decodeSignedTransaction,
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

/** A group whose quote authorization was signed by the backend. */
export interface PartialSignedGroup {
  /** Complete ordered group, encoded without signatures. */
  transactions: Uint8Array[];
  /** Signed transaction blobs keyed by their group index. */
  signedTransactions: Record<string, Uint8Array>;
  /** The quote-signer transaction index, required to be the final index. */
  quoteSignerIndex: number;
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

/**
 * Sign and submit a group that already contains backend signatures.
 *
 * The group is already assembled and grouped by the engine. Unlike
 * `signAndSend`, this function must not prepend opt-ins, clear group IDs or
 * reassign the group: doing any of those would invalidate the quote-signer's
 * signature and the signed floor note.
 */
/**
 * Compare a possibly-absent byte array against one that is always present.
 *
 * `left` is optional because a transaction handed back by a wallet may carry
 * no group at all - that is a divergence, and treating absent as empty is what
 * reports it rather than reading off undefined. `right` is not optional: both
 * call sites pass something the caller has already established exists, and an
 * `?? new Uint8Array()` there was a branch no input could reach.
 */
function sameBytes(left: Uint8Array | null | undefined, right: Uint8Array): boolean {
  const a = left ?? new Uint8Array();
  return a.length === right.length && a.every((v, i) => v === right[i]);
}

/**
 * What a Falcon-1024 signature costs above an Ed25519 one, in microALGO.
 *
 * Two minimum fees, mirroring `router.contract.PQ_FEE_PREMIUM`. Duplicated
 * rather than fetched because this is a diagnostic: it must work on the run
 * that fails, without a round trip that may be the thing that is broken.
 */
const PQ_FEE_PREMIUM = 2000;

/**
 * Say whether the backend could still authorise the group the wallet returned.
 *
 * **The one fact the sign-last design turns on.** A wallet that rewrites the
 * transactions it signs re-groups them, and the backend's authorisation - the
 * last transaction, which the wallet does not sign - keeps the old group id.
 * That is the `inconsistent group values` failure. The proposed fix is to sign
 * that authorisation *after* the wallet has had its way: take the re-grouped
 * transactions back, re-check the note against them, and re-sign over the
 * group id the wallet left.
 *
 * That only works if the wallet's group id covers an authorisation the backend
 * can reproduce. It computed that id over its own view of all the members
 * including the one it did not sign, and it may or may not have raised that
 * one's fee along the way. Nothing in the failure says which - but it is
 * decidable here, offline, from bytes already in hand: recompute the group id
 * over the returned transactions plus each candidate authorisation and see
 * which the wallet agreed with.
 *
 * The alternative is asking the user for another failed swap per guess.
 *
 * @param bodies     - Decoded transaction bodies, index-aligned with the group;
 *                     every entry but `quoteIndex` as the wallet returned it,
 *                     and `quoteIndex` as the backend built it.
 * @param quoteIndex - Index of the backend's authorisation.
 * @param target     - The group id the wallet stamped on what it returned.
 * @returns One sentence naming the authorisation that would fit, or saying
 *          none does.
 */
export function rescueDiagnosis(
  bodies: any[],
  quoteIndex: number,
  target: Uint8Array,
): string {
  const attempts: Array<[string, number]> = [
    ["exactly as the backend built it", 0],
    ["with the post-quantum premium added to its fee", PQ_FEE_PREMIUM],
  ];
  for (const [label, extra] of attempts) {
    let candidates: any[];
    try {
      candidates = bodies.map((body, index) => {
        const fresh: any = decodeUnsignedTransaction(
          encodeUnsignedTransaction(body),
        );
        // not defaulted: `fresh` came out of `decodeUnsignedTransaction`, which
        // always sets a fee - the same reason the consistency check above
        // defaults the wallet's answer and not its own
        if (index === quoteIndex && extra) {
          fresh.fee = BigInt(fresh.fee) + BigInt(extra);
        }
        // **Clearing is not optional.** `assignGroupID` hashes the fields it
        // is given and does not blank an existing group first, so recomputing
        // over already-grouped transactions yields an id that matches nothing
        // - verified against algosdk 3.7.0 rather than assumed.
        fresh.group = undefined;
        return fresh;
      });
      assignGroupID(candidates);
    } catch {
      continue;
    }
    if (sameBytes(candidates[0]?.group, target)) {
      return `signing the authorisation last would rescue it: the wallet's group covers the authorisation ${label}`;
    }
  }
  return (
    "signing the authorisation last would not rescue it: the wallet's group " +
    "covers neither the authorisation as built nor one carrying the premium, " +
    "so it changed something else as well"
  );
}

export async function signAndSendPartial(
  group: PartialSignedGroup,
  deps: SignAndSendDeps,
): Promise<string> {
  if (!group || group.transactions.length === 0) {
    throw new Error("Empty transaction group");
  }
  if (group.quoteSignerIndex !== group.transactions.length - 1) {
    throw new Error("Quote authorization must be the final transaction");
  }

  const preSigned = new Map<number, Uint8Array>();
  for (const [rawIndex, blob] of Object.entries(group.signedTransactions)) {
    const index = Number(rawIndex);
    if (!Number.isInteger(index) || index < 0 || index >= group.transactions.length) {
      throw new Error("Backend signature has an invalid group index");
    }
    if (!(blob instanceof Uint8Array) || blob.length === 0) {
      throw new Error("Backend signature is empty");
    }
    const signed = decodeSignedTransaction(blob) as any;
    const unsigned = signed?.txn
      ? encodeUnsignedTransaction(signed.txn)
      : undefined;
    const expected = group.transactions[index];
    if (
      !unsigned ||
      unsigned.length !== expected.length ||
      unsigned.some((value: number, offset: number) => value !== expected[offset])
    ) {
      throw new Error("Backend signature does not match the grouped transaction");
    }
    if (!signed.sig || signed.sig.length === 0) {
      throw new Error("Backend quote transaction is not signed");
    }
    preSigned.set(index, blob);
  }
  if (!preSigned.has(group.quoteSignerIndex)) {
    throw new Error("Backend quote signature is missing");
  }

  const decoded = group.transactions.map((blob) => decodeUnsignedTransaction(blob));
  if (decoded.some((txn) => !txn.group)) {
    throw new Error("Backend group is not grouped");
  }

  const walletIndexes = decoded
    .map((_, index) => index)
    .filter((index) => !preSigned.has(index));
  const walletSigned = await deps.signTransactions(
    group.transactions,
    walletIndexes,
  );
  if (walletSigned.length !== group.transactions.length) {
    throw new Error("Wallet returned an incomplete transaction group");
  }

  const signed = group.transactions.map((_, index) => {
    const backend = preSigned.get(index);
    if (backend) return backend;
    const wallet = walletSigned[index];
    if (!wallet) throw new Error("Wallet did not sign a required transaction");
    return wallet;
  });

  // **What comes back must be the group that went out.**
  //
  // A quote-signed group carries a backend signature over exact group members,
  // so a wallet that rebuilds a transaction - correcting a fee it considers
  // too low, re-encoding, re-grouping - invalidates it. algod reports the
  // symptom rather than the cause: `inconsistent group values: A != B`, two
  // base32 hashes naming neither the transaction that changed nor what changed
  // in it. Decoding here costs one pass and turns that into a sentence.
  //
  // Post-quantum accounts make this concrete rather than theoretical. A Falcon
  // signature costs three minimum fees where Ed25519 costs one, so a wallet
  // that corrects an underpaid fee on the caller's behalf is behaving
  // reasonably and breaking a group signed over the original at the same time.
  // non-null because the guard above rejected the group unless every
  // transaction carries one; `some` is not a narrowing TypeScript can follow
  const expected = decoded[0].group as Uint8Array;
  const divergences: string[] = [];
  // Kept index-aligned so a failure can be diagnosed rather than only
  // reported, and filled rather than left sparse: `every` skips holes, so an
  // array with a gap where an undecodable transaction should be would report
  // itself complete and the probe would run on nothing.
  const bodies: any[] = signed.map(() => undefined);
  let regrouped: Uint8Array | undefined;
  signed.forEach((blob, index) => {
    let returned: any;
    try {
      returned = decodeSignedTransaction(blob) as any;
    } catch {
      divergences.push(`[${index}] came back undecodable`);
      return;
    }
    const txn = returned?.txn;
    if (!txn) {
      divergences.push(`[${index}] came back without a transaction body`);
      return;
    }
    bodies[index] = txn;

    const before = decoded[index];
    const differences: string[] = [];
    if (!sameBytes(txn.group, expected)) {
      differences.push("re-grouped");
      if (!regrouped && txn.group) regrouped = txn.group;
    }
    // `txn.fee` is defaulted because the wallet's answer is not trusted to
    // have one; `before.fee` is not, because it came from a transaction this
    // module decoded and algosdk always sets it - a default there was a branch
    // no input could reach.
    if (Number(txn.fee ?? 0) !== Number(before.fee)) {
      differences.push(`fee ${before.fee} -> ${txn.fee}`);
    }
    // Anything else at all: re-encoding the returned transaction and comparing
    // it to the one sent catches a changed field this does not name, which
    // matters because the named ones are guesses about what a wallet might do
    // and the byte comparison is not.
    if (!differences.length) {
      try {
        const again = encodeUnsignedTransaction(txn);
        if (!sameBytes(again, group.transactions[index])) {
          differences.push("changed in some other field");
        }
      } catch {
        differences.push("could not be re-encoded to compare");
      }
    }
    if (differences.length) {
      divergences.push(`[${index}] ${differences.join(", ")}`);
    }
  });

  // **Every divergence, not the first.** Reporting one at a time hides the
  // cause behind the symptom: a wallet that raises a fee must re-group to keep
  // the group hash valid, so "re-grouped" is what you see and the fee change
  // is what you needed to know. Post-quantum accounts make that the likely
  // case, since a Falcon signature costs three minimum fees where this group
  // pays one.
  if (divergences.length) {
    // **And say whether it is recoverable.** The report above names what the
    // wallet changed; on its own that has cost two sessions of guessing at
    // what to do about it. The probe answers that in the same breath, from the
    // bytes already decoded, so a failed swap carries its own verdict on the
    // fix rather than requiring another one to test it.
    const verdict =
      regrouped && bodies.every(Boolean)
        ? ` - ${rescueDiagnosis(bodies, group.quoteSignerIndex, regrouped)}`
        : "";
    throw new Error(
      `The wallet returned ${divergences.length} transaction(s) different ` +
        `from the ones it was given, so the backend's quote signature no ` +
        `longer covers this group: ${divergences.join("; ")}${verdict}`,
    );
  }

  const txid = await deps.submit(signed);
  await deps.waitForConfirmation(txid);
  return txid;
}


/** Extra collaborator for {@link optIn}: build the (impure) opt-in transaction. */
export interface OptInDeps extends SignAndSendDeps {
  /** Build the encoded, unsigned 0-amount self asset-transfer that opts in. */
  buildOptIn: (assetId: number) => Promise<Uint8Array[]>;
}

/** The one algod call {@link assetCreator} needs, injected so it can be tested. */
export interface AssetLookupDeps {
  /** Fetch an asset's on-chain parameters (algod `getAssetByID`). */
  getAsset: (assetId: number) => Promise<unknown>;
}

/**
 * Return the on-chain creator of `assetId`, or null when it cannot be read.
 *
 * **This is a security control's only source of truth, not a convenience.**
 * The dust sweep gives a holding away by closing it to the asset's creator,
 * and its browser-side check used to compare that destination against an
 * address carried in the same response as the transaction bytes — so a
 * response that agreed with itself could name anything (audit finding `S2`).
 * This is the second opinion that check needs, and it lives here rather than
 * in `swapBootstrap` because that module is `istanbul ignore file`d as
 * untestable glue. Deciding a forfeit is not glue.
 *
 * **Null on every failure, deliberately.** The caller refuses a forfeit it
 * cannot confirm, so a thrown request, an asset that does not exist and a
 * response missing `params` must all reach it the same way. Returning null
 * rather than rethrowing keeps that decision in one place.
 *
 * @param assetId - The asset whose creator to read.
 * @param deps    - Injected algod lookup.
 * @returns The creator address, or null when it could not be determined.
 */
export async function assetCreator(
  assetId: number,
  deps: AssetLookupDeps,
): Promise<string | null> {
  try {
    const asset = (await deps.getAsset(assetId)) as {
      params?: { creator?: unknown };
    } | null;
    const creator = asset?.params?.creator;
    // Guard the type as well as the presence: a non-string here would be
    // compared against a decoded address and silently never match, which
    // would read as "the engine lied" rather than "we could not tell".
    return typeof creator === "string" && creator ? creator : null;
  } catch {
    return null;
  }
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
