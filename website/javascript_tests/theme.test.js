/**
 * @jest-environment jsdom
 */

const T = require("../static/js/theme.js");

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
      const setItem = jest
        .spyOn(Storage.prototype, "setItem")
        .mockImplementation(() => {
          throw new Error("QuotaExceededError");
        });
      expect(T.applyTheme("retro")).toBe(true);
      expect(document.documentElement.getAttribute("data-theme")).toBe("retro");
      setItem.mockRestore();
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
      const getItem = jest
        .spyOn(Storage.prototype, "getItem")
        .mockImplementation(() => {
          throw new Error("SecurityError");
        });
      const inputs = mountPicker(["asastats", "nord"]);
      expect(T.wireThemePicker(document)).toBe(2);
      expect(inputs.some((i) => i.checked)).toBe(false);
      getItem.mockRestore();
    });
  });
});
