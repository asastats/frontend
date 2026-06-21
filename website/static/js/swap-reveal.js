/*
 * Reveals the per-ASA Swap buttons in the address-page accordion once the
 * non-cached swap-entry partial has injected its #id-swap-enabled gate marker.
 *
 * Kept out of the template so the gate logic can be unit tested. The CSS hides
 * `.swap-asa-entry` by default and shows it under `body.swap-enabled`; this
 * module toggles that class from the marker's presence (a plain-class
 * replacement for `body:has(#id-swap-enabled)`, for browsers without :has()).
 */

function applySwapReveal(doc) {
  var enabled = !!doc.querySelector("#id-swap-enabled");
  if (doc.body) {
    doc.body.classList.toggle("swap-enabled", enabled);
  }
  return enabled;
}

/* istanbul ignore next -- DOM wiring; behaviour is covered via applySwapReveal */
function initSwapReveal() {
  var run = function () { applySwapReveal(document); };
  var wire = function () {
    // The marker arrives via the htmx swap of #id-swap-entry-container, so
    // re-evaluate after htmx settles content as well as on first load.
    document.body.addEventListener("htmx:afterSwap", run);
    document.body.addEventListener("htmx:load", run);
    run();
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wire);
  } else {
    wire();
  }
}

/* istanbul ignore else -- in the browser we self-start; under jest we export */
if (typeof module !== "undefined" && module.exports) {
  module.exports = { applySwapReveal: applySwapReveal, initSwapReveal: initSwapReveal };
} else {
  /* istanbul ignore next -- browser entry point */
  initSwapReveal();
}
