/**
 * @file Flash-free color mode
 * @author Ivica Paleka
 * @description Applies the persisted dark/light choice to <html> BEFORE the
 * stylesheets paint, so there is no light-then-dark flash. Dark mode is stored
 * only in localStorage (never sent by the server), so this must run on the
 * client. CSS targets `html.dark ...`.
 */
(function () {
  "use strict";
  if (localStorage.getItem("mode") === "dark") {
    document.documentElement.classList.add("dark");
  }
})();
