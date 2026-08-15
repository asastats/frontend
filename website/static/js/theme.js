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
 */
(function () {
  "use strict";

  /** localStorage key shared with the inline head script in base_tw.html. */
  var STORAGE_KEY = "theme";

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
      wireThemePicker: wireThemePicker,
    };
  } else {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", function () {
        wireThemePicker(document);
      });
    } else {
      wireThemePicker(document);
    }
    // The header can be replaced by an htmx swap; re-tick and re-bind after one.
    document.body.addEventListener("htmx:afterSwap", function () {
      wireThemePicker(document);
    });
  }
})();
