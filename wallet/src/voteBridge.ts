/**
 * @file The Voting dApp's `vote` call: build, sign, submit, confirm (docs/logbook.md).
 *
 * Pure orchestration like `manageBridge`: wallet and algod come in as {@link VoteDeps}.
 */

import {
  ABIMethod,
  decodeAddress,
  encodeUnsignedTransaction,
  makeApplicationNoOpTxnFromObject,
  type ABIType,
  type Transaction,
} from "algosdk";

/** One vote, as the panel's data attributes describe it. */
export interface VoteRequest {
  /** Governor seat; must be a connected account, it signs. */
  seat: string;
  /** Voting dApp id. */
  appId: number;
  /** Permission dApp id; the contract reads `votes_of` from it. */
  permissionAppId: number;
  /** Voting session id. */
  sessionId: number;
  /** Zero-based option index. */
  option: number;
  /** ARC-4 signature from the ARC-56 file, e.g. `vote(uint64,uint64)void`. */
  method: string;
}

/** Wallet and algod collaborators of {@link castVote}. */
export interface VoteDeps {
  /** Every account of every connected wallet. */
  accounts: () => string[];
  /** Make `address` the active account of the wallet holding it. */
  useAccount: (address: string) => void;
  /** Sign with the active wallet; one blob (or null) per index to sign. */
  signTransactions: (
    txns: Uint8Array[],
    indexesToSign: number[],
  ) => Promise<(Uint8Array | null)[]>;
  /** algod suggested parameters. */
  suggestedParams: () => Promise<any>;
  /** Submit signed blobs; resolves with the transaction id. */
  submit: (signed: Uint8Array[]) => Promise<string>;
  /** Resolve once `txid` is confirmed. */
  waitForConfirmation: (txid: string) => Promise<void>;
}

/** Big-endian 8-byte encoding of a box key's integer part. */
function uint64Bytes(value: number): Uint8Array {
  const bytes = new Uint8Array(8);
  new DataView(bytes.buffer).setBigUint64(0, BigInt(value));
  return bytes;
}

/** Concatenate byte arrays. */
function concat(...parts: Uint8Array[]): Uint8Array {
  const out = new Uint8Array(parts.reduce((total, part) => total + part.length, 0));
  let offset = 0;
  for (const part of parts) {
    out.set(part, offset);
    offset += part.length;
  }
  return out;
}

/**
 * Box references the `vote` call needs; the names match `dapp/helpers.py`.
 *
 * @param req - The vote.
 * @returns session box `s`+id, ballot box `v`+id+seat, and the Permission dApp's seat box.
 */
export function voteBoxes(req: VoteRequest): { appIndex: number; name: Uint8Array }[] {
  const seatKey = decodeAddress(req.seat).publicKey;
  const id = uint64Bytes(req.sessionId);
  return [
    { appIndex: req.appId, name: concat(Uint8Array.of(0x73), id) },
    { appIndex: req.appId, name: concat(Uint8Array.of(0x76), id, seatKey) },
    { appIndex: req.permissionAppId, name: seatKey },
  ];
}

/**
 * Build the unsigned `vote` application call.
 *
 * The fee is twice the minimum, flat: the call pays for its inner `votes_of` call.
 *
 * @param req - The vote.
 * @param suggestedParams - algod suggested parameters.
 * @returns The transaction.
 */
export function buildVoteTransaction(req: VoteRequest, suggestedParams: any): Transaction {
  const method = ABIMethod.fromSignature(req.method);
  if (method.args.length !== 2) {
    throw new Error(`Unexpected vote method: ${req.method}`);
  }
  const values = [req.sessionId, req.option];
  const minFee = BigInt(suggestedParams.minFee ?? 1000);
  return makeApplicationNoOpTxnFromObject({
    sender: req.seat,
    appIndex: req.appId,
    appArgs: [
      method.getSelector(),
      ...method.args.map((arg, index) => (arg.type as ABIType).encode(BigInt(values[index]))),
    ],
    foreignApps: [req.permissionAppId],
    boxes: voteBoxes(req),
    suggestedParams: { ...suggestedParams, flatFee: true, fee: 2n * minFee },
  });
}

/**
 * Vote as `req.seat`: select its account, sign, submit and wait for confirmation.
 *
 * @param req - The vote.
 * @param deps - Wallet and algod collaborators.
 * @returns The confirmed transaction id.
 */
export async function castVote(req: VoteRequest, deps: VoteDeps): Promise<string> {
  if (!deps.accounts().includes(req.seat)) {
    throw new Error(`Connect the wallet holding ${req.seat} first`);
  }
  deps.useAccount(req.seat);
  const txn = buildVoteTransaction(req, await deps.suggestedParams());
  const [signed] = await deps.signTransactions([encodeUnsignedTransaction(txn)], [0]);
  if (!signed) {
    throw new Error("The wallet did not sign the vote");
  }
  const txid = await deps.submit([signed]);
  await deps.waitForConfirmation(txid);
  return txid;
}
