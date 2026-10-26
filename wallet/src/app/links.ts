/**
 * @file Where a tapped link goes inside the app.
 *
 * Another site opens in the in-app browser sheet, never in place of the app's
 * page. A same-site link with `target="_blank"` opens in place: the app has
 * no tabs. Other schemes (`mailto:`, `tel:`, wallet hand-offs) are left to the
 * WebView, which passes them to the OS.
 */

import { Browser } from "@capacitor/browser";

import { rememberReturn } from "./returnPage";

/** What to do with a tapped link. */
export type LinkAction = "browser" | "in-place" | "default";

/**
 * Decide what a tap on `anchor` should do.
 *
 * @param anchor - the tapped link.
 * @param origin - the site's origin, e.g. `https://www.asastats.com`.
 * @returns the action.
 */
export function classifyLink(anchor: HTMLAnchorElement, origin: string): LinkAction {
  let url: URL;
  try {
    url = new URL(anchor.href);
  } catch {
    return "default";
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") return "default";
  if (url.origin !== origin) return "browser";
  return anchor.target === "_blank" ? "in-place" : "default";
}

/**
 * Handle one click, if it is a plain tap on a link this module owns.
 *
 * @param event - the click.
 * @param origin - the site's origin.
 * @param navigate - goes to a same-site URL in place.
 * @returns whether the click was taken over.
 */
export function handleLinkClick(
  event: MouseEvent,
  origin: string,
  navigate: (url: string) => void
): boolean {
  if (event.defaultPrevented || event.button !== 0) return false;
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
  const anchor = (event.target as Element | null)?.closest?.("a[href]");
  if (!(anchor instanceof HTMLAnchorElement)) return false;
  if (anchor.hasAttribute("data-app-download") || anchor.hasAttribute("download")) {
    return false;
  }

  const action = classifyLink(anchor, origin);
  if (action === "default") return false;
  event.preventDefault();
  if (action === "browser") {
    rememberReturn(window.location.href);
    void Browser.open({ url: anchor.href });
  } else {
    navigate(anchor.href);
  }
  return true;
}

/**
 * Take over link taps on `doc`.
 *
 * Bubble phase, so a page script that handles its own link first wins.
 *
 * @param doc - the document to listen on.
 * @param navigate - goes to a same-site URL in place.
 */
export function installLinks(
  doc: Document = document,
  navigate: (url: string) => void = (url) => window.location.assign(url)
): void {
  doc.addEventListener("click", (event) => {
    handleLinkClick(event, window.location.origin, navigate);
  });
}
