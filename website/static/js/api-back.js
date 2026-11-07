/**
 * @file The Back link on the Swagger page (templates/api/swagger_ui.html).
 * @description A file rather than an inline script, for the CSP.
 */

(function () {
  "use strict";
  var link = document.getElementById("api-back");
  if (!link) return;
  link.addEventListener("click", function (event) {
    // A page opened straight here has no history: the link's own href then.
    if (window.history.length > 1) {
      event.preventDefault();
      window.history.back();
    }
  });
})();
