import { BaseWallet, WalletManager } from "@txnlab/use-wallet";
import {
  makePaymentTxnWithSuggestedParamsFromObject,
  encodeUnsignedTransaction,
  isValidAddress,
} from "algosdk";

/** Default mount point of the walletauth API (overridable per instance). */
const DEFAULT_API_BASE = "/api/v2/wallet";

/**
 * Escape HTML special characters so untrusted text can be placed into an HTML
 * sink (e.g. Materialize's toast `html` option) without injecting markup.
 *
 * @param value - Untrusted text.
 * @returns The text with `& < > " '` replaced by entities.
 */
function escapeHtml(value: string): string {
  return value.replace(
    /[&<>"']/g,
    (c) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[c] as string)
  );
}

/**
 * Manages a single Algorand wallet's connection and the address-authorization
 * flow for the ASA Stats authorize page.
 *
 * Each supported wallet is rendered as its own card and driven by one
 * `WalletComponent`. The component reflects connection/active state into the
 * card's controls and, on authorize, proves control of the active account by
 * signing a 0-ALGO self-payment whose note carries a server nonce. The signed
 * transaction is posted to the backend for off-chain verification and is never
 * submitted to the network.
 *
 * Authorize does not log the user in: the user is already authenticated, and a
 * successful verify authorizes the address onto their profile, then redirects
 * to the profile page.
 *
 * @example
 * ```typescript
 * const component = new WalletComponent(wallet, manager);
 * component.bind(document.getElementById("wallet-pera")!);
 * ```
 */
export class WalletComponent {
  /** The wallet instance this component manages. */
  wallet: BaseWallet;
  /** The wallet manager, used here for its configured algod client. */
  manager: WalletManager;
  /** Base path of the walletauth API endpoints. */
  private apiBase: string;
  /** Unsubscribe handle returned by `wallet.subscribe`. */
  private unsubscribe?: () => void;
  /** The bound DOM root of this wallet's card, or null before `bind`. */
  private element: HTMLElement | null = null;

  /**
   * @param wallet - The wallet instance to manage.
   * @param manager - The wallet manager providing the algod client.
   * @param apiBase - Base path of the walletauth API (default
   *   `/api/v2/wallet`); pass a different value when the API is mounted
   *   elsewhere in a fork.
   */
  constructor(
    wallet: BaseWallet,
    manager: WalletManager,
    apiBase: string = DEFAULT_API_BASE
  ) {
    this.wallet = wallet;
    this.manager = manager;
    this.apiBase = apiBase;
    this.unsubscribe = wallet.subscribe(() => {
      this.render(this.wallet as any);
    });
  }

  /**
   * Binds the component to its card element and wires event listeners.
   *
   * @param element - The wallet card root (`#wallet-<id>`).
   */
  bind(element: HTMLElement) {
    this.element = element;
    this.addEventListeners();
    this.render(this.wallet as any);
  }

