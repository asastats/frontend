/**
 * @file Status bar icons that stay readable on the active theme.
 *
 * The page draws under the status bar (edge-to-edge), so the icons have to
 * contrast with the page's own background. `Style.Dark` means light icons, for
 * dark backgrounds.
 */

import { StatusBar, Style } from "@capacitor/status-bar";

/**
 * Return whether a CSS colour is dark, by relative luminance.
 *
 * @param color - a computed colour, `rgb(...)` or `rgba(...)`.
 * @returns true for a dark colour; false when it cannot be read.
 */
export function isDark(color: string): boolean {
  const parts = /rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)/.exec(color);
  if (!parts) return false;
  const [r, g, b] = parts.slice(1, 4).map((value) => {
    const c = Number(value) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  // 0.179: where white and black text have equal contrast (WCAG).
  return 0.2126 * r + 0.7152 * g + 0.0722 * b < 0.179;
}

/**
 * Match the status bar to the body's background now.
 *
 * @param doc - the document.
 */
export function syncStatusBar(doc: Document = document): void {
  const view = doc.defaultView ?? window;
  const background = view.getComputedStyle(doc.body).backgroundColor;
  void StatusBar.setStyle({ style: isDark(background) ? Style.Dark : Style.Light });
}

/**
 * Sync now and whenever theme.js switches the theme (`data-theme` on `<html>`).
 *
 * @param doc - the document.
 * @returns the observer, for tests.
 */
export function installStatusBar(doc: Document = document): MutationObserver {
  syncStatusBar(doc);
  const observer = new MutationObserver(() => syncStatusBar(doc));
  observer.observe(doc.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  return observer;
}
