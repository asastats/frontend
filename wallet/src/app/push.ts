/**
 * @file Alerts as native notifications, through Firebase Cloud Messaging.
 *
 * The alerts modal (widgets `alerts.js`) calls `enablePush` / `checkPush` with
 * the two device urls; they are kept in localStorage so a refreshed token and
 * a logout can reach the server from any page.
 */

import { App } from "@capacitor/app";
import { Capacitor, registerPlugin, type PluginListenerHandle } from "@capacitor/core";

/** The device register/unregister endpoints, from the modal's data attributes. */
export interface DeviceUrls {
  register: string;
  unregister: string;
}

/** What `enablePush` tells the modal. */
export interface PushResult {
  ok: boolean;
  message: string;
}

/**
 * The part of `@capacitor-firebase/messaging` this module calls.
 *
 * Declared here rather than imported: that package's web half imports the
 * Firebase SDK, which `app.js` must not pull in. See docs/logbook.md.
 */
export interface FirebaseMessagingPlugin {
  checkPermissions(): Promise<{ receive: string }>;
  requestPermissions(): Promise<{ receive: string }>;
  getToken(): Promise<{ token: string }>;
  deleteToken(): Promise<void>;
  addListener(
    eventName: "tokenReceived",
    listener: (event: { token: string }) => void
  ): Promise<PluginListenerHandle>;
  addListener(
    eventName: "notificationActionPerformed",
    listener: (event: { notification: { data?: unknown } }) => void
  ): Promise<PluginListenerHandle>;
}

export const FirebaseMessaging = registerPlugin<FirebaseMessagingPlugin>("FirebaseMessaging");

/** localStorage key holding the `DeviceUrls` once this device is on. */
export const STORAGE_KEY = "asastats.push";

/** allauth's logout; `ACCOUNT_LOGOUT_ON_GET` makes the link itself log out. */
export const LOGOUT_PATH = "/accounts/logout/";

export const MESSAGES = {
  on: "This device is on.",
  denied: "Notifications are off for ASA Stats. Turn them on in the phone's Settings.",
  refused: "The server refused this device.",
  failed: "Could not enable notifications.",
};

/**
 * Return the stored device urls, or null when this device was never turned on.
 *
 * @returns the urls, or null.
 */
export function storedUrls(): DeviceUrls | null {
  try {
    const urls = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    return urls && urls.register && urls.unregister ? urls : null;
  } catch {
    return null;
  }
}

/**
 * Read Django's CSRF cookie.
 *
 * @returns the token, or "".
 */
export function csrfToken(): string {
  const match = document.cookie.match(/(^|;)\s*csrftoken\s*=\s*([^;]+)/);
  return match ? match[2] : "";
}

/**
 * POST `body` as JSON with the CSRF header.
 *
 * @param url - same-site endpoint.
 * @param body - the payload.
 * @returns whether the server accepted it.
 */
async function post(url: string, body: object): Promise<boolean> {
  const response = await fetch(url, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
    body: JSON.stringify(body),
  });
  return response.ok;
}

/**
 * Send this device's token to the server.
 *
 * @param urls - the device endpoints.
 * @param token - the FCM registration token.
 * @returns whether it was stored.
 */
export async function register(urls: DeviceUrls, token: string): Promise<boolean> {
  const { version } = await App.getInfo();
  return post(urls.register, { token, platform: Capacitor.getPlatform(), app_version: version });
}

/**
 * Ask permission, get the token and register it; remember the urls on success.
 *
 * @param urls - the device endpoints.
 * @returns what happened, for the modal's state line.
 */
export async function enablePush(urls: DeviceUrls): Promise<PushResult> {
  try {
    const { receive } = await FirebaseMessaging.requestPermissions();
    if (receive !== "granted") return { ok: false, message: MESSAGES.denied };
    const { token } = await FirebaseMessaging.getToken();
    if (!(await register(urls, token))) return { ok: false, message: MESSAGES.refused };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(urls));
    return { ok: true, message: MESSAGES.on };
  } catch (error) {
    return { ok: false, message: (error as Error)?.message || MESSAGES.failed };
  }
}

/**
 * Re-register silently a device the reader turned on; never prompts.
 *
 * Android before 13 grants the permission at install, so a granted
 * permission alone is not the reader's consent.
 *
 * @param urls - the device endpoints.
 * @returns whether this device is on.
 */
export async function checkPush(urls: DeviceUrls): Promise<boolean> {
  if (!storedUrls()) return false;
  try {
    const { receive } = await FirebaseMessaging.checkPermissions();
    if (receive !== "granted") return false;
    const { token } = await FirebaseMessaging.getToken();
    if (!(await register(urls, token))) return false;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(urls));
    return true;
  } catch {
    return false;
  }
}

/**
 * Remove this device from the account and drop its token. Never throws: a
 * logout must go ahead even offline (the server re-homes the token anyway).
 */
export async function disablePush(): Promise<void> {
  const urls = storedUrls();
  localStorage.removeItem(STORAGE_KEY);
  if (!urls) return;
  try {
    const { token } = await FirebaseMessaging.getToken();
    await post(urls.unregister, { token });
    await FirebaseMessaging.deleteToken();
  } catch {
    // Nothing to do; see the docstring.
  }
}

/**
 * Return `href` if it is a page of this site, else null.
 *
 * @param href - from the notification's data.
 * @param origin - the site's origin.
 * @returns the absolute URL, or null.
 */
export function sameOriginUrl(href: unknown, origin: string): string | null {
  if (typeof href !== "string" || !href) return null;
  try {
    const url = new URL(href, origin);
    return url.origin === origin ? url.href : null;
  } catch {
    return null;
  }
}

/**
 * Whether `target` points at the logout page.
 *
 * @param target - a link's href or a form's action.
 * @returns true for `LOGOUT_PATH` on this origin.
 */
export function isLogout(target: string): boolean {
  const url = sameOriginUrl(target, window.location.origin);
  return url !== null && new URL(url).pathname === LOGOUT_PATH;
}

/**
 * Re-register refreshed tokens, open tapped notifications, unregister on logout.
 *
 * @param doc - the document to listen on.
 * @param navigate - goes to a URL.
 */
export function installPush(
  doc: Document = document,
  navigate: (url: string) => void = (url) => window.location.assign(url)
): void {
  void FirebaseMessaging.addListener("tokenReceived", ({ token }) => {
    const urls = storedUrls();
    if (urls) void register(urls, token).catch(() => false);
  });

  void FirebaseMessaging.addListener("notificationActionPerformed", ({ notification }) => {
    const data = notification?.data as { url?: unknown } | undefined;
    const url = sameOriginUrl(data?.url, window.location.origin);
    if (url) navigate(url);
  });

  doc.addEventListener("click", (event) => {
    if (event.defaultPrevented || event.button !== 0 || !storedUrls()) return;
    const anchor = (event.target as Element | null)?.closest?.("a[href]");
    if (!(anchor instanceof HTMLAnchorElement) || !isLogout(anchor.href)) return;
    event.preventDefault();
    void disablePush().then(() => navigate(anchor.href));
  });

  doc.addEventListener("submit", (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || event.defaultPrevented || !storedUrls()) return;
    if (!isLogout(form.action)) return;
    event.preventDefault();
    // `submit()` does not fire this listener again.
    void disablePush().then(() => form.submit());
  });
}
