/**
 * @jest-environment jsdom
 */

describe("profile-authorize.js", () => {
  beforeEach(() => {
    // Clear the require cache so the IIFE executes fresh in every test
    jest.resetModules();

    // Clean up the DOM and global window variables
    document.body.innerHTML = "";
    delete window.__WALLET_TEST__;
    delete window.M;
  });

  /*
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   * SECTION: Wallet Test Flag Tests
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   */
  describe("Wallet Test Flag", () => {
    it("should set window.__WALLET_TEST__ to true if the flag element is present and value is '1'", () => {
      const flagDiv = document.createElement("div");
      flagDiv.id = "id-wallet-flags";
      flagDiv.dataset.walletTest = "1";
      document.body.appendChild(flagDiv);

      require("../static/js/profile-authorize.js");

      expect(window.__WALLET_TEST__).toBe(true);
    });

    it("should NOT set window.__WALLET_TEST__ if the value is not '1'", () => {
      const flagDiv = document.createElement("div");
      flagDiv.id = "id-wallet-flags";
      flagDiv.dataset.walletTest = "0";
      document.body.appendChild(flagDiv);

      require("../static/js/profile-authorize.js");

      expect(window.__WALLET_TEST__).toBeUndefined();
    });

    it("should NOT set window.__WALLET_TEST__ if the flag element is missing entirely", () => {
      // Body is empty, no element exists
      require("../static/js/profile-authorize.js");

      expect(window.__WALLET_TEST__).toBeUndefined();
    });
  });
});
