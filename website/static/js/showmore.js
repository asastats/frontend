/**
 * Unfolding the tail of a section.
 *
 * The address page shows the rows accounting for the first
 * `ADDRESS_SECTION_THRESHOLD` of a section's magnitude and folds the rest --
 * see `utils/cutoff.py` for the rule and why it measures magnitude. Every row
 * is in the document either way; this only flips which are displayed.
 *
 * There is nothing to fetch, so there is no loading state, no failure state and
 * no request. The payload is in hand before the page renders, and a round trip
 * to reveal dust would cost more than the markup already does.
 *
 * The button owns the state in `aria-expanded`, and the stylesheet reads it for
 * both the rows and the button's own label. That is deliberate: a script that
 * also wrote the label could leave the text and the attribute disagreeing, and
 * the attribute is the half a screen reader believes.
 */
(function () {
  "use strict";

  /** Set on the container once its folded rows are revealed. */
  var UNFOLDED_CLASS = "unfolded";
  /** Guards against a second execution binding a second handler. */
  var BOUND_ATTR = "data-showmore-bound";

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
   * Toggle one section between folded and unfolded.
   *
   * @param {Element} button - the control that was pressed.
   */
  function toggle(button) {
    var container = containerFor(button);
    if (!container) return;

    var unfolded = container.classList.toggle(UNFOLDED_CLASS);
    button.setAttribute("aria-expanded", unfolded ? "true" : "false");
  }

  /**
   * Bind the delegated handler.
   *
   * Delegated from the document so a section arriving later needs no
   * rebinding, and guarded so a second execution of this file -- which the
   * page's htmx partials make possible -- does not toggle twice per click.
   */
  function init() {
    // Design 1 only. This reveals a section's whole tail in one press; the
    // money-column designs show a fixed first batch and add one batch per
    // press, which is `toolbar.js`'s job. Two handlers on one control would
    // both act -- the tail revealed *and* the batch counted -- and the second
    // press would then have nothing left to do.
    if (document.querySelector(".money-page")) return;
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
  window.asastatsShowMore = { toggle: toggle, containerFor: containerFor };
})();
