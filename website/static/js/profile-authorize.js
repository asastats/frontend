/**
 * @file Page-scoped script for profile_authorize.
 * @description Sets the wallet test flag the bundle reads.
 *
 * Load this in the page footer BEFORE the wallet bundle, so the flag is set
 * synchronously before the bundle reads it.
 */

(function () {
  "use strict";

  /**
   * Reads the server-rendered dataset value and sets the global test flag.
   */
  var flags = document.getElementById("id-wallet-flags");
  if (flags && flags.dataset.walletTest === "1") {
    window.__WALLET_TEST__ = true;
  }
})();
