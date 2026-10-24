/**
 * @file Links that open the app: Universal Links and App Links to the site.
 */

import { App, type URLOpenListenerEvent } from "@capacitor/app";

/**
 * Open `event.url` in the WebView if it is a page of this site.
 *
 * @param event - from the App plugin.
 * @param origin - the site's origin.
 * @param navigate - goes to the URL.
 * @returns whether the URL was followed.
 */
export function handleAppUrl(
  event: URLOpenListenerEvent,
  origin: string,
  navigate: (url: string) => void
): boolean {
  let url: URL;
  try {
    url = new URL(event.url);
  } catch {
    return false;
  }
  if (url.origin !== origin) return false;
  navigate(url.href);
  return true;
}

/**
 * Follow links to the site that the OS hands to the app.
 *
 * @param navigate - goes to the URL.
 */
export function installDeepLinks(
  navigate: (url: string) => void = (url) => window.location.assign(url)
): void {
  void App.addListener("appUrlOpen", (event) =>
    handleAppUrl(event, window.location.origin, navigate)
  );
}
