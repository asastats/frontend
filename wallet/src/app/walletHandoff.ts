/**
 * @file Say so when the phone closed the app behind a wallet.
 *
 * MIUI kills the WebView while Pera or Defly is open, and the app starts over
 * with the wallet step lost. See docs/logbook.md.
 */

import { App } from "@capacitor/app";

import { forgetReturn } from "./returnPage";

/** localStorage key: `{id, name, url, at}` of the wallet step in progress. */
export const HANDOFF_KEY = "asastats.walletHandoff";

/** localStorage key: the wallet `{id, name}` to explain on the next page. */
export const NOTICE_KEY = "asastats.walletNotice";

/** sessionStorage key: set once this WebView has loaded a page; gone after a restart. */
export const ALIVE_KEY = "asastats.alive";

/** How long after the wallet opened a fresh start still explains it. */
export const HANDOFF_FOR_MS = 10 * 60 * 1000;

/** Buttons that hand over to the wallet (walletComponent.ts ids). */
const HANDOFF_BUTTONS = '[id^="connect-button-"], [id^="auth-button-"]';

/** The wallet a hand-off was made to. */
export interface HandoffWallet {
  id: string;
  name: string;
}

/** What `installHandoff` reads from the window. */
export type HandoffWindow = Pick<Window, "localStorage" | "sessionStorage" | "document"> & {
  location: Pick<Location, "href" | "origin" | "replace">;
};

/**
 * The wallet behind a tapped hand-off button, or null for any other click.
 *
 * @param target - the clicked element.
 * @returns the wallet's id and card title.
 */
export function handoffWallet(target: EventTarget | null): HandoffWallet | null {
  if (!(target instanceof Element)) return null;
  const button = target.closest(HANDOFF_BUTTONS);
  if (!button) return null;
  const id = button.id.replace(/^(connect|auth)-button-/, "");
  const name = button.ownerDocument
    .getElementById(`wallet-${id}`)
    ?.querySelector(".card-title")
    ?.textContent?.trim();
  return { id, name: name || "your wallet" };
}

/**
 * Note that the reader is about to leave for `wallet`.
 *
 * @param wallet - the wallet.
 * @param url - the page it was opened from.
 * @param storage - where to keep it.
 * @param now - the time, in ms.
 */
export function rememberHandoff(
  wallet: HandoffWallet,
  url: string,
  storage: Storage,
  now: number
): void {
  try {
    storage.setItem(HANDOFF_KEY, JSON.stringify({ ...wallet, url, at: now }));
  } catch {
    // storage blocked: no explanation after a restart, as before
  }
}

/**
 * Drop the noted hand-off.
 *
 * @param storage - where it is kept.
 */
export function forgetHandoff(storage: Storage): void {
  try {
    storage.removeItem(HANDOFF_KEY);
  } catch {
    // nothing to drop
  }
}

/**
 * Return the interrupted hand-off, if this load is the app starting over.
 *
 * Reads the noted hand-off once and drops it; marks this WebView as alive.
 *
 * @param storage - localStorage.
 * @param session - sessionStorage, which a restart empties.
 * @param origin - this site's origin.
 * @param now - the time, in ms.
 * @returns the wallet and the page to go back to, or null.
 */
export function handoffTarget(
  storage: Storage,
  session: Storage,
  origin: string,
  now: number
): (HandoffWallet & { url: string }) | null {
  let alive: boolean;
  let saved: { id?: unknown; name?: unknown; url?: unknown; at?: unknown } | null;
  try {
    alive = session.getItem(ALIVE_KEY) !== null;
    session.setItem(ALIVE_KEY, "1");
    saved = JSON.parse(storage.getItem(HANDOFF_KEY) || "null");
  } catch {
    return null;
  }
  forgetHandoff(storage);
  // a page change in the same WebView, not a restart
  if (alive || !saved) return null;
  const { id, name, url, at } = saved;
  if (typeof id !== "string" || typeof name !== "string") return null;
  if (typeof url !== "string" || typeof at !== "number") return null;
  if (now < at || now - at > HANDOFF_FOR_MS) return null;
  try {
    if (new URL(url).origin !== origin) return null;
  } catch {
    return null;
  }
  return { id, name, url };
}

/**
 * Explain the lost wallet step in the wallet's card, or at the top of the page.
 *
 * @param doc - the page.
 * @param wallet - the wallet that was open.
 * @returns the notice, or null when the page has nowhere to put it.
 */
export function showHandoffNotice(doc: Document, wallet: HandoffWallet): HTMLElement | null {
  const card = doc.getElementById(`wallet-${wallet.id}`);
  const host = card && card.getClientRects().length > 0 ? card : doc.querySelector("main");
  if (!host) return null;
  const notice = doc.createElement("div");
  notice.dataset.notice = "info";
  notice.setAttribute("role", "status");
  notice.textContent =
    `Your phone closed ASA Stats while ${wallet.name} was open, so that step did not finish. ` +
    "Please connect again.";
  if (host === card) host.appendChild(notice);
  else host.prepend(notice);
  return notice;
}

/**
 * Note wallet hand-offs; after a restart go back to their page and explain.
 *
 * @param target - the window.
 * @param now - the time, in ms.
 * @returns whether the page is being replaced.
 */
export function installHandoff(target: HandoffWindow = window, now: number = Date.now()): boolean {
  const storage = target.localStorage;
  target.document.addEventListener(
    "click",
    (event) => {
      const wallet = handoffWallet(event.target);
      if (wallet) rememberHandoff(wallet, target.location.href, storage, Date.now());
    },
    true
  );
  void App.addListener("resume", () => forgetHandoff(storage));

  let pending: HandoffWallet | null = null;
  try {
    pending = JSON.parse(storage.getItem(NOTICE_KEY) || "null");
    storage.removeItem(NOTICE_KEY);
  } catch {
    pending = null;
  }
  if (pending && typeof pending.id === "string" && typeof pending.name === "string") {
    showHandoffNotice(target.document, pending);
  }

  const lost = handoffTarget(storage, target.sessionStorage, target.location.origin, now);
  if (!lost) return false;
  const wallet = { id: lost.id, name: lost.name };
  if (lost.url === target.location.href) {
    showHandoffNotice(target.document, wallet);
    return false;
  }
  try {
    storage.setItem(NOTICE_KEY, JSON.stringify(wallet));
  } catch {
    return false;
  }
  // this page wins over the browser sheet's remembered one
  forgetReturn(storage);
  target.location.replace(lost.url);
  return true;
}