  /**
   * Reflects the current wallet state into the card's controls.
   *
   * Toggles button visibility, maintains the "Active" badge on the card
   * heading, and repopulates the account dropdown. All lookups are null-safe so
   * a card may omit controls it does not need (e.g. there is no test-transaction
   * button on the authorize page).
   *
   * @param state - Current wallet connection/active snapshot.
   * @param state.isConnected - Whether the wallet is connected.
   * @param state.isActive - Whether this wallet is the active wallet.
   * @param state.accounts - Connected accounts.
   * @param state.activeAccount - The currently active account, if any.
   */
  private render(state: {
    isConnected: boolean;
    isActive: boolean;
    accounts: any[];
    activeAccount: any;
  }) {
    /* istanbul ignore next */
    if (!this.element) return;

    const { isConnected, isActive, accounts, activeAccount } = state;

    /** Connect/disconnect/set-active/authorize controls (any may be absent). */
    const connectBtn = this.element.querySelector<HTMLButtonElement>(
      `#connect-button-${this.wallet.id}`
    );
    const disconnectBtn = this.element.querySelector<HTMLButtonElement>(
      `#disconnect-button-${this.wallet.id}`
    );
    const setActiveBtn = this.element.querySelector<HTMLButtonElement>(
      `#set-active-button-${this.wallet.id}`
    );
    const authBtn = this.element.querySelector<HTMLButtonElement>(
      `#auth-button-${this.wallet.id}`
    );
    /** Single account dropdown and the card heading carrying the name/badge. */
    const accountSelect = this.element.querySelector<HTMLSelectElement>("select");
    const nameHeader = this.element.querySelector<HTMLHeadingElement>("h4");

    if (connectBtn) connectBtn.style.display = isConnected ? "none" : "block";
    if (disconnectBtn)
      disconnectBtn.style.display = isConnected ? "block" : "none";
    if (setActiveBtn)
      setActiveBtn.style.display = isConnected && !isActive ? "block" : "none";
    if (authBtn)
      authBtn.style.display = isConnected && isActive ? "block" : "none";

    if (nameHeader) {
      /** Existing "Active" badge node, if currently shown. */
      let activeBadge = nameHeader.querySelector(".badge");
      if (isActive && !activeBadge) {
        activeBadge = document.createElement("span");
        activeBadge.className = "badge new myteal white-text";
        activeBadge.setAttribute("data-badge-caption", "");
        activeBadge.textContent = "Active";
        nameHeader.appendChild(activeBadge);
      } else if (!isActive && activeBadge) {
        activeBadge.remove();
      }
    }

    if (accountSelect) {
      accountSelect.innerHTML = "";
      if (isConnected && accounts.length > 0) {
        accounts.forEach((account) => {
          /** One option per connected account; active one preselected. */
          const option = document.createElement("option");
          option.value = account.address;
          option.textContent = `${account.address.substring(
            0,
            6
          )}...${account.address.substring(account.address.length - 6)}`;
          option.selected = account.address === activeAccount?.address;
          accountSelect.appendChild(option);
        });
      } else {
        const option = document.createElement("option");
        option.textContent = "No accounts";
        option.disabled = true;
        accountSelect.appendChild(option);
      }
    }
  }

  /** Connects the wallet. */
  connect = async () => {
    await this.wallet?.connect();
  };

  /** Disconnects the wallet and clears its session. */
  disconnect = async () => {
    await this.wallet?.disconnect();
  };

  /** Makes this wallet the active wallet for signing. */
  setActive = async () => {
    await this.wallet?.setActive();
  };

  /**
   * Reads the CSRF token from the cookie, falling back to a hidden input.
   *
   * @returns The CSRF token, or an empty string when none is present.
   */
  private getCsrfToken(): string {
    /** Value parsed from the `csrftoken` cookie, if any. */
    const cookieValue =
      document.cookie.match("(^|;)\\s*csrftoken\\s*=\\s*([^;]+)")?.pop() || "";
    return (
      cookieValue ||
      (
        document.querySelector(
          'input[name="csrfmiddlewaretoken"]'
        ) as HTMLInputElement | null
      )?.value ||
      ""
    );
  }

  /**
   * Surfaces an error to the user via a Materialize toast when available,
   * otherwise appends a transient message node to the card.
   *
   * The message can contain wallet-derived text (e.g. an active account
   * address), so it is HTML-escaped before being handed to the toast, whose
   * `html` option is inserted as markup. The DOM fallback uses `textContent`
   * and is already safe.
   *
   * @param message - Human-readable error text (treated as untrusted).
   */
  private showError(message: string) {
    /** Optional Materialize global; absent under jsdom/tests. */
    const M = (window as any).M;
    if (M?.toast) {
      M.toast({ html: escapeHtml(message), classes: "red darken-1" });
      return;
    }
    /* istanbul ignore next */
    if (this.element) {
      const errorDiv = document.createElement("div");
      errorDiv.className = "card-panel red lighten-2 white-text";
      errorDiv.textContent = message;
      this.element.appendChild(errorDiv);
      setTimeout(() => errorDiv.remove(), 5000);
    }
  }

