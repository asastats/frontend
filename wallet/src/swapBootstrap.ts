import { WalletManager } from "@txnlab/use-wallet";
import { createWalletManager } from "./walletAdapters";
import {
  encodeUnsignedTransaction,
  makeAssetTransferTxnWithSuggestedParamsFromObject,
  waitForConfirmation as algoWaitForConfirmation,
  type Transaction,
  type TransactionSigner,
} from "algosdk";
import {
  assetCreator,
  optIn,
  signAndSend,
  signAndSendPartial,
  type OptInDeps,
  type PartialSignedGroup,
  type SwapOpts,
} from "./swapBridge";

const DEFAULT_API_BASE = "/api/v2/wallet";
/** Rounds to wait for a swap group to confirm before timing out. */
const CONFIRM_ROUNDS = 6;
/**
 * Every entry point that needs a wallet: the swap's shell accordion, its
 * per-ASA modal marker, and the dust sweep's toolbar.
 *
 * **The sweep belongs on this list even though it is not a swap.** It signs
 * through the same bridge -- `signAndSend`, `signAndSendPartial` and
 * `assetCreator` are all its callers too -- so what this module publishes is
 * the wallet's signing bridge, whatever its name says.
 *
 * `_swap_entry.html` renders the sweep under its own condition
 * (`{% if dustsweep_address %}`), independent of the swap's
 * (`{% if swap_url %}`). Mounting only for the swap's entries left a reader who
 * qualified for the sweep but whose page had no router with nothing published
 * at all, so the sweep button stayed hidden with nothing in the console to say
 * why.
 */
const WALLET_ENTRIES = ["#id-swap-swap", "#id-swap-enabled", "#id-dustsweep"];

/**
 * Signer type Haystack's composer calls: Transaction objects + indexes to sign.
 * Distinct from use-wallet's TransactionSigner which takes encoded Uint8Array[].
 */
export type HaystackSignerFn = (
  txnGroup: Transaction[],
  indexesToSign: number[],
) => Promise<(Uint8Array | null)[]>;

/** The narrow surface the swap widget (widgets repo) calls via the global. */
export interface SwapBridgeApi {
  /** Currently active/connected Algorand address, or null. */
  activeAddress: () => string | null;
  /** Sign + submit + confirm a prepared, grouped, unsigned txn group. */
  signAndSend: (group: Uint8Array[], opts: SwapOpts) => Promise<string>;
  /** Sign and submit an engine group with a backend-signed quote transaction. */
  signAndSendPartial: (group: PartialSignedGroup) => Promise<string>;
  /** Opt the active account into `assetId` (pre-flight 0-amount self-transfer). */
  optIn: (assetId: number) => Promise<string>;
  /**
   * Creator address of `assetId` read from the chain, or null when it cannot
   * be read.
   *
   * Exists for the dust sweep, which gives a holding away by closing it to the
   * asset's creator. Its browser-side check compared that destination against
   * an address carried in the same response as the transaction bytes, so a
   * consistent answer could name anything (audit finding `S2`). This is the
   * independent source that check needed, and the algod client is already here
   * for `isOptedIn`.
   */
  assetCreator: (assetId: number) => Promise<string | null>;
  /**
   * Signer for composer-based routers (Haystack) that pass live Transaction
   * objects. Pre-encodes each Transaction to bytes before forwarding to
   * use-wallet's signer, bridging the cross-bundle object/bytes boundary.
   */
  haystackSigner: HaystackSignerFn;
  /**
   * @deprecated Use haystackSigner for Haystack. Kept for back-compat.
   * use-wallet's raw TransactionSigner (expects encoded Uint8Array[], not
   * Transaction objects — will DataView-fail if called with live Transactions
   * from a foreign bundle).
   */
  signer: TransactionSigner;
}

/**
 * Which Algorand account this browser has connected -- and nothing else.
 *
 * **Published separately from {@link SwapBridgeApi} on purpose.** Connection
 * state is a fact about the browser that several features need and none of them
 * owns. It used to be readable only off `window.asastatsSwap`, so the dust
 * sweep -- which needs a connected wallet and no part of the swap -- could only
 * learn it by asking the swap. Any swap-side failure then removed a feature
 * that does not depend on the swap, and one did: see the note on `signer`.
 */
export interface WalletConnectionApi {
  /** Currently active/connected Algorand address, or null. */
  activeAddress: () => string | null;
}

