/* istanbul ignore file -- browser/wallet adapters; not exercisable headless */
import { WalletManager, type WalletId } from "@txnlab/use-wallet";
import {
  makePaymentTxnWithSuggestedParamsFromObject,
  encodeUnsignedTransaction,
} from "algosdk";

/**
 * Signs `message` with the wallet holding `address` on `chain`; resolves to the
 * proof fragment merged into the step-up POST (`{ signature }` for EVM,
 * `{ signedTransaction }` for Algorand). Rejects if the connected account is not
 * the primary, so step-up can only be met by the real primary key.
 */
export type StepUpSigner = (
  address: string,
  chain: string,
  message: string
) => Promise<Record<string, unknown>>;

/** Options for {@link buildStepUpSign}. */
export interface StepUpOptions {
  /** Walletauth API base, e.g. "/api/v2/wallet" (used for the wallets list). */
  apiBase: string;
  /** WalletConnect project id; empty string means injected wallets only. */
  wcProjectId: string;
  /** Optional override for Algorand step-up signing (built-in is used otherwise). */
  algorandStepUpSign?: (
    address: string,
    message: string
  ) => Promise<Record<string, unknown>>;
}

async function evmStepUp(
  primary: string,
  message: string,
  wcProjectId: string
): Promise<Record<string, unknown>> {
  // Loaded on demand so viem/WalletConnect stay in a lazy chunk (matching
  // evmBootstrap); a static import here would pull them into the main bundle.
  const { getDefaultConnectors, defaultEvmSigner } = await import(
    "./evmConnectors"
  );
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

let cachedManager: WalletManager | null = null;

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
 * Build the {@link StepUpSigner} for the manage page (EVM + Algorand).
 *
 * @param options - API base, WalletConnect id, optional Algorand override.
 * @returns A signer the htmx bridge calls to obtain step-up proof.
 */
export function buildStepUpSign(options: StepUpOptions): StepUpSigner {
  return async (address, chain, message) => {
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
  };
}
