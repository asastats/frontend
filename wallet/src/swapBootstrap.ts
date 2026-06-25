/* istanbul ignore file -- browser/wallet/algod glue; orchestration is tested in swapBridge.test */
import { WalletManager, type WalletId } from "@txnlab/use-wallet";
import {
  makeAssetTransferTxnWithSuggestedParamsFromObject,
  waitForConfirmation as algoWaitForConfirmation,
  type TransactionSigner,
} from "algosdk";
import { optIn, signAndSend, type OptInDeps, type SwapOpts } from "./swapBridge";

const DEFAULT_API_BASE = "/api/v2/wallet";
/** Rounds to wait for a swap group to confirm before timing out. */
const CONFIRM_ROUNDS = 6;

/** The narrow surface the swap widget (widgets repo) calls via the global. */
export interface SwapBridgeApi {
  /** Currently active/connected Algorand address, or null. */
  activeAddress: () => string | null;
  /** Sign + submit + confirm a prepared, grouped, unsigned txn group. */
  signAndSend: (group: Uint8Array[], opts: SwapOpts) => Promise<string>;
  /** Opt the active account into `assetId` (pre-flight 0-amount self-transfer). */
  optIn: (assetId: number) => Promise<string>;
  /** use-wallet signer; used by composer-based routers (Haystack). */
  signer: TransactionSigner;
}

declare global {
  interface Window {
    asastatsSwap?: SwapBridgeApi;
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
  const manager = new WalletManager({
    wallets: wallets.map((w: { id: WalletId }) => w.id),
    defaultNetwork: "mainnet",
  });
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
 * Assemble the injected collaborators the pure {@link signAndSend} needs from a
 * resumed WalletManager: active address, wallet signing, algod submit, algod
 * account queries, and confirmation polling.
 */
function buildDeps(manager: WalletManager): OptInDeps {
  const algod = manager.algodClient;
  return {
    activeAddress: () => connectedWallet(manager)?.activeAccount?.address ?? null,
    signTransactions: (txns) => {
      const wallet = connectedWallet(manager);
      if (!wallet) {
        throw new Error("Connect your Algorand wallet and select an account");
      }
      return wallet.signTransactions(txns);
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
 * Wire the swap bridge when a swap widget is present on the page.
 *
 * No-ops unless a swap entry point is present: the shell accordion container
 * (`#id-folks-swap`) OR the per-ASA modal marker (`#id-swap-enabled`).
 * On a swap page it resumes the wallet manager, publishes `window.asastatsSwap`,
 * then dispatches `asastats:swap-ready` so a widget controller that ran before
 * the wallet bundle can re-run its render gate.
 */
export async function initSwapBridge(doc: Document = document): Promise<void> {
  const container =
    doc.querySelector<HTMLElement>("#id-folks-swap") ||
    doc.querySelector<HTMLElement>("#id-swap-enabled");
  if (!container) {
    return;
  }
  const apiBase = container.dataset.apiBase || DEFAULT_API_BASE;
  try {
    const manager = await swapManager(apiBase);
    const deps = buildDeps(manager);
    window.asastatsSwap = {
      activeAddress: deps.activeAddress,
      signAndSend: (group: Uint8Array[], opts: SwapOpts) =>
        signAndSend(group, deps, opts),
      optIn: (assetId: number) => optIn(assetId, deps),
      // use-wallet's signer; used by composer-based routers (Haystack).
      signer: manager.transactionSigner,
    };
    window.dispatchEvent(new CustomEvent("asastats:swap-ready"));
  } catch (error) {
    console.error("Error initializing swap bridge:", error);
  }
}
