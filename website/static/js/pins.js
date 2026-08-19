/**
 * Pinning assets and collections to the top of their section.
 *
 * A pin is remembered per address/bundle, in the reader's own browser, and is
 * never sent to the server. That is forced rather than chosen: the address page
 * is `cache_page`'d and its entry is shared between signed-in readers, so
 * anything per-reader rendered into it would be handed to whoever asked next.
 * The markup therefore ships every pin unpressed and this file presses the ones
 * that belong to whoever is looking. See `core/views.py:LayoutPreferenceView`
 * for the same constraint solved the other way, for a preference that does live
 * on the server.
 *
 * **Entries are moved in the DOM, not reordered with CSS `order`.** `order`
 * would be cheaper and would avoid a reflow, but it moves a row visually while
 * leaving it where it was for a screen reader and for keyboard navigation --
 * the precise fault the position component was rebuilt to remove. A pinned row
 * has to be first in both senses or it is not first.
 *
 * The server's order is captured once, before anything moves, and every
 * subsequent render is rebuilt from it: pinned entries in the order they were
 * pinned, then the rest exactly as they arrived. Rebuilding from the original
 * rather than mutating in place is what makes unpinning put a row back where it
 * belongs instead of wherever it happened to end up.
 */
(function () {
  "use strict";

  /** localStorage key prefix; the page's own path completes it. */
  var STORAGE_PREFIX = "pins:";
  /** Marks a pinned entry for the stripe in input.css. */
  var PINNED_CLASS = "pinned";

  /**
   * Original document order per container, captured before the first move.
   *
   * Keyed by the container element itself, so two sections never share one
   * list. A Map rather than an attribute because the value is a live array of
   * elements, and stringifying it would only mean looking them up again.
   */
  var served = new Map();

  /**
   * Return the storage key for the page being read.
   *
   * The path *is* the identity of an address page -- `/<address>` or
   * `/<bundle hash>` -- so it needs nothing rendered into the markup to
   * identify it, and it namespaces every page apart without a scheme. It also
   * keeps the historic widget's own copy of this page separate for free.
   *
   * @returns {string} the localStorage key for this page's pins.
   */
  function storageKey() {
    return STORAGE_PREFIX + window.location.pathname.replace(/^\/+|\/+$/g, "");
  }

  /**
   * Read the pinned ids for this page, oldest pin first.
   *
   * Anything unreadable -- absent, malformed, or written by a future version
   * that stored something other than an array -- is treated as no pins at all.
   * A reader with corrupt state gets the page in value order, which is the
   * server's order and a perfectly good page.
   *
   * @returns {string[]} entry ids, in the order they were pinned.
   */
  function read() {
    var raw;
    try {
      raw = localStorage.getItem(storageKey());
    } catch (e) {
      return [];
    }
    if (!raw) return [];
    try {
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed.filter(function (id) {
        return typeof id === "string";
      }) : [];
    } catch (e) {
      return [];
    }
  }

  /**
   * Persist the pinned ids for this page.
   *
   * A failure here is silent on purpose: private browsing and a full quota both
   * throw, and neither is a reason to refuse to pin. The reader gets the
   * arrangement they asked for and does not get it back tomorrow.
   *
   * @param {string[]} ids - entry ids, in pin order.
   */
  function write(ids) {
    try {
      localStorage.setItem(storageKey(), JSON.stringify(ids));
    } catch (e) {
      // Nothing to do, and nothing worth telling the reader.
    }
  }

  /**
   * Return the containers holding pinnable entries, with their served order.
   *
   * A pin button's entry is `closest('.fitem')` and its container is that
   * entry's parent. Deriving the container from the button rather than
   * selecting it by name means nested entries -- an NFT item inside its
   * collection -- are never candidates, because they carry no pin button.
   *
   * @param {Document|Element} root - where to look for pin controls.
   * @returns {Map<Element, Element[]>} container to its entries, as served.
   */
  function containers(root) {
    var found = new Map();
    var buttons = root.querySelectorAll("[data-pin]");

    Array.prototype.forEach.call(buttons, function (button) {
      var entry = button.closest(".fitem");
      if (!entry || !entry.parentNode) return;
      var parent = entry.parentNode;
      if (!found.has(parent)) found.set(parent, []);
      found.get(parent).push(entry);
    });

    found.forEach(function (entries, parent) {
      if (!served.has(parent)) served.set(parent, entries.slice());
    });
    return found;
  }

  /**
   * Lay a container out: pinned entries first, then the rest as served.
   *
   * `appendChild` on an element already in the document moves it, so this is a
   * reorder rather than a rebuild -- open `<details>`, bound handlers and
   * scroll position all survive it. Entries are appended in their final order,
   * which leaves anything else in the container (there is nothing today) ahead
   * of them rather than shuffled among them.
   *
   * @param {Element} parent - the container to lay out.
   * @param {string[]} pinned - entry ids in pin order.
   */
  function layout(parent, pinned) {
    var order = served.get(parent);
    if (!order) return;

    var byId = {};
    order.forEach(function (entry) {
      byId[entry.id] = entry;
    });

    var first = [];
    pinned.forEach(function (id) {
      if (byId[id]) first.push(byId[id]);
    });
    var rest = order.filter(function (entry) {
      return first.indexOf(entry) === -1;
    });

    first.concat(rest).forEach(function (entry) {
      parent.appendChild(entry);
    });
  }

  /**
   * Reflect the pinned set in the controls and the rows.
   *
   * @param {Document|Element} root - where the controls are.
   * @param {string[]} pinned - entry ids in pin order.
   */
  function mark(root, pinned) {
    Array.prototype.forEach.call(root.querySelectorAll("[data-pin]"), function (button) {
      var isPinned = pinned.indexOf(button.getAttribute("data-pin")) !== -1;
      button.setAttribute("aria-pressed", isPinned ? "true" : "false");
      var entry = button.closest(".fitem");
      if (entry) entry.classList.toggle(PINNED_CLASS, isPinned);
    });
  }

  /**
   * Apply the stored pins to the page.
   *
   * @param {Document|Element} root - the subtree to arrange.
   */
  function apply(root) {
    var pinned = read();
    containers(root).forEach(function (entries, parent) {
      layout(parent, pinned);
    });
    mark(root, pinned);
  }

  /**
   * Toggle one entry's pin and re-apply.
   *
   * A newly pinned entry goes to the *end* of the stored list, so it lands at
   * the bottom of the pinned group rather than displacing what is already
   * there. Pinning a second thing should not move the first.
   *
   * @param {string} id - the entry id carried in `data-pin`.
   * @param {Document|Element} root - the subtree to re-arrange.
   */
  function toggle(id, root) {
    var pinned = read();
    var at = pinned.indexOf(id);
    if (at === -1) {
      pinned.push(id);
    } else {
      pinned.splice(at, 1);
    }
    write(pinned);
    apply(root);
  }

  /**
   * Bind the delegated click handler and arrange the page.
   *
   * Delegated from the document so entries arriving later -- a filter redraw,
   * an htmx swap -- need no rebinding.
   */
  function init() {
    if (!document.querySelector("[data-pin]")) return;

    document.addEventListener("click", function (event) {
      var button = event.target.closest ? event.target.closest("[data-pin]") : null;
      if (!button) return;
      // The control sits inside a <summary>, so without this a pin click would
      // also open or close the entry it is pinning.
      event.preventDefault();
      event.stopPropagation();
      toggle(button.getAttribute("data-pin"), document);
    });

    apply(document);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Exposed for the jest suite, which drives these directly rather than
  // through a hundred synthetic clicks.
  window.asastatsPins = {
    apply: apply,
    toggle: toggle,
    read: read,
    write: write,
    storageKey: storageKey,
  };
})();
