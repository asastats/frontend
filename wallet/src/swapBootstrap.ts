/* istanbul ignore file -- browser/wallet/algod glue; orchestration is tested in swapBridge.test */
import { WalletManager, type WalletId } from "@txnlab/use-wallet";
import {
  makeAssetTransferTxnWithSuggestedParamsFromObject,
  waitForConfirmation as algoWaitForConfirmation,
} from "algosdk";
import { optIn, signAndSend, type OptInDeps } from "./swapBridge";

const DEFAULT_API_BASE = "/api/v2/wallet";
/** Rounds to wait for a swap group to confirm before timing out. */
const CONFIRM_ROUNDS = 6;

/** The narrow surface the swap widget (widgets repo) calls via the global. */
export interface SwapBridgeApi {
  /** Currently active/connected Algorand address, or null. */
  activeAddress: () => string | null;
  /** Sign + submit + confirm a prepared, grouped, unsigned txn group. */
  signAndSend: (group: Uint8Array[]) => Promise<string>;
  /** Opt the active account into `assetId` (pre-flight 0-amount self-transfer). */
  optIn: (assetId: number) => Promise<string>;
}

declare global {
  interface Window {
    asastatsSwap?: SwapBridgeApi;
  }
}

let cachedManager: WalletManager | null = null;

/**
 * Build (once) and resume a mainnet WalletManager, reusing the same supported-
 * wallets list the authorize/manage flows fetch. Mirrors manageAdapters so the
 * swap path connects to the same wallets the user already authorizes with.
 *
 * @param apiBase - Walletauth API base, e.g. "/api/v2/wallet".
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
 * resumed WalletManager: active address, wallet signing, algod submit, and
 * confirmation polling.
 *
 * @param manager - A resumed mainnet WalletManager.
 */
function buildDeps(manager: WalletManager): OptInDeps {
  return {
    activeAddress: () => connectedWallet(manager)?.activeAccount?.address ?? null,
    signTransactions: (txns) => {
      const wallet = connectedWallet(manager);
      if (!wallet) {
        throw new Error("Connect your Algorand wallet and select an account");
      }
      return wallet.signTransactions(txns);
    },
    submit: async (signed) => {
      const response = await manager.algodClient.sendRawTransaction(signed).do();
      // algosdk v3 returns { txid }; tolerate the older { txId } shape too.
      return (response as { txid?: string; txId?: string }).txid ??
        (response as { txId?: string }).txId ??
        "";
    },
    waitForConfirmation: async (txid) => {
      await algoWaitForConfirmation(manager.algodClient, txid, CONFIRM_ROUNDS);
    },
    buildOptIn: async (assetId) => {
      const sender = connectedWallet(manager)?.activeAccount?.address;
      if (!sender) {
        throw new Error("Connect your Algorand wallet and select an account");
      }
      const suggestedParams = await manager.algodClient
        .getTransactionParams()
        .do();
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
 * No-ops unless the swap container (`#id-folks-swap`, shared by all router
 * widgets) exists, so it is safe to run everywhere — matching initManageAddresses
 * / initEvm. On a swap page it resumes the wallet manager, publishes
 * `window.asastatsSwap`, then dispatches `asastats:swap-ready` so a widget
 * controller that ran before the wallet bundle can re-run its render gate.
 *
 * @param doc - Document to query (defaults to the global document).
 */
export async function initSwapBridge(doc: Document = document): Promise<void> {
  const container = doc.querySelector<HTMLElement>("#id-folks-swap");
  if (!container) {
    return;
  }
  const apiBase = container.dataset.apiBase || DEFAULT_API_BASE;
  try {
    const manager = await swapManager(apiBase);
    const deps = buildDeps(manager);
    window.asastatsSwap = {
      activeAddress: deps.activeAddress,
      signAndSend: (group: Uint8Array[]) => signAndSend(group, deps),
      optIn: (assetId: number) => optIn(assetId, deps),
    };
    window.dispatchEvent(new CustomEvent("asastats:swap-ready"));
  } catch (error) {
    console.error("Error initializing swap bridge:", error);
  }
}
