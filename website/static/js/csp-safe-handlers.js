/**
 * @file CSP-safe event delegation handlers
 * @description Replaces inline HTML attributes (onerror, onfocus) and the old
 * inline color-mode <script>, so the site complies with a strict Content
 * Security Policy that omits 'unsafe-inline'. Load this at the START of <body>
 * so the mode class is applied before first paint.
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
  /*
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   * SECTION: Color Mode (light / dark)
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   */
  /**
   * Apply the color mode as a <body> class. Replaces the inline script:
   *   var mode = '{{ mode }}' || localStorage.getItem('mode') || 'light';
   *   document.body.classList.add(mode);
   *
   * Precedence is unchanged: the server value (rendered as <html data-mode>)
   * wins, then the persisted localStorage choice, then "light". Applied
   * immediately when <body> already exists (this file loads at body start, so
   * no flash); otherwise deferred to DOMContentLoaded as a safety net.
   */
  (function applyColorMode() {
    var root = document.documentElement; // <html>, always present here
    var serverMode = (root && root.dataset && root.dataset.mode) || "";
    var mode = serverMode || localStorage.getItem("mode") || "light";
    if (document.body) {
      document.body.classList.add(mode);
    } else {
      document.addEventListener("DOMContentLoaded", function () {
        document.body.classList.add(mode);
      });
    }
  })();
})();
