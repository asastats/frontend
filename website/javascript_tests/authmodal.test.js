/**
 * @jest-environment jsdom
 */

const A = require("../static/js/authmodal.js");

/** The shape snippets/modal_login_tw.html renders. */
function mountModal() {
  document.body.innerHTML = `
    <a id="opener" href="#modalLogin">Log in</a>
    <dialog id="modalLogin">
      <div role="tablist">
        <a role="tab" aria-selected="true" class="is-active" href="#modal-tab-login">Log in</a>
        <a role="tab" aria-selected="false" href="#modal-tab-social">Social</a>
        <a role="tab" aria-selected="false" href="#modal-tab-wallet">Wallet</a>
      </div>
      <div>
        <div id="modal-tab-login" class="modal-tab-panel is-active"></div>
        <div id="modal-tab-social" class="modal-tab-panel" hidden></div>
        <div id="modal-tab-wallet" class="modal-tab-panel" hidden></div>
      </div>
      <button type="button" class="id-modal-close" id="id_cancel">Cancel</button>
    </dialog>`;
  // jsdom implements no <dialog> behaviour, so showModal/close are stubbed.
  const dialog = document.getElementById("modalLogin");
  dialog.showModal = jest.fn(() => {
    dialog.open = true;
  });
  dialog.close = jest.fn(() => {
    dialog.open = false;
  });
  return dialog;
}

/** Which panel is currently revealed. */
function visiblePanel() {
  return [...document.querySelectorAll(".modal-tab-panel")].find((p) => !p.hidden).id;
}

describe("authmodal.js", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
    // The bind-once flag lives on <body>, which survives innerHTML = "" and
    // would otherwise leak between tests. In a browser that persistence is the
    // point: an htmx swap replaces body content, not the body itself.
    delete document.body.dataset.authModalBound;
  });

  describe("showTab", () => {
    it("reveals the requested panel and hides the others", () => {
      mountModal();
      expect(A.showTab(document, "modal-tab-wallet")).toBe(true);
      expect(visiblePanel()).toBe("modal-tab-wallet");
      expect(document.getElementById("modal-tab-login").hidden).toBe(true);
    });

    it("moves the selected state onto the matching tab", () => {
      mountModal();
      A.showTab(document, "modal-tab-social");
      const selected = [...document.querySelectorAll("[role='tab']")].map((t) =>
        t.getAttribute("aria-selected")
      );
      expect(selected).toEqual(["false", "true", "false"]);
    });

    it("leaves siblings that are not panels alone", () => {
      mountModal();
      const note = document.createElement("p");
      note.id = "not-a-panel";
      document.getElementById("modal-tab-login").parentNode.appendChild(note);
      A.showTab(document, "modal-tab-wallet");
      expect(note.hidden).toBe(false);
    });

    it("reports an unknown panel rather than hiding everything", () => {
      mountModal();
      expect(A.showTab(document, "modal-tab-nope")).toBe(false);
      expect(visiblePanel()).toBe("modal-tab-login");
    });
  });

  describe("opening and closing", () => {
    it("opens the dialog", () => {
      const dialog = mountModal();
      expect(A.openAuthModal(document)).toBe(true);
      expect(dialog.showModal).toHaveBeenCalledTimes(1);
    });

    it("does not re-open a dialog that is already open", () => {
      const dialog = mountModal();
      A.openAuthModal(document);
      A.openAuthModal(document);
      expect(dialog.showModal).toHaveBeenCalledTimes(1);
    });

    it("reports when the page carries no login modal", () => {
      expect(A.openAuthModal(document)).toBe(false);
      expect(A.closeAuthModal(document)).toBe(false);
    });

    it("closes an open dialog and leaves a closed one alone", () => {
      const dialog = mountModal();
      A.closeAuthModal(document);
      expect(dialog.close).not.toHaveBeenCalled();
      A.openAuthModal(document);
      A.closeAuthModal(document);
      expect(dialog.close).toHaveBeenCalledTimes(1);
    });

    it("leaves a browser without <dialog> support alone", () => {
      document.body.innerHTML = '<dialog id="modalLogin"></dialog>';
      expect(document.getElementById("modalLogin").showModal).toBeUndefined();
      expect(A.openAuthModal(document)).toBe(true);
    });
  });

  describe("wireAuthModal", () => {
    it("opens the modal from the header link", () => {
      const dialog = mountModal();
      A.wireAuthModal(document);
      document.getElementById("opener").click();
      expect(dialog.showModal).toHaveBeenCalled();
    });

    it("switches tabs when their anchors are clicked", () => {
      mountModal();
      A.wireAuthModal(document);
      document.querySelector('[href="#modal-tab-wallet"]').click();
      expect(visiblePanel()).toBe("modal-tab-wallet");
    });

    it("closes from the cancel button", () => {
      const dialog = mountModal();
      A.wireAuthModal(document);
      A.openAuthModal(document);
      document.getElementById("id_cancel").click();
      expect(dialog.close).toHaveBeenCalled();
    });

    it("stops the anchors navigating, so the URL keeps no #hash", () => {
      mountModal();
      A.wireAuthModal(document);
      const link = document.querySelector('[href="#modal-tab-social"]');
      const event = new MouseEvent("click", { bubbles: true, cancelable: true });
      link.dispatchEvent(event);
      expect(event.defaultPrevented).toBe(true);
    });

    it("binds once, so a second call cannot double-handle a click", () => {
      const dialog = mountModal();
      expect(A.wireAuthModal(document)).toBe(true);
      expect(A.wireAuthModal(document)).toBe(false);
      document.getElementById("opener").click();
      expect(dialog.showModal).toHaveBeenCalledTimes(1);
    });

    it("defaults to the whole document when given no root", () => {
      const dialog = mountModal();
      expect(A.wireAuthModal()).toBe(true);
      document.getElementById("opener").click();
      expect(dialog.showModal).toHaveBeenCalled();
      expect(A.openAuthModal()).toBe(true);
      expect(A.closeAuthModal()).toBe(true);
    });

    it("scopes to the subtree it is given", () => {
      mountModal();
      const dialog = document.getElementById("modalLogin");
      expect(A.showTab(dialog, "modal-tab-social")).toBe(true);
      expect(visiblePanel()).toBe("modal-tab-social");
    });

    it("ignores an event whose target cannot be matched", () => {
      mountModal();
      A.wireAuthModal(document);
      // The document itself has no closest(), which is the guard's real case.
      const event = new MouseEvent("click", { bubbles: true, cancelable: true });
      expect(() => document.dispatchEvent(event)).not.toThrow();
      expect(event.defaultPrevented).toBe(false);
    });

    it("ignores clicks that hit nothing it owns", () => {
      mountModal();
      A.wireAuthModal(document);
      const event = new MouseEvent("click", { bubbles: true, cancelable: true });
      document.body.dispatchEvent(event);
      expect(event.defaultPrevented).toBe(false);
      expect(visiblePanel()).toBe("modal-tab-login");
    });
  });
});

