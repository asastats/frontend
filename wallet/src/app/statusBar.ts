/**
 * @file Status bar icons that stay readable on the active theme.
 *
 * The page draws under the status bar (edge-to-edge), so the icons have to
 * contrast with the page's own background. `Style.Dark` means light icons, for
 * dark backgrounds.
 */

import { StatusBar, Style } from "@capacitor/status-bar";

/**
 * Linear sRGB of an `oklch(L C H)` colour, clamped to the sRGB gamut.
 *
 * @param color - a computed colour; WebKit and Chrome return daisyUI themes in oklch.
 * @returns [r, g, b] in 0..1, or null when it is not oklch.
 */
export function oklchToLinear(color: string): [number, number, number] | null {
  const parts = /oklch\(\s*([\d.]+)(%?)\s+([\d.]+)\s+([\d.]+)/.exec(color);
  if (!parts) return null;
  const lightness = Number(parts[1]) / (parts[2] ? 100 : 1);
  const chroma = Number(parts[3]);
  const hue = (Number(parts[4]) * Math.PI) / 180;
  const a = chroma * Math.cos(hue);
  const b = chroma * Math.sin(hue);
  const l = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (lightness - 0.0894841775 * a - 1.291485548 * b) ** 3;
  const clamp = (value: number) => Math.min(1, Math.max(0, value));
  return [
    clamp(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
    clamp(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
    clamp(-0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s),
  ];
}

/**
 * Return whether a CSS colour is dark, by relative luminance.
 *
 * @param color - a computed colour, `rgb(...)`, `rgba(...)` or `oklch(...)`.
 * @returns true for a dark colour; false when it cannot be read.
 */
export function isDark(color: string): boolean {
  let linear = oklchToLinear(color);
  if (!linear) {
    const parts = /rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)/.exec(color);
    if (!parts) return false;
    linear = parts.slice(1, 4).map((value) => {
      const c = Number(value) / 255;
      return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    }) as [number, number, number];
  }
  const [r, g, b] = linear;
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
