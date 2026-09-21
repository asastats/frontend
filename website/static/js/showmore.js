/**
 * Unfolding the tail of a section, a batch at a time.
 *
 * Design 1's address page shows the first `ADDRESS_INITIAL_ASSETS` assets and
 * `ADDRESS_INITIAL_COLLECTIONS` collections, and each press of the control adds
 * that many again. The section publishes the number as `data-initial`, from the
 * same setting the template rendered the first fold from, so the two cannot
 * disagree about what one press is worth.
 *
 * This replaced a magnitude rule -- show the rows accounting for 99.5% of the
 * section's value, then reveal *all* of the rest in one press. Both halves read
 * as arbitrary from the outside: the first showed 33 rows on one address and 8
 * on the next with nothing on the page to explain the difference, and the second
 * made the control's own label untrue, promising "Show 39 more assets" and then
 * being a one-shot unfold rather than a load-more. The dynamic designs already
 * worked this way (`toolbar.js`), so this is the two designs agreeing.
 *
 * There is nothing to fetch, so there is no loading state, no failure state and
 * no request. The payload is in hand before the page renders, and a round trip
 * to reveal dust would cost more than the markup already does.
 *
 * The button owns the state in `aria-expanded`, and the stylesheet reads it to
 * pick which of the two labels shows. The script writes the *count* inside the
 * "show more" label and nothing else: which label is visible stays a function
 * of the attribute a screen reader already reads, so the two cannot disagree.
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
   *
   * The control sits after its container rather than inside it -- it is not one
   * of the rows -- so this looks backwards from the wrapper it lives in rather
   * than upwards from the button.
   *
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
   *
   * Its `.fitem` children only. A container may hold other things -- a heading
   * arriving later, a note -- and counting those would shift the fold by
   * however many of them there are.
   *
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
   *
   * Read off the *section* rather than off the folding container, because that
   * is where the dynamic designs publish it and `toolbar.js` reads it from --
   * one place for the number in both designs, so they cannot drift apart.
   *
   * Falls back to "all of them" when no section publishes a batch size, which
   * is the pre-batching behaviour: a template that forgets the attribute keeps
   * working rather than revealing one row per press.
   *
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
   *
   * **Read from the same attribute the stylesheet reads.** `base.html` stamps
   * it before paint from `localStorage`, the `html.prefold` rules act on it for
   * the gap before this script runs, and this reads it afterwards. One value in
   * one place: a script and a stylesheet disagreeing about how many rows are
   * shown surfaces as a control offering to reveal rows already on screen.
   *
   * Which section it is comes from the section's own class, the same pair the
   * stylesheet keys on - `.asasec` and `.nftsec` exist in both designs.
   *
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
   *
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
    if (button.parentNode) {
      button.parentNode.hidden = batch === Infinity;
    }
    // **The stylesheet's job is over the moment this runs.** `html.prefold`
    // rules position rows by DOM index, which is right until something starts
    // folding by a filtered index instead. This script does not filter, but it
    // does own `.folded` from here on, and leaving both in force would mean two
    // answers to one question. Dropped here rather than at load because, unlike
    // the dynamic designs, nothing paints this page until a press: until then
    // the stylesheet *is* the reader's fold.
    document.documentElement.classList.remove("prefold");
  }

  /**
   * Act on one press: reveal another batch, or collapse back to the first.
   *
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
   *
   * Delegated from the document so a section arriving later needs no
   * rebinding, and guarded so a second execution of this file -- which the
   * page's htmx partials make possible -- does not toggle twice per click.
   */
  function init() {
    // Design 1 only. The dynamic designs fold from the toolbar, which also
    // filters and sorts, and two handlers on one control would both act -- a
    // batch revealed *and* the batch counted -- so the second press would have
    // nothing left to do.
    if (document.querySelector(".dynamic-page")) return;
    if (document.documentElement.hasAttribute(BOUND_ATTR)) return;
    document.documentElement.setAttribute(BOUND_ATTR, "");

    document.addEventListener("click", function (event) {
      var button = event.target.closest
        ? event.target.closest("[data-show-more]")
        : null;
      if (!button) return;
      // Belt as well as braces. The attribute above stops a second *binding*;
      // this stops a second binding that slipped past it from acting, because
      // the failure mode is silent -- two handlers toggle and untoggle, and the
      // button simply looks dead. `defaultPrevented` is the standard way to ask
      // "has something already handled this", and the first handler sets it.
      if (event.defaultPrevented) return;
      event.preventDefault();
      toggle(button);
    });
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
