/** Default mount point of the EVM walletauth API (overridable per instance). */
export const DEFAULT_EVM_API_BASE = "/api/v2/wallet/login";

/** Matches a 0x-prefixed 20-byte hex EVM address. */
const EVM_ADDRESS_RE = /^0x[0-9a-fA-F]{40}$/;

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

/** Minimal EIP-1193 provider surface used by the EVM flow. */
export interface Eip1193Provider {
  request(args: { method: string; params?: unknown[] }): Promise<unknown>;
}

/**
 * A selectable EVM wallet. Concrete connectors are produced by the browser-only
 * adapters in `evmConnectors.ts` (EIP-6963 injected wallets and WalletConnect),
 * but the component depends only on this shape so it stays testable.
 */
export interface EvmConnector {
  /** Stable identifier (EIP-6963 rdns, or `"walletconnect"`). */
  id: string;
  /** Human-readable wallet name shown on the button. */
  name: string;
  /** Optional data-URI icon (EIP-6963 announces one). */
  icon?: string;
  /** Opens the wallet and returns its provider and selected address. */
  connect(): Promise<{ provider: Eip1193Provider; address: string }>;
}

/** Signs `message` for `address` via `provider`; resolves to a 0x signature. */
export type EvmSigner = (
  provider: Eip1193Provider,
  address: string,
  message: string
) => Promise<string>;

/** Injected collaborators; defaulted to viem/browser implementations in bootstrap. */
export interface EvmDeps {
  /** Returns the connectors to offer (injected discovery + WalletConnect). */
  listConnectors: () => EvmConnector[] | Promise<EvmConnector[]>;
  /** Produces a signature for the challenge message. */
  sign: EvmSigner;
  /** `fetch` implementation (defaults to the global). */
  fetchFn?: typeof fetch;
  /** Navigation side effect on success (defaults to `window.location`). */
  navigate?: (url: string) => void;
}

/**
 * Drives the EVM / xChain wallet flow for both authentication (login) and
 * authorization (linking). The two modes differ only by `apiBase`
 * (`/api/v2/wallet/login` vs `/api/v2/wallet/link`); the request shape is
 * identical, mirroring the Algorand component.
 *
 * Flow on selecting a connector: open the wallet, fetch a nonce for the
 * address, sign `prefix + nonce` (EIP-191 `personal_sign`), post
 * `{ nonce, chain: "evm", signature }` to `<apiBase>/verify/`, then navigate to
 * the URL the server returns. The wallet libraries are injected, so the
 * orchestration is exercised without a browser or a real wallet.
 *
 * @example
 * ```typescript
 * const c = new EvmWalletComponent(el, "/api/v2/wallet/link", deps);
 * await c.bind();
 * ```
 */
export class EvmWalletComponent {
  /** The bound container (carries `#evm-wallet-list` and error slot). */
  private element: HTMLElement;
  /** Base path of the EVM walletauth endpoints. */
  private apiBase: string;
  /** Injected collaborators. */
  private deps: EvmDeps;
  /** Connectors rendered on the last `render`, for click lookup. */
  private connectors: EvmConnector[] = [];

  /**
   * @param element - Container element (`#evm-wallet-connect`).
   * @param apiBase - EVM API base; `/api/v2/wallet/login` or `.../link`.
   * @param deps - Injected wallet/network collaborators.
   */
  constructor(
    element: HTMLElement,
    apiBase: string = DEFAULT_EVM_API_BASE,
    deps: EvmDeps
  ) {
    this.element = element;
    this.apiBase = apiBase;
    this.deps = deps;
  }

  /** Discovers connectors, renders buttons, and wires click delegation. */
  async bind() {
    await this.render();
    this.addEventListeners();
  }

