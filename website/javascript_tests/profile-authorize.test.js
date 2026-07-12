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

  /*
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   * SECTION: Materialize Collapsible Tests
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   */
  describe("Materialize Collapsible Initialization", () => {
    let addEventListenerSpy;

    beforeEach(() => {
      // Spy on addEventListener to intercept the listener and avoid
      // JSDOM global listener accumulation issues across tests.
      addEventListenerSpy = jest.spyOn(document, "addEventListener");
    });

    afterEach(() => {
      addEventListenerSpy.mockRestore();
    });

    it("should initialize collapsibles on DOMContentLoaded if Materialize is present", () => {
      window.M = {
        Collapsible: {
          init: jest.fn(),
        },
      };

      const col1 = document.createElement("ul");
      col1.className = "collapsible";
      document.body.appendChild(col1);

      require("../static/js/profile-authorize.js");

      // Extract the specific callback attached during THIS test
      const call = addEventListenerSpy.mock.calls.find(
        (c) => c[0] === "DOMContentLoaded",
      );
      const callback = call[1];

      // Execute the callback directly instead of dispatching globally
      callback();

      expect(window.M.Collapsible.init).toHaveBeenCalledTimes(1);
      const args = window.M.Collapsible.init.mock.calls[0][0];
      expect(args.length).toBe(1);
      expect(args[0]).toBe(col1);
    });

    it("should fail gracefully if window.M is missing", () => {
      require("../static/js/profile-authorize.js");

      const call = addEventListenerSpy.mock.calls.find(
        (c) => c[0] === "DOMContentLoaded",
      );
      const callback = call[1];

      // Execute directly; expect it not to throw
      expect(() => {
        callback();
      }).not.toThrow();
    });

    it("should fail gracefully if window.M exists but window.M.Collapsible is missing", () => {
      window.M = {};

      require("../static/js/profile-authorize.js");

      const call = addEventListenerSpy.mock.calls.find(
        (c) => c[0] === "DOMContentLoaded",
      );
      const callback = call[1];

      // Execute directly; expect it not to throw
      expect(() => {
        callback();
      }).not.toThrow();
    });
  });
});
