/**
 * @jest-environment jsdom
 */

const T = require("../static/js/theme.js");

/** Build the light/dark switch a signed-out reader gets. */
function mountToggle(light, dark) {
  document.body.innerHTML =
    `<button data-theme-toggle data-theme-light="${light}" ` +
    `data-theme-dark="${dark}" aria-pressed="false"></button>`;
  return document.querySelector("[data-theme-toggle]");
}

/** Build the picker markup the theme_picker.html snippet renders. */
function mountPicker(themes) {
  document.body.innerHTML =
    '<details id="menu"><summary></summary><ul>' +
    themes
      .map(
        (t) =>
          `<li><input type="radio" name="theme-dropdown" value="${t}" aria-label="${t}"></li>`
      )
      .join("") +
    "</ul></details>";
  return [...document.querySelectorAll("input[name='theme-dropdown']")];
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

describe("theme.js", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
    document.body.innerHTML = "";
  });

  describe("applyTheme", () => {
    it("stamps the theme on <html> and remembers it", () => {
      expect(T.applyTheme("asastats-dark")).toBe(true);
      expect(document.documentElement.getAttribute("data-theme")).toBe(
        "asastats-dark"
      );
      expect(localStorage.getItem(T.STORAGE_KEY)).toBe("asastats-dark");
    });

    it("ignores an empty theme rather than clearing the current one", () => {
      T.applyTheme("nord");
      expect(T.applyTheme("")).toBe(false);
      expect(document.documentElement.getAttribute("data-theme")).toBe("nord");
    });

    it("still applies when storage refuses the write", () => {
      const restore = breakStorage("setItem", "QuotaExceededError");
      expect(T.applyTheme("retro")).toBe(true);
      expect(document.documentElement.getAttribute("data-theme")).toBe("retro");
      restore();
    });
  });

  describe("wireThemePicker", () => {
    it("ticks the saved theme so the picker opens on the current choice", () => {
      localStorage.setItem(T.STORAGE_KEY, "luxury");
      const inputs = mountPicker(["asastats", "luxury", "nord"]);
      T.wireThemePicker(document);
      expect(inputs.map((i) => i.checked)).toEqual([false, true, false]);
    });

    it("ticks nothing when no theme has been chosen yet", () => {
      const inputs = mountPicker(["asastats", "nord"]);
      T.wireThemePicker(document);
      expect(inputs.some((i) => i.checked)).toBe(false);
    });

    it("applies the theme the viewer picks", () => {
      const inputs = mountPicker(["asastats", "sunset"]);
      T.wireThemePicker(document);
      inputs[1].checked = true;
      inputs[1].dispatchEvent(new Event("change"));
      expect(document.documentElement.getAttribute("data-theme")).toBe("sunset");
      expect(localStorage.getItem(T.STORAGE_KEY)).toBe("sunset");
    });

    it("closes the menu once a theme is chosen", () => {
      const inputs = mountPicker(["asastats", "dim"]);
      const menu = document.getElementById("menu");
      menu.open = true;
      T.wireThemePicker(document);
      inputs[1].dispatchEvent(new Event("change"));
      expect(menu.open).toBe(false);
    });

    it("binds each input once, so a re-wire cannot double-apply", () => {
      const inputs = mountPicker(["asastats", "dim"]);
      expect(T.wireThemePicker(document)).toBe(2);
      // An htmx swap would call this again over the same DOM.
      expect(T.wireThemePicker(document)).toBe(0);
      // Count the writes directly. A MutationObserver cannot be used here:
      // its callback is a microtask, so it has not run yet at the point the
      // assertion is made.
      const setAttr = jest.spyOn(document.documentElement, "setAttribute");
      inputs[1].dispatchEvent(new Event("change"));
      expect(setAttr.mock.calls.filter((c) => c[0] === "data-theme")).toEqual([
        ["data-theme", "dim"],
      ]);
      setAttr.mockRestore();
    });

    it("re-ticks inputs that arrived in a later swap", () => {
      localStorage.setItem(T.STORAGE_KEY, "coffee");
      T.wireThemePicker(document); // nothing on the page yet
      const inputs = mountPicker(["asastats", "coffee"]);
      expect(T.wireThemePicker(document)).toBe(2);
      expect(inputs[1].checked).toBe(true);
    });

    it("applies the theme even when the picker is not in a disclosure", () => {
      document.body.innerHTML =
        '<input type="radio" name="theme-dropdown" value="nord">';
      const input = document.querySelector("input");
      T.wireThemePicker(document);
      expect(() => input.dispatchEvent(new Event("change"))).not.toThrow();
      expect(document.documentElement.getAttribute("data-theme")).toBe("nord");
    });

    it("no-ops on a page without a picker", () => {
      expect(T.wireThemePicker(document)).toBe(0);
    });

    it("defaults to the whole document when given no root", () => {
      mountPicker(["asastats"]);
      expect(T.wireThemePicker()).toBe(1);
    });

    it("survives storage being unreadable", () => {
      const restore = breakStorage("getItem", "SecurityError");
      const inputs = mountPicker(["asastats", "nord"]);
      expect(T.wireThemePicker(document)).toBe(2);
      expect(inputs.some((i) => i.checked)).toBe(false);
      restore();
    });
  });
});


