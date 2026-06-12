import { WalletManager, WalletId } from "@txnlab/use-wallet";
import { WalletComponent } from "./WalletComponent";

/** Default mount point of the walletauth API (overridable via data attribute). */
const DEFAULT_API_BASE = "/api/v2/wallet";

/**
 * Bootstraps the wallet-connect experience on the ASA Stats authorize page.
 *
 * Initializes only when wallet card elements are present, fetches the list of
 * supported wallets from the backend, builds a mainnet `WalletManager`, binds a
 * `WalletComponent` per wallet, and resumes any prior sessions. There is no
 * network selector: ASA Stats authorizes on mainnet only.
 */
export class App {
  /** The wallet manager, or null until `App.init()` runs. */
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
      /** Wallet ids handed to use-wallet. */
      const walletIds = walletsData.map((w: any) => w.id as WalletId);

      this.walletManager = new WalletManager({
        wallets: walletIds,
        defaultNetwork: "mainnet",
      });

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

// Test-only: when the page sets `window.__WALLET_TEST__` (emitted solely under
// settings.WALLET_TEST_MODE), lazy-load the mock wallet harness. The dynamic
// import is code-split into its own chunk, so production never fetches it.
if ((window as any).__WALLET_TEST__) {
  import("./walletTestHarness").then((m) => m.install());
}