declare global {
  interface Window {
    asastatsSwap?: SwapBridgeApi;
    asastatsWallet?: WalletConnectionApi;
  }
}

let cachedManager: WalletManager | null = null;

/**
 * Build (once) and resume a mainnet WalletManager, reusing the same supported-
 * wallets list the authorize/manage flows fetch.
 */
async function swapManager(apiBase: string): Promise<WalletManager> {
  if (cachedManager) {
    await cachedManager.resumeSessions();
    return cachedManager;
  }
  const response = await fetch(`${apiBase}/wallets/`);
  if (!response.ok) {
    throw new Error("Failed to load supported wallets");
  }
  const wallets = await response.json();
  const manager = createWalletManager(wallets);
  await manager.resumeSessions();
  cachedManager = manager;
  return manager;
}

/** Return the connected wallet whose active account address is set, or null. */
function connectedWallet(manager: WalletManager) {
  return (
    manager.wallets.find((w) => w.isConnected && w.activeAccount?.address) || null
  );
}

/**
 * Return the active account's address, or null.
 *
 * Named rather than inlined because it is asked in two places for two reasons:
 * the swap's deps need it to build transactions, and {@link WalletConnectionApi}
 * publishes it as a fact in its own right. One expression so the two answers
 * cannot drift.
 */
function activeAddressOf(manager: WalletManager): string | null {
  return connectedWallet(manager)?.activeAccount?.address ?? null;
}

/**
 * Assemble the injected collaborators the pure {@link signAndSend} needs from a
 * resumed WalletManager: active address, wallet signing, algod submit, algod
 * account queries, and confirmation polling.
 */
function buildDeps(manager: WalletManager): OptInDeps {
  const algod = manager.algodClient;
  return {
    activeAddress: () => activeAddressOf(manager),
    signTransactions: (txns, indexesToSign) => {
      const wallet = connectedWallet(manager);
      if (!wallet) {
        throw new Error("Connect your Algorand wallet and select an account");
      }
      // Forward all txns + explicit indexes: wallets like Pera verify group
      // integrity by checking the group-id field on every transaction in the
      // group. If we sent only the wallet-signed subset, Pera would see a
      // partial group and reject with "Missing transaction(s)".
      return wallet.signTransactions(txns, indexesToSign);
    },
    suggestedParams: () => algod.getTransactionParams().do(),
    isOptedIn: async (addr: string, assetId: number) => {
      try {
        await algod.accountAssetInformation(addr, assetId).do();
        return true;
      } catch {
        return false; // 404 => not opted in
      }
    },
    availableMicroAlgos: async (addr: string) => {
      const info = await algod.accountInformation(addr).do();
      return (
        BigInt(info.amount) -
        BigInt((info as any)["min-balance"] ?? (info as any).minBalance ?? 0)
      );
    },
    submit: async (signed) => {
      const response = await algod.sendRawTransaction(signed).do();
      // algosdk v3 returns { txid }; tolerate the older { txId } shape too.
      return (
        (response as { txid?: string; txId?: string }).txid ??
        (response as { txId?: string }).txId ??
        ""
      );
    },
    waitForConfirmation: async (txid) => {
      await algoWaitForConfirmation(algod, txid, CONFIRM_ROUNDS);
    },
    buildOptIn: async (assetId) => {
      const sender = connectedWallet(manager)?.activeAccount?.address;
      if (!sender) {
        throw new Error("Connect your Algorand wallet and select an account");
      }
      const suggestedParams = await algod.getTransactionParams().do();
      // 0-amount self transfer of the target asset = opt-in (0.1 ALGO MBR).
      const txn = makeAssetTransferTxnWithSuggestedParamsFromObject({
        sender,
        receiver: sender,
        amount: 0,
        assetIndex: assetId,
        suggestedParams,
      });
      return [txn.toByte()];
    },
  };
}

