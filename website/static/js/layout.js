/**
 * Applies the reader's address-page layout, and remembers it for next time.
 *
 * The address page is `cache_page`'d and its entry is shared between signed-in
 * readers, so the page cannot be rendered with anyone's layout in it. The
 * preference arrives instead in `_layout_preference.html`, a non-cached partial
 * htmx loads after the page -- the same arrangement `_swap_entry.html` uses for
 * the swap config, and for the same reason.
 *
 * Loading after the page would normally mean a visible reflow on every visit,
 * so the value is mirrored into localStorage and stamped onto `<html>` by the
 * inline script in base.html before the first paint. This file is what keeps
 * that copy honest: on a first visit in a new browser it stamps the layout for
 * the first time, and afterwards it corrects the remembered value only when the
 * server disagrees with it.
 *
 * The stamped attribute is `data-layout-position`, whose only job is to select
 * the grid areas in `input.css`. `data-layout` is the layout's own key, carried
 * for anything that later wants to know which of the four is in force.
 */
(function () {
  "use strict";

  /** Shared with the inline head script in base.html. */
  var STORAGE_KEY = "layout-position";
  /** Selects the grid areas in input.css. */
  var ATTRIBUTE = "data-layout-position";
  /** The only two values `input.css` knows how to place. */
  var KNOWN = ["rows", "cards"];

  /**
   * Apply `position` to the document root and remember it.
   *
   * Writing the attribute unconditionally would be simpler, but a no-op write
   * still invalidates style for the subtree, and this runs on a page holding
   * a couple of hundred positions.
   *
   * @param {string} position - "rows" or "cards".
   */
  function apply(position) {
    var root = document.documentElement;
    if (root.getAttribute(ATTRIBUTE) !== position) {
      root.setAttribute(ATTRIBUTE, position);
    }
    try {
      localStorage.setItem(STORAGE_KEY, position);
    } catch (e) {
      // Private browsing, or storage full. The attribute is already applied;
      // only the no-reflow-next-time optimisation is lost.
    }
  }

  /**
   * Read the preference the partial delivered and apply it.
   *
   * An unknown or missing value is ignored rather than defaulted: the CSS
   * already treats "no attribute" as rows, so clearing it here would only add
   * a way for a bad value to blank the layout.
   */
  function init() {
    var marker = document.getElementById("id-layout-preference");
    if (!marker) return;

    var position = marker.getAttribute("data-layout-position");
    if (KNOWN.indexOf(position) === -1) return;

    apply(position);
  }

  init();
})();
