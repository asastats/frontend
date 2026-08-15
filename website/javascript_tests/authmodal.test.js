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
