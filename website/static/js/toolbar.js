/**
 * The dynamic toolbar: filtering, sorting, grouping and currency.
 *
 * Pass 2 of designs 2 and 3. Everything here acts on the page already in the
 * browser -- the whole payload is in the DOM, with sort keys, categories and
 * search text rendered onto the rows as data attributes -- so nothing fetches
 * and nothing waits. Filtering 190 positions is a class toggle.
 *
 * It also has to be that way. The address page is `cache_page`'d and its entry
 * is shared between every reader on the layout, so the server cannot know what
 * this reader has filtered to and must not render it. The state lives in their
 * browser under `view:<path>`, beside the pins and the saved order.
 *
 * ## One state, three drawings
 *
 * The allocation bar, the five category figures and the donuts are three
 * drawings of one set of numbers, and all three are wired to the same
 * `state.cats`. A reader who saw the bar and the figures disagree would have no
 * way to tell which one lied, so they are recomputed together, from the same
 * pass over the same rows, every time anything changes.
 *
 * ## The one figure that never moves
 *
 * The headline is what the address is worth. No filter, no search, no category
 * toggle may touch it: a reader who hides a category has not become poorer.
 * Everything below it is a subtotal and is free to respond. This file never
 * writes to `.total`.
 *
 * ## How it shares the page
 *
 * Three other scripts already own parts of this page, and the toolbar defers to
 * each rather than duplicating it:
 *
 *   `pins.js`     owns the *order*. Sorting does not reorder the DOM directly;
 *                 it hands `pins.rebase` a new baseline and lets pinning apply
 *                 on top, so a pinned row stays pinned through a sort.
 *   `showmore.js` owned the fold and no longer does here. It reveals a whole
 *                 tail in one press, which is design 1's rule; these designs
 *                 show a fixed first batch and add one batch per press, so it
 *                 stands down on `.dynamic-page` and this file folds instead.
 *   `dynamic.js`    owns the donuts. The toolbar hands it filtered slice data and
 *                 asks it to redraw.
 *
 * Currency is the exception, and deliberately: `address.js` has `setCurrency`,
 * and it is wrong for this page. It writes `innerHTML` including the unit into
 * every `span.val`, which on this markup destroys the nested `<span class="unit">`
 * inside a venue subtotal and leaves the asset header reading "253.74 ALGO
 * ALGO" -- the value cell has a *sibling* unit element. It also cannot reach a
 * breakdown control, which is a `<button>` rather than a span. `address.js` no
 * longer touches `.dynamic-page`; the writer here does, and it writes the number
 * only, leaving every unit element alone.
 */