  /**
   * Renders one button per discovered connector into `#evm-wallet-list`
   * (falling back to the container itself). With no connectors, reveals the
   * `#evm-app-error` slot instead.
   */
  private async render() {
    const list =
      this.element.querySelector<HTMLElement>("#evm-wallet-list") ||
      this.element;

    this.connectors = await Promise.resolve(this.deps.listConnectors());
    if (this.connectors.length === 0) {
      this.showNoWallets();
      return;
    }

    list.innerHTML = "";
    this.connectors.forEach((connector) => {
      /** One button per connector; name set via textContent (safe). */
      const button = document.createElement("button");
      button.type = "button";
      button.className =
        "btn whenmoon waves-effect waves-mydark evm-connect-button";
      button.dataset.connectorId = connector.id;

      if (connector.icon) {
        /** Optional wallet icon; src is the connector-announced data URI. */
        const img = document.createElement("img");
        img.src = connector.icon;
        img.alt = "";
        img.className = "evm-wallet-icon";
        img.width = 20;
        img.height = 20;
        button.appendChild(img);
      }
      button.appendChild(document.createTextNode(` ${connector.name}`));
      list.appendChild(button);
    });
  }

  /** Reveals the no-wallet error banner when present. */
  private showNoWallets() {
    /** Optional page-level "no EVM wallet" banner. */
    const banner = this.element.querySelector<HTMLElement>("#evm-app-error");
    /* istanbul ignore else */
    if (banner) {
      banner.style.display = "block";
    }
  }

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
   * Surfaces an error via a Materialize toast when available, otherwise a
   * transient card panel. The message may carry wallet-derived text, so it is
   * HTML-escaped before being handed to the toast `html` sink.
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
    const errorDiv = document.createElement("div");
    errorDiv.className = "card-panel red lighten-2 white-text";
    errorDiv.textContent = message;
    this.element.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 5000);
  }

  /** Wires click delegation; routes connector-button clicks to the flow. */
  private addEventListeners() {
    this.element.addEventListener("click", async (e: Event) => {
      /** Nearest connector button to the click target, if any. */
      const button = (e.target as HTMLElement).closest<HTMLElement>(
        ".evm-connect-button"
      );
      if (!button) return;
      /** Connector matching the clicked button's id. */
      const connector = this.connectors.find(
        (c) => c.id === button.dataset.connectorId
      );
      if (connector) {
        await this.authorizeWith(connector);
      }
    });
  }

  /**
   * Connects the chosen wallet and runs the nonce → sign → verify exchange.
   *
   * @param connector - The wallet the user selected.
   */
  async authorizeWith(connector: EvmConnector) {
    try {
      /** Provider and selected address from the opened wallet. */
      const { provider, address } = await connector.connect();
      /** Canonical lower-cased address (the backend stores lower-case). */
      const addr = (address || "").toLowerCase();
      if (!EVM_ADDRESS_RE.test(addr)) {
        throw new Error(`Invalid EVM address: ${address || "undefined"}`);
      }

      const fetchFn = this.deps.fetchFn || fetch.bind(window);
      /** Shared headers, including CSRF for the session-authenticated link API. */
      const headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": this.getCsrfToken(),
      };

      const nonceResponse = await fetchFn(`${this.apiBase}/nonce/`, {
        method: "POST",
        headers,
        body: JSON.stringify({ address: addr, chain: "evm" }),
      });
      /** `{ nonce, prefix }` on success, or `{ error }`. */
      const nonceData = await nonceResponse.json();
      if (nonceData.error) {
        throw new Error(nonceData.error);
      }

      /** EIP-191 signature over `prefix + nonce`. */
      const signature = await this.deps.sign(
        provider,
        addr,
        `${nonceData.prefix}${nonceData.nonce}`
      );

      const verifyResponse = await fetchFn(`${this.apiBase}/verify/`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          nonce: nonceData.nonce,
          chain: "evm",
          signature,
        }),
      });
      /** `{ success, redirect_url }` or `{ success:false, error }`. */
      const verifyData = await verifyResponse.json();
      if (!verifyData.success) {
        throw new Error(verifyData.error || "Verification failed");
      }

      const navigate =
        this.deps.navigate ||
        /* istanbul ignore next - default browser navigation */
        ((url: string) => {
          window.location.href = url;
        });
      navigate(verifyData.redirect_url || "/");
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      this.showError(message);
    }
  }
}
