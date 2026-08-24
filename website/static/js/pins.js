/**
 * Arranging the address page: pinning entries, and reordering them.
 *
 * Both are the reader's own arrangement of one address or bundle, both are
 * remembered in their browser, and neither is ever sent to the server. That is
 * forced rather than chosen: the address page is `cache_page`'d and its entry is
 * shared between signed-in readers, so anything per-reader rendered into it
 * would be handed to whoever asked next. The markup therefore ships every
 * control at rest and this file sets the ones belonging to whoever is looking.
 * The layout preference is the counter-example: it *does* live on the server,
 * and it reaches the page by being part of the cache key rather than by being
 * fetched separately -- see `core/views.py:BaseAddressView.dispatch`. An
 * arrangement cannot go that way, because keying the cache on it would mean one
 * entry per reader.
 *
 * **Entries are moved in the DOM, not reordered with CSS `order`.** `order`
 * would be cheaper and would avoid a reflow, but it moves a row visually while
 * leaving it where it was for a screen reader and for keyboard navigation --
 * the precise fault the position component was rebuilt to remove. A row the
 * reader put first has to be first in both senses or it is not first.
 *
 * ## The model
 *
 * A section is laid out as **pinned entries, then the rest**. Two stores:
 *
 *   `pins:<path>`   ids in pin order, across both sections
 *   `order:<path>`  section key -> ids in the reader's order
 *
 * The server's order is captured once, before anything moves, and every render
 * is rebuilt from it. Rebuilding from the original rather than mutating in place
 * is what lets unpinning put a row back where it belongs instead of wherever it
 * happened to end up, and what keeps an entry that has appeared since the last
 * visit in its served position rather than at an arbitrary end.
 *
 * A drag is confined to its own group: a pinned row reorders among pinned rows,
 * an unpinned row among unpinned. Letting a row cross the boundary would mean
 * either silently pinning it or recording an order that the next render undoes.
 */