(function () {
  "use strict";

  /** Guards a second execution against binding a second set of handlers. */
  var BOUND_ATTR = "data-toolbar-bound";
  /** localStorage key prefix; the page's own path completes it. */
  var VIEW_PREFIX = "view:";
  /** Set on a row the current filter excludes. */
  var HIDDEN_CLASS = "tb-hidden";
  /** Marks the container while the venue grouping is assembled. */
  var VENUE_CLASS = "grouped-by-venue";

  /**
   * Settings that belong to the *reader*, not to this address.
   *
   * Kept in their own top-level keys, and in design 1's keys deliberately, so
   * both designs and every open tab agree about them. A reader who picks USD
   * means USD -- not "USD on this address". The page-level view (what is
   * filtered, sorted and grouped) stays under `view:<path>`, because that
   * genuinely is about one address.
   *
   * `refresh` is design 1's too, and reading it is what makes auto-refresh work
   * here at no cost: `address.js` already runs the timer and reloads when this
   * key says to.
   */
  var SHARED = {
    ccy: "cur",
    nonft: "totalnonft",
    refresh: "refresh",
  };

  /** The four categories that describe a *position*. NFT is a section. */
  var CATEGORIES = ["balance", "staked", "liquidity", "defi"];

  /** Sort keys, mapped to the data attribute each reads. */
  var SORTS = {
    value: "data-sort-value",
    amount: "data-sort-amount",
    name: "data-sort-name",
    positions: "data-sort-positions",
  };

  /** The view as served: every control's default, and what "Reset" restores. */
  var DEFAULTS = {
    q: "",
    group: "asset",
    sort: "value",
    dir: -1,
    cats: CATEGORIES.slice(),
    nft: true,
    // Extra batches of rows revealed, per section. "Show more" adds one.
    more: { asa: 0, nft: 0 },
  };

  /** Defaults for the reader-level settings, which "Reset view" does not touch. */
  var SHARED_DEFAULTS = { ccy: "ALGO", nonft: false, refresh: false };

  var state = null;

  // -- storage --------------------------------------------------------------

  /**
   * @returns {string} the page's path, which is an address page's identity.
   */
  function pagePath() {
    return window.location.pathname.replace(/^\/+|\/+$/g, "");
  }

  /**
   * @returns {string} the localStorage key holding this page's view.
   */
  function viewKey() {
    return VIEW_PREFIX + pagePath();
  }

  /**
   * Read the stored view, falling back to the defaults field by field.
   *
   * Field by field rather than all-or-nothing: a stored view written by an
   * older build is missing whatever has been added since, and discarding the
   * whole thing would throw away a reader's currency because a sort key
   * appeared. Each field is validated on its own terms, so a value that is no
   * longer offered -- a removed sort, a category that stopped existing --
   * falls back without disturbing the rest.
   *
   * @returns {object} the view state.
   */
  function readView() {
    var stored = {};
    var settings = {};
    // One try for every read. A store that refuses one refuses them all -- a
    // private window, cleared site data, a browser set to block it -- so a
    // second catch further down would be a branch nothing can reach.
    try {
      stored = JSON.parse(window.localStorage.getItem(viewKey())) || {};
      Object.keys(SHARED).forEach(function (name) {
        settings[name] = window.localStorage.getItem(SHARED[name]) || "";
      });
    } catch (error) {
      stored = {};
      settings = {};
    }
    if (!stored || typeof stored !== "object") stored = {};

    var cats = Array.isArray(stored.cats)
      ? stored.cats.filter(function (key) {
          return CATEGORIES.indexOf(key) !== -1;
        })
      : null;

    return {
      q: typeof stored.q === "string" ? stored.q : DEFAULTS.q,
      group: stored.group === "venue" ? "venue" : "asset",
      sort: SORTS[stored.sort] ? stored.sort : DEFAULTS.sort,
      dir: stored.dir === 1 ? 1 : -1,
      // An empty stored array is a reader who switched every category off, and
      // is not the same as no stored array at all.
      cats: cats ? cats : DEFAULTS.cats.slice(),
      nft: stored.nft === false ? false : true,
      more: {
        asa: batches(stored.more && stored.more.asa),
        nft: batches(stored.more && stored.more.nft),
      },
      // Read from their own keys, not from this address's view. See SHARED.
      ccy: settings.ccy === "USD" ? "USD" : "ALGO",
      nonft: settings.nonft === "y",
      refresh: settings.refresh === "y",
    };
  }

  /**
   * @param {*} value - a stored batch count.
   * @returns {number} it as a non-negative whole number, or 0.
   */
  function batches(value) {
    var count = parseInt(value, 10);
    return isFinite(count) && count > 0 ? count : 0;
  }

  /**
   * Persist one reader-level setting to the key both designs read.
   *
   * @param {string} name - a key of `SHARED`.
   * @param {string} value - what to store.
   */
  function writeShared(name, value) {
    try {
      window.localStorage.setItem(SHARED[name], value);
    } catch (error) {
      // See `writeView`: losing persistence costs the next visit, not this one.
    }
  }

  /**
   * Persist the view, or forget it once it is back to the default.
   *
   * Removing rather than storing the defaults keeps a reader who has reset from
   * carrying a key that says nothing, and means "has this reader customised
   * anything" is answerable without comparing objects.
   */
  function writeView() {
    writeShared("ccy", state.ccy);
    writeShared("nonft", state.nonft ? "y" : "");
    writeShared("refresh", state.refresh ? "y" : "");
    try {
      if (isDefault()) window.localStorage.removeItem(viewKey());
      else {
        // The reader-level settings are stored under their own keys above;
        // writing them here too would give one setting two homes that can
        // disagree.
        var view = {};
        Object.keys(DEFAULTS).forEach(function (key) {
          view[key] = state[key];
        });
        window.localStorage.setItem(viewKey(), JSON.stringify(view));
      }
    } catch (error) {
      // A full or disabled store costs persistence, not the page. Every
      // control still works for as long as this tab is open.
    }
  }

  /**
   * @returns {boolean} true if nothing has been changed from the served view.
   */
  function isDefault() {
    return (
      state.q === DEFAULTS.q &&
      state.group === DEFAULTS.group &&
      state.sort === DEFAULTS.sort &&
      state.dir === DEFAULTS.dir &&
      state.nft === DEFAULTS.nft &&
      state.more.asa === 0 &&
      state.more.nft === 0 &&
      state.cats.length === CATEGORIES.length
    );
  }

  // -- numbers --------------------------------------------------------------

  /**
   * @param {Element|null} element - the element carrying the attribute.
   * @param {string} name - the attribute to read.
   * @returns {number} its value as a number, or 0.
   */
  function num(element, name) {
    if (!element) return 0;
    var value = parseFloat(element.getAttribute(name));
    return isFinite(value) ? value : 0;
  }

  /**
   * @returns {number} USD per ALGO, from the header's own data attributes.
   */
  function rate() {
    var head = document.querySelector(".dynamic-page .pricetip");
    var value = head ? parseFloat(head.getAttribute("data-pricealgo")) : NaN;
    return isFinite(value) ? value : 0;
  }

  /**
   * Format one ALGO figure in the current currency.
   *
   * Two decimals turn a small borrowing into "0.00", which reads as nothing
   * owed rather than as a debt -- so anything under half a cent widens to six
   * places instead of rounding away. That rule is the prototype's and it is the
   * only rounding on this page that changes what a row means.
   *
   * @param {number} algo - the figure, in ALGO.
   * @returns {string} the formatted number, with no unit.
   */
  function fmt(algo) {
    var value = state.ccy === "USD" ? algo * rate() : algo;
    if (value !== 0 && Math.abs(value) < 0.005) {
      return value.toLocaleString("en-US", {
        minimumFractionDigits: 6,
        maximumFractionDigits: 6,
      });
    }
    return value.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }

  // -- the filter -----------------------------------------------------------

  /**
   * @param {Element} element - a row carrying `data-search`.
   * @returns {boolean} true if it matches the current query.
   */
  function matches(element) {
    if (!state.q) return true;
    return (element.getAttribute("data-search") || "")
      .toLowerCase()
      .indexOf(state.q) !== -1;
  }

  /**
   * @returns {Element[]} every asset card on the page, in DOM order.
   */
  function assets() {
    return Array.prototype.slice.call(
      document.querySelectorAll("#asset-list > .fitem")
    );
  }

  /**
   * @returns {Element[]} every position row on the page, wherever it sits.
   *
   * Selected from the document rather than from inside an asset card, because
   * for as long as "Group by venue" is on the rows are not inside one -- they
   * have been moved into the venue that holds them. Each row says which asset
   * it belongs to in `data-owner`, which is how anything per-asset is still
   * totalled while they are away.
   */
  function positions() {
    return Array.prototype.slice.call(
      document.querySelectorAll(".dynamic-page .position")
    );
  }

  /**
   * @returns {Element[]} every venue group on the page, wherever it sits.
   */
  function groups() {
    return Array.prototype.slice.call(
      document.querySelectorAll(".dynamic-page .pgroup")
    );
  }

  /**
   * Decide what survives the filter, and total up what does.
   *
   * One pass, producing everything the rest of the render needs: which
   * positions are live, which assets keep any, each asset's filtered value, and
   * the four category totals the band draws. Computing these separately is how
   * a bar and a figure come to disagree.
   *
   * A position is live when its category is on **and** it matches the query, or
   * its asset does -- typing an asset's ticker should not require every row
   * inside it to repeat the ticker.
   *
   * **The category totals ignore the category filter**, and that is not an
   * oversight. Two reasons, and the second is decisive. A figure reading
   * "Liquidity 0.00" the moment it is switched off tells the reader they hold
   * none, when what happened is that they hid it -- the honest reading is the
   * real number, dimmed. And a bar segment whose width went to zero would have
   * no box to click, so the only way to switch a category back on would be the
   * figure beside it: the control would disable itself. They respond to the
   * search, which genuinely narrows what the address is being asked about.
   *
   * @returns {object} {rows, live, values, totals}
   */
  function evaluate() {
    var rows = assets();
    var found = {};
    var values = {};
    var kept = {};
    var totals = { balance: 0, staked: 0, liquidity: 0, defi: 0 };

    rows.forEach(function (card) {
      found[card.id] = matches(card);
      values[card.id] = 0;
      kept[card.id] = 0;
    });

    positions().forEach(function (position) {
      var owner = position.getAttribute("data-owner");
      var category = position.getAttribute("data-cat") || "defi";
      var hit = found[owner] || matches(position);
      var on = hit && state.cats.indexOf(category) !== -1;
      position.classList.toggle(HIDDEN_CLASS, !on);

      // Totalled on the search alone: see the note above about why the band
      // reports what the reader holds rather than what is on screen.
      if (hit && totals[category] !== undefined) {
        totals[category] += num(position, "data-value");
      }
      if (!on || values[owner] === undefined) return;
      kept[owner] += 1;
      values[owner] += num(position, "data-value");
    });

    // An asset every one of whose positions was filtered out has nothing left
    // to show, so the card goes too -- rather than standing there as an empty
    // heading claiming a value it is no longer displaying.
    var live = rows.filter(function (card) {
      return kept[card.id] > 0;
    });

    filterCollections();

    return { rows: rows, live: live, values: values, totals: totals };
  }

  /**
   * Apply the search to the NFT collections.
   *
   * The search only -- the category filter has nothing to say about a
   * collection, which is the NFT band's own business and is a whole section
   * rather than a category of position. A reader filtering for a collection's
   * name is asking about the same page, so leaving that section untouched
   * would show them every collection beside three matching assets.
   */
  function filterCollections() {
    Array.prototype.forEach.call(
      document.querySelectorAll(".dynamic-page .nftsec .rows > .fitem"),
      function (card) {
        card.classList.toggle(HIDDEN_CLASS, !matches(card));
      }
    );
  }

  // -- the load-more rule ---------------------------------------------------

  /**
   * Return how many rows a section shows.
   *
   * A plain count: the first `ADDRESS_INITIAL_*` rows, plus one batch of the
   * same size for every press of "Show more". Not the magnitude rule design 1
   * uses, and not the prototype's 95%/99%/99.5%/All control -- that was a way
   * to *demonstrate* the page with everything on screen before a load-more
   * existed, and "show me the rows carrying 99.5% of the value" is not a
   * sentence a reader thinks in.
   *
   * The numbers come from the server (`data-initial-*` on the section), so the
   * first fold the template renders and every fold after it are the same rule
   * rather than two copies of it.
   *
   * @param {Element} section - the section element.
   * @param {string} key - "asa" or "nft".
   * @returns {number} how many rows to show.
   */
  function limit(section, key) {
    var initial = parseInt(section.getAttribute("data-initial"), 10);
    if (!isFinite(initial) || initial < 1) initial = 1;
    return initial * (1 + state.more[key]);
  }

  // -- rendering ------------------------------------------------------------

  /**
   * Order the live assets, and hand the result to `pins.js`.
   *
   * Not applied to the DOM here. `pins.js` owns the order: it floats pinned
   * rows above the rest and applies any order the reader dragged, and if this
   * file also called `appendChild` the two would each undo the other depending
   * on which ran last. Instead the sorted list becomes the *baseline* it
   * arranges from, and pinning still wins -- which is right, because pinning is
   * the reader saying "this one, whatever else is going on".
   *
   * Name sorts by the ticker and ties break on it too, so two assets worth
   * exactly the same amount do not swap places between renders.
   *
   * @param {Element[]} rows - every asset card, live or not.
   */
  function order(rows) {
    var attribute = SORTS[state.sort];
    var textual = state.sort === "name";

    var sorted = rows.slice().sort(function (a, b) {
      var left = textual
        ? a.getAttribute(attribute) || ""
        : num(a, attribute);
      var right = textual
        ? b.getAttribute(attribute) || ""
        : num(b, attribute);
      if (left === right) {
        var tieA = a.getAttribute(SORTS.name) || "";
        var tieB = b.getAttribute(SORTS.name) || "";
        return tieA < tieB ? -1 : tieA > tieB ? 1 : 0;
      }
      return (left > right ? 1 : -1) * state.dir;
    });

    var pins = window.asastatsPins;
    var list = document.getElementById("asset-list");
    if (!pins || !list) return;
    // The served order is the default sort, so restoring it is what "Reset"
    // hands back -- and `rebase(parent, null)` is the only way to get it,
    // because nothing else keeps a copy.
    pins.rebase(list, isDefaultOrder() ? null : sorted);
    pins.apply(document);
  }

  /**
   * @returns {boolean} true if the sort is the one the server rendered in.
   */
  function isDefaultOrder() {
    return state.sort === DEFAULTS.sort && state.dir === DEFAULTS.dir;
  }

  /**
   * Show, hide and fold the asset list, and update the load-more control.
   *
   * @param {object} view - the result of `evaluate`.
   */
  function paintAssets(view) {
    var live = {};
    view.live.forEach(function (card) {
      live[card.id] = true;
    });

    // Read back from the DOM rather than from `view.live`: `pins.js` has just
    // reordered, and the fold applies to the first N *as displayed*, which is
    // not the order this function was handed.
    var displayed = assets().filter(function (card) {
      return live[card.id];
    });

    assets().forEach(function (card) {
      card.classList.toggle(HIDDEN_CLASS, !live[card.id]);
    });

    var keep = fold(".asasec", "asa", displayed, "asset");
    // Grouping by venue puts a different list on screen, so the control that
    // unfolds this one has nothing to say.
    if (state.group === "venue") {
      var control = document.querySelector(".dynamic-page .asasec [data-show-more]");
      if (control) control.parentNode.hidden = true;
    }

    return { shown: keep, total: view.rows.length };
  }

  /**
   * Fold one section's tail and put the count on its control.
   *
   * Shared by the two sections because they are the same rule applied to
   * different lists -- and because a second copy is how the assets and the
   * collections come to disagree about what "show more" means.
   *
   * @param {string} selector - the section's class selector.
   * @param {string} key - "asa" or "nft".
   * @param {Element[]} displayed - its rows, filtered, in display order.
   * @param {string} noun - what one row is, for the label.
   * @returns {number} how many rows are showing.
   */
  function fold(selector, key, displayed, noun) {
    var section = document.querySelector(".dynamic-page " + selector);
    if (!section) return displayed.length;

    var keep = Math.min(limit(section, key), displayed.length);
    displayed.forEach(function (card, index) {
      card.classList.toggle("folded", index >= keep);
    });

    var hidden = displayed.length - keep;
    var control = section.querySelector("[data-show-more]");
    if (control) {
      var label = control.querySelector(".show-more-open");
      if (label) {
        // What the next press reveals, not the whole tail. "Show 20 more" is a
        // promise the control keeps; "Show 56 more" over a control that reveals
        // twenty is not.
        var batch = parseInt(section.getAttribute("data-initial"), 10);
        var next = Math.min(hidden, isFinite(batch) && batch > 0 ? batch : hidden);
        label.textContent =
          "Show " + next + " more " + noun + (next === 1 ? "" : "s");
      }
      // Nothing folded means nothing to reveal. Left in the document rather
      // than removed, because the next keystroke may fold rows again.
      control.parentNode.hidden = hidden <= 0;
    }
    return keep;
  }

  /**
   * Fold the NFT section, which the toolbar owns for the same reason.
   *
   * `showmore.js` is design 1's and reveals a section's whole tail in one
   * press; these designs reveal a batch at a time, so it no longer binds here.
   */
  function paintCollections() {
    var list = document.getElementById("nft-list");
    if (!list) return;

    var displayed = Array.prototype.slice
      .call(list.children)
      .filter(function (card) {
        return !card.classList.contains(HIDDEN_CLASS);
      });
    fold(".nftsec", "nft", displayed, "collection");
  }

  /**
   * Redraw the subtotals every filtered figure feeds.
   *
   * Venue subtotals and asset headers are recomputed from the live positions
   * rather than left at what the server rendered: a reader who has hidden
   * Liquidity is shown an asset header that still counts it, and the numbers
   * stop adding up down the column -- which is the one thing this design
   * promises.
   *
   * @param {object} view - the result of `evaluate`.
   */
  function paintFigures(view) {
    assets().forEach(function (card) {
      var value = card.querySelector(".cval .val");
      if (value) write(value, view.values[card.id]);
    });

    groups().forEach(function (group) {
      var subtotal = 0;
      var kept = 0;
      Array.prototype.forEach.call(group.querySelectorAll(".position"), function (position) {
        if (position.classList.contains(HIDDEN_CLASS)) return;
        kept += 1;
        subtotal += num(position, "data-value");
      });
      group.classList.toggle(HIDDEN_CLASS, kept === 0);
      var total = group.querySelector(".pgroup-total");
      if (total) {
        write(total, subtotal);
        // A subtotal over a single row is that row's own figure said twice,
        // three lines apart, and the two cannot differ. The template leaves it
        // out for a group served with one position; a filter can take a bigger
        // group down to one, so the same rule applies here.
        total.hidden = kept === 1;
      }
      var count = group.querySelector(".pgroup-name .n");
      if (count) {
        count.textContent = String(kept);
        count.hidden = kept === 1;
      }
    });

    // Every other figure on the page keeps its own value and only changes
    // currency: a position's value is not a subtotal of anything, and neither
    // is an NFT's estimate, floor or purchase price. The NFT section is in this
    // list because it is part of this design now -- it used to be design 1's
    // markup, whose figures `address.js` converted.
    Array.prototype.forEach.call(
      document.querySelectorAll(
        ".dynamic-page .position-val .val, .dynamic-page .dist .val," +
          " .dynamic-page .nftsec .val"
      ),
      function (element) {
        write(element, num(element, "data-val"));
      }
    );
  }

  /**
   * Write a figure into an element without disturbing its unit.
   *
   * The reason this file has a currency writer of its own. Every value cell on
   * this page pairs a number with a unit, and the unit is a separate element --
   * a sibling in the asset header, a child in a venue subtotal. `innerHTML` on
   * the value destroys or duplicates it. Only the number is written, and only
   * into the first text node, so an element that holds `12.34 <span>ALGO</span>`
   * keeps its span.
   *
   * @param {Element} element - the value element.
   * @param {number} algo - the figure, in ALGO.
   */
  function write(element, algo) {
    var text = fmt(algo);
    var node = element.firstChild;
    if (node && node.nodeType === 3) node.nodeValue = text + (element.querySelector(".unit") ? " " : "");
    else element.insertBefore(document.createTextNode(text), element.firstChild);

    element.classList.toggle("neg", algo < 0);
    var unit = element.querySelector(".unit");
    if (unit) unit.textContent = state.ccy;
  }

  /**
   * Write the headline, and the line under it.
   *
   * The one figure no *filter* may move -- a reader who hides a category has
   * not become poorer -- but the currency is not a filter. It is the unit the
   * whole page is denominated in, and a page whose every figure says USD above
   * a total that says ALGO is not showing a total at all. That was the reading
   * this file got wrong.
   *
   * "Total without NFTs" moves it legitimately, because it changes *what is
   * being totalled* rather than how it is displayed. It is design 1's setting
   * and design 1's storage key, so the two pages agree.
   *
   * `.pricetip`'s own data attributes carry both currencies and both totals, so
   * nothing here recomputes from rendered text.
   *
   * @param {object} view - the result of `evaluate`.
   */
  function paintTotal(view) {
    var head = document.querySelector(".dynamic-page .pricetip");
    if (!head) return;

    var algo = num(head, "data-totalwnft");
    if (state.nonft) algo -= num(head, "data-totalnft");

    var usd = algo * rate();
    var inChosen = state.ccy === "USD" ? usd : algo;
    var other = state.ccy === "USD" ? algo : usd;

    // The unit goes *inside* this element: it is written wholesale, and a
    // sibling would survive the write and read "216.30 USD ALGO".
    head.textContent = plain(inChosen) + " " + state.ccy;
    head.setAttribute(
      "data-tip",
      plain(other) + " " + (state.ccy === "USD" ? "ALGO" : "USD")
    );

    var sub = document.querySelector(".dynamic-page .total-sub .num");
    if (sub) {
      sub.textContent =
        plain(other) +
        " " +
        (state.ccy === "USD" ? "ALGO" : "USD") +
        " at " +
        rate().toLocaleString("en-US", {
          minimumFractionDigits: 6,
          maximumFractionDigits: 6,
        }) +
        " USD/ALGO";
    }

    var note = document.querySelector(".dynamic-page .total-note");
    if (note) {
      note.textContent = state.nonft
        ? "Everything this address holds, except the NFTs."
        : "Everything this address holds.";
    }
  }

  /**
   * @param {number} value - a figure already in the chosen currency.
   * @returns {string} it, grouped, to two places.
   */
  function plain(value) {
    return value.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }

  /**
   * Say what the visible categories add up to.
   *
   * The headline is the whole address and does not move, which is right and
   * also leaves a reader who has switched DeFi off with no way to see what the
   * rest comes to. This is that number, and it appears only when it differs
   * from the headline -- an unfiltered page does not need to be told that its
   * total is its total.
   *
   * @param {object} view - the result of `evaluate`.
   */
  function paintReadout(view) {
    var readout = document.getElementById("band-readout");
    if (!readout) return;

    var head = document.querySelector(".dynamic-page .pricetip");
    var whole = head ? num(head, "data-totalwnft") : 0;
    var shown = CATEGORIES.reduce(function (sum, key) {
      return sum + (state.cats.indexOf(key) === -1 ? 0 : view.totals[key]);
    }, 0);
    if (state.nft && head) shown += num(head, "data-totalnft");

    // Compared in ALGO, and loosely: the categories are summed from the rows
    // and the headline comes from the payload, so they differ in the last
    // fraction even when nothing is filtered.
    if (Math.abs(shown - whole) < 0.01) {
      readout.textContent = "";
      return;
    }
    readout.textContent =
      "Showing " +
      fmt(shown) +
      " " +
      state.ccy +
      " of " +
      fmt(whole) +
      " " +
      state.ccy;
  }

  /**
   * Set every unit label on the page, including the ones outside a value cell.
   */
  function paintUnits() {
    Array.prototype.forEach.call(
      document.querySelectorAll(".dynamic-page .u.unit, .dynamic-page .fig-val .unit"),
      function (unit) {
        unit.textContent = state.ccy;
      }
    );
  }

  /**
   * Redraw the band: the bar, the five figures, and the donuts.
   *
   * All three from `view.totals`, in one place, because they are three drawings
   * of one set of numbers and a reader who sees them disagree has no way to
   * know which one lied.
   *
   * @param {object} view - the result of `evaluate`.
   */
  function paintBand(view) {
    // Applied here rather than only where it is toggled, so a reader who hid
    // the collections and came back is not handed them again while the figure
    // still reads "off". Every other part of the state is applied on every
    // render; this one was not, and only a reload showed it.
    var section = document.querySelector(".dynamic-page .nftsec");
    if (section) section.hidden = !state.nft;

    var nft = num(document.querySelector('.dynamic-page .fig[data-band="nft"] .fig-val'), "data-val");
    var totals = {
      balance: view.totals.balance,
      staked: view.totals.staked,
      liquidity: view.totals.liquidity,
      defi: view.totals.defi,
      nft: state.nft ? nft : 0,
    };
    var summed = Object.keys(totals).reduce(function (sum, key) {
      return sum + Math.abs(totals[key]);
    }, 0);

    Array.prototype.forEach.call(
      document.querySelectorAll(".dynamic-page #allocation-bar [data-band]"),
      function (segment) {
        var key = segment.getAttribute("data-band");
        var share = summed ? (Math.abs(totals[key]) / summed) * 100 : 0;
        segment.style.width = share + "%";
        segment.hidden = share === 0;
        segment.setAttribute("aria-pressed", pressed(key) ? "true" : "false");
      }
    );

    Array.prototype.forEach.call(
      document.querySelectorAll(".dynamic-page .figs .fig"),
      function (fig) {
        var key = fig.getAttribute("data-band");
        var share = summed ? (Math.abs(totals[key]) / summed) * 100 : 0;
        fig.setAttribute("aria-pressed", pressed(key) ? "true" : "false");
        var value = fig.querySelector(".fig-val");
        // The NFT figure keeps its served value: it is not a subtotal of
        // anything the position filter can reach.
        if (value && key !== "nft") write(value, totals[key]);
        else if (value) write(value, nft);
        var percent = fig.querySelector(".fig-share");
        if (percent) percent.textContent = share.toFixed(1) + "%";
      }
    );

    redrawCharts(totals, summed);
  }

  /**
   * @param {string} key - a category key.
   * @returns {boolean} true if that category is currently showing.
   */
  function pressed(key) {
    if (key === "nft") return state.nft;
    return state.cats.indexOf(key) !== -1;
  }

  /**
   * Hand the filtered allocation to `dynamic.js` and ask it to redraw.
   *
   * Only the allocation donut is the toolbar's business -- it is the same five
   * numbers as the bar. The other charts are of the whole address and are left
   * alone, which is the same rule the headline follows.
   *
   * @param {object} totals - the five category totals.
   * @param {number} summed - their magnitudes' sum.
   */
  function redrawCharts(totals, summed) {
    var dynamic = window.asastatsDynamic;
    var panel = document.getElementById("charts");
    if (!dynamic || !dynamic.redrawAllocation || !panel || !panel.open) return;
    dynamic.redrawAllocation(totals, summed, state.ccy);
  }

  // -- grouping by venue ----------------------------------------------------

  /**
   * Build the venue list by moving every `.pgroup` into the venue that holds it.
   *
   * Moved, never copied: a copy would put a second element on the page with the
   * same `data-pid`, and a pin names a position by that id. Moving also keeps
   * open breakdowns, bound handlers and the position pins working, because they
   * are the same nodes -- `appendChild` on an element already in the document
   * relocates it.
   *
   * Where each group came from is remembered on the group itself, so switching
   * back is exact rather than reconstructed.
   */
  function toVenues() {
    var list = document.getElementById("venue-list");
    if (!list || list.childElementCount) return;

    var byVenue = {};
    Array.prototype.forEach.call(
      document.querySelectorAll("#asset-list .pgroup"),
      function (group) {
        if (!group._asastatsHome) {
          // The *index* among its siblings, not the sibling itself. A
          // remembered `nextElementSibling` is only valid while that sibling is
          // still where it was, and an asset holding four venues has all four
          // moved away -- so restoring the first one threw, because the node it
          // was to be inserted before had itself been moved. An index survives
          // its neighbours leaving and coming back.
          group._asastatsHome = {
            parent: group.parentNode,
            index: Array.prototype.indexOf.call(group.parentNode.children, group),
          };
        }
        var venue = group.getAttribute("data-venue") || "Wallet balance";
        if (!byVenue[venue]) byVenue[venue] = [];
        byVenue[venue].push(group);
      }
    );

    Object.keys(byVenue).forEach(function (venue) {
      list.appendChild(venueCard(venue, byVenue[venue]));
    });
  }

  /**
   * Build one venue card.
   *
   * `createElement` and `textContent` throughout: venue names come off the
   * chain, and this is the one place on the page where markup could be
   * smuggled in through one.
   *
   * @param {string} venue - the venue's name.
   * @param {Element[]} groups - the `.pgroup` elements it holds.
   * @returns {Element} the card.
   */
  function venueCard(venue, groups) {
    var card = document.createElement("details");
    card.className = "fitem mcard venue-card";
    card.open = true;
    card.setAttribute("data-venue-card", venue);

    var head = document.createElement("summary");
    head.className = "chead";

    var id = document.createElement("span");
    id.className = "cid";
    var top = document.createElement("span");
    top.className = "cid-top";
    var name = document.createElement("span");
    name.className = "cid-name";
    // The venue's own link, if its groups carried one. The card is built from a
    // name, so the href is lifted off the first group's heading rather than
    // resolved again here -- `program_url` needs the reader's chosen explorer,
    // which is a template concern and is not available to a script.
    var link = groups[0] && groups[0].querySelector(".pgroup-venue a");
    if (link) {
      var anchor = document.createElement("a");
      anchor.className = "out";
      anchor.href = link.href;
      anchor.target = "_blank";
      anchor.textContent = venue;
      name.appendChild(anchor);
    } else {
      name.textContent = venue;
    }
    top.appendChild(name);
    id.appendChild(top);

    var value = document.createElement("span");
    value.className = "cval";
    var figure = document.createElement("span");
    figure.className = "v val venue-total";
    var unit = document.createElement("span");
    unit.className = "u unit";
    unit.textContent = state.ccy;
    value.appendChild(figure);
    value.appendChild(unit);

    head.appendChild(id);
    head.appendChild(value);

    var body = document.createElement("div");
    body.className = "cbody";
    var inner = document.createElement("div");
    inner.className = "cbody-inner";
    groups.forEach(function (group) {
      inner.appendChild(group);
    });
    body.appendChild(inner);

    card.appendChild(head);
    card.appendChild(body);
    return card;
  }

  /**
   * Put every `.pgroup` back where the server rendered it, and drop the cards.
   */
  function toAssets() {
    var list = document.getElementById("venue-list");
    if (!list) return;

    // Sorted by where each group belongs before any of them moves, so an asset
    // holding four venues gets them back in the order the server ranked them
    // rather than in whatever order the venue cards happened to be built.
    // Appending in ascending index order rebuilds the sequence exactly, because
    // `.program-groups` holds nothing but these.
    Array.prototype.slice
      .call(list.querySelectorAll(".pgroup"))
      .filter(function (group) {
        return group._asastatsHome && group._asastatsHome.parent;
      })
      .sort(function (a, b) {
        return a._asastatsHome.index - b._asastatsHome.index;
      })
      .forEach(function (group) {
        group._asastatsHome.parent.appendChild(group);
      });

    // The emptied cards, not the list's whole contents. Wiping the list would
    // take a group that somehow has no remembered home with it -- and a
    // position row deleted from the page is the worst thing this file could do,
    // because the reader has no way to tell it was ever there.
    Array.prototype.slice
      .call(list.querySelectorAll("[data-venue-card]"))
      .forEach(function (card) {
        if (!card.querySelector(".pgroup")) card.remove();
      });
  }

  /**
   * Show the list the current grouping calls for, and total the venue cards.
   *
   * @param {object} view - the result of `evaluate`.
   */
  function regroup() {
    var assetList = document.getElementById("asset-list");
    var venueList = document.getElementById("venue-list");
    if (!assetList || !venueList) return;

    if (state.group === "venue") toVenues();
    else toAssets();

    assetList.hidden = state.group === "venue";
    venueList.hidden = state.group !== "venue";
    assetList.classList.toggle(VENUE_CLASS, state.group === "venue");

    // The section still called itself "Assets 76" over a list of venues. The
    // served text is kept rather than rebuilt, so switching back restores
    // exactly what the template rendered -- including a count that is the
    // server's, not this script's arithmetic.
    var heading = document.querySelector(".dynamic-page .asasec .section-head h2");
    var count = document.querySelector(".dynamic-page .asasec .section-head .count");
    if (!heading || !count) return;
    if (heading._asastatsServed === undefined) {
      heading._asastatsServed = heading.textContent;
      count._asastatsServed = count.textContent;
    }
    if (state.group === "venue") {
      heading.textContent = "Venues";
      count.textContent = String(venueList.childElementCount);
    } else {
      heading.textContent = heading._asastatsServed;
      count.textContent = count._asastatsServed;
    }
  }

  /**
   * Total the venue cards from whatever survived the filter.
   */
  function paintVenues() {
    var venueList = document.getElementById("venue-list");
    if (!venueList || state.group !== "venue") return;

    Array.prototype.forEach.call(venueList.children, function (card) {
      var subtotal = 0;
      var kept = 0;
      Array.prototype.forEach.call(card.querySelectorAll(".position"), function (position) {
        if (position.classList.contains(HIDDEN_CLASS)) return;
        kept += 1;
        subtotal += num(position, "data-value");
      });
      card.classList.toggle(HIDDEN_CLASS, kept === 0);
      var total = card.querySelector(".venue-total");
      if (total) total.textContent = fmt(subtotal);
    });
  }

  // -- the controls ---------------------------------------------------------

  /**
   * @returns {object} {shown, total} for the venue list.
   */
  function venueCounts() {
    var venueList = document.getElementById("venue-list");
    if (!venueList) return { shown: 0, total: 0 };
    var cards = Array.prototype.slice.call(venueList.children);
    return {
      shown: cards.filter(function (card) {
        return !card.classList.contains(HIDDEN_CLASS);
      }).length,
      total: cards.length,
    };
  }

  /**
   * Reflect the state in the toolbar's own controls.
   *
   * @param {object} counts - {shown, total} for the status line.
   */
  function paintControls(counts) {
    press("#tb-group", "data-group", state.group);
    press("#tb-sort", "data-sort", state.sort);
    press("#tb-ccy", "data-ccy", state.ccy);
    toggle("#tb-nonft", state.nonft);
    toggle("#tb-refresh", state.refresh);

    var field = document.getElementById("tb-q");
    if (field && field.value !== state.q) field.value = state.q;

    var direction = document.getElementById("tb-dir");
    if (direction) {
      direction.textContent = state.dir === -1 ? "↓ Desc" : "↑ Asc";
      direction.setAttribute("aria-pressed", state.dir === 1 ? "true" : "false");
    }

    var reset = document.getElementById("tb-reset");
    if (reset) reset.disabled = isDefault();

    var status = document.getElementById("tb-status");
    if (status) {
      // Counts what the reader is actually looking at. In venue mode the asset
      // list is not on screen, so reporting a number of assets would be
      // describing a page they cannot see.
      var noun = state.group === "venue" ? "venues" : "assets";
      var shown = state.group === "venue" ? venueCounts() : counts;
      status.textContent = isDefault()
        ? ""
        : "Showing " + shown.shown + " of " + shown.total + " " + noun + ".";
    }
  }

  /**
   * Set one toggle button's pressed state.
   *
   * @param {string} selector - the button's id selector.
   * @param {boolean} on - whether it is on.
   */
  function toggle(selector, on) {
    var button = document.querySelector(selector);
    if (button) button.setAttribute("aria-pressed", on ? "true" : "false");
  }

  /**
   * Set `aria-pressed` across one segmented group.
   *
   * @param {string} selector - the group's id selector.
   * @param {string} attribute - the attribute naming each button's value.
   * @param {string} value - the value that is on.
   */
  function press(selector, attribute, value) {
    var group = document.querySelector(selector);
    if (!group) return;
    Array.prototype.forEach.call(group.children, function (button) {
      button.setAttribute(
        "aria-pressed",
        button.getAttribute(attribute) === value ? "true" : "false"
      );
    });
  }

  // -- the render -----------------------------------------------------------

  /**
   * Apply the whole state to the page.
   *
   * One function, called after every change. Partial updates are how a bar and
   * a figure come to disagree, and the work is a few hundred class toggles --
   * cheaper than the reasoning needed to skip any of it correctly.
   */
  function render() {
    // Structure first, and that ordering is load-bearing. Switching to venues
    // *moves* the position rows out of their asset cards, so anything that
    // measured before the move would total an asset at zero and hide every card
    // on the page -- which is exactly what "Reset view" did until this ran
    // first.
    regroup();

    var view = evaluate();
    order(view.rows);
    var counts = paintAssets(view);
    paintFigures(view);
    paintUnits();
    paintTotal(view);
    paintBand(view);
    paintReadout(view);
    paintCollections();
    paintVenues();
    paintControls(counts);
    writeView();
  }

  // -- events ---------------------------------------------------------------

  /**
   * Toggle one category, or the NFT section.
   *
   * Turning the last one off would leave a page with nothing on it and no
   * obvious way back, so the last category on cannot be switched off -- it
   * turns the others back on instead, which is the reading of "I want only
   * this one" that a reader pressing an already-solo category means.
   *
   * @param {string} key - the category pressed.
   */
  function toggleCategory(key) {
    if (key === "nft") {
      state.nft = !state.nft;
      return;
    }
    var at = state.cats.indexOf(key);
    if (at === -1) state.cats.push(key);
    else if (state.cats.length === 1) state.cats = CATEGORIES.slice();
    else state.cats.splice(at, 1);
  }

  /**
   * Handle a press anywhere in the toolbar or the band.
   *
   * @param {Event} event - the click.
   * @returns {boolean} true if the press was one of ours.
   */
  function onClick(event) {
    var target = event.target;
    if (!target || !target.closest) return false;

    var control = target.closest("[data-group], [data-sort], [data-ccy], [data-band]");
    if (control) {
      if (control.hasAttribute("data-group")) state.group = control.getAttribute("data-group");
      else if (control.hasAttribute("data-sort")) state.sort = control.getAttribute("data-sort");
      else if (control.hasAttribute("data-ccy")) state.ccy = control.getAttribute("data-ccy");
      else toggleCategory(control.getAttribute("data-band"));
      render();
      return true;
    }

    if (target.closest("#tb-nonft")) {
      state.nonft = !state.nonft;
      render();
      return true;
    }

    if (target.closest("#tb-refresh")) {
      state.refresh = !state.refresh;
      render();
      return true;
    }

    if (target.closest("#tb-dir")) {
      state.dir *= -1;
      render();
      return true;
    }

    if (target.closest("#tb-reset")) {
      reset();
      return true;
    }

    return false;
  }

  /**
   * Put the view back to what the server rendered.
   */
  function reset() {
    // The view, not the reader's settings. Currency, auto-refresh and
    // "without NFTs" are preferences that follow them across addresses and
    // tabs; "Reset view" undoes what they did to *this* page.
    state.q = DEFAULTS.q;
    state.group = DEFAULTS.group;
    state.sort = DEFAULTS.sort;
    state.dir = DEFAULTS.dir;
    state.cats = DEFAULTS.cats.slice();
    state.nft = DEFAULTS.nft;
    state.more = { asa: 0, nft: 0 };
    render();
  }

  /**
   * Bind the toolbar.
   *
   * Bound to the two containers that own the controls -- the toolbar and the
   * band -- rather than delegated from `document` the way `pins.js` and
   * `showmore.js` are. Those two have to listen at the document because the
   * controls they serve are on rows, and rows are moved, folded and reordered;
   * these controls are on elements the server renders once and nothing
   * replaces. Binding where the controls actually live means a handler dies
   * with the element it belongs to, instead of outliving it and acting on a
   * page it no longer describes.
   *
   * The guard goes on the toolbar itself for the same reason. A second
   * execution finds the attribute and returns, so two sets of handlers cannot
   * toggle a category on and straight back off -- silent, and
   * indistinguishable from a dead control. And if the toolbar ever *is* swapped
   * out by an htmx partial, the attribute goes with the old element and the
   * next execution correctly binds the new one.
   */
  function init() {
    var toolbar = document.querySelector(".dynamic-page #toolbar");
    if (!toolbar || toolbar.hasAttribute(BOUND_ATTR)) return;
    toolbar.setAttribute(BOUND_ATTR, "");

    state = readView();

    var press = function (event) {
      if (event.defaultPrevented) return;
      if (onClick(event)) event.preventDefault();
    };
    toolbar.addEventListener("click", press);
    var band = document.querySelector(".dynamic-page .band");
    if (band) band.addEventListener("click", press);

    // The load-more controls, one per section. `showmore.js` reveals a whole
    // tail in one press and is design 1's; these designs reveal a batch, so it
    // stands down here and this takes over.
    Array.prototype.forEach.call(
      document.querySelectorAll(".dynamic-page .asasec, .dynamic-page .nftsec"),
      function (section) {
        section.addEventListener("click", function (event) {
          if (event.defaultPrevented) return;
          var control = event.target.closest
            ? event.target.closest("[data-show-more]")
            : null;
          if (!control) return;
          event.preventDefault();
          state.more[section.classList.contains("nftsec") ? "nft" : "asa"] += 1;
          render();
        });
      }
    );

    var field = document.getElementById("tb-q");
    if (field) {
      var typed = function () {
        state.q = field.value.trim().toLowerCase();
        render();
      };
      field.addEventListener("input", typed);
      // A search field's clear button fires `search`, not `input`, in Safari.
      field.addEventListener("search", typed);
    }

    render();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Exposed for the jest suite, which drives these directly.
  window.asastatsToolbar = {
    init: init,
    render: render,
    reset: reset,
    readView: readView,
    writeView: writeView,
    viewKey: viewKey,
    evaluate: evaluate,
    limit: limit,
    fmt: fmt,
    paintTotal: paintTotal,
    paintReadout: paintReadout,
    paintCollections: paintCollections,
    write: write,
    toVenues: toVenues,
    regroup: regroup,
    paintVenues: paintVenues,
    toAssets: toAssets,
    toggleCategory: toggleCategory,
    isDefault: isDefault,
    state: function (next) {
      if (next) state = next;
      return state;
    },
  };
})();
