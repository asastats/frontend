/**
 * @file The reader's stored preferences, stamped before the stylesheet paints.
 * @description Loaded synchronously in base.html's <head> (not deferred): run
 * any later and the reader sees the theme flash. A file rather than an inline
 * script so the CSP needs no 'unsafe-inline' (docs/logbook.md).
 */

(function () {
  "use strict";
  var root = document.documentElement;
  var saved = localStorage.getItem("theme");
  if (saved) root.setAttribute("data-theme", saved);
  var face = localStorage.getItem("typeface");
  if (face) root.setAttribute("data-typeface", face);
  // `prefold` scopes the CSS that folds sections before the scripts run.
  // `toolbar.js` and `showmore.js` drop it and own folding from then on.
  var folds = { "fold-assets": 1, "fold-collections": 1 };
  var stamped = false;
  for (var key in folds) {
    var value = localStorage.getItem(key);
    if (value) {
      root.setAttribute("data-" + key, value);
      stamped = true;
    }
  }
  if (stamped) root.classList.add("prefold");
})();
