/**
 * @jest-environment jsdom
 */

describe("color-mode.js", () => {
  beforeEach(() => {
    // Clear the require cache so the IIFE script executes fresh in each test
    jest.resetModules();

    // Reset the DOM and localStorage to a clean slate
    localStorage.clear();
    document.documentElement.className = "";
  });

  it("should add the 'dark' class to the html element if localStorage has mode='dark'", () => {
    // 1. Setup the environment
    localStorage.setItem("mode", "dark");

    // 2. Execute the script
    require("../static/js/color-mode.js");

    // 3. Assert the class was added to <html>
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("should NOT add the 'dark' class if localStorage has mode='light'", () => {
    localStorage.setItem("mode", "light");

    require("../static/js/color-mode.js");

    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("should NOT add the 'dark' class if localStorage is empty", () => {
    // localStorage is already cleared in beforeEach

    require("../static/js/color-mode.js");

    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });
});
