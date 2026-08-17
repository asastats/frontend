/**
 * @jest-environment jsdom
 */

const T = require("../static/js/theme.js");

/** Build the typeface picker the appearance page renders. */
function mountTypefaces(names) {
  document.body.innerHTML =
    '<label><input type="radio" name="typeface-choice" value=""></label>' +
    names
      .map(
        (n) =>
          `<label data-typeface="${n}"><input type="radio" name="typeface-choice" value="${n}"></label>`
      )
      .join("");
  return [...document.querySelectorAll("input[name='typeface-choice']")];
}

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


describe("applyTypeface", function () {
  beforeEach(function () {
    document.documentElement.removeAttribute("data-typeface");
    localStorage.clear();
  });

  it("stamps the pairing on the document", function () {
    T.applyTypeface("rosepine");

    expect(document.documentElement.getAttribute("data-typeface")).toBe(
      "rosepine"
    );
  });

  it("remembers it", function () {
    T.applyTypeface("rosepine");

    expect(localStorage.getItem(T.TYPEFACE_KEY)).toBe("rosepine");
  });

  it("an empty value clears the override rather than setting one", function () {
    // "Theme default" is the empty choice: it returns the reader to whatever
    // their theme brings, which means removing the attribute, not writing "".
    T.applyTypeface("rosepine");

    T.applyTypeface("");

    expect(document.documentElement.hasAttribute("data-typeface")).toBe(false);
    expect(localStorage.getItem(T.TYPEFACE_KEY)).toBeNull();
  });

  it("survives a localStorage that refuses to be written", function () {
    const restore = breakStorage("setItem");
    try {
      expect(T.applyTypeface("rosepine")).toBe(true);
      expect(document.documentElement.getAttribute("data-typeface")).toBe(
        "rosepine"
      );
    } finally {
      restore();
    }
  });

  it("survives a localStorage that refuses to be cleared", function () {
    const restore = breakStorage("removeItem");
    try {
      expect(T.applyTypeface("")).toBe(true);
    } finally {
      restore();
    }
  });
});


describe("wireTypefacePicker", function () {
  beforeEach(function () {
    document.documentElement.removeAttribute("data-typeface");
    localStorage.clear();
  });

  it("applies the pairing that is chosen", function () {
    const inputs = mountTypefaces(["rosepine", "nord"]);
    T.wireTypefacePicker(document);

    inputs[1].checked = true;
    inputs[1].dispatchEvent(new Event("change"));

    expect(document.documentElement.getAttribute("data-typeface")).toBe(
      "rosepine"
    );
  });

  it("ticks the saved pairing", function () {
    localStorage.setItem(T.TYPEFACE_KEY, "nord");
    const inputs = mountTypefaces(["rosepine", "nord"]);

    T.wireTypefacePicker(document);

    expect(inputs.find((i) => i.value === "nord").checked).toBe(true);
  });

  it("ticks Theme default when nothing is saved", function () {
    const inputs = mountTypefaces(["rosepine"]);

    T.wireTypefacePicker(document);

    expect(inputs.find((i) => i.value === "").checked).toBe(true);
  });

  it("clears the override when Theme default is chosen", function () {
    const inputs = mountTypefaces(["rosepine"]);
    T.wireTypefacePicker(document);
    inputs[1].checked = true;
    inputs[1].dispatchEvent(new Event("change"));

    inputs[0].checked = true;
    inputs[0].dispatchEvent(new Event("change"));

    expect(document.documentElement.hasAttribute("data-typeface")).toBe(false);
  });

  it("does not double-bind when wired twice", function () {
    const inputs = mountTypefaces(["rosepine"]);
    T.wireTypefacePicker(document);

    expect(T.wireTypefacePicker(document)).toBe(0);
  });

  it("wires nothing on a page without the picker", function () {
    // Which is every page but the appearance one, and the appearance page
    // itself for a reader below the tier.
    document.body.innerHTML = "";

    expect(T.wireTypefacePicker(document)).toBe(0);
  });

  it("defaults to the whole document when called with no root", function () {
    mountTypefaces(["rosepine"]);

    expect(T.wireTypefacePicker()).toBe(2);
  });

  it("survives a localStorage that refuses to be read", function () {
    mountTypefaces(["rosepine"]);
    const restore = breakStorage("getItem");
    try {
      expect(T.wireTypefacePicker(document)).toBe(2);
    } finally {
      restore();
    }
  });
});

