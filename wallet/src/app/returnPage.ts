/**
 * @file Back to the page the reader left for another site.
 *
 * Android can destroy the app while the browser sheet is up, and Capacitor
 * then starts again at the site's root. See docs/logbook.md.
 */

import { App } from "@capacitor/app";
import { Browser } from "@capacitor/browser";

/** localStorage key: `{url, at}` of the page the browser sheet was opened from. */
export const RETURN_KEY = "asastats.return";

/** How long after opening the sheet a fresh start still goes back. */
export const RETURN_FOR_MS = 30 * 60 * 1000;

/** What `installReturn` reads from the window. */
export type ReturnWindow = Pick<Window, "localStorage"> & {
  location: Pick<Location, "href" | "origin" | "pathname" | "search" | "replace">;
};

/**
 * Remember `url` as the page to come back to.
 *
 * @param url - the page the sheet is opened from.
 * @param storage - where to keep it.
 * @param now - the time, in ms.
 */
export function rememberReturn(
  url: string,
  storage: Storage = window.localStorage,
  now: number = Date.now()
): void {
  try {
    storage.setItem(RETURN_KEY, JSON.stringify({ url, at: now }));
  } catch {
    // storage full or blocked: the reader lands on the root, as before
  }
}

/**
 * Drop the remembered page.
 *
 * @param storage - where it is kept.
 */
export function forgetReturn(storage: Storage = window.localStorage): void {
  try {
    storage.removeItem(RETURN_KEY);
  } catch {
    // nothing to drop
  }
}

/**
 * Return the page to go back to, if this load is the app starting over.
 *
 * Reads the remembered page once and drops it.
 *
 * @param location - where the WebView is now.
 * @param storage - where the page is kept.
 * @param now - the time, in ms.
 * @returns a same-site URL, or null to stay.
 */
export function returnTarget(
  location: ReturnWindow["location"],
  storage: Storage,
  now: number
): string | null {
  let saved: { url?: unknown; at?: unknown } | null;
  try {
    saved = JSON.parse(storage.getItem(RETURN_KEY) || "null");
  } catch {
    saved = null;
  }
  forgetReturn(storage);
  if (!saved || typeof saved.url !== "string" || typeof saved.at !== "number") return null;
  // Capacitor starts over at the root, never anywhere else
  if (location.pathname !== "/" || location.search) return null;
  if (now < saved.at || now - saved.at > RETURN_FOR_MS) return null;
  let url: URL;
  try {
    url = new URL(saved.url);
  } catch {
    return null;
  }
  if (url.origin !== location.origin || url.href === location.href) return null;
  return url.href;
}

/**
 * Go back to the remembered page on a fresh start; forget it on a normal return.
 *
 * @param target - the window.
 * @param now - the time, in ms.
 * @returns whether the page is being replaced.
 */
export function installReturn(target: ReturnWindow = window, now: number = Date.now()): boolean {
  const url = returnTarget(target.location, target.localStorage, now);
  const forget = () => forgetReturn(target.localStorage);
  void App.addListener("resume", forget);
  void Browser.addListener("browserFinished", forget);
  if (!url) return false;
  target.location.replace(url);
  return true;
}
