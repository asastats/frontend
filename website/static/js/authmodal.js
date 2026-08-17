/**
 * @file Login modal on the DaisyUI base template
 * @author Ivica Paleka
 * @description Opens `#modalLogin` and switches its tabs. Materialize supplied
 * both behaviours (`M.Modal` and `M.Tabs`); this replaces them with a native
 * `<dialog>` and a few lines of delegation, so the modal needs no framework.
 *
 * Tabs stay anchor-driven (`<a href="#modal-tab-wallet">`) rather than becoming
 * radio inputs: the anchors are addressable, they work as ordinary links with
 * no JS, and the existing functional tests click them.
 */
(function () {
  "use strict";

  /** Marks the panel and its tab as the visible one. */
  var ACTIVE = "is-active";

  /**
   * Show the tab panel with the given id, hiding its siblings.
   *
   * @param {Document|Element} root - subtree holding the tabs
   * @param {string} panelId - id of the panel to reveal
   * @returns {boolean} whether a matching panel was found
   */
  function showTab(root, panelId) {
    var panel = root.querySelector("#" + panelId);
    if (!panel) return false;
    var group = panel.parentNode;
    Array.prototype.forEach.call(group.children, function (child) {
      if (child.classList.contains("modal-tab-panel")) {
        child.classList.toggle(ACTIVE, child === panel);
        child.hidden = child !== panel;
      }
    });
    Array.prototype.forEach.call(
      root.querySelectorAll('[href^="#modal-tab-"]'),
      function (link) {
        var on = link.getAttribute("href") === "#" + panelId;
        link.classList.toggle(ACTIVE, on);
        link.setAttribute("aria-selected", String(on));
      }
    );
    return true;
  }

  /** Open the login dialog. Returns false when the page has no such dialog. */
  function openAuthModal(doc) {
    var dialog = (doc || document).getElementById("modalLogin");
    if (!dialog) return false;
    if (dialog.showModal && !dialog.open) dialog.showModal();
    return true;
  }

  /** Close the login dialog if it is open. */
  function closeAuthModal(doc) {
    var dialog = (doc || document).getElementById("modalLogin");
    if (dialog && dialog.close && dialog.open) dialog.close();
    return !!dialog;
  }

  /**
   * Step out of the way of a wallet's own picker, then come back.
   *
   * `showModal()` puts the login dialog in the browser's *top layer*, which
   * sits above every element in the normal layer no matter what z-index they
   * carry. Wallet SDKs render their picker as ordinary DOM appended to
   * `<body>`, so from inside this dialog the picker was painted underneath it:
   * unreachable without closing the dialog first, and the connect attempt died
   * along with the flow when the reader did. That is why the same wallet works
   * on the dedicated login page, which has no dialog to be trapped behind.
   *
   * Neither element can be persuaded to yield -- the top layer is not
   * negotiable from CSS -- so the dialog leaves it. It closes as the picker
   * opens, and reopens on the wallet tab once the picker is gone, which covers
   * a completed connection and an abandoned one alike: either way the SDK
   * removes what it added.
   *
   * If an SDK leaves its container behind, the dialog simply stays closed and
   * the reader opens it again -- exactly the position they are in today.
   *
   * @param {Document} host - document holding the dialog
   * @param {Element} dialog - the login dialog, already open
   * @returns {boolean} whether the handoff was armed
   */
  function walletHandoff(host, dialog) {
    if (typeof MutationObserver === "undefined") return false;

    /** Everything on the body before the SDK ran: the page itself. */
    var before = Array.prototype.slice.call(host.body.children);

    /** What the SDK has appended since. Its removal is our cue to come back. */
    var injected = [];

    var observer = new MutationObserver(function (records) {
      Array.prototype.forEach.call(records, function (record) {
        Array.prototype.forEach.call(record.addedNodes, function (node) {
          if (node.nodeType !== 1) return;
          if (before.indexOf(node) !== -1) return;
          if (injected.indexOf(node) === -1) injected.push(node);
        });
      });

      // Nothing has appeared yet -- the SDK may still be loading.
      if (!injected.length) return;

      var stillThere = injected.some(function (node) {
        return host.body.contains(node);
      });
      if (stillThere) return;

      observer.disconnect();
      openAuthModal(host);
      showTab(host, "modal-tab-wallet");
    });

    observer.observe(host.body, { childList: true });
    closeAuthModal(host);
    return true;
  }

  /**
   * Delegate every interaction from one listener on the document.
   *
   * @param {Document} doc - document to bind to
   * @returns {boolean} whether binding happened
   */
  function wireAuthModal(doc) {
    var host = doc || document;
    if (!host.body || host.body.dataset.authModalBound === "1") return false;
    host.body.dataset.authModalBound = "1";

    host.addEventListener("click", function (ev) {
      var target = ev.target;
      if (!target || !target.closest) return;

      var opener = target.closest('[href="#modalLogin"]');
      if (opener) {
        ev.preventDefault();
        openAuthModal(host);
        return;
      }
      var closer = target.closest(".id-modal-close");
      if (closer) {
        ev.preventDefault();
        closeAuthModal(host);
        return;
      }
      var tab = target.closest('[href^="#modal-tab-"]');
      if (tab) {
        ev.preventDefault();
        showTab(host, tab.getAttribute("href").slice(1));
        return;
      }
      // Not preventDefault'd and not returned early: the wallet package binds
      // its own listener to this button and must still receive the click.
      var connect = target.closest('[id^="connect-button-"]');
      if (connect && connect.closest("#modalLogin")) {
        var dialog = host.getElementById("modalLogin");
        if (dialog && dialog.open) walletHandoff(host, dialog);
      }
    });
    return true;
  }

  /* istanbul ignore else -- in the browser we self-start; under jest we export */
  if (typeof module !== "undefined" && module.exports) {
    module.exports = {
      showTab: showTab,
      openAuthModal: openAuthModal,
      closeAuthModal: closeAuthModal,
      walletHandoff: walletHandoff,
      wireAuthModal: wireAuthModal,
    };
  } else {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", function () {
        wireAuthModal(document);
      });
    } else {
      wireAuthModal(document);
    }
  }
})();
