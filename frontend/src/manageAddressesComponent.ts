/** Default mount point of the walletauth API. */
export const DEFAULT_MANAGE_API_BASE = "/api/v2/wallet";

/**
 * Escape HTML special characters before placing untrusted text into an HTML
 * sink (the Materialize toast).
 *
 * @param value - Untrusted text.
 * @returns Text with `& < > " '` replaced by entities.
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

/** A connected address as returned by `manage/addresses/`. */
export interface AddressRow {
  id: number;
  address: string;
  chain: string;
  is_primary: boolean;
  login_enabled: boolean;
  label: string;
}

/** Injected collaborators; the wallet-touching ones are browser-only adapters. */
export interface ManageDeps {
  /** `fetch` implementation (defaults to the global). */
  fetchFn?: typeof fetch;
  /**
   * Sign `message` with the wallet holding `address` on `chain` (step-up).
   * Resolves to the payload fragment to merge into the verify POST (e.g.
   * `{ signature }` for EVM). Must reject if the connected account is not
   * `address`, so step-up can only be satisfied by the real primary key.
   */
  stepUpSign: (
    address: string,
    chain: string,
    message: string
  ) => Promise<Record<string, unknown>>;
  /** Run the full "add address" link flow against `apiBase`. */
  addAddress: (apiBase: string) => Promise<void>;
}

/**
 * Drives the connected-addresses management page: lists the caller's addresses
 * and performs set-primary / remove / login-toggle / add-address against the
 * walletauth endpoints. Privilege-expanding actions (make primary, enable
 * login) obtain a step-up challenge and sign it with the current primary; the
 * wallet interactions are injected, so the orchestration is fully testable.
 */
export class ManageAddressesComponent {
  private element: HTMLElement;
  private apiBase: string;
  private deps: ManageDeps;
  private rows: AddressRow[] = [];

  /**
   * @param element - Container (`#connected-addresses`).
   * @param apiBase - walletauth API base (default `/api/v2/wallet`).
   * @param deps - Injected fetch / signer / add-address collaborators.
   */
  constructor(
    element: HTMLElement,
    apiBase: string = DEFAULT_MANAGE_API_BASE,
    deps: ManageDeps
  ) {
    this.element = element;
    this.apiBase = apiBase;
    this.deps = deps;
  }

  /** Wire click delegation and load the current address list. */
  async bind() {
    this.addEventListeners();
    await this.load();
  }

  private get fetchFn(): typeof fetch {
    /* istanbul ignore next -- default global fetch in the browser */
    return this.deps.fetchFn || fetch.bind(window);
  }