describe("wireThemeToggle", function () {
  beforeEach(function () {
    document.documentElement.removeAttribute("data-theme");
    localStorage.clear();
  });

  it("applies the dark theme first when nothing is set", function () {
    const button = mountToggle("asastats", "asastats-dark");
    T.wireThemeToggle(document);

    button.click();

    expect(document.documentElement.getAttribute("data-theme")).toBe(
      "asastats-dark"
    );
  });

  it("switches back to light on a second click", function () {
    const button = mountToggle("asastats", "asastats-dark");
    T.wireThemeToggle(document);

    button.click();
    button.click();

    expect(document.documentElement.getAttribute("data-theme")).toBe("asastats");
  });

  it("treats any other theme as not-dark, so the first click goes dark", function () {
    // Someone picks `dracula` while signed in, then signs out. The switch has
    // only two positions; landing on dark is the useful move, and doing
    // nothing would look broken.
    document.documentElement.setAttribute("data-theme", "dracula");
    const button = mountToggle("asastats", "asastats-dark");
    T.wireThemeToggle(document);

    button.click();

    expect(document.documentElement.getAttribute("data-theme")).toBe(
      "asastats-dark"
    );
  });

  it("reflects the state for a screen reader", function () {
    const button = mountToggle("asastats", "asastats-dark");
    T.wireThemeToggle(document);
    expect(button.getAttribute("aria-pressed")).toBe("false");

    button.click();
    expect(button.getAttribute("aria-pressed")).toBe("true");

    button.click();
    expect(button.getAttribute("aria-pressed")).toBe("false");
  });

  it("remembers the choice", function () {
    const button = mountToggle("asastats", "asastats-dark");
    T.wireThemeToggle(document);

    button.click();

    expect(localStorage.getItem(T.STORAGE_KEY)).toBe("asastats-dark");
  });

  it("ignores a button with no pair, rather than applying undefined", function () {
    document.body.innerHTML = "<button data-theme-toggle></button>";

    expect(T.wireThemeToggle(document)).toBe(0);
    document.querySelector("[data-theme-toggle]").click();
    expect(document.documentElement.getAttribute("data-theme")).toBeNull();
  });

  it("does not double-bind when wired twice", function () {
    // The header can be replaced by an htmx swap, which re-runs the wiring.
    // A second listener would toggle twice per click and appear to do nothing.
    const button = mountToggle("asastats", "asastats-dark");
    T.wireThemeToggle(document);
    expect(T.wireThemeToggle(document)).toBe(0);

    button.click();

    expect(document.documentElement.getAttribute("data-theme")).toBe(
      "asastats-dark"
    );
  });

  it("wires nothing on a page with no switch", function () {
    document.body.innerHTML = "";
    expect(T.wireThemeToggle(document)).toBe(0);
  });

  it("defaults to the whole document when called with no root", function () {
    // The self-start path calls it that way, and an htmx swap re-runs it.
    mountToggle("asastats", "asastats-dark");

    expect(T.wireThemeToggle()).toBe(1);
  });
});


describe("currentTheme", function () {
  beforeEach(function () {
    document.documentElement.removeAttribute("data-theme");
    localStorage.clear();
  });

  it("prefers what is applied to the document", function () {
    document.documentElement.setAttribute("data-theme", "nord");
    localStorage.setItem(T.STORAGE_KEY, "dracula");

    expect(T.currentTheme()).toBe("nord");
  });

  it("falls back to what was saved", function () {
    localStorage.setItem(T.STORAGE_KEY, "dracula");

    expect(T.currentTheme()).toBe("dracula");
  });

  it("returns an empty string when nothing is set", function () {
    expect(T.currentTheme()).toBe("");
  });

  it("survives a localStorage that refuses to be read", function () {
    // Private browsing can throw on access rather than return null.
    const restore = breakStorage("getItem");
    try {
      expect(T.currentTheme()).toBe("");
    } finally {
      restore();
    }
  });
});
