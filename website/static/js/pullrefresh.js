/**
 * @file Pull down to refresh on the address pages, in the app only.
 * @description Loaded by templates/snippets/app_pull_refresh.html; the indicator's
 * look is in that snippet. See docs/logbook.md.
 */

(function () {
  "use strict";
  var root = document.documentElement;
  if (!root.classList.contains("in-app")) return;

  /** Finger travel shrinks to this share on screen, so the pull feels weighted. */
  var DAMPING = 0.5;
  /** Indicator travel, in px, at which letting go refreshes. */
  var TRIGGER_PX = 64;
  /** The indicator stops here, in px, however far the finger goes. */
  var MAX_PX = 96;

  var indicator = null;
  var startX = 0;
  var startY = 0;
  var tracking = false;
  var pulling = false;
  var ready = false;
  var refreshing = false;

  /** Return the indicator, creating it on first use. */
  function getIndicator() {
    if (!indicator) {
      indicator = document.createElement("div");
      indicator.id = "pull-refresh";
      indicator.setAttribute("aria-hidden", "true");
      indicator.innerHTML =
        '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" ' +
        'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">' +
        '<path d="M20 12a8 8 0 1 1-2.34-5.66"/><path d="M20 4v4h-4"/></svg>';
      document.body.appendChild(indicator);
    }
    return indicator;
  }

  /** True if a touch on `target` belongs to something other than the page. */
  function startsElsewhere(target) {
    if (document.querySelector("dialog[open]")) return true;
    for (var node = target; node && node !== document.body; node = node.parentElement) {
      if (/^(INPUT|TEXTAREA|SELECT)$/.test(node.tagName)) return true;
      // Inside a box that is itself scrolled: the pull scrolls that box back.
      if (node.scrollTop > 0) return true;
    }
    return false;
  }

  /** Move the indicator to `distance` px below its hidden place. */
  function show(distance) {
    var el = getIndicator();
    el.classList.add("dragging");
    el.style.transform = "translate(-50%, " + distance + "px) rotate(" + distance * 4 + "deg)";
    el.style.opacity = String(Math.min(distance / TRIGGER_PX, 1));
    el.classList.toggle("ready", distance >= TRIGGER_PX);
  }

  function hide() {
    if (indicator) {
      indicator.style.transform = "";
      indicator.style.opacity = "0";
      indicator.classList.remove("ready", "dragging");
    }
  }

  function reset() {
    tracking = pulling = ready = false;
  }

  function onTouchStart(event) {
    reset();
    if (refreshing || event.touches.length !== 1 || window.scrollY > 0) return;
    if (startsElsewhere(event.target)) return;
    startX = event.touches[0].clientX;
    startY = event.touches[0].clientY;
    tracking = true;
  }

  function onTouchMove(event) {
    if (!tracking) return;
    var touch = event.touches[0];
    var dy = touch.clientY - startY;
    var dx = touch.clientX - startX;
    if (event.touches.length !== 1 || window.scrollY > 0 || (!pulling && (dy < 0 || Math.abs(dx) > dy))) {
      // A second finger, a scroll, or a sideways or upward first move: not a pull.
      tracking = false;
      if (pulling) hide();
      pulling = ready = false;
      return;
    }
    pulling = true;
    var distance = Math.min(Math.max(dy, 0) * DAMPING, MAX_PX);
    ready = distance >= TRIGGER_PX;
    show(distance);
  }

  function onTouchEnd() {
    if (!tracking) return;
    var fire = ready;
    reset();
    if (!fire) {
      hide();
      return;
    }
    refreshing = true;
    show(TRIGGER_PX);
    indicator.classList.remove("dragging");
    indicator.classList.add("spinning");
    // address.js's reloadPage reopens the sections that were open.
    if (typeof window.reloadPage === "function") {
      window.reloadPage();
    } else {
      window.location.reload();
    }
  }

  function onTouchCancel() {
    reset();
    hide();
  }

  document.addEventListener("touchstart", onTouchStart, { passive: true });
  document.addEventListener("touchmove", onTouchMove, { passive: true });
  document.addEventListener("touchend", onTouchEnd, { passive: true });
  document.addEventListener("touchcancel", onTouchCancel, { passive: true });
  // Back from the bfcache must not keep a spinner from before the reload.
  window.addEventListener("pageshow", function () {
    refreshing = false;
    reset();
    if (indicator) indicator.classList.remove("spinning");
    hide();
  });
})();
