/**
 * @file DaisyUI appearance picker
 * @author Ivica Paleka
 * @description Records the viewer's chosen theme and applies it to
 * `<html data-theme="...">`. The *first* application happens inline in the
 * document head, before the stylesheet paints, so there is no flash of the
 * default theme; this file only handles the picker itself and the writing.
 *
 * The theme is a client-side preference and is never sent to the server. The
 * list of themes offered comes from `settings.AVAILABLE_THEMES` via the
 * template, so this file never needs to know the names.
 *
 * Two controls share this file, because a signed-out reader gets a smaller
 * choice than a signed-in one:
 *
 *   * `[data-theme-toggle]` -- a plain light/dark switch, the only appearance
 *     control an anonymous reader sees. It flips between the two brand themes
 *     and nothing else;
 *   * `input[name=theme-dropdown]` -- the full list, for signed-in readers.
 *
 * The pair the toggle flips between is read from the button's own data
 * attributes rather than written here, so the brand theme names live in
 * settings and templates only.
 */
(function () {
  "use strict";

  /** localStorage key shared with the inline head script in base.html. */
  var STORAGE_KEY = "theme";

  /** The reader's typeface override, if they have chosen one. */
  var TYPEFACE_KEY = "typeface";

  /**
   * Apply `theme` to the document and remember it.
   *
   * @param {string} theme - a theme name registered in input.css
   * @returns {boolean} whether anything was applied
   */
  function applyTheme(theme) {
    if (!theme) return false;
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) {
      // Private-browsing quota rules can refuse the write. The theme still
      // applies for this page; it just will not survive a reload.
    }
    return true;
  }

  /**
   * Apply `typeface` to the document and remember it.
   *
   * The value is a pairing name, which happens to be a theme name: each theme
   * brings a display and body face, and choosing a "typeface" is choosing to
   * borrow another theme's pair. `[data-typeface]` is written after the theme
   * blocks in the stylesheet, so it wins on source order.
   *
   * An empty value clears the override and returns the reader to whatever
   * their theme brings, which is what the "Theme default" choice does.
   *
   * @param {string} typeface - a pairing name, or "" to clear
   * @returns {boolean} whether anything was applied
   */
  function applyTypeface(typeface) {
    if (typeface) {
      document.documentElement.setAttribute("data-typeface", typeface);
    } else {
      document.documentElement.removeAttribute("data-typeface");
    }
    try {
      if (typeface) {
        localStorage.setItem(TYPEFACE_KEY, typeface);
      } else {
        localStorage.removeItem(TYPEFACE_KEY);
      }
    } catch (e) {
      // Private-browsing quota rules can refuse the write. The choice still
      // applies for this page; it just will not survive a reload.
    }
    return true;
  }

  /**
   * Wire the typeface picker, if this reader has one.
   *
   * The control is rendered only above a subscription tier, so on most pages
   * there is nothing to wire and this does nothing.
   *
   * @param {Document|Element} [root=document] - subtree to wire
   * @returns {number} how many inputs were wired this call
   */
  function wireTypefacePicker(root) {
    var host = root || document;
    var inputs = host.querySelectorAll("input[name='typeface-choice']");
    var saved = null;
    try {
      saved = localStorage.getItem(TYPEFACE_KEY);
    } catch (e) {
      saved = null;
    }

    var wired = 0;
    Array.prototype.forEach.call(inputs, function (input) {
      if (input.value === (saved || "")) input.checked = true;
      if (input.dataset.typefaceBound === "1") return;
      input.dataset.typefaceBound = "1";
      input.addEventListener("change", function () {
        applyTypeface(input.value);
      });
      wired += 1;
    });
    return wired;
  }

  /**
   * Return the theme currently applied, falling back to what was saved.
   *
   * @returns {string} the active theme name, or "" when none is set
   */
  function currentTheme() {
    var applied = document.documentElement.getAttribute("data-theme");
    if (applied) return applied;
    try {
      return localStorage.getItem(STORAGE_KEY) || "";
    } catch (e) {
      return "";
    }
  }

  /**
   * Wire the signed-out light/dark switch.
   *
   * The button carries its own pair in `data-theme-light` / `data-theme-dark`,
   * so this never hard-codes a brand theme name. Anything else that happens to
   * be applied -- a theme saved while signed in, then signed out -- counts as
   * "not the dark one", so the first click lands on dark rather than doing
   * nothing.
   *
   * @param {Document|Element} [root=document] - subtree to wire
   * @returns {number} how many toggles were wired this call
   */
  function wireThemeToggle(root) {
    var host = root || document;
    var toggles = host.querySelectorAll("[data-theme-toggle]");
    var wired = 0;

    Array.prototype.forEach.call(toggles, function (button) {
      var light = button.dataset.themeLight;
      var dark = button.dataset.themeDark;
      if (!light || !dark) return;

      // Reflect the state for a screen reader, and again after every click.
      var sync = function () {
        button.setAttribute(
          "aria-pressed", String(currentTheme() === dark)
        );
      };
      sync();

      if (button.dataset.themeBound === "1") return;
      button.dataset.themeBound = "1";
      button.addEventListener("click", function () {
        applyTheme(currentTheme() === dark ? light : dark);
        sync();
      });
      wired += 1;
    });
    return wired;
  }

  /** How often each theme has been chosen and kept, as {theme: count}. */
  var USAGE_KEY = "themeUsage";

  /** The last theme counted, so a count is not repeated on every page. */
  var COUNTED_KEY = "themeCounted";

  /**
   * Read the usage tally.
   *
   * @returns {Object} {theme: count}, empty when there is nothing to read
   */
  function themeUsage() {
    try {
      var raw = localStorage.getItem(USAGE_KEY);
      var parsed = raw ? JSON.parse(raw) : null;
      // Anything but an object means another tab, an older version or a person
      // with devtools open wrote something else here. Start over rather than
      // throw: this is a convenience, and it must never break the page.
      if (!parsed || typeof parsed !== "object" || parsed.constructor === Array) {
        return {};
      }
      return parsed;
    } catch (e) {
      return {};
    }
  }

  /**
   * Count the theme in use, once per change rather than once per page.
   *
   * Called on load, deliberately. The alternative is to count on the way out
   * -- `beforeunload` or `pagehide` -- which is unreliable on mobile, where a
   * tab is often killed without either firing.
   *
   * Counting at load time also gives the rule this exists for: flipping
   * through swatches on the appearance page fires no page load, so browsing
   * costs nothing, and the theme that survives a navigation is the one that
   * scores. A reader who then visits ten more pages adds nothing further,
   * which is why the count reads as "chosen and kept" rather than "page
   * views".
   *
   * Nothing here is sent to the server. The theme is a client-side preference,
   * so its tally belongs in the same place -- a tally that synced while the
   * theme did not would order the menu by a history this browser never had.
   *
   * @returns {number} the theme's new count, or 0 when nothing was counted
   */
  function countThemeUse() {
    var active = currentTheme();
    if (!active) return 0;

    try {
      if (localStorage.getItem(COUNTED_KEY) === active) return 0;
    } catch (e) {
      return 0;
    }

    var usage = themeUsage();
    var count = (typeof usage[active] === "number" ? usage[active] : 0) + 1;
    usage[active] = count;

    try {
      localStorage.setItem(USAGE_KEY, JSON.stringify(usage));
      localStorage.setItem(COUNTED_KEY, active);
    } catch (e) {
      // Quota or private browsing. The theme still applies; only the ordering
      // of the menu is lost, which is the least important thing here.
      return 0;
    }
    return count;
  }

  /**
   * Return the most-used themes, most first.
   *
   * @param {number} limit - how many to return
   * @returns {string[]} theme names, longest-serving first on a tie
   */
  function recentThemes(limit) {
    var usage = themeUsage();
    return Object.keys(usage)
      .filter(function (theme) {
        return typeof usage[theme] === "number" && usage[theme] > 0;
      })
      .sort(function (a, b) {
        // Ties resolve by name so the order is stable between loads rather
        // than depending on however the keys happened to be enumerated.
        return usage[b] - usage[a] || (a < b ? -1 : 1);
      })
      .slice(0, limit);
  }

  /**
   * Fill the dropdown's Recent group from what this browser has used.
   *
   * Items are cloned from one the template already rendered, so the markup for
   * a theme entry exists in exactly one place. A theme promoted into Recent is
   * removed from the list below, because two radios sharing a name and a value
   * are one control rendered twice -- they fight over which shows as chosen.
   *
   * @param {Document|Element} [root=document] - subtree to fill
   * @returns {number} how many themes were promoted
   */
  function wireRecentThemes(root) {
    var host = root || document;
    var list = host.querySelector("#id-theme-list");
    var title = host.querySelector("#id-theme-recent-title");
    if (!list || !title) return 0;

    // Clear a previous run, so an htmx swap does not stack duplicates.
    Array.prototype.forEach.call(
      list.querySelectorAll("[data-theme-recent]"),
      function (item) {
        item.remove();
      }
    );

    var limit = parseInt(list.dataset.recentShown, 10) || 0;
    var wanted = recentThemes(limit);
    if (!wanted.length) {
      title.hidden = true;
      return 0;
    }

    // The anchor moves with each insertion, so the group comes out in the
    // order `wanted` is in. Inserting each one after the title instead would
    // build the list backwards.
    var anchor = title;
    var promoted = 0;

    wanted.forEach(function (theme) {
      var existing = list.querySelector(
        "input[name='theme-dropdown'][value='" + theme + "']"
      );
      var item;
      if (existing) {
        // Already on the list: move its row up rather than clone it, which is
        // what keeps one theme from being two radios with the same value.
        item = existing.closest("li");
      } else {
        var prototypeInput = list.querySelector("input[name='theme-dropdown']");
        if (!prototypeInput) return;
        item = prototypeInput.closest("li").cloneNode(true);
        var input = item.querySelector("input");
        input.value = theme;
        input.setAttribute("aria-label", theme);
        input.checked = false;
        // The clone carries the prototype's bound flag; without clearing it
        // wireThemePicker would skip this input and the entry would be inert.
        delete input.dataset.themeBound;
      }
      item.dataset.themeRecent = "1";
      anchor.parentNode.insertBefore(item, anchor.nextSibling);
      anchor = item;
      promoted += 1;
    });

    title.hidden = false;
    return promoted;
  }

  /**
   * Open the appearance tab that holds the theme currently in use.
   *
   * The tabs are radio inputs with a fixed `checked` in the markup, so without
   * this the page always opens on Dark -- and a reader on a light theme lands
   * on a panel their theme is not in, with no sign that it is one tab away.
   *
   * Does nothing on pages with no tabs, which is every page but this one.
   *
   * @param {Document|Element} [root=document] - subtree to search
   * @returns {string} the scheme opened, or "" when nothing was changed
   */
  function selectSchemeTab(root) {
    var host = root || document;
    var active = currentTheme();
    if (!active) return "";

    var chosen = host.querySelector(
      "input[name='theme-dropdown'][value='" + active + "']"
    );
    if (!chosen) return "";

    // The panel is the tab input's next sibling, so the tab for a panel is
    // whichever tab input precedes it.
    var panel = chosen.closest && chosen.closest("[role='tabpanel']");
    if (!panel) return "";
    var tab = panel.previousElementSibling;
    if (!tab || tab.name !== "appearance-tab") return "";

    tab.checked = true;
    return tab.dataset.tabScheme || "";
  }

  /**
   * Wire the picker: tick the saved theme, and apply whatever is chosen.
   *
   * Idempotent, so it is safe to call again after an htmx swap replaces the
   * header. Guarded by a data flag rather than by removing listeners, which
   * would need a reference the caller does not keep.
   *
   * @param {Document|Element} [root=document] - subtree to wire
   * @returns {number} how many inputs were wired this call
   */
  function wireThemePicker(root) {
    var host = root || document;
    var inputs = host.querySelectorAll("input[name='theme-dropdown']");
    var saved = null;
    try {
      saved = localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      saved = null;
    }

    var wired = 0;
    Array.prototype.forEach.call(inputs, function (input) {
      if (saved && input.value === saved) input.checked = true;
      if (input.dataset.themeBound === "1") return;
      input.dataset.themeBound = "1";
      input.addEventListener("change", function () {
        applyTheme(input.value);
        // Close the disclosure the picker lives in, so the choice is visible.
        var menu = input.closest && input.closest("details");
        if (menu) menu.open = false;
      });
      wired += 1;
    });
    return wired;
  }

  /* istanbul ignore else -- in the browser we self-start; under jest we export */
  if (typeof module !== "undefined" && module.exports) {
    module.exports = {
      STORAGE_KEY: STORAGE_KEY,
      applyTheme: applyTheme,
      applyTypeface: applyTypeface,
      TYPEFACE_KEY: TYPEFACE_KEY,
      wireTypefacePicker: wireTypefacePicker,
      currentTheme: currentTheme,
      USAGE_KEY: USAGE_KEY,
      COUNTED_KEY: COUNTED_KEY,
      themeUsage: themeUsage,
      countThemeUse: countThemeUse,
      recentThemes: recentThemes,
      wireRecentThemes: wireRecentThemes,
      selectSchemeTab: selectSchemeTab,
      wireThemeToggle: wireThemeToggle,
      wireThemePicker: wireThemePicker,
    };
  } else {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", function () {
        countThemeUse();
        wireRecentThemes(document);
        wireThemePicker(document);
        wireThemeToggle(document);
        wireTypefacePicker(document);
        selectSchemeTab(document);
      });
    } else {
      countThemeUse();
      wireRecentThemes(document);
      wireThemePicker(document);
      wireThemeToggle(document);
      wireTypefacePicker(document);
      selectSchemeTab(document);
    }
    // The header can be replaced by an htmx swap; re-tick and re-bind after one.
    document.body.addEventListener("htmx:afterSwap", function () {
      wireRecentThemes(document);
      wireThemePicker(document);
      wireThemeToggle(document);
      wireTypefacePicker(document);
      selectSchemeTab(document);
    });
  }
})();
