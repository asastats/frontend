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
      selectSchemeTab: selectSchemeTab,
      wireThemeToggle: wireThemeToggle,
      wireThemePicker: wireThemePicker,
    };
  } else {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", function () {
        wireThemePicker(document);
        wireThemeToggle(document);
        wireTypefacePicker(document);
        selectSchemeTab(document);
      });
    } else {
      wireThemePicker(document);
      wireThemeToggle(document);
      wireTypefacePicker(document);
      selectSchemeTab(document);
    }
    // The header can be replaced by an htmx swap; re-tick and re-bind after one.
    document.body.addEventListener("htmx:afterSwap", function () {
      wireThemePicker(document);
      wireThemeToggle(document);
      wireTypefacePicker(document);
      selectSchemeTab(document);
    });
  }
})();