/**
 * Publish wallet connection state, and the swap bridge when a swap is present.
 *
 * **Two halves, deliberately, and the smaller one comes first.**
 *
 * `window.asastatsWallet` is which account this browser has connected. It is
 * published **first, and outside the `try`** below, so that a signing bridge
 * which cannot be built cannot take it away. `asastats:wallet-ready` announces
 * it.
 *
 * `window.asastatsSwap` is the signing bridge, published for every entry in
 * `WALLET_ENTRIES` -- the sweep signs through it too.
 *
 * **Why the first half exists at all.** Deciding whether to *offer* a feature
 * is not the same question as being able to *sign*, and only the sweep asks the
 * first one: it reveals its button for a connected account. Reading that off
 * the signing bridge meant the button vanished whenever the bridge did -- once
 * because building it threw (see the note on `signer`), once because the page
 * had no entry to mount it at all. Connection state is a fact about the browser
 * that no feature owns, so it is published as one.
 *
 * Safe to call repeatedly: htmx delivers `#id-swap-enabled` after
 * DOMContentLoaded, so `main.ts` retries on every settle, and this returns at
 * once once both are up.
 */
export async function initSwapBridge(doc: Document = document): Promise<void> {
  const container = WALLET_ENTRIES.reduce<HTMLElement | null>(
    (found, selector) => found || doc.querySelector<HTMLElement>(selector),
    null,
  );
  if (!container) {
    return;
  }
  // Already up. The retry on every htmx settle lands here.
  if (window.asastatsWallet && window.asastatsSwap) {
    return;
  }
  const apiBase = container.dataset.apiBase || DEFAULT_API_BASE;

  let manager: WalletManager;
  try {
    manager = await swapManager(apiBase);
  } catch (error) {
    // Nothing can be published without it, including the sweep's half.
    console.error("Error connecting the wallet:", error);
    return;
  }

  window.asastatsWallet = { activeAddress: () => activeAddressOf(manager) };
  window.dispatchEvent(new CustomEvent("asastats:wallet-ready"));

  try {
    const deps = buildDeps(manager);
    /**
     * Adapter for Haystack's composer: it calls signer(Transaction[], indexes)
     * with live Transaction objects from its own bundle. use-wallet's
     * transactionSigner expects encoded Uint8Array[], so we encode each txn with
     * our algosdk first, then forward to the wallet for signing.
     *
     * Both bundles use algosdk v3, but Transaction objects can't cross the bundle
     * boundary safely via use-wallet's signer (which re-encodes them internally
     * using its own class instance, causing the DataView overread). Encoding to
     * bytes here is the safe handoff point: bytes are just bytes.
     */
    const haystackSigner: HaystackSignerFn = (txnGroup, indexesToSign) => {
      const wallet = connectedWallet(manager);
      if (!wallet) {
        throw new Error("Connect your Algorand wallet and select an account");
      }
      const encoded = txnGroup.map((txn) => encodeUnsignedTransaction(txn));
      return wallet.signTransactions(encoded, indexesToSign);
    };

    window.asastatsSwap = {
      activeAddress: deps.activeAddress,
      signAndSend: (group: Uint8Array[], opts: SwapOpts) =>
        signAndSend(group, deps, opts),
      signAndSendPartial: (group: PartialSignedGroup) =>
        signAndSendPartial(group, deps),
      optIn: (assetId: number) => optIn(assetId, deps),
      // The decision lives in swapBridge, which is covered; this is the wiring.
      assetCreator: (assetId: number) =>
        assetCreator(assetId, {
          getAsset: (id) => manager.algodClient.getAssetByID(id).do(),
        }),
      haystackSigner,
      /*
       * Kept for back-compat; Haystack must use haystackSigner instead.
       *
       * **A getter, and it has to be.** `manager.transactionSigner` is a getter
       * in use-wallet that *throws* `No active wallet found!` when no wallet is
       * active. Read eagerly here, it threw while this object literal was being
       * built -- so `window.asastatsSwap` was never assigned at all, the
       * `asastats:swap-ready` event never fired, and the whole bridge was lost
       * for every reader who simply had no wallet connected. The catch below
       * turned that into one console line and no other symptom.
       *
       * It cost a live feature. `dustsweep.js` reads `activeAddress()` off this
       * object to decide whether to reveal its button; with the object missing
       * it stayed hidden, and its `setInterval` could not recover because it
       * polls a bridge that was never built. Users reported the Dust Sweep
       * button had vanished and not come back.
       *
       * Deferring the read costs nothing: by the contract above nothing should
       * be reading `signer` any more, and a caller that does gets the same
       * error it would have got before -- at the point it asks, rather than
       * taking every other method down with it.
       */
      get signer(): TransactionSigner {
        return manager.transactionSigner;
      },
    };
    window.dispatchEvent(new CustomEvent("asastats:swap-ready"));
  } catch (error) {
    console.error("Error initializing swap bridge:", error);
  }
}