  /**
   * Authorizes the active account against the backend.
   *
   * Flow: fetch a nonce for the active address, sign a 0-ALGO self-payment
   * whose note is `prefix + nonce`, post the signed transaction to
   * `<apiBase>/verify/` with `chain: "algorand"`, then redirect to the URL the
   * server returns (the profile page). The `chain` field lets the deferred EVM
   * branch slot in without a request reshape.
   */
  auth = async () => {
    try {
      /** Address currently selected as active in the wallet. */
      const activeAddress = this.wallet?.activeAccount?.address;
      if (!activeAddress || !isValidAddress(activeAddress)) {
        throw new Error(
          `Invalid or missing address: ${activeAddress || "undefined"}`
        );
      }

      /** Shared headers, including CSRF for the session-authenticated API. */
      const headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": this.getCsrfToken(),
      };

      const nonceResponse = await fetch(`${this.apiBase}/nonce/`, {
        method: "POST",
        headers,
        body: JSON.stringify({ address: activeAddress, chain: "algorand" }),
      });
      /** `{ nonce, prefix }` on success, or `{ error }`. */
      const nonceData = await nonceResponse.json();
      if (nonceData.error) {
        throw new Error(nonceData.error);
      }

      /** Note bytes the wallet will sign: `prefix + nonce`. */
      const note = new TextEncoder().encode(`${nonceData.prefix}${nonceData.nonce}`);
      const suggestedParams = await this.manager.algodClient
        .getTransactionParams()
        .do();
      const transaction = makePaymentTxnWithSuggestedParamsFromObject({
        sender: activeAddress,
        receiver: activeAddress,
        amount: 0,
        note,
        suggestedParams,
      });
      const encodedTx = encodeUnsignedTransaction(transaction);
      /** Wallet-signed transactions (one element for our single txn). */
      const signedTxs = await this.wallet.signTransactions([encodedTx]);
      if (!signedTxs[0]) {
        throw new Error("No signed transaction returned");
      }

      /** Base64 of the signed transaction bytes, as the backend expects. */
      const signedTxBase64 = btoa(String.fromCharCode(...signedTxs[0]));

      const verifyResponse = await fetch(`${this.apiBase}/verify/`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          address: activeAddress,
          signedTransaction: signedTxBase64,
          nonce: nonceData.nonce,
          chain: "algorand",
        }),
      });
      /** `{ success, redirect_url }` on success, or `{ success:false, error }`. */
      const verifyData = await verifyResponse.json();
      if (!verifyData.success) {
        throw new Error(verifyData.error || "Verification failed");
      }

      /* istanbul ignore next */
      window.location.href = verifyData.redirect_url || "/";
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      this.showError(message);
    }
  };

  /**
   * Sets the active account from the dropdown selection.
   *
   * @param event - The `change` event from the account `<select>`.
   */
  setActiveAccount = async (event: Event) => {
    /** The newly selected account address. */
    const target = event.target as HTMLSelectElement;
    await this.wallet?.setActiveAccount(target.value);
  };

  /**
   * Wires click and change delegation on the card root.
   *
   * Clicks are routed by element id to connect/disconnect/set-active/authorize;
   * a change on the account `<select>` updates the active account.
   */
  addEventListeners() {
    /* istanbul ignore next */
    if (!this.element) return;

    this.element.addEventListener("click", async (e: Event) => {
      /** The clicked element, matched against this wallet's control ids. */
      const target = e.target as HTMLElement;
      if (target.id === `connect-button-${this.wallet.id}`) {
        await this.connect();
      } else if (target.id === `disconnect-button-${this.wallet.id}`) {
        await this.disconnect();
      } else if (target.id === `set-active-button-${this.wallet.id}`) {
        await this.setActive();
      } else if (target.id === `auth-button-${this.wallet.id}`) {
        await this.auth();
      }
    });

    this.element.addEventListener("change", async (e: Event) => {
      const target = e.target as HTMLElement;
      if (target.tagName.toLowerCase() === "select") {
        await this.setActiveAccount(e);
      }
    });
  }

  /**
   * Tears down the wallet state subscription.
   *
   * Should be called when the component is discarded to avoid leaks.
   */
  destroy() {
    if (this.unsubscribe) {
      this.unsubscribe();
    }
  }
}
