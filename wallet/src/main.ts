import { WalletManager } from "@txnlab/use-wallet";
import { createWalletManager } from "./walletAdapters";
import { WalletComponent } from "./walletComponent";
import { install as installTestHarness } from "./walletTestHarness";
import { initEvm } from "./evmBootstrap";
import { initManageAddresses } from "./manageBootstrap";
import { initSwapBridge } from "./swapBootstrap";

/** Default mount point of the walletauth API (overridable via data attribute). */
const DEFAULT_API_BASE = "/api/v2/wallet";

/**
 * Bootstraps the wallet-connect experience on the website authorize page.
 *
 * Initializes only when wallet card elements are present, fetches the list of
 * supported wallets from the backend, builds a mainnet `WalletManager`, binds a
 * `WalletComponent` per wallet, and resumes any prior sessions. There is no
 * network selector: website authorizes on mainnet only.
 */
export class App {
  /** The wallet manager, or null until {@link App.init} runs. */
  walletManager: WalletManager | null = null;
  /** Bound wallet components, retained for cleanup. */
  private walletComponents: WalletComponent[] = [];
  /** Resolved walletauth API base path. */
  private apiBase: string = DEFAULT_API_BASE;

  /** Registers initialization on `DOMContentLoaded`. */
  constructor() {
    document.addEventListener("DOMContentLoaded", this.init.bind(this));
  }

  /**
   * Initializes wallets and binds components.
   *
   * No-ops on pages without wallet cards. On failure it reveals the
   * `#app-error` element if present and logs the error.
   */
  async init() {
    try {
      /** Root carrying optional `data-api-base`; also gates initialization. */
      const container = document.querySelector<HTMLElement>("#wallet-connect");
      /** Whether any wallet card exists on this page. */
      const hasWalletElements =
        !!container || document.querySelector('[id^="wallet-"]') !== null;
      if (!hasWalletElements) {
        return;
      }
      this.apiBase = container?.dataset.apiBase || DEFAULT_API_BASE;

      const walletsResponse = await fetch(`${this.apiBase}/wallets/`);
      if (!walletsResponse.ok) {
        throw new Error("Failed to fetch supported wallets");
      }
      /** Backend wallet descriptors: `[{ id, name }, ...]`. */
      const walletsData = await walletsResponse.json();

      this.walletManager = createWalletManager(walletsData);

      walletsData.forEach((walletData: any) => {
        /** The use-wallet wallet instance for this id. */
        const wallet = this.walletManager!.getWallet(walletData.id);
        if (wallet) {
          /** The wallet's card root, if rendered on this page. */
          const walletEl = document.getElementById(`wallet-${wallet.id}`);
          if (walletEl) {
            const component = new WalletComponent(
              wallet,
              this.walletManager!,
              this.apiBase
            );
            component.bind(walletEl);
            this.walletComponents.push(component);
          }
        }
      });

      await this.walletManager.resumeSessions();

      window.addEventListener("beforeunload", () => {
        this.walletComponents.forEach((c) => c.destroy?.());
      });
    } catch (error) {
      console.error("Error initializing wallet app:", error);
      /** Optional page-level error banner. */
      const errorDiv = document.getElementById("app-error");
      if (errorDiv) {
        errorDiv.style.display = "block";
      }
    }
  }
}

// Initialize the application.
new App();

/* istanbul ignore next -- bootstrap glue; orchestration is tested in evmBootstrap.test */
{
  // Mount the EVM/xChain wallet UI when present. No-ops on pages without the
  // `#evm-wallet-connect` container, so it is safe to run everywhere.
  const bootstrapEvm = () => {
    void initEvm();
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootstrapEvm);
  } else {
    bootstrapEvm();
  }
}

/* istanbul ignore next -- bootstrap glue; orchestration is tested in manageBridge.test */
{
  // Mount the connected-addresses manager when present. No-ops on pages without
  // the `#connected-addresses` container, so it is safe to run everywhere.
  const bootstrapManage = () => {
    void initManageAddresses();
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootstrapManage);
  } else {
    bootstrapManage();
  }
}

/* istanbul ignore next -- bootstrap glue; orchestration is tested in swapBridge.test */
{
  // Mount wallet connection state when anything on the page needs it, and the
  // swap bridge when a swap entry is present. No-ops on pages with neither.
  const bootstrapSwap = () => {
    void initSwapBridge();
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootstrapSwap);
  } else {
    bootstrapSwap();
  }
  // The #id-swap-enabled marker is a non-cached htmx partial (hx-trigger="load"
  // in address.html), so it arrives after DOMContentLoaded. Re-attempt whenever
  // htmx settles new content, until this page's needs are met.
  //
  // The guard that used to live here -- `if (!window.asastatsSwap)` -- cannot
  // ask the question any more: a page carrying only the dust sweep publishes
  // wallet state and no swap bridge, so that condition would be true forever
  // and re-resume the wallet on every settle. `initSwapBridge` owns the
  // decision now, because it is the half that knows what this page asked for.
  // `htmx:after:settle` is htmx 4's spelling; htmx 2 called it
  // `htmx:afterSettle` and fires nothing under the new name. This bundle is
  // vendored into the Django static tree as a built artifact, so a page serving
  // htmx 4 against a stale bundle would simply never re-init the swap bridge -
  // no error, just a Swap button and a Dust Sweep button that never wire up,
  // because the entry partial arrives by htmx swap after DOMContentLoaded.
  document.body.addEventListener("htmx:after:settle", () => {
    void initSwapBridge();
  });
}

// Test-only: when the page sets `window.__WALLET_TEST__` (emitted solely under
// settings.WALLET_TEST_MODE), install the mock wallet harness synchronously so
// `window.__installMockWallet` is defined by the time bundle.js finishes
// executing -- before Selenium regains control. The harness is inert (never
// installed) when the flag is absent, so production is unaffected.
if ((window as any).__WALLET_TEST__) {
  installTestHarness();
}
