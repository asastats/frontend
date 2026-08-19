/**
 * @jest-environment jsdom
 */

/** Build the preference marker the _layout_preference.html partial delivers. */
function mountMarker(position) {
  const el = document.createElement("div");
  el.id = "id-layout-preference";
  if (position !== undefined) {
    el.setAttribute("data-layout-position", position);
  }
  document.body.appendChild(el);
  return el;
}

/**
 * Swap localStorage for one whose `method` throws; returns a restore function.
 *
 * Neither obvious approach works in both environments this suite runs in:
 * spying on `Storage.prototype` misses `jest-localstorage-mock` (which the
 * project's jest config loads, and which replaces localStorage with a plain
 * object), while assigning `localStorage.getItem = fn` misses real jsdom --
 * its Storage is a Proxy, so that stores a value under the key "getItem"
 * instead of overriding the method. Redefining the property on `window` is
 * above both mechanisms and behaves the same either way.
 */
function breakStorage(method, message) {
  const real = window.localStorage;
  const broken = {
    getItem: (k) => real.getItem(k),
    setItem: (k, v) => real.setItem(k, v),
    removeItem: (k) => real.removeItem(k),
    clear: () => real.clear(),
  };
  broken[method] = () => {
    throw new Error(message);
  };
  const define = (value) =>
    Object.defineProperty(window, "localStorage", { value, configurable: true });
  define(broken);
  return () => define(real);
}

describe("layout.js", () => {
  beforeEach(() => {
    jest.resetModules();
    document.documentElement.removeAttribute("data-layout-position");
    document.body.innerHTML = "";
    localStorage.clear();
  });

  it("does nothing when the layout preference marker is not present", () => {
    require("../static/js/layout.js");

    expect(document.documentElement.hasAttribute("data-layout-position")).toBe(
      false
    );
    expect(localStorage.getItem("layout-position")).toBeNull();
  });

  it("does nothing when the marker lacks a data-layout-position attribute", () => {
    mountMarker();

    require("../static/js/layout.js");

    expect(document.documentElement.hasAttribute("data-layout-position")).toBe(
      false
    );
    expect(localStorage.getItem("layout-position")).toBeNull();
  });

  it("ignores an unknown layout position rather than blanking the layout", () => {
    mountMarker("grid");

    require("../static/js/layout.js");

    expect(document.documentElement.hasAttribute("data-layout-position")).toBe(
      false
    );
    expect(localStorage.getItem("layout-position")).toBeNull();
  });

  it("ignores an empty layout position", () => {
    mountMarker("");

    require("../static/js/layout.js");

    expect(document.documentElement.hasAttribute("data-layout-position")).toBe(
      false
    );
    expect(localStorage.getItem("layout-position")).toBeNull();
  });

  it("applies 'cards' layout to document root and remembers it in localStorage", () => {
    mountMarker("cards");

    require("../static/js/layout.js");

    expect(document.documentElement.getAttribute("data-layout-position")).toBe(
      "cards"
    );
    expect(localStorage.getItem("layout-position")).toBe("cards");
  });

  it("applies 'rows' layout to document root and remembers it in localStorage", () => {
    mountMarker("rows");

    require("../static/js/layout.js");

    expect(document.documentElement.getAttribute("data-layout-position")).toBe(
      "rows"
    );
    expect(localStorage.getItem("layout-position")).toBe("rows");
  });

  it("does not rewrite the attribute if document root already has the matching position", () => {
    document.documentElement.setAttribute("data-layout-position", "cards");
    mountMarker("cards");

    const setAttributeSpy = jest.spyOn(
      document.documentElement,
      "setAttribute"
    );

    require("../static/js/layout.js");

    expect(setAttributeSpy).not.toHaveBeenCalled();
    expect(localStorage.getItem("layout-position")).toBe("cards");

    setAttributeSpy.mockRestore();
  });

  it("updates the attribute if document root has a differing position", () => {
    document.documentElement.setAttribute("data-layout-position", "rows");
    mountMarker("cards");

    require("../static/js/layout.js");

    expect(document.documentElement.getAttribute("data-layout-position")).toBe(
      "cards"
    );
    expect(localStorage.getItem("layout-position")).toBe("cards");
  });

  it("still applies the layout attribute when localStorage throws", () => {
    const restore = breakStorage("setItem", "QuotaExceededError");
    mountMarker("cards");

    try {
      expect(() => {
        require("../static/js/layout.js");
      }).not.toThrow();
      expect(
        document.documentElement.getAttribute("data-layout-position")
      ).toBe("cards");
    } finally {
      restore();
    }
  });
});
