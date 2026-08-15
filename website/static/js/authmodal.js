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
