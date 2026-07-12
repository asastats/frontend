/**
 * @jest-environment jsdom
 */

// Requiring the file executes the IIFE and attaches the listeners to the global document
require("../static/js/csp-safe-handlers.js");

describe("CSP-safe handlers", () => {
  beforeEach(() => {
    // Clear the DOM before each test to ensure a clean slate
    document.body.innerHTML = "";
  });

  /*
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   * SECTION: Image Error Fallback Tests
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   */
  describe("Image error fallback handler", () => {
    it("should replace src with the fallback URL on error", () => {
      const img = document.createElement("img");
      img.dataset.fallback = "fallback-image.png";
      img.src = "broken-image.png";
      document.body.appendChild(img);

      // Dispatch error event (handler uses capture phase)
      const errorEvent = new Event("error");
      img.dispatchEvent(errorEvent);

      expect(img.src).toContain("fallback-image.png");
      expect(img.dataset.fellBack).toBe("1");
    });

    it("should not loop if it has already fallen back once", () => {
      const img = document.createElement("img");
      img.dataset.fallback = "fallback-image.png";
      img.dataset.fellBack = "1"; // Simulate already having failed over
      img.src = "broken-image.png";
      document.body.appendChild(img);

      const errorEvent = new Event("error");
      img.dispatchEvent(errorEvent);

      expect(img.src).toContain("broken-image.png"); // Src remains unchanged
    });

    it("should ignore non-IMG elements that trigger errors", () => {
      const div = document.createElement("div");
      div.dataset.fallback = "fallback-image.png";
      document.body.appendChild(div);

      const errorEvent = new Event("error");
      div.dispatchEvent(errorEvent);

      expect(div.dataset.fellBack).toBeUndefined();
    });

    it("should ignore IMG elements that lack a data-fallback attribute", () => {
      const img = document.createElement("img");
      img.src = "broken-image.png";
      document.body.appendChild(img);

      const errorEvent = new Event("error");
      img.dispatchEvent(errorEvent);

      expect(img.dataset.fellBack).toBeUndefined();
    });
  });

  /*
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   * SECTION: Select On Focus Tests
   * * * * * * * * * * * * * * * * * * * * * * * * * * *
   */
  describe("Select on focusin handler", () => {
    it("should call select() when an element with data-select-on-focus gains focus", () => {
      const input = document.createElement("input");
      input.dataset.selectOnFocus = ""; // Matches HTML empty attribute boolean logic
      input.select = jest.fn();
      document.body.appendChild(input);

      // Focusin bubbles, matching the listener
      const focusEvent = new Event("focusin", { bubbles: true });
      input.dispatchEvent(focusEvent);

      expect(input.select).toHaveBeenCalledTimes(1);
    });

    it("should not call select() if data-select-on-focus is missing", () => {
      const input = document.createElement("input");
      input.select = jest.fn();
      document.body.appendChild(input);

      const focusEvent = new Event("focusin", { bubbles: true });
      input.dispatchEvent(focusEvent);

      expect(input.select).not.toHaveBeenCalled();
    });

    it("should gracefully ignore elements that lack a select() function", () => {
      const div = document.createElement("div");
      div.dataset.selectOnFocus = "";
      // divs do not have a select() method natively
      document.body.appendChild(div);

      const focusEvent = new Event("focusin", { bubbles: true });

      // We expect the dispatch not to throw a TypeError
      expect(() => {
        div.dispatchEvent(focusEvent);
      }).not.toThrow();
    });
  });

  describe("Color Mode (light / dark) initialization", () => {
    const originalBody = document.body;

    beforeEach(() => {
      // Clear the require cache so the IIFE script executes fresh in each test
      jest.resetModules();

      // Reset state
      localStorage.clear();
      document.documentElement.dataset.mode = "";
      if (document.body) {
        document.body.className = "";
      }
    });

    afterEach(() => {
      // Safely restore document.body in case a test removed it
      Object.defineProperty(document, "body", {
        value: originalBody,
        configurable: true,
      });
    });

    it("should apply mode from HTML dataset immediately if body exists", () => {
      document.documentElement.dataset.mode = "dark";

      // Execute the script
      require("../static/js/csp-safe-handlers.js");

      expect(document.body.classList.contains("dark")).toBe(true);
    });

    it("should defer applying mode to DOMContentLoaded if document.body is not yet parsed", () => {
      // 1. Temporarily mock document.body to be null
      Object.defineProperty(document, "body", {
        value: null,
        configurable: true,
      });
      localStorage.setItem("mode", "dark");

      // 2. Execute the script. Because body is null, this hits the uncovered lines 92-93
      require("../static/js/csp-safe-handlers.js");

      // 3. Restore the body so the event listener has an element to modify
      Object.defineProperty(document, "body", {
        value: originalBody,
        configurable: true,
      });

      // Verify the class hasn't been added yet
      expect(document.body.classList.contains("dark")).toBe(false);

      // 4. Trigger the DOMContentLoaded event
      document.dispatchEvent(new Event("DOMContentLoaded"));

      // 5. Verify the deferred function successfully ran
      expect(document.body.classList.contains("dark")).toBe(true);
    });
  });
});