/*
 * The appearance page's three tabs are radio inputs with Dark checked in the
 * markup, so a reader on a light theme would land on a panel their theme is
 * not in, with nothing to say it is one tab away.
 */
describe("selectSchemeTab", () => {
  /** The shape profile_appearance.html renders. */
  function mountTabs() {
    document.body.innerHTML = `
      <div role="tablist" id="id-appearance-tabs">
        <input type="radio" name="appearance-tab" id="id-tab-dark"
               data-tab-scheme="Dark" checked>
        <div role="tabpanel">
          <input type="radio" name="theme-dropdown" value="asastats-dark">
          <input type="radio" name="theme-dropdown" value="mocha">
        </div>
        <input type="radio" name="appearance-tab" id="id-tab-light"
               data-tab-scheme="Light">
        <div role="tabpanel">
          <input type="radio" name="theme-dropdown" value="asastats">
          <input type="radio" name="theme-dropdown" value="latte">
        </div>
      </div>`;
  }

  beforeEach(() => {
    document.documentElement.removeAttribute("data-theme");
    localStorage.clear();
  });

  it("opens Light when a light theme is active", () => {
    mountTabs();
    T.applyTheme("latte");

    expect(T.selectSchemeTab(document)).toBe("Light");
    expect(document.getElementById("id-tab-light").checked).toBe(true);
  });

  it("opens Dark when a dark theme is active", () => {
    mountTabs();
    T.applyTheme("mocha");

    expect(T.selectSchemeTab(document)).toBe("Dark");
    expect(document.getElementById("id-tab-dark").checked).toBe(true);
  });

  it("leaves the markup's own choice alone with no theme set", () => {
    mountTabs();

    expect(T.selectSchemeTab(document)).toBe("");
    expect(document.getElementById("id-tab-dark").checked).toBe(true);
  });

  it("does nothing for a theme that is no longer offered", () => {
    // A theme culled from settings can still be sitting in localStorage.
    mountTabs();
    T.applyTheme("catppuccin");

    expect(T.selectSchemeTab(document)).toBe("");
  });

  it("does nothing on a page with no tabs", () => {
    // Which is every page but this one -- the header picker has no panels.
    document.body.innerHTML =
      '<input type="radio" name="theme-dropdown" value="latte">';
    T.applyTheme("latte");

    expect(T.selectSchemeTab(document)).toBe("");
  });

  it("ignores a panel that is not preceded by a tab", () => {
    document.body.innerHTML = `
      <div role="tabpanel">
        <input type="radio" name="theme-dropdown" value="latte">
      </div>`;
    T.applyTheme("latte");

    expect(T.selectSchemeTab(document)).toBe("");
  });

  it("still opens a tab that carries no scheme label", () => {
    // The Fonts tab has no `data-tab-scheme`; the label is for reporting, and
    // its absence must not stop the tab being selected.
    document.body.innerHTML = `
      <div role="tablist">
        <input type="radio" name="appearance-tab" id="id-tab-x">
        <div role="tabpanel">
          <input type="radio" name="theme-dropdown" value="latte">
        </div>
      </div>`;
    T.applyTheme("latte");

    expect(T.selectSchemeTab(document)).toBe("");
    expect(document.getElementById("id-tab-x").checked).toBe(true);
  });

  it("defaults to the document when given no root", () => {
    mountTabs();
    T.applyTheme("latte");

    expect(T.selectSchemeTab()).toBe("Light");
  });
});

/*
 * The dropdown offers ten themes, and promotes what this browser actually uses
 * above them. The tally is localStorage only, like the theme it ranks: one
 * that synced while the theme did not would order the menu by a history this
 * browser never had.
 */
