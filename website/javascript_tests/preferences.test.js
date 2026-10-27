/**
 * @jest-environment jsdom
 */

"use strict";

function run() {
  jest.resetModules();
  require("../static/js/preferences.js");
}

describe("preferences.js", () => {
  const root = document.documentElement;

  beforeEach(() => {
    localStorage.clear();
    for (const name of ["data-theme", "data-typeface", "data-fold-assets", "data-fold-collections"]) {
      root.removeAttribute(name);
    }
    root.classList.remove("prefold");
  });

  test("stamps nothing for a reader without preferences", () => {
    run();
    expect(root.hasAttribute("data-theme")).toBe(false);
    expect(root.hasAttribute("data-typeface")).toBe(false);
    expect(root.classList.contains("prefold")).toBe(false);
  });

  test("stamps the theme, the typeface and both folds", () => {
    localStorage.setItem("theme", "dark");
    localStorage.setItem("typeface", "mono");
    localStorage.setItem("fold-assets", "20");
    localStorage.setItem("fold-collections", "5");
    run();
    expect(root.getAttribute("data-theme")).toBe("dark");
    expect(root.getAttribute("data-typeface")).toBe("mono");
    expect(root.getAttribute("data-fold-assets")).toBe("20");
    expect(root.getAttribute("data-fold-collections")).toBe("5");
    expect(root.classList.contains("prefold")).toBe(true);
  });

  test("marks prefold for a single fold", () => {
    localStorage.setItem("fold-collections", "5");
    run();
    expect(root.hasAttribute("data-fold-assets")).toBe(false);
    expect(root.classList.contains("prefold")).toBe(true);
  });
});