(function () {
  "use strict";

  /** localStorage keys; the page's own path completes them. */
  var PINS_PREFIX = "pins:";
  var ORDER_PREFIX = "order:";
  var POSITIONS_PREFIX = "positions:";
  /** Marks a pinned entry for the stripe in input.css. */
  var PINNED_CLASS = "pinned";
  /** On the entry being dragged, for the lifted look. */
  var DRAGGING_CLASS = "dragging";
  /** Pointer travel before a press becomes a drag, in CSS pixels. */
  var DRAG_THRESHOLD = 4;

  /**
   * Property holding a container's original order, and the binding marker.
   *
   * The served order is kept **on the container element**, not in a module-level
   * Map, and the listeners are bound once per document rather than once per
   * execution. Both are for the same reason: this script can run twice. It is a
   * plain `<script>` today, but the address page already pulls one in through an
   * htmx partial, and a second execution with module-scoped state would bind a
   * second set of delegated handlers -- so a single arrow key would move a row
   * twice, and each instance would consult its own idea of the served order.
   *
   * With the state on the DOM, a second execution is a no-op that re-applies.
   */
  var SERVED_PROP = "_asastatsServedEntries";
  var BOUND_ATTR = "data-pins-bound";

  /**
   * The baseline `layout` arranges from, when something has replaced the
   * served one.
   *
   * The toolbar sorts this list. Sorting and pinning are the same operation
   * applied twice -- both decide what order the rows are in -- so they cannot
   * each own the DOM independently: whichever ran second would undo the first.
   * Instead the toolbar hands its sorted order here and `layout` treats it as
   * the order the page arrived in, floating pinned rows above it exactly as
   * before.
   *
   * Kept apart from `SERVED_PROP` rather than overwriting it, because "what
   * the server sent" is still needed: `rebase(parent, null)` restores it, which
   * is what "Reset view" means, and there is no other copy of it anywhere.
   */
  var BASELINE_PROP = "_asastatsBaselineEntries";

  /** The drag in progress, or null. Reset on every pointerup. */
  var dragging = null;

  // -- storage --------------------------------------------------------------

  /**
   * Return the path identifying the page being read.
   *
   * The path *is* the identity of an address page -- `/<address>` or
   * `/<bundle hash>` -- so it needs nothing rendered into the markup, and it
   * namespaces every page apart without a scheme. It also keeps the historic
   * widget's own copy of this page separate for free.
   *
   * @returns {string} the page's path, without surrounding slashes.
   */
  function pagePath() {
    return window.location.pathname.replace(/^\/+|\/+$/g, "");
  }

  /**
   * @returns {string} the localStorage key holding this page's pins.
   */
  function storageKey() {
    return PINS_PREFIX + pagePath();
  }

  /**
   * @returns {string} the localStorage key holding this page's row order.
   */
  function orderKey() {
    return ORDER_PREFIX + pagePath();
  }

  /**
   * Read and parse a stored value, or return `fallback`.
   *
   * Anything unreadable -- absent, malformed, or written by a future version
   * that stored a different shape -- is treated as nothing stored. A reader
   * with corrupt state gets the page in the server's order, which is a
   * perfectly good page rather than an error.
   *
   * @param {string} key - the localStorage key.
   * @param {Function} valid - predicate the parsed value must satisfy.
   * @param {*} fallback - returned when the value is missing or unusable.
   * @returns {*} the parsed value, or `fallback`.
   */
  function load(key, valid, fallback) {
    var raw;
    try {
      raw = localStorage.getItem(key);
    } catch (e) {
      return fallback;
    }
    if (!raw) return fallback;
    try {
      var parsed = JSON.parse(raw);
      return valid(parsed) ? parsed : fallback;
    } catch (e) {
      return fallback;
    }
  }

  /**
   * Persist a value, silently tolerating a store that refuses.
   *
   * Private browsing and a full quota both throw, and neither is a reason to
   * refuse to rearrange the page. The reader gets the arrangement they asked
   * for and does not get it back tomorrow.
   *
   * @param {string} key - the localStorage key.
   * @param {*} value - JSON-serialisable value to store.
   */
  function save(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      // Nothing to do, and nothing worth telling the reader.
    }
  }

  /**
   * @returns {string[]} pinned entry ids, in the order they were pinned.
   */
  function read() {
    var ids = load(storageKey(), Array.isArray, []);
    return ids.filter(function (id) {
      return typeof id === "string";
    });
  }

  /**
   * @param {string[]} ids - pinned entry ids, in pin order.
   */
  function write(ids) {
    save(storageKey(), ids);
  }

  /**
   * @returns {object} section key to the reader's ordering of its entries.
   */
  function readOrder() {
    return load(
      orderKey(),
      function (value) {
        return value && typeof value === "object" && !Array.isArray(value);
      },
      {},
    );
  }

  /**
   * @param {object} order - section key to an array of entry ids.
   */
  function writeOrder(order) {
    save(orderKey(), order);
  }

  // -- the page -------------------------------------------------------------

  /**
   * Return a stable key for the section a container belongs to.
   *
   * The section classes are already a contract with `address.js` -- it reopens
   * remembered entries inside them -- so they are the most durable name
   * available, and they survive the containers themselves being re-wrapped.
   *
   * @param {Element} parent - a container holding entries.
   * @returns {string} "asa", "nft", or "" when it belongs to neither.
   */
  function sectionKey(parent) {
    if (parent.closest(".asasec")) return "asa";
    if (parent.closest(".nftsec")) return "nft";
    return "";
  }

  /**
   * Return the containers holding arrangeable entries, capturing served order.
   *
   * A control's entry is `closest('.fitem')` and its container is that entry's
   * parent. Deriving the container from the control rather than selecting it by
   * name means nested entries -- an NFT item inside its collection -- are never
   * candidates, because they carry no controls.
   *
   * @param {Document|Element} root - where to look for controls.
   * @returns {Map<Element, Element[]>} container to its entries, as served.
   */
  function containers(root) {
    var found = new Map();

    Array.prototype.forEach.call(root.querySelectorAll("[data-pin]"), function (control) {
      var entry = control.closest(".fitem");
      if (!entry || !entry.parentNode) return;
      var parent = entry.parentNode;
      if (!found.has(parent)) found.set(parent, []);
      found.get(parent).push(entry);
    });

    found.forEach(function (entries, parent) {
      if (!parent[SERVED_PROP]) parent[SERVED_PROP] = entries.slice();
    });
    return found;
  }

  /**
   * Return `entries` sorted by `ids`, with anything unlisted keeping its place.
   *
   * An entry the reader has never moved, or one that has appeared since they
   * last visited, stays where the server put it relative to its neighbours
   * rather than being swept to either end.
   *
   * @param {Element[]} entries - entries in served order.
   * @param {string[]} ids - the reader's order, possibly partial or stale.
   * @returns {Element[]} entries in the reader's order.
   */
  function arrange(entries, ids) {
    if (!ids || !ids.length) return entries.slice();

    var rank = {};
    ids.forEach(function (id, index) {
      rank[id] = index;
    });

    return entries
      .map(function (entry, index) {
        return { entry: entry, served: index, rank: rank[entry.id] };
      })
      .sort(function (a, b) {
        if (a.rank === undefined && b.rank === undefined) return a.served - b.served;
        if (a.rank === undefined) return 1;
        if (b.rank === undefined) return -1;
        return a.rank - b.rank;
      })
      .map(function (row) {
        return row.entry;
      });
  }

  /**
   * Return the order `parent` should be arranged from.
   *
   * The toolbar's sorted order when there is one, the served order otherwise.
   *
   * @param {Element} parent - the container.
   * @returns {Element[]|undefined} the baseline entries.
   */
  function baseline(parent) {
    return parent[BASELINE_PROP] || parent[SERVED_PROP];
  }

  /**
   * Replace the order `parent` is arranged from, or restore the served one.
   *
   * Only entries the server actually sent are accepted, and every one of them
   * has to appear: a caller that dropped a row would delete it from the page
   * the next time `layout` ran, because `layout` rebuilds from this list. A
   * sort reorders; it does not filter. Filtering is a class on the row.
   *
   * @param {Element} parent - the container to re-base.
   * @param {Element[]|null} entries - the new order, or null to restore.
   * @returns {boolean} true if the baseline changed.
   */
  function rebase(parent, entries) {
    if (!entries) {
      delete parent[BASELINE_PROP];
      return true;
    }

    var served = parent[SERVED_PROP];
    if (!served || entries.length !== served.length) return false;
    var known = served.slice();
    var complete = entries.every(function (entry) {
      var at = known.indexOf(entry);
      if (at === -1) return false;
      known.splice(at, 1);
      return true;
    });
    if (!complete) return false;

    parent[BASELINE_PROP] = entries.slice();
    return true;
  }

  /**
   * Lay a container out: pinned entries first, then the rest.
   *
   * `appendChild` on an element already in the document moves it, so this is a
   * reorder rather than a rebuild -- open `<details>`, bound handlers and
   * scroll position all survive it.
   *
   * @param {Element} parent - the container to lay out.
   * @param {string[]} pinned - entry ids in pin order.
   * @param {object} order - section key to the reader's ordering.
   */
  function layout(parent, pinned, order) {
    var entries = baseline(parent);
    if (!entries) return;

    var ordered = arrange(entries, order[sectionKey(parent)]);
    var isPinned = function (entry) {
      return pinned.indexOf(entry.id) !== -1;
    };
    var top = ordered.filter(isPinned).sort(function (a, b) {
      return pinned.indexOf(a.id) - pinned.indexOf(b.id);
    });
    var rest = ordered.filter(function (entry) {
      return !isPinned(entry);
    });

    top.concat(rest).forEach(function (entry) {
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
    Array.prototype.forEach.call(root.querySelectorAll("[data-pin]"), function (control) {
      var isPinned = pinned.indexOf(control.getAttribute("data-pin")) !== -1;
      control.setAttribute("aria-pressed", isPinned ? "true" : "false");
      var entry = control.closest(".fitem");
      if (entry) entry.classList.toggle(PINNED_CLASS, isPinned);
    });
  }

  /**
   * Apply the stored arrangement to the page.
   *
   * @param {Document|Element} root - the subtree to arrange.
   */
  function apply(root) {
    var pinned = read();
    var order = readOrder();
    containers(root).forEach(function (entries, parent) {
      layout(parent, pinned, order);
    });
    mark(root, pinned);
    applyPositions(root);
  }

  /**
   * Record the current DOM order of `parent` as the reader's order.
   *
   * Read back from the document rather than computed, so whatever the reader
   * sees after a move is exactly what is stored. Both groups are written as one
   * list: a row cannot cross the pinned boundary by dragging, so the list stays
   * consistent with the pinned set that `layout` will re-split it by.
   *
   * @param {Element} parent - the container whose order to record.
   */
  function remember(parent) {
    var key = sectionKey(parent);
    if (!key) return;

    var order = readOrder();
    order[key] = Array.prototype.filter
      .call(parent.children, function (el) {
        return el.classList.contains("fitem") && el.id;
      })
      .map(function (el) {
        return el.id;
      });
    writeOrder(order);
  }

  // -- pinning --------------------------------------------------------------

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

  // -- pinning positions ----------------------------------------------------

  /**
   * @returns {string} the localStorage key holding this page's pinned positions.
   */
  function positionsKey() {
    return POSITIONS_PREFIX + pagePath();
  }

  /**
   * Read the pinned positions for this page.
   *
   * Each entry is `{pid, amount}`. The amount is a *witness*, not part of the
   * identity -- see :func:`resolve`.
   *
   * @returns {object[]} pinned positions, in the order they were pinned.
   */
  function readPositions() {
    return load(positionsKey(), Array.isArray, []).filter(function (entry) {
      return entry && typeof entry.pid === "string";
    });
  }

  /**
   * @param {object[]} entries - pinned positions in pin order.
   */
  function writePositions(entries) {
    save(positionsKey(), entries);
  }

  /**
   * Find the position a stored pin refers to.
   *
   * Most pids name exactly one row and this is a lookup. Some do not: where the
   * payload carries nothing that tells two positions of the same program apart
   * -- same asset, same type, same venue, same link -- they hash to the same
   * pid, and the row is marked `data-pid-ambiguous`.
   *
   * For those, the stored **amount** breaks the tie. It is not part of the pid
   * on purpose: hashing it in would change the id whenever the amount changed,
   * which is the one property the id exists to have. Amount rather than value
   * because value moves with the price on every load, while amount moves only
   * when the reader actually stakes or unstakes -- so the witness is stable in
   * exactly the situation the pin has to survive.
   *
   * An exact amount wins outright; otherwise the nearest. This can still pick
   * the wrong row, but only if two positions of one program cross in magnitude
   * between visits -- far narrower than an ordinal, which breaks on *any*
   * reordering -- and the row says so via `data-pid-ambiguous`.
   *
   * @param {object} pin - `{pid, amount}` as stored.
   * @param {Document|Element} root - where to look.
   * @returns {Element|null} the matching position, or null if it is gone.
   */
  function resolve(pin, root) {
    var candidates = Array.prototype.slice.call(
      root.querySelectorAll('.position[data-pid="' + pin.pid + '"]'),
    );
    if (candidates.length <= 1) return candidates[0] || null;

    var wanted = parseFloat(pin.amount);
    if (isNaN(wanted)) return candidates[0];

    var best = null;
    var bestGap = Infinity;
    candidates.forEach(function (candidate) {
      var amount = parseFloat(candidate.getAttribute("data-amount"));
      if (isNaN(amount)) return;
      var gap = Math.abs(amount - wanted);
      if (gap < bestGap) {
        bestGap = gap;
        best = candidate;
      }
    });
    return best || candidates[0];
  }

  /**
   * Lay out one asset's positions: pinned first, the rest as served.
   *
   * @param {Element} parent - a `[data-positions]` container.
   * @param {Element[]} resolved - the pinned positions, in pin order.
   */
  function layoutPositions(parent, resolved) {
    var entries = parent[SERVED_PROP];
    if (!entries) return;

    var top = resolved.filter(function (position) {
      return position.parentNode === parent;
    });
    var rest = entries.filter(function (position) {
      return top.indexOf(position) === -1;
    });
    top.concat(rest).forEach(function (position) {
      parent.appendChild(position);
    });
  }

  /**
   * Apply the stored position pins.
   *
   * @param {Document|Element} root - the subtree to arrange.
   */
  function applyPositions(root) {
    var pins = readPositions();
    var resolved = [];
    pins.forEach(function (pin) {
      var position = resolve(pin, root);
      if (position) resolved.push(position);
    });

    var parents = [];
    Array.prototype.forEach.call(
      root.querySelectorAll("[data-positions]"),
      function (parent) {
        if (!parent[SERVED_PROP]) {
          parent[SERVED_PROP] = Array.prototype.filter.call(
            parent.children,
            function (child) {
              return child.classList.contains("position");
            },
          );
        }
        parents.push(parent);
      },
    );

    parents.forEach(function (parent) {
      layoutPositions(parent, resolved);
    });

    Array.prototype.forEach.call(
      root.querySelectorAll("[data-pin-position]"),
      function (control) {
        var position = control.closest(".position");
        var isPinned = position && resolved.indexOf(position) !== -1;
        control.setAttribute("aria-pressed", isPinned ? "true" : "false");
        if (position) position.classList.toggle(PINNED_CLASS, isPinned);
      },
    );

    renderBand(root, pins);
  }

  /**
   * Fill the pinned band at the top of the page, if the design has one.
   *
   * The dynamic designs put pinned positions in their own band rather than
   * only floating them within their venue. A position pinned from an asset the
   * reader has to scroll to and open is otherwise pinned somewhere they cannot
   * see, which is most of the value gone -- and in a venue holding one position
   * there is no order for floating to change at all.
   *
   * The band holds **copies**, not the rows themselves. Moving a position out
   * of its asset would take it away from the money column it is aligned to, and
   * from the venue subtotal it contributes to; both are the reasons the number
   * can be read at all.
   *
   * A pin whose position is not on the page any more keeps its card, marked
   * `.stale`. Dropping it silently would tell the reader nothing about why the
   * thing they pinned vanished -- and the position may simply be inside a
   * folded tail rather than gone.
   *
   * Built with `createElement` and `textContent`. Card text is asset and venue
   * names that came off the chain, and `innerHTML` here would be the one place
   * on this page markup could be smuggled in.
   *
   * @param {Document|Element} root - the subtree being arranged.
   * @param {object[]} pins - the stored pins, in pin order.
   */
  function renderBand(root, pins) {
    // `root` is addressed with `querySelectorAll` unguarded by `resolve`, which
    // has already run by the time anything reaches here -- so a root without
    // the query methods would have thrown long before this. Guarding only here
    // would have been a guard against a case the file as a whole does not
    // survive anyway.
    var section = root.querySelector("#pinned-section");
    var grid = root.querySelector("#pin-grid");
    if (!section || !grid) return;

    grid.textContent = "";
    pins.forEach(function (pin) {
      grid.appendChild(bandCard(pin, resolve(pin, root)));
    });

    // The counter is optional: a design may show the band without one.
    var count = root.querySelector("#pin-count");
    if (count) {
      count.textContent = pins.length ? String(pins.length) : "";
    }
    section.hidden = pins.length === 0;
  }

  /**
   * Build one card for the pinned band.
   *
   * @param {object} pin - the stored pin.
   * @param {Element|null} position - the row it resolved to, if any.
   * @returns {Element} the card.
   */
  function bandCard(pin, position) {
    var card = document.createElement("div");
    card.className = "pin-card";
    card.setAttribute("data-pin-card", pin.pid);

    var label = document.createElement("div");
    label.className = "position-label";
    var value = document.createElement("div");
    value.className = "amt num";

    if (position) {
      var source = position.querySelector(".position-label");
      label.textContent = source ? source.textContent.trim() : pin.pid;
      var figure = position.querySelector(".amt");
      value.textContent = figure ? figure.textContent.trim() : "";
      // `hasAttribute`, not the value: presence is the signal. The template
      // writes `="true"`, but an empty attribute is the ordinary HTML way to
      // say the same thing and reads as false through `getAttribute`.
      if (position.hasAttribute("data-pid-ambiguous")) {
        // It resolved by the amount witness rather than outright, so the page
        // says "cannot promise" instead of pinning one row and hoping.
        card.classList.add("ambiguous");
      }
    } else {
      label.textContent = pin.label || pin.pid;
      value.textContent = "";
      card.classList.add("stale");
    }

    var unit = document.createElement("span");
    unit.className = "unit";
    unit.textContent = "ALGO";

    var remove = document.createElement("button");
    remove.type = "button";
    remove.className = "pin-x";
    remove.setAttribute("data-unpin-position", pin.pid);
    remove.setAttribute("aria-label", "Unpin " + label.textContent);
    remove.textContent = "×";

    card.appendChild(label);
    card.appendChild(value);
    card.appendChild(unit);
    card.appendChild(remove);
    return card;
  }

  /**
   * Toggle a position's pin.
   *
   * Identified by the control's own row rather than by the pid alone: two rows
   * can share a pid, and the reader pressed one of them. The amount is captured
   * from that row at pin time, which is what makes it the witness.
   *
   * @param {Element} control - the pressed control.
   * @param {Document|Element} root - the subtree to re-arrange.
   */
  function togglePosition(control, root) {
    var position = control.closest(".position");
    if (!position) return;

    var pid = position.getAttribute("data-pid");
    var amount = position.getAttribute("data-amount");
    var pins = readPositions();
    var at = -1;
    pins.forEach(function (pin, index) {
      if (at === -1 && resolve(pin, root) === position) at = index;
    });

    if (at === -1) {
      // The label is stored alongside the identity so a pin that stops
      // resolving can still say what it was. A stale card reading `p1-3935...`
      // tells the reader nothing about what they pinned or whether they want
      // it back.
      var labelled = position.querySelector(".position-label");
      pins.push({
        pid: pid,
        amount: amount,
        label: labelled ? labelled.textContent.trim() : "",
      });
    } else {
      pins.splice(at, 1);
    }
    writePositions(pins);
    applyPositions(root);
  }

  /**
   * Remove a pin by its identity, from the band's own control.
   *
   * By pid rather than by row, because the card in the band may have no row to
   * point at -- unpinning a stale card is the main thing this is for.
   *
   * @param {string} pid - the pinned position's identity.
   * @param {Document|Element} root - the subtree to re-arrange.
   */
  function unpinPosition(pid, root) {
    writePositions(
      readPositions().filter(function (pin) {
        return pin.pid !== pid;
      }),
    );
    applyPositions(root);
  }

  // -- reordering -----------------------------------------------------------

  /**
   * Return the entries a given entry may be reordered among.
   *
   * Its own group, in document order: pinned rows move among pinned rows and
   * unpinned among unpinned. Crossing the boundary would mean either silently
   * pinning a row or recording an order the next render undoes.
   *
   * @param {Element} entry - the entry being moved.
   * @returns {Element[]} its siblings in the same group, including itself.
   */
  function group(entry) {
    var pinnedNow = entry.classList.contains(PINNED_CLASS);
    return Array.prototype.filter.call(entry.parentNode.children, function (el) {
      return (
        el.classList.contains("fitem") &&
        el.id &&
        el.classList.contains(PINNED_CLASS) === pinnedNow
      );
    });
  }

  /**
   * Move `entry` by `offset` places within its group, and remember the result.
   *
   * @param {Element} entry - the entry to move.
   * @param {number} offset - places to move; negative is towards the top.
   * @returns {boolean} whether anything moved.
   */
  function move(entry, offset) {
    var peers = group(entry);
    var from = peers.indexOf(entry);
    var to = Math.max(0, Math.min(peers.length - 1, from + offset));
    if (from === to) return false;

    // Insert *after* the target when moving down, before it when moving up --
    // otherwise a one-place move down lands back where it started.
    if (to > from) {
      peers[to].after(entry);
    } else {
      peers[to].before(entry);
    }
    remember(entry.parentNode);
    return true;
  }

  /**
   * Move `entry` to the start or end of its group.
   *
   * @param {Element} entry - the entry to move.
   * @param {boolean} toStart - true for the top of the group.
   * @returns {boolean} whether anything moved.
   */
  function moveToEnd(entry, toStart) {
    return move(entry, toStart ? -group(entry).length : group(entry).length);
  }

  /**
   * Announce a move for a reader who cannot see it happen.
   *
   * The grip's own label is rewritten rather than a separate live region: the
   * control keeps focus across the move, so a screen reader re-reads it, and
   * one element cannot drift out of step with another that does not exist.
   *
   * @param {Element} grip - the control that was used.
   * @param {Element} entry - the entry it moved.
   */
  function announce(grip, entry) {
    var peers = group(entry);
    var at = peers.indexOf(entry) + 1;
    var of = peers.length;
    var base = grip.getAttribute("data-label") || grip.getAttribute("aria-label");
    if (!grip.getAttribute("data-label")) grip.setAttribute("data-label", base);
    grip.setAttribute("aria-label", base + " Now " + at + " of " + of + ".");
  }

  /**
   * Handle an arrow, Home or End press on a grip.
   *
   * The keyboard path is not a courtesy: a pointer drag is unusable without
   * sight and awkward with a tremor, and this is the same operation.
   *
   * @param {KeyboardEvent} event - the key event.
   * @returns {void}
   */
  function onKeydown(event) {
    var grip = event.target.closest ? event.target.closest("[data-drag]") : null;
    if (!grip || event.defaultPrevented) return;
    var entry = grip.closest(".fitem");
    if (!entry) return;

    var moved = false;
    if (event.key === "ArrowUp") moved = move(entry, -1);
    else if (event.key === "ArrowDown") moved = move(entry, 1);
    else if (event.key === "Home") moved = moveToEnd(entry, true);
    else if (event.key === "End") moved = moveToEnd(entry, false);
    else return;

    event.preventDefault();
    if (moved) {
      // The move re-parents the button, which drops focus in some browsers.
      grip.focus();
      announce(grip, entry);
    }
  }

  /**
   * Begin a pointer drag.
   *
   * Pointer Events rather than HTML5 drag-and-drop: the latter does not fire on
   * touch at all, so half the readers of this page could not use it.
   *
   * @param {PointerEvent} event - the pointerdown event.
   */
  function onPointerDown(event) {
    var grip = event.target.closest ? event.target.closest("[data-drag]") : null;
    if (!grip || event.button !== 0 || event.defaultPrevented) return;
    var entry = grip.closest(".fitem");
    if (!entry) return;

    dragging = { entry: entry, grip: grip, startY: event.clientY, active: false };
    // Capture keeps the gesture with the grip when the pointer outruns it,
    // which it will -- the row moves only once the pointer passes a neighbour's
    // edge. Guarded because it is absent in jsdom and in older browsers, and a
    // drag that merely gets choppy is better than a handler that throws.
    if (grip.setPointerCapture && event.pointerId !== undefined) {
      try {
        grip.setPointerCapture(event.pointerId);
      } catch (e) {
        // Capture is an optimisation; the document-level listeners still fire.
      }
    }
  }

  /**
   * Reorder live as the pointer moves.
   *
   * The row under the pointer is found by its midpoint rather than by
   * `elementFromPoint`, which would return the dragged row itself.
   *
   * @param {PointerEvent} event - the pointermove event.
   */
  function onPointerMove(event) {
    if (!dragging) return;

    if (!dragging.active) {
      // A press that never travels is a click on the grip, not a drag.
      if (Math.abs(event.clientY - dragging.startY) < DRAG_THRESHOLD) return;
      dragging.active = true;
      dragging.entry.classList.add(DRAGGING_CLASS);
    }
    event.preventDefault();

    var entry = dragging.entry;
    var peers = group(entry);
    var index = peers.indexOf(entry);

    var above = peers[index - 1];
    var below = peers[index + 1];
    if (above && event.clientY < above.getBoundingClientRect().bottom) {
      above.before(entry);
      remember(entry.parentNode);
    } else if (below && event.clientY > below.getBoundingClientRect().top) {
      below.after(entry);
      remember(entry.parentNode);
    }
  }

  /**
   * End a pointer drag.
   *
   * @param {PointerEvent} event - the pointerup or pointercancel event.
   */
  function onPointerUp(event) {
    if (!dragging) return;
    dragging.entry.classList.remove(DRAGGING_CLASS);
    try {
      if (dragging.grip.hasPointerCapture &&
          dragging.grip.hasPointerCapture(event.pointerId)) {
        dragging.grip.releasePointerCapture(event.pointerId);
      }
    } catch (e) {
      // See onPointerDown: capture may never have been taken.
    }
    dragging = null;
  }

  // -- wiring ---------------------------------------------------------------

  /**
   * Bind the delegated handlers and arrange the page.
   *
   * Delegated from the document so entries arriving later -- a filter redraw,
   * an htmx swap -- need no rebinding.
   */
  function init() {
    // Either control is reason enough to run: an asset list and a position list
    // are arranged independently, and a page carrying only one of them still
    // has an arrangement to restore.
    if (!document.querySelector("[data-pin], [data-pin-position]")) return;

    // Arrange first, so a second execution still picks up entries that arrived
    // since the first -- it just does not bind a second set of handlers.
    apply(document);
    if (document.documentElement.hasAttribute(BOUND_ATTR)) return;
    document.documentElement.setAttribute(BOUND_ATTR, "");

    // Every handler below bails on an already-handled event. The attribute
    // above stops a second *binding*; this stops a second binding that slipped
    // past it from acting twice, because the failure is silent -- one arrow key
    // moves a row two places, and every single-test run passes. Same guard
    // showmore.js uses, for the same reason.
    document.addEventListener("click", function (event) {
      var position = event.target.closest
        ? event.target.closest("[data-pin-position]")
        : null;
      if (!position || event.defaultPrevented) return;
      event.preventDefault();
      event.stopPropagation();
      togglePosition(position, document);
    });

    // The band's own remove control. Bound before `[data-pin]` below because a
    // card carries neither attribute, but keeping the order explicit means a
    // future card that carries both cannot toggle two pins with one click.
    document.addEventListener("click", function (event) {
      var control = event.target.closest
        ? event.target.closest("[data-unpin-position]")
        : null;
      if (!control || event.defaultPrevented) return;
      event.preventDefault();
      event.stopPropagation();
      unpinPosition(control.getAttribute("data-unpin-position"), document);
    });

    document.addEventListener("click", function (event) {
      var control = event.target.closest ? event.target.closest("[data-pin]") : null;
      if (!control || event.defaultPrevented) return;
      // The controls sit inside a <summary>, so without this a click would also
      // open or close the entry being arranged.
      event.preventDefault();
      event.stopPropagation();
      toggle(control.getAttribute("data-pin"), document);
    });

    // Same reason, for the grip: a press on it must not toggle the entry.
    document.addEventListener("click", function (event) {
      if (
        event.target.closest &&
        event.target.closest("[data-drag]") &&
        !event.defaultPrevented
      ) {
        event.preventDefault();
        event.stopPropagation();
      }
    });

    document.addEventListener("keydown", onKeydown);
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("pointermove", onPointerMove);
    document.addEventListener("pointerup", onPointerUp);
    document.addEventListener("pointercancel", onPointerUp);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Exposed for the jest suite, which drives these directly rather than
  // through a hundred synthetic pointer gestures.
  window.asastatsPins = {
    apply: apply,
    baseline: baseline,
    rebase: rebase,
    containers: containers,
    toggle: toggle,
    move: move,
    moveToEnd: moveToEnd,
    read: read,
    write: write,
    readOrder: readOrder,
    writeOrder: writeOrder,
    storageKey: storageKey,
    orderKey: orderKey,
    readPositions: readPositions,
    writePositions: writePositions,
    togglePosition: togglePosition,
    applyPositions: applyPositions,
    unpinPosition: unpinPosition,
    renderBand: renderBand,
    resolve: resolve,
    positionsKey: positionsKey,
  };
})();
