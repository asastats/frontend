/* istanbul ignore file -- browser/wallet adapters; not exercisable headless */
import { WalletManager, type WalletId } from "@txnlab/use-wallet";
import {
  makePaymentTxnWithSuggestedParamsFromObject,
  encodeUnsignedTransaction,
} from "algosdk";
import { getDefaultConnectors, defaultEvmSigner } from "./evmConnectors";
import type { ManageDeps } from "./manageAddressesComponent";

/**
 * Browser-only wiring for the connected-addresses page. Produces the
 * {@link ManageDeps} the manage component depends on: a step-up signer that
 * proves control of the *current primary* (EVM via viem, Algorand via
 * use-wallet), and an add-address action that sends the user to the link page
 * (which reuses the authorize-page wallet UI for every chain). None of this runs
 * under jsdom, so the file is excluded from coverage; the testable orchestration
 * lives in `manageAddressesComponent.ts`.
 */

/** Options for {@link defaultManageDeps}. */
export interface ManageAdapterOptions {
  /** Walletauth API base, e.g. "/api/v2/wallet" (used for the wallets list). */
  apiBase: string;
  /** WalletConnect project id; empty string means injected wallets only. */
  wcProjectId: string;
  /** URL of the link page to add a new address (any chain). */
  addUrl: string;
  /**
   * Optional override for Algorand step-up signing. When omitted, the built-in
   * use-wallet signer is used (resumes the session of the wallet the user signed
   * in with and signs with it). Inject this only to customise the flow.
   */
  algorandStepUpSign?: (
    address: string,
    message: string
  ) => Promise<Record<string, unknown>>;
  /** Navigation side effect (defaults to `window.location`). */
  navigate?: (url: string) => void;
}

/**
 * Connect an EVM wallet and require it to be the current primary, then sign.
 *
 * The recovered account must equal `primary` (case-folded); otherwise the
 * signer rejects, so step-up cannot be satisfied by any wallet other than the
 * one holding the primary key.
 */
async function evmStepUp(
  primary: string,
  message: string,
  wcProjectId: string
): Promise<Record<string, unknown>> {
  const [connector] = await getDefaultConnectors(wcProjectId);
  if (!connector) {
    throw new Error("No EVM wallet available");
  }
  const { provider, address } = await connector.connect();
  if (!address || address.toLowerCase() !== primary.toLowerCase()) {
    throw new Error("Connected wallet is not your primary address");
  }
  return { signature: await defaultEvmSigner(provider, address, message) };
}

/** Cached use-wallet manager so repeated step-ups reuse the live session. */
let cachedManager: WalletManager | null = null;

/**
 * Build (once) a mainnet WalletManager from the backend's supported-wallet list
 * and resume any persisted session -- mirrors `main.ts` so the wallet the user
 * signed in with is restored without rendering any cards.
 */
async function algorandManager(apiBase: string): Promise<WalletManager> {
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

/**
 * Step-up signing for an Algorand primary: sign a 0-ALGO self-payment whose note
 * is the challenge, with the connected wallet whose active account *is* the
 * primary. Returns `{ signedTransaction }` for the manage POST; the backend
 * recovers the sender from the signed transaction and checks it == primary.
 *
 * Requires the primary wallet to be connected (the session the user signed in
 * with is resumed automatically). If it is not the active account, the caller
 * sees an actionable error rather than a silent failure.
 */
async function algorandStepUp(
  primary: string,
  message: string,
  apiBase: string
): Promise<Record<string, unknown>> {
  const manager = await algorandManager(apiBase);
  const wallet = manager.wallets.find(
    (w) => w.isConnected && w.activeAccount?.address === primary
  );
  if (!wallet) {
    throw new Error(
      "Connect your primary Algorand wallet (the one you sign in with) and " +
        "make it the active account, then try again"
    );
  }
  const note = new TextEncoder().encode(message);
  const suggestedParams = await manager.algodClient.getTransactionParams().do();
  const transaction = makePaymentTxnWithSuggestedParamsFromObject({
    sender: primary,
    receiver: primary,
    amount: 0,
    note,
    suggestedParams,
  });
  const encoded = encodeUnsignedTransaction(transaction);
  const signed = await wallet.signTransactions([encoded]);
  if (!signed[0]) {
    throw new Error("No signed transaction returned");
  }
  return { signedTransaction: btoa(String.fromCharCode(...signed[0])) };
}

/**
 * Build the {@link ManageDeps} for the connected-addresses page.
 *
 * @param options - API base, WalletConnect id, link-page URL, optional hook.
 * @returns Dependencies for the manage component.
 */
export function defaultManageDeps(options: ManageAdapterOptions): ManageDeps {
  const navigate =
    options.navigate ||
    ((url: string) => {
      window.location.href = url;
    });
  return {
    stepUpSign: async (address, chain, message) => {
      if (chain === "evm") {
        return evmStepUp(address, message, options.wcProjectId);
      }
      if (chain === "algorand") {
        const signer =
          options.algorandStepUpSign ||
          ((a: string, m: string) => algorandStepUp(a, m, options.apiBase));
        return signer(address, message);
      }
      throw new Error(`Unsupported chain: ${chain}`);
    },
    addAddress: async () => {
      navigate(options.addUrl);
    },
  };
}
