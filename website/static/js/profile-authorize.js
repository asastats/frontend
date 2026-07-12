/**
 * @file Page-scoped script for profile_authorize.
 * @description Sets the wallet test flag and initializing Materialize collapsibles.
 * 
 * Note: Include this in the page footer BEFORE the wallet bundle, ensuring 
 * the flag is set synchronously before the bundle attempts to read it. Kept 
 * page-local to prevent double-initialization of collapsibles globally.
 */

(function () {
  "use strict";

  /*
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   * SECTION: Wallet Test Flag Initialization
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   */

  /**
   * Reads the server-rendered dataset value and sets the global test flag.
   */
  var flags = document.getElementById("id-wallet-flags");
  if (flags && flags.dataset.walletTest === "1") {
    window.__WALLET_TEST__ = true;
  }

  /*
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   * SECTION: Materialize Collapsibles
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   */

  /**
   * Initializes Materialize collapsibles once the DOM is ready.
   */
  document.addEventListener("DOMContentLoaded", function () {
    if (window.M && window.M.Collapsible) {
      window.M.Collapsible.init(document.querySelectorAll(".collapsible"));
    }
  });
})();