  /** CSRF token from cookie, falling back to a hidden input. */
  private getCsrfToken(): string {
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

  private headers(): Record<string, string> {
    return {
      "Content-Type": "application/json",
      "X-CSRFToken": this.getCsrfToken(),
    };
  }

  /** Surface an error via a Materialize toast, or a card panel fallback. */
  private showError(message: string) {
    const M = (window as any).M;
    if (M?.toast) {
      M.toast({ html: escapeHtml(message), classes: "red darken-1" });
      return;
    }
    const div = document.createElement("div");
    div.className = "card-panel red lighten-2 white-text";
    div.textContent = message;
    this.element.appendChild(div);
    setTimeout(() => div.remove(), 5000);
  }

  /** Fetch the caller's addresses and render them. */
  async load() {
    try {
      const response = await this.fetchFn(`${this.apiBase}/manage/addresses/`, {
        headers: this.headers(),
      });
      const data = await response.json();
      this.rows = data.addresses || [];
      this.render();
    } catch (error: unknown) {
      this.showError(this.messageOf(error));
    }
  }

  /**
   * Render the addresses as a Materialize collapsible: one `<li>` per address,
   * the address in its `collapsible-header` and that address's actions tucked
   * into the `collapsible-body`. The primary row's body shows a note instead of
   * actions (it has none).
   */
  private render() {
    const list =
      this.element.querySelector<HTMLElement>("#connected-addresses-list") ||
      this.element;
    list.innerHTML = "";

    const ul = document.createElement("ul");
    ul.className = "collapsible expandable center-align";

    this.rows.forEach((row) => {
      const item = document.createElement("li");
      item.className = "connected-address-row";
      item.id = `address-${row.id}`;
      item.dataset.id = String(row.id);

      // --- HEADER ---
      const header = document.createElement("div");
      header.className = "collapsible-header";
      
      const text = document.createElement("span");
      text.className = "address-text";
      // Apply the special class if this is the primary address
      if (row.is_primary) {
        text.classList.add("mylight-text");
      }
      
      const truncatedAddress = `${row.address.slice(0, 5)}...${row.address.slice(-5)}`;
      text.textContent = truncatedAddress;
      
      header.appendChild(text);
      item.appendChild(header);

      // --- BODY ---
      const body = document.createElement("div");
      body.className = "collapsible-body";

      // 1. Full Address (Responsive/Wrapping)
      const fullAddressContainer = document.createElement("div");
      fullAddressContainer.className = "full-address-text";
      // CSS word-break ensures long hex strings wrap across lines on narrow mobile screens
      fullAddressContainer.style.wordBreak = "break-all"; 
      fullAddressContainer.style.marginBottom = "4px";
      fullAddressContainer.textContent = row.address;
      body.appendChild(fullAddressContainer);

      // 2. Chain Information
      const chainContainer = document.createElement("div");
      chainContainer.className = "chain-text text-muted";
      chainContainer.style.marginBottom = "16px"; // Add space before buttons
      chainContainer.textContent = `(${row.chain})`;
      body.appendChild(chainContainer);

      // 3. Actions or Note
      const actionsContainer = document.createElement("div");
      actionsContainer.className = "address-actions";

      if (row.is_primary) {
        const note = document.createElement("span");
        note.className = "address-note";
        note.textContent = "This is your primary address.";
        actionsContainer.appendChild(note);
      } else {
        actionsContainer.appendChild(this.actionButton("Make primary", "set_primary", row.id));
        actionsContainer.appendChild(
          row.login_enabled
            ? this.actionButton("Disable login", "disable_login", row.id)
            : this.actionButton("Enable login", "enable_login", row.id)
        );
        actionsContainer.appendChild(this.actionButton("Remove", "remove", row.id));
      }
      
      body.appendChild(actionsContainer);
      item.appendChild(body);
      
      ul.appendChild(item);
    });

    list.appendChild(ul);
    this.initCollapsible(ul);
  }

  /* istanbul ignore next -- MaterializeCSS runtime init; browser only */
  private initCollapsible(ul: HTMLElement) {
    // 1. Update the type definition to accept the options object
    const M = (window as unknown as { 
      M?: { 
        Collapsible?: { 
          init(el: Element, options?: { accordion: boolean }): unknown 
        } 
      } 
    }).M;

    if (M?.Collapsible?.init) {
      // 2. Pass the { accordion: false } config exactly as the docs specify
      M.Collapsible.init(ul, { accordion: false });
    }
  }

  private actionButton(label: string, action: string, id: number): HTMLButtonElement {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `btn whenmoon waves-effect manage-action manage-${action}`;
    button.dataset.action = action;
    button.dataset.id = String(id);
    button.textContent = label;
    return button;
  }

  /** Delegate clicks on action buttons (including the static "add" button). */
  private addEventListeners() {
    this.element.addEventListener("click", (e: Event) => {
      const button = (e.target as HTMLElement).closest<HTMLElement>(
        ".manage-action"
      );
      if (!button) return;
      const action = button.dataset.action || "";
      const id = Number(button.dataset.id);
      void this.handle(action, id);
    });
  }

  /**
   * Route an action to its handler with shared error reporting and reload.
   *
   * @param action - The data-action of the clicked button.
   * @param id - The target address id (NaN for "add").
   */
  private async handle(action: string, id: number) {
    try {
      if (action === "add") {
        await this.deps.addAddress(this.apiBase);
      } else if (action === "remove") {
        await this.post({ operation: "remove", target_id: id });
      } else if (action === "disable_login") {
        await this.post({ operation: "set_login", target_id: id, enabled: false });
      } else if (action === "enable_login") {
        await this.stepUp({ operation: "set_login", target_id: id, enabled: true });
      } else if (action === "set_primary") {
        await this.stepUp({ operation: "set_primary", target_id: id });
      } else {
        return;
      }
      await this.load();
    } catch (error: unknown) {
      this.showError(this.messageOf(error));
    }
  }

  /** POST a non-step-up management operation; throws on a failed result. */
  private async post(body: Record<string, unknown>) {
    const response = await this.fetchFn(`${this.apiBase}/manage/`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || "Operation failed");
    }
  }

  /**
   * Perform a step-up operation: fetch a challenge bound to the current
   * primary, sign it with that wallet, then POST the operation with the proof.
   *
   * @param body - The operation payload (operation, target_id, extras).
   */
  private async stepUp(body: Record<string, unknown>) {
    const nonceResponse = await this.fetchFn(`${this.apiBase}/manage/nonce/`, {
      method: "POST",
      headers: this.headers(),
      body: "{}",
    });
    const challenge = await nonceResponse.json();
    if (challenge.error) {
      throw new Error(challenge.error);
    }
    const proof = await this.deps.stepUpSign(
      challenge.address,
      challenge.chain,
      `${challenge.prefix}${challenge.nonce}`
    );
    await this.post({
      ...body,
      nonce: challenge.nonce,
      chain: challenge.chain,
      ...proof,
    });
  }

  private messageOf(error: unknown): string {
    return error instanceof Error ? error.message : String(error);
  }
}