describe("theme usage", () => {
  beforeEach(() => {
    document.documentElement.removeAttribute("data-theme");
    localStorage.clear();
  });

  describe("countThemeUse", () => {
    it("counts the theme in use", () => {
      T.applyTheme("mocha");

      expect(T.countThemeUse()).toBe(1);
      expect(T.themeUsage()).toEqual({ mocha: 1 });
    });

    it("counts a theme once however many pages follow", () => {
      // The count means "chosen and kept", not "page views".
      T.applyTheme("mocha");
      T.countThemeUse();

      expect(T.countThemeUse()).toBe(0);
      expect(T.themeUsage()).toEqual({ mocha: 1 });
    });

    it("counts again when the reader changes theme and comes back", () => {
      T.applyTheme("mocha");
      T.countThemeUse();
      T.applyTheme("latte");
      T.countThemeUse();
      T.applyTheme("mocha");

      expect(T.countThemeUse()).toBe(2);
      expect(T.themeUsage()).toEqual({ mocha: 2, latte: 1 });
    });

    it("counts nothing when no theme is set", () => {
      expect(T.countThemeUse()).toBe(0);
      expect(T.themeUsage()).toEqual({});
    });

    it("survives a tally that is not an object", () => {
      // Another tab, an older version, or a person with devtools open.
      localStorage.setItem(T.USAGE_KEY, '"nonsense"');
      T.applyTheme("mocha");

      expect(T.countThemeUse()).toBe(1);
      expect(T.themeUsage()).toEqual({ mocha: 1 });
    });

    it("survives a tally that is an array", () => {
      localStorage.setItem(T.USAGE_KEY, "[1,2,3]");

      expect(T.themeUsage()).toEqual({});
    });

    it("survives a tally that is not valid JSON", () => {
      localStorage.setItem(T.USAGE_KEY, "{nope");

      expect(T.themeUsage()).toEqual({});
    });

    it("ignores a non-numeric count for a theme", () => {
      localStorage.setItem(T.USAGE_KEY, '{"mocha":"lots"}');
      T.applyTheme("mocha");

      expect(T.countThemeUse()).toBe(1);
    });
  });

  describe("when localStorage refuses", () => {
    // Private browsing and quota limits. The theme still applies and the page
    // still works; only the ordering of the menu is lost, which is the least
    // important thing here.
    it("counts nothing when the tally cannot be read", () => {
      T.applyTheme("mocha");
      const restore = breakStorage("getItem", "denied");

      try {
        expect(T.countThemeUse()).toBe(0);
      } finally {
        restore();
      }
    });

    it("counts nothing when the tally cannot be written", () => {
      T.applyTheme("mocha");
      const restore = breakStorage("setItem", "quota");

      try {
        expect(T.countThemeUse()).toBe(0);
      } finally {
        restore();
      }
    });
  });

  describe("recentThemes", () => {
    it("returns the most used first", () => {
      localStorage.setItem(T.USAGE_KEY, '{"latte":1,"mocha":5,"nord":3}');

      expect(T.recentThemes(3)).toEqual(["mocha", "nord", "latte"]);
    });

    it("honours the limit", () => {
      localStorage.setItem(T.USAGE_KEY, '{"latte":1,"mocha":5,"nord":3}');

      expect(T.recentThemes(2)).toEqual(["mocha", "nord"]);
    });

    it("breaks ties by name so the order does not wander", () => {
      localStorage.setItem(T.USAGE_KEY, '{"nord":2,"latte":2}');

      expect(T.recentThemes(2)).toEqual(["latte", "nord"]);
    });

    it("breaks ties by name whichever way the keys were stored", () => {
      // The other ordering of the same tie, so the comparison is exercised in
      // both directions rather than however this browser enumerated the keys.
      localStorage.setItem(T.USAGE_KEY, '{"latte":2,"nord":2}');

      expect(T.recentThemes(2)).toEqual(["latte", "nord"]);
    });

    it("skips themes with no uses", () => {
      localStorage.setItem(T.USAGE_KEY, '{"latte":0,"mocha":2}');

      expect(T.recentThemes(3)).toEqual(["mocha"]);
    });

    it("returns nothing when nothing has been used", () => {
      expect(T.recentThemes(3)).toEqual([]);
    });
  });

  describe("wireRecentThemes", () => {
    /** The shape snippets/theme_picker.html renders. */
    function mountDropdown() {
      document.body.innerHTML = `
        <ul id="id-theme-list" data-recent-shown="3">
          <li id="id-theme-recent-title" hidden>Recent</li>
          <li class="group">Light</li>
          <li><input type="radio" name="theme-dropdown" value="asastats" aria-label="asastats"></li>
          <li><input type="radio" name="theme-dropdown" value="latte" aria-label="latte"></li>
          <li class="group">Dark</li>
          <li><input type="radio" name="theme-dropdown" value="asastats-dark" aria-label="asastats-dark"></li>
        </ul>`;
    }

    /** Theme values in the Recent group, in the order they appear. */
    function recentValues() {
      return [...document.querySelectorAll("[data-theme-recent] input")].map(
        (i) => i.value
      );
    }

    it("stays hidden until something has been used", () => {
      mountDropdown();

      expect(T.wireRecentThemes(document)).toBe(0);
      expect(document.getElementById("id-theme-recent-title").hidden).toBe(true);
    });

    it("promotes used themes, most used first", () => {
      mountDropdown();
      localStorage.setItem(T.USAGE_KEY, '{"latte":1,"mocha":5,"nord":3}');

      expect(T.wireRecentThemes(document)).toBe(3);
      expect(recentValues()).toEqual(["mocha", "nord", "latte"]);
      expect(document.getElementById("id-theme-recent-title").hidden).toBe(false);
    });

    it("clones an entry for a theme the dropdown does not list", () => {
      // mocha is not among the ten defaults, so its row has to be made.
      mountDropdown();
      localStorage.setItem(T.USAGE_KEY, '{"mocha":2}');

      T.wireRecentThemes(document);
      const input = document.querySelector("[data-theme-recent] input");

      expect(input.value).toBe("mocha");
      expect(input.getAttribute("aria-label")).toBe("mocha");
    });

    it("moves a listed theme rather than duplicating it", () => {
      // Two radios sharing a name and a value are one control rendered twice,
      // and they fight over which shows as chosen.
      mountDropdown();
      localStorage.setItem(T.USAGE_KEY, '{"latte":2}');

      T.wireRecentThemes(document);

      expect(
        document.querySelectorAll(
          'input[name="theme-dropdown"][value="latte"]'
        ).length
      ).toBe(1);
    });

    it("leaves a promoted clone wirable", () => {
      // The clone inherits the prototype's bound flag; if it is not cleared,
      // wireThemePicker skips it and the entry does nothing when clicked.
      mountDropdown();
      T.wireThemePicker(document);
      localStorage.setItem(T.USAGE_KEY, '{"mocha":2}');

      T.wireRecentThemes(document);
      T.wireThemePicker(document);
      document
        .querySelector('[data-theme-recent] input[value="mocha"]')
        .dispatchEvent(new Event("change"));

      expect(document.documentElement.getAttribute("data-theme")).toBe("mocha");
    });

    it("does not stack duplicates when run again", () => {
      // An htmx swap re-runs the wiring over a list it already filled.
      mountDropdown();
      localStorage.setItem(T.USAGE_KEY, '{"mocha":2}');

      T.wireRecentThemes(document);
      T.wireRecentThemes(document);

      expect(recentValues()).toEqual(["mocha"]);
    });

    it("honours the count the template asks for", () => {
      mountDropdown();
      document.getElementById("id-theme-list").dataset.recentShown = "1";
      localStorage.setItem(T.USAGE_KEY, '{"latte":1,"mocha":5,"nord":3}');

      expect(T.wireRecentThemes(document)).toBe(1);
      expect(recentValues()).toEqual(["mocha"]);
    });

    it("promotes nothing when the template names no count", () => {
      // A dropdown rendered without data-recent-shown asks for no Recent
      // group; it must not silently pick a number of its own.
      mountDropdown();
      delete document.getElementById("id-theme-list").dataset.recentShown;
      localStorage.setItem(T.USAGE_KEY, '{"mocha":2}');

      expect(T.wireRecentThemes(document)).toBe(0);
      expect(document.getElementById("id-theme-recent-title").hidden).toBe(true);
    });

    it("does nothing on a page with no dropdown", () => {
      document.body.innerHTML = "";

      expect(T.wireRecentThemes(document)).toBe(0);
    });

    it("does nothing when the list has no entry to clone from", () => {
      document.body.innerHTML = `
        <ul id="id-theme-list" data-recent-shown="3">
          <li id="id-theme-recent-title" hidden>Recent</li>
        </ul>`;
      localStorage.setItem(T.USAGE_KEY, '{"mocha":2}');

      expect(T.wireRecentThemes(document)).toBe(0);
    });

    it("defaults to the document when given no root", () => {
      mountDropdown();
      localStorage.setItem(T.USAGE_KEY, '{"mocha":2}');

      expect(T.wireRecentThemes()).toBe(1);
    });
  });
});
