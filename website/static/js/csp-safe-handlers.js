/**
 * @file CSP-safe event delegation handlers
 * @author Ivica Paleka
 * @description Replaces inline HTML attributes (onerror, onfocus) so the site
 * complies with a strict Content Security Policy that omits 'unsafe-inline'.
 */

(function () {
  "use strict";

  /*
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   * SECTION: Image Error Fallback
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   */

  /**
   * Handle image load errors by swapping to a fallback URL.
   * Replaces: onerror="this.onerror=null; this.src='FALLBACK'"
   *
   * Uses the capture phase (true) since 'error' events do not bubble.
   *
   * @param {Event} event - The triggered error event
   */
  document.addEventListener(
    "error",
    function (event) {
      var el = event.target;
      if (
        el &&
        el.tagName === "IMG" &&
        el.dataset &&
        el.dataset.fallback &&
        el.dataset.fellBack !== "1"
      ) {
        el.dataset.fellBack = "1"; // Guard against a loop if the fallback 404s
        el.src = el.dataset.fallback;
      }
    },
    true
  );


  /*
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   * SECTION: Auto-Select on Focus
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   */

  /**
   * Auto-select input text when elements gain focus.
   * Replaces: onfocus="this.select()"
   *
   * Uses 'focusin' event as standard 'focus' events do not bubble.
   *
   * @param {Event} event - The triggered focusin event
   */
  document.addEventListener("focusin", function (event) {
    var el = event.target;
    if (
      el &&
      el.dataset &&
      el.dataset.selectOnFocus !== undefined &&
      typeof el.select === "function"
    ) {
      el.select();
    }
  });
})();