/*
 * The login dialog opens with showModal(), which puts it in the browser's top
 * layer -- above every element in the normal layer, whatever z-index they
 * carry. Wallet SDKs append their picker to <body> as ordinary DOM, so from
 * inside the dialog it was painted underneath: the reader had to close the
 * dialog to reach it, and the connect attempt died with the flow when they did.
 * The dialog steps out of the top layer instead, and comes back when the
 * picker is gone.
 */
describe("wallet handoff", () => {
  /** Adds a wallet card inside the dialog, as snippets/wallet_signing.html does.
   *
   * The hidden controls are part of the shape, not decoration: `frontend/wallet`
   * reveals them from its own subscription to the wallet state, and that reveal
   * is one of the two cues the handoff watches.
   */
  function mountWalletTab(dialog) {
    document.getElementById("modal-tab-wallet").innerHTML = `
      <div id="wallet-connect">
        <div id="wallet-pera">
          <button id="connect-button-pera" type="button">Connect</button>
          <button id="set-active-button-pera" type="button" style="display:none">Set active</button>
          <button id="disconnect-button-pera" type="button" style="display:none">Disconnect</button>
          <select id="account-select-pera"></select>
          <button id="auth-button-pera" type="button" style="display:none">Sign in</button>
        </div>
      </div>`;
    return document.getElementById("connect-button-pera");
  }

  /** MutationObserver callbacks are microtasks; let them run. */
  const settle = () => new Promise((resolve) => setTimeout(resolve, 0));

  it("closes the dialog when a wallet connect starts", () => {
    const dialog = mountModal();
    const connect = mountWalletTab(dialog);
    A.wireAuthModal(document);
    A.openAuthModal(document);

    connect.click();

    expect(dialog.open).toBe(false);
  });

  it("lets the click through to the wallet package", () => {
    // The wallet package binds its own listener to this button. Swallowing the
    // click would close the dialog and connect nothing at all.
    const dialog = mountModal();
    const connect = mountWalletTab(dialog);
    const walletListener = jest.fn();
    connect.addEventListener("click", walletListener);
    A.wireAuthModal(document);
    A.openAuthModal(document);

    connect.click();

    expect(walletListener).toHaveBeenCalled();
  });

  it("reopens on the wallet tab once the picker is gone", async () => {
    const dialog = mountModal();
    const connect = mountWalletTab(dialog);
    A.wireAuthModal(document);
    A.openAuthModal(document);
    connect.click();

    const picker = document.createElement("div");
    picker.id = "pera-wallet-modal";
    document.body.appendChild(picker);
    await settle();
    expect(dialog.open).toBe(false);

    picker.remove();
    await settle();

    expect(dialog.open).toBe(true);
    expect(visiblePanel()).toBe("modal-tab-wallet");
  });

  it("stays closed while the picker is still up", async () => {
    const dialog = mountModal();
    const connect = mountWalletTab(dialog);
    A.wireAuthModal(document);
    A.openAuthModal(document);
    connect.click();

    document.body.appendChild(document.createElement("div"));
    await settle();

    expect(dialog.open).toBe(false);
  });

  it("does not mistake the page's own elements for the picker", async () => {
    // Everything already on the body is the page. Counting it as the SDK's
    // would mean waiting for the footer to be removed before reopening --
    // which is to say, never.
    const dialog = mountModal();
    const connect = mountWalletTab(dialog);
    A.wireAuthModal(document);
    A.openAuthModal(document);

    connect.click();
    await settle();

    expect(dialog.open).toBe(false);
  });

  it("ignores a text node the SDK leaves behind", async () => {
    // A stray text node is not a picker. Counting one would arm the "gone"
    // check against something that never had a visible presence.
    const dialog = mountModal();
    const connect = mountWalletTab(dialog);
    A.wireAuthModal(document);
    A.openAuthModal(document);
    connect.click();

    document.body.appendChild(document.createTextNode(" "));
    await settle();

    expect(dialog.open).toBe(false);
  });

  it("does not re-add a picker it is already tracking", async () => {
    // Observers batch, so the same node can arrive in two records. Recording
    // it twice would leave a phantom entry that never reports as removed.
    const dialog = mountModal();
    const connect = mountWalletTab(dialog);
    A.wireAuthModal(document);
    A.openAuthModal(document);
    connect.click();

    const picker = document.createElement("div");
    document.body.appendChild(picker);
    await settle();
    document.body.appendChild(picker); // moved, not duplicated
    await settle();

    picker.remove();
    await settle();

    expect(dialog.open).toBe(true);
  });

  it("ignores a page element that is merely moved", async () => {
    // Re-appending an existing child reports it as an addition. It was on the
    // body before the picker opened, so it is the page, and the dialog must
    // not sit waiting for the page to be dismantled before it reopens.
    const dialog = mountModal();
    const connect = mountWalletTab(dialog);
    A.wireAuthModal(document);
    A.openAuthModal(document);
    connect.click();

    document.body.appendChild(document.getElementById("opener"));
    await settle();

    expect(dialog.open).toBe(false);
  });

  it("ignores a connect button outside the login dialog", () => {
    // The dedicated /accounts/login/ page renders the same wallet snippet with
    // no dialog around it. There is nothing to step out of the way of there.
    const dialog = mountModal();
    document.body.insertAdjacentHTML(
      "beforeend",
      '<button id="connect-button-defly" type="button">Connect</button>'
    );
    A.wireAuthModal(document);
    A.openAuthModal(document);

    document.getElementById("connect-button-defly").click();

    expect(dialog.open).toBe(true);
  });

  it("does nothing when the dialog is already closed", () => {
    const dialog = mountModal();
    const connect = mountWalletTab(dialog);
    A.wireAuthModal(document);

    connect.click();

    expect(dialog.close).not.toHaveBeenCalled();
  });

  /**
   * The reconnect path, which the picker cue alone could not serve.
   *
   * A reader arrives with a wallet session restored from a previous visit --
   * the card shows Disconnect, not Connect -- disconnects, and connects again.
   * The SDK is warm by then, so its container is already on the body and lands
   * in the "this is the page" snapshot: nothing is ever recorded as injected,
   * nothing is ever seen to leave, and the dialog stayed shut. The reader had
   * to open it a second time to reach Sign in and sign the 0 ALGO message.
   */
  describe("when the SDK is already warm", () => {
    /** Put the SDK's container on the body before the handoff is armed. */
    function warmSdk() {
      const container = document.createElement("div");
      container.id = "pera-wallet-modal";
      document.body.appendChild(container);
      return container;
    }

    /** What `frontend/wallet` does to a control when the state changes. */
    function show(id) {
      document.getElementById(id).style.display = "block";
    }

    it("reopens when the connection lands, picker or no picker", async () => {
      const dialog = mountModal();
      const connect = mountWalletTab(dialog);
      warmSdk();
      A.wireAuthModal(document);
      A.openAuthModal(document);
      connect.click();
      await settle();
      expect(dialog.open).toBe(false);

      show("auth-button-pera");
      await settle();

      expect(dialog.open).toBe(true);
      expect(visiblePanel()).toBe("modal-tab-wallet");
    });

    it("reopens for a connection that still needs Set active", async () => {
      // Connected, but another wallet is the active one. Still a next step,
      // and still one the reader can only take inside the dialog.
      const dialog = mountModal();
      const connect = mountWalletTab(dialog);
      warmSdk();
      A.wireAuthModal(document);
      A.openAuthModal(document);
      connect.click();

      show("set-active-button-pera");
      await settle();

      expect(dialog.open).toBe(true);
    });

    it("stays closed while the picker is up and nothing has connected", async () => {
      // The cue is a control appearing, not the card being touched at all.
      const dialog = mountModal();
      const connect = mountWalletTab(dialog);
      warmSdk();
      A.wireAuthModal(document);
      A.openAuthModal(document);
      connect.click();

      document.getElementById("account-select-pera").style.display = "block";
      await settle();

      expect(dialog.open).toBe(false);
    });

    it("does not read a disconnect as a connection", async () => {
      // The same property, written the other way: `frontend/wallet` sets
      // display:none on these controls when the wallet disconnects, and that
      // must not bring the dialog back over the picker.
      const dialog = mountModal();
      const connect = mountWalletTab(dialog);
      warmSdk();
      A.wireAuthModal(document);
      A.openAuthModal(document);
      connect.click();

      document.getElementById("auth-button-pera").style.display = "none";
      await settle();

      expect(dialog.open).toBe(false);
    });

    it("does not reopen on a card that has simply never rendered", async () => {
      // The trap in reading the buttons directly rather than reacting to a
      // change: a control that was never given a display carries "", which is
      // not "none" -- so a naive check reopens the dialog the instant it closes.
      const dialog = mountModal();
      const connect = mountWalletTab(dialog);
      document.getElementById("auth-button-pera").removeAttribute("style");
      warmSdk();
      A.wireAuthModal(document);
      A.openAuthModal(document);

      connect.click();
      await settle();

      expect(dialog.open).toBe(false);
    });

    it("leaves the tabs alone when the reader reopened it themselves", async () => {
      // A reader who gave up waiting and clicked Log in may be typing a
      // password. Arriving late and moving them to the wallet tab would be the
      // second surprise in a row.
      const dialog = mountModal();
      const connect = mountWalletTab(dialog);
      warmSdk();
      A.wireAuthModal(document);
      A.openAuthModal(document);
      connect.click();
      A.openAuthModal(document);
      A.showTab(document, "modal-tab-login");

      show("auth-button-pera");
      await settle();

      expect(dialog.open).toBe(true);
      expect(visiblePanel()).toBe("modal-tab-login");
    });

    it("stops watching once it has reopened", async () => {
      // Both cues can fire for one connection -- the SDK removes its picker
      // and the card reveals Sign in. The second must not act on a dialog the
      // reader has since closed again.
      const dialog = mountModal();
      const connect = mountWalletTab(dialog);
      A.wireAuthModal(document);
      A.openAuthModal(document);
      connect.click();

      const picker = document.createElement("div");
      document.body.appendChild(picker);
      await settle();
      picker.remove();
      await settle();
      expect(dialog.open).toBe(true);

      A.closeAuthModal(document);
      show("auth-button-pera");
      await settle();

      expect(dialog.open).toBe(false);
    });
  });

  it("reports when there is no MutationObserver to arm", () => {
    const dialog = mountModal();
    const saved = global.MutationObserver;
    // eslint-disable-next-line no-global-assign
    delete global.MutationObserver;

    expect(A.walletHandoff(document, dialog)).toBe(false);

    global.MutationObserver = saved;
  });
});
