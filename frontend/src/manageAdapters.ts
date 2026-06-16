/* istanbul ignore file -- browser/wallet adapters; not exercisable headless */
import { EvmWalletComponent, type EvmDeps } from "./EvmWalletComponent";
import { getDefaultConnectors, defaultEvmSigner } from "./evmConnectors";
import type { ManageDeps } from "./ManageAddressesComponent";

/**
 * Browser-only wiring for the connected-addresses page. Produces the
 * {@link ManageDeps} the {@link ManageAddressesComponent} depends on: a step-up
 * signer that proves control of the *current primary*, and an add-address flow
 * that reuses the EVM link component. None of this runs under jsdom (it touches
 * wallet globals, EIP-6963, WalletConnect and viem), so the file is excluded
 * from coverage; the testable orchestration lives in `ManageAddressesComponent`.
 */

/** Options for {@link defaultManageDeps}. */
export interface ManageAdapterOptions {
  /** walletauth API base (e.g. `/api/v2/wallet`). */
  apiBase: string;
  /** WalletConnect project id; empty string means injected wallets only. */
  wcProjectId: string;
  /** Panel revealed to host the add-address connector buttons. */
  addPanel: HTMLElement;
  /**
   * Step-up signing for an Algorand primary: build and sign the self-payment
   * challenge transaction (note = ``message``) and return the verify payload.
   * Wire this to the existing Algorand `WalletComponent`; without it, an
   * Algorand primary cannot complete step-up.
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
 * The recovered account must equal ``primary`` (case-folded); otherwise the
 * signer rejects, so step-up cannot be satisfied by any wallet other than the
 * one holding the primary key.
 *
 * @param primary - The current primary address (0x form).
 * @param message - The challenge to sign (prefix + nonce).
 * @param wcProjectId - WalletConnect project id (empty = injected only).
 * @returns The verify payload fragment, `{ signature }`.
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

/**
 * Build the {@link ManageDeps} for the connected-addresses page.
 *
 * @param options - API base, WalletConnect id, add panel, and Algorand hooks.
 * @returns Dependencies for {@link ManageAddressesComponent}.
 */
export function defaultManageDeps(options: ManageAdapterOptions): ManageDeps {
  return {
    stepUpSign: async (address, chain, message) => {
      if (chain === "evm") {
        return evmStepUp(address, message, options.wcProjectId);
      }
      if (chain === "algorand") {
        if (!options.algorandStepUpSign) {
          throw new Error("Algorand step-up is not configured");
        }
        return options.algorandStepUpSign(address, message);
      }
      throw new Error(`Unsupported chain: ${chain}`);
    },
    addAddress: async (apiBase) => {
      options.addPanel.hidden = false;
      const deps: EvmDeps = {
        listConnectors: () => getDefaultConnectors(options.wcProjectId),
        sign: defaultEvmSigner,
        navigate:
          options.navigate ||
          ((url: string) => {
            window.location.href = url;
          }),
      };
      const evm = new EvmWalletComponent(options.addPanel, `${apiBase}/link`, deps);
      await evm.bind();
    },
  };
}
