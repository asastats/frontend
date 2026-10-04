/**
 * Unfolding the tail of a section, a batch at a time.
 * Design 1: first ADDRESS_INITIAL_ASSETS/COLLECTIONS, each press adds batch.
 * Section publishes data-initial from same setting template used.
 * Replaced magnitude rule (99.5% then all at once): arbitrary from outside.
 * No fetch/loading/failure state; payload in hand before render.
 * Button owns state in aria-expanded; stylesheet reads it for labels.
 */
(function () {
  "use strict";

  /** On a row that is not currently shown. `input.css` hides it. */
  var FOLDED_CLASS = "folded";
  /** Guards against a second execution binding a second handler. */
  var BOUND_ATTR = "data-showmore-bound";
  /**
   * Extra batches revealed, per container.
   *
   * A property on the element rather than an attribute: it is this page view's
   * state, not something the markup describes, and an attribute would be one
   * more thing a stylesheet or a test could come to depend on.
   */
  var BATCHES_PROP = "_asastatsShowMoreBatches";

  /**
   * Return the container of rows a control unfolds.
   * Control sits after container; looks backwards from wrapper.
   * Falls back to nearest section.
   * @param {Element} button - the show-more control.
   * @returns {Element|null} the container, or null if the markup changed.
   */
  function containerFor(button) {
    var wrapper = button.parentNode;
    if (!wrapper) return null;
    var previous = wrapper.previousElementSibling;
    if (previous && previous.hasAttribute("data-folding")) return previous;
    // Fall back to the nearest section, so a wrapper added between the two
    // degrades to "unfolds the right section" rather than to nothing at all.
    var section = button.closest(".asasec, .nftsec");
    return section ? section.querySelector("[data-folding]") : null;
  }

  /**
   * Return the rows a container folds.
   * Only .fitem children; other things shift fold.
   * @param {Element} container - the `[data-folding]` element.
   * @returns {Element[]} the rows, in display order.
   */
  function rows(container) {
    return Array.prototype.filter.call(container.children, function (child) {
      return child.classList.contains("fitem");
    });
  }

  /**
   * Return how many rows one press reveals.
   * Read from section (dynamic designs publish it, toolbar.js reads it).
   * Falls back to "all" when no section publishes batch size.
   * @param {Element} container - the `[data-folding]` element.
   * @param {number} total - how many rows it holds.
   * @returns {number} the batch size.
   */
  function batchSize(container, total) {
    var section = container.closest("[data-initial]");
    var chosen = foldSize(section);
    if (chosen === Infinity) return Infinity;
    if (isFinite(chosen) && chosen > 0) return chosen;
    var initial = section
      ? parseInt(section.getAttribute("data-initial"), 10)
      : NaN;
    return isFinite(initial) && initial > 0 ? initial : total;
  }

  /**
   * The reader's own fold size for a section, or NaN to use the server's.
   * Read from same attribute stylesheet reads (one value in one place).
   * "all" = Infinity so Math.min works without magic constant.
   * @param {Element} section - the `[data-initial]` section, or null.
   * @returns {number} the reader's size, Infinity for all, or NaN if unset.
   */
  function foldSize(section) {
    if (!section || !section.classList) return NaN;
    var name = section.classList.contains("nftsec")
      ? "data-fold-collections"
      : "data-fold-assets";
    var chosen = document.documentElement.getAttribute(name);
    if (!chosen) return NaN;
    if (chosen === "all") return Infinity;
    return parseInt(chosen, 10);
  }

  /**
   * Fold the tail, and put the next batch's size on the control.
   * Everything showing = only "Show fewer" left.
   * @param {Element} container - the `[data-folding]` element.
   * @param {Element} button - its control.
   */
  function paint(container, button) {
    var entries = rows(container);
    var batch = batchSize(container, entries.length);
    var keep = Math.min(batch * (1 + (container[BATCHES_PROP] || 0)), entries.length);

    entries.forEach(function (entry, index) {
      entry.classList.toggle(FOLDED_CLASS, index >= keep);
    });

    var folded = entries.length - keep;
    var label = button.querySelector(".show-more-open");
    if (label) {
      var noun = button.getAttribute("data-noun") || "rows";
      var next = Math.min(folded, batch);
      label.textContent = "Show " + next + " more " + noun;
    }
    // Everything is showing, so the only thing left to offer is putting it back.
    button.setAttribute("aria-expanded", folded ? "false" : "true");
    // **Unless there was never anything to put back.** A reader who chose to
    // see every row gets a control whose only remaining offer is "Show fewer",
    // and pressing it would reveal the same rows again - the batch is already
    // the whole list. The template renders the control from the *server's*
    // fold, which does not know what the reader chose, so hiding it is this
    // script's job. `toolbar.js` does the same for the dynamic designs.
    // Likewise a list no longer than one batch: nothing to fold or put back.
    if (button.parentNode) {
      button.parentNode.hidden = batch === Infinity || entries.length <= batch;
    }
    // **The stylesheet's job is over the moment this runs.** `html.prefold`
    // rules position rows by DOM index, which is right until something starts
    // folding by a filtered index instead. This script does not filter, but it
    // does own `.folded` from here on, and leaving both in force would mean two
    // answers to one question. Dropped here rather than at load: without a
    // reader's fold nothing paints until a press, and until then the stylesheet
    // *is* the fold; with one, `init` paints by that same size.
    document.documentElement.classList.remove("prefold");
  }

  /**
   * Act on one press: reveal another batch, or collapse back to the first.
   * Press that never travels = click on grip, not drag.
   * @param {Element} button - the control that was pressed.
   */
  function toggle(button) {
    var container = containerFor(button);
    if (!container) return;

    var entries = rows(container);
    var batch = batchSize(container, entries.length);
    var showing = batch * (1 + (container[BATCHES_PROP] || 0));

    if (showing >= entries.length) {
      container[BATCHES_PROP] = 0;
    } else {
      container[BATCHES_PROP] = (container[BATCHES_PROP] || 0) + 1;
    }
    paint(container, button);
  }

  /**
   * Bind the delegated handler.
   * Design 1 only (dynamic designs fold from toolbar).
   * Delegated from document; guarded against double-bind.
   * defaultPrevented stops second binding acting (silent failure).
   */
  function init() {
    // Design 1 only (dynamic designs fold from toolbar).
    if (document.querySelector(".dynamic-page")) return;
    if (document.documentElement.hasAttribute(BOUND_ATTR)) return;
    document.documentElement.setAttribute(BOUND_ATTR, "");

    // Every handler bails on already-handled event. Attribute stops second
    // binding; this stops second binding acting twice.
    document.addEventListener("click", function (event) {
      var button = event.target.closest
        ? event.target.closest("[data-show-more]")
        : null;
      if (!button) return;
      // Belt as well as braces. Attribute stops second *binding*;
      // this stops second binding acting twice (silent failure).
      if (event.defaultPrevented) return;
      event.preventDefault();
      toggle(button);
    });

    // The reader's own fold size: fold by it now, so a control the server
    // served hidden appears when that fold hides rows. See docs/logbook.md.
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-show-more]"),
      function (button) {
        var container = containerFor(button);
        if (container && !isNaN(foldSize(container.closest("[data-initial]")))) {
          paint(container, button);
        }
      }
    );
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Exposed for the jest suite.
  window.asastatsShowMore = {
    toggle: toggle,
    paint: paint,
    containerFor: containerFor,
  };
})();
