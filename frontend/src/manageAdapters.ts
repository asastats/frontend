/* istanbul ignore file -- browser/wallet adapters; not exercisable headless */
import { getDefaultConnectors, defaultEvmSigner } from "./evmConnectors";
import type { ManageDeps } from "./manageAddressesComponent";

/**
 * Browser-only wiring for the connected-addresses page. Produces the
 * {@link ManageDeps} the manage component depends on: a step-up signer that
 * proves control of the *current primary*, and an add-address action that sends
 * the user to the dedicated link page (which reuses the authorize-page wallet UI
 * for Algorand *and* EVM, pointed at the link endpoints). None of this runs
 * under jsdom, so the file is excluded from coverage; the testable orchestration
 * lives in `manageAddressesComponent.ts`.
 */

/** Options for {@link defaultManageDeps}. */
export interface ManageAdapterOptions {
  /** WalletConnect project id; empty string means injected wallets only. */
  wcProjectId: string;
  /** URL of the link page to add a new address (any chain). */
  addUrl: string;
  /**
   * Step-up signing for an Algorand primary: build and sign the self-payment
   * challenge transaction (note = ``message``) and return the verify payload
   * (e.g. ``{ address, signedTransaction }``). Wire this to the Algorand
   * use-wallet stack; without it, an Algorand primary cannot complete step-up.
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

/**
 * Build the {@link ManageDeps} for the connected-addresses page.
 *
 * @param options - WalletConnect id, link-page URL, and Algorand hook.
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
        if (!options.algorandStepUpSign) {
          throw new Error("Algorand step-up is not configured");
        }
        return options.algorandStepUpSign(address, message);
      }
      throw new Error(`Unsupported chain: ${chain}`);
    },
    addAddress: async () => {
      navigate(options.addUrl);
    },
  };
}